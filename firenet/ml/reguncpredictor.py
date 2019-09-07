import numpy as np
import pandas as pd
from .singlepredictor import SinglePredictor

class RegUncPredictor:
    """
    For a single train/test split, train a regressor 
    and uncertainty estimator
    """
    def __init__(self, d_data):
        self.d_data = d_data
        self.reg = SinglePredictor(d_data, reg=True)
        self.unc = SinglePredictor(d_data, reg=False)

    def preprocess(self, idx_train=0.75, idx_test=None):
        """The default preprocessing for the predictor.
        
        Parameters
        ----------
        idx_train : array or float, default 0.75
            Array of galaxy ids that are used for training.
            If float, the fraction of samples used for training.
        idx_test : array or None, default None
            Array of galaxy ids used for testing.
            If None, use the remaining samples.
        """

        # Only preprocess regressor.
        # Preprocessing uncertainty estimator requires Y_pred from reg.
        self.reg.preprocess(idx_train, idx_test)

    def train_regressor(self, model=None, **predictor_kwargs):
        """Train the regressor."""

        self.reg.train(model=model, **predictor_kwargs)

    def train_uncertainty(self, model=None, apply_correction=True, **predictor_kwargs):
        """Train the uncertainty estimator."""

        self.unc.preprocess(idx_train=self.reg.X_train.index,
                            idx_test=self.reg.X_test.index,
                            Y_pred=self.reg.Y_pred)
        self.unc.train(model=model, apply_correction=apply_correction,
                       **predictor_kwargs)

    def predict_idx(self, idx):
        """Predict on a set of indices (which are in X)"""

        idx = pd.Index(idx)
        if not np.all(idx.isin(self.reg.X.index)):
            raise ValueError("Not all indices in X!")
        return self.predict(self.reg.X.loc[idx, :], self.unc.X.loc[idx, :])

    def predict(self, X_reg, X_unc):
        """Predict on a given set of inputs. Returns Y_pred, Y_unc (stdev)"""

        Y_pred = self.reg.predict(X_reg)
        Z_pred = self.unc.predict(X_unc)
        return Y_pred, 1 / np.sqrt(Z_pred)

    def get_target_set(self, tset='test', to_err=True):
        """
        Get Y_true, Y_pred, Y_unc for the given set (train or test).
        
        Parameters
        ----------
        tset : train', 'test', 'val', or 'tr', default 'test'
            The target set. total = tr + val + test. train = tr + val.
        to_err : bool, default: True
            For uncertainty estimator, give \sigma (= 1 / sqrt(z)) instead of z
        """

        Y_true, Y_pred = self.reg.get_target_set(tset=tset)
        Y_diff, Y_unc = self.unc.get_target_set(tset=tset, to_err=to_err)
        return Y_true, Y_pred, Y_unc