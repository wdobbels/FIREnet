import pickle
from abc import ABC, abstractmethod  # abstract base class
import numpy as np
import pandas as pd
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import torch
from .modelbuilder import (build_pytorch_nnet, default_skorch_nnet, 
                           default_scaled_nnet)
from .preprocessing import LogNormaliser, FeatureSelect

def rmse(y_true, y_pred):
    return np.sqrt(mean_squared_error(y_true, y_pred))

def mean_chisq(ydiff_sq, y_err):
    return np.mean(ydiff_sq / np.square(y_err))

METRICS = {'r2': r2_score, 'mse': mean_squared_error,
           'rmse': rmse, 'mean_chisq': mean_chisq}

class SinglePredictor(ABC):
    """Single model, trained on one train/test split. 
    Either a regressor or uncertainty estimator. """

    def __init__(self, d_data):
        if d_data is None:
            with open('./data/d_data.pkl', 'rb') as ddf_file:
                d_data = pickle.load(ddf_file)
        self.d_data = d_data
        self.X, self.Y = None, None
        self.X_train, self.X_test = None, None
        self.Y_train, self.Y_test = None, None
        self.log_normaliser = None
        self.model = None
        # Extra factor for predictions (uncertainty estimator)
        self.correction_factor = 1

    def preprocess(self, idx_train=0.75, idx_test=None, **kwargs):
        """The default preprocessing for the predictor.
        
        Parameters
        ----------
        idx_train : array or float, default 0.75
            Array of galaxy ids that are used for training.
            If float, the fraction of samples used for training.
        idx_test : array or None, default None
            Array of galaxy ids used for testing.
            If None, use the remaining samples.
        Y_pred : DataFrame or None, default None
            Only used (but mandatory) for uncertainty estimator.
            The uncertainty estimator does not use Y directly, but
            (Y_true - Y_pred)^2 as a target.
        """

        # Select features and target
        self.X = self._feature_select()
        self.Y = FeatureSelect.select_y(self.d_data)
        # Log normalise the fluxes
        xcols = self.X.columns
        ignore_bands = list(xcols[~xcols.isin(self.d_data['fullbay'].columns)])
        kwargs.setdefault('ignore_bands', ignore_bands)
        self.log_normaliser = LogNormaliser(**kwargs)
        self.X, self.Y = self.log_normaliser.transform(self.X, self.Y)
        self.train_test_split(idx_train, idx_test)

    def train(self, model=None, apply_correction=True, **predictor_kwargs):
        """Train the model."""

        if model is None:
            model = self._get_default_model(**predictor_kwargs)
        self.model = model

        # Skorch only supports numpy arrays, no DataFrames
        self.model.fit(self.to_array(self.X_train), 
                       self.to_array(self.Y_train))
        self.Y_pred = self.predict(self.X)
        self.Y_pred_train = self.Y_pred.loc[self.X_train.index, :]
        self.Y_pred_test = self.Y_pred.loc[self.X_test.index, :]
        # Uncertainty estimator: correct to unit validation mean chisq
        self._apply_correction(apply_correction)

    def predict_idx(self, idx):
        """Predict on a set of indices (which are in X)"""

        idx = pd.Index(idx)
        if not np.all(idx.isin(X.index)):
            raise ValueError("Not all indices in X!")
        return self.predict(self.X.loc[idx, :])

    def predict(self, X):
        """Predict on a given set of inputs"""

        Y_pred = self.model.predict(self.to_array(X))
        Y_pred = pd.DataFrame(Y_pred, index=X.index,
                              columns=self.Y_test.columns)
        Y_pred = Y_pred * self.correction_factor
        return Y_pred

    def test(self, metric=None, tset='test', multi_band=True, **kwargs):
        """
        Evaluate the model with a given metric
        
        Parameters
        ----------
        metric : string, callable, or None, default None
            if string : a metric available in METRICS
            if callable, a metric taking (y_t, y_p) as arguments
            if None, use 'rmse' for reg and 'mean_chisq' for uncertainty estimator.

        tset : 'test' or 'train', default 'test'
        multi_band : bool
            Return a pd.Series, with each target column having a metric
        kwargs : keyword arguments passed to the metric function
        """

        y_t, y_p = self.get_target_set(tset)
        if metric is None:
            metric = self._get_default_metric()
        if metric in METRICS:
            metric_name = metric
            metric = METRICS[metric]
        elif not callable(metric):
            raise ValueError("Metric must be in METRICS or callable.")
        else:
            metric_name = 'score'
        if multi_band:
            li_score = [metric(y_t[band], y_p[band], **kwargs) 
                            for band in self.Y.columns]
            return pd.Series(li_score, name=metric_name, index=self.Y.columns)
        return metric(y_t, y_p, **kwargs)

    def train_test_split(self, idx_train=0.75, idx_test=None, seed=123):
        """Create train and test dataframes (views of self.X and self.Y)"""

        np.random.seed(seed)
        if isinstance(idx_train, float):
            idx_tot = self.X.index.values.copy()
            np.random.shuffle(idx_tot)
            n_train = int(idx_train * len(idx_tot))
            idx_train = idx_tot[:n_train]
        if idx_test is None:  # take remaining as test
            idx_test = self.X.index.difference(idx_train).values
            np.random.shuffle(idx_test)
        # To np.array and copy
        if isinstance(idx_train, (pd.Series, pd.Index)):
            idx_train = idx_train.values
        if isinstance(idx_test, (pd.Series, pd.Index)):
            idx_test = idx_test.values
        idx_train, idx_test = idx_train.copy(), idx_test.copy()
        # Create train and test dataframes
        self.X_train, self.X_test = self.X.loc[idx_train], self.X.loc[idx_test]
        self.Y_train, self.Y_test = self.Y.loc[idx_train], self.Y.loc[idx_test]

    def get_target_set(self, tset='test', **kwargs):
        """
        Get true and predicted target for the given set (train or test).
        
        Parameters
        ----------
        tset : train', 'test', 'val', or 'tr', default 'test'
            The target set. total = tr + val + test. train = tr + val.
        to_err : bool, default: True
            For uncertainty estimator, give \sigma (= 1 / sqrt(z)) instead of z
        """

        if tset == 'test':
            y_t, y_p = self.Y_test, self.Y_pred_test
        elif tset == 'train':
            y_t, y_p = self.Y_train, self.Y_pred_train
        else:
            if tset == 'tr':
                idx_tr = self._get_tr_val('tr')
                y_t, y_p = self.Y_train.iloc[idx_tr, :], self.Y_pred_train.iloc[idx_tr, :]
            elif tset == 'val':
                idx_val = self._get_tr_val('val')
                y_t, y_p = self.Y_train.iloc[idx_val, :], self.Y_pred_train.iloc[idx_val, :]
            else:
                raise ValueError(f"Invalid target set {tset}. Should be train, test, "
                                 "tr, or val.")
        return y_t, y_p

    @abstractmethod
    def _feature_select(self):
        pass

    def _get_default_model(self, **predictor_kwargs):
        pass

    def _apply_correction(self, should_apply):
        pass

    @abstractmethod
    def _get_default_metric(self):
        pass

    def _get_tr_val(self, which='tr'):
        idx = 0 if which == 'tr' else 1
        if 'neuralnet' in self.model.named_steps:
            split = self.model.named_steps['neuralnet'].train_split(self.X_train)
        elif 'neuralnet_scaled' in self.model.named_steps:
            split = self.model.named_steps['neuralnet'].regressor.train_split(self.X_train)
        else:
            raise ValueError("tr or val set requires a 'neuralnet' or 'neuralnet_scaled' "
                             "in the pipeline")
        return split[idx].indices

    def build_model(self, steps, **predictor_kwargs):
        """Build a sklearn compatible model (pipeline)
        
        Parameters
        ----------
        steps : list or tuple
            The steps of the pipeline, as strings or transformers/models.
        """

        nnet_kwargs = dict(reg=self._is_reg(), insize=self.X.shape[1], 
                           outsize=self.Y.shape[1], **predictor_kwargs)
        d_transformers = {'std_scale': StandardScaler(), 
                          'neuralnet': default_skorch_nnet(**nnet_kwargs),
                          'neuralnet_scaled': default_scaled_nnet(**nnet_kwargs)}
        pipeline = []
        for i, step in enumerate(steps):
            if isinstance(step, str) and step in d_transformers:  # Step is a name
                step = (step, d_transformers[step])
            elif not isinstance(step, (list, tuple)):  # Step is the transform itself
                stepname = type(step).__name__.lower()
                step = (stepname, step)
            # else: step is (stepname, steptransformer)
            pipeline.append(step)
        return Pipeline(pipeline)

    @abstractmethod
    def _is_reg(self):
        pass

    @staticmethod
    def to_array(X):
        if isinstance(X, (pd.Series, pd.DataFrame)):
            X = X.values
        return X.astype(np.float32)


class SingleRegressor(SinglePredictor):
    """Single regressor, trained on one train/test split."""

    def _feature_select(self):
        return FeatureSelect.select_xreg(self.d_data)

    def _get_default_model(self, **predictor_kwargs):
        return self.build_model(['std_scale', 'neuralnet_scaled'], **predictor_kwargs)

    def _get_default_metric(self):
        return 'rmse'

    def _is_reg(self):
        return True


class SingleUncertaintyEstimator(SinglePredictor):
    """Single uncertainty estimator, trained on one train/test split."""

    def preprocess(self, idx_train=0.75, idx_test=None, **kwargs):
        Y_pred = kwargs.pop('Y_pred', None)
        self._check_Y_pred(Y_pred)
        super().preprocess(idx_train=idx_train, idx_test=idx_test, **kwargs)
        # Uncertainty estimator: target = (Y_true - Y_pred)^2
        self.Y = self._transform_target(self.Y, Y_pred)
        self.Y_train = self._transform_target(self.Y_train, Y_pred)
        self.Y_test = self._transform_target(self.Y_test, Y_pred)

    def _check_Y_pred(self, Y_pred):
        if Y_pred is None:
            raise ValueError("Uncertainty estimator requires Y_pred from regressor.")
        if not isinstance(Y_pred, pd.DataFrame):
            raise ValueError(f"Y_pred should be a DataFrame, was {type(Y_pred)}")

    def _feature_select(self):
        return FeatureSelect.select_xunc(self.d_data)

    @staticmethod
    def _transform_target(Y, Y_pred):
        return np.square(Y - Y_pred.loc[Y.index, :])

    def _get_default_model(self, **predictor_kwargs):
        return self.build_model(['std_scale', 'neuralnet'], **predictor_kwargs)

    def _apply_correction(self, should_apply):
        if should_apply:
            self.unit_chisq_correction()

    def unit_chisq_correction(self):
        """Sets the correction factor so the validation set has \chi^2 = 1."""

        Y_diff_sq, Y_err = self.get_target_set('val')
        chi_sq = Y_diff_sq / np.square(Y_err)
        agg = lambda band: 1 / np.mean(chi_sq[band])
        inv_mean_chisq = [agg(band) for band in Y_diff_sq.columns]
        inv_mean_chisq = pd.Series(inv_mean_chisq, name=r'1 / <\chi^2_val>', index=Y_diff_sq.columns)
        self.correction_factor = inv_mean_chisq
        # Correct predictions so far
        li_preds = [self.Y_pred, self.Y_pred_train, self.Y_pred_test]
        for pred in li_preds:
            pred.loc[:, :] = pred.multiply(self.correction_factor, axis=1)
        return self.correction_factor
    
    def _get_default_metric(self):
        return 'mean_chisq'

    def get_target_set(self, tset='test', **kwargs):
        y_t, y_p = super().get_target_set(tset=tset, **kwargs)
        if kwargs.get('to_err', True):
            y_p = 1 / np.sqrt(y_p)
        return y_t, y_p

    def _is_reg(self):
        return False