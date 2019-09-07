import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from .reguncpredictor import RegUncPredictor

class FullSetPredictor:
    """
    Split the complete dataset in a few train/test folds, and train a model
    for each train-test split.
    """

    def __init__(self, d_data):
        self.d_data = d_data
        self.predictors = []

    def prepare_splits(self, n_splits=4, shuffle_state=123, idx_tot=None):
        """Prepare the train/test splits and models"""

        if len(self.predictors) > 0:
            raise ValueError("prepare_splits should be called once only!")
        if idx_tot is None:
            idx_tot = self.d_data['fullbay'].index
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=shuffle_state)
        np.random.seed(shuffle_state)
        for train_ids, test_ids in kf.split(idx_tot):
            # train_ids: numerical indices, idx_train: galaxy names
            np.random.shuffle(train_ids), np.random.shuffle(test_ids)
            idx_train, idx_test = idx_tot[train_ids], idx_tot[test_ids]
            pred = RegUncPredictor(self.d_data)
            pred.preprocess(idx_train, idx_test)
            self.predictors.append(pred)
        
    def train(self, reg_kwargs=None, unc_kwargs=None):
        """Train the predictors"""

        reg_kwargs, unc_kwargs = self._set_default_kwargs(reg_kwargs, unc_kwargs)
        for i, predictor in enumerate(self.predictors):
            print(f'Start training model {i+1}/{len(self.predictors)}...')
            predictor.train_regressor(**reg_kwargs)
            predictor.train_uncertainty(**unc_kwargs)

    def get_combined_test(self):
        """Get combined y_t, y_p, y_err from all test sets"""

        y_ts, y_ps, y_errs = [], [], []
        for predictor in self.predictors:
            y_t, y_p, y_err = predictor.get_target_set()
            y_ts.append(y_t), y_ps.append(y_p), y_errs.append(y_err)
        y_t, y_p, y_err = pd.concat(y_ts), pd.concat(y_ps), pd.concat(y_errs)
        return y_t, y_p, y_err

    @staticmethod
    def _set_default_kwargs(reg_kwargs, unc_kwargs):
        if reg_kwargs is None:
            reg_kwargs = {}
        if unc_kwargs is None:
            unc_kwargs = {}

        reg_kwargs.setdefault('verbose', False)
        unc_kwargs.setdefault('verbose', False)
        return reg_kwargs, unc_kwargs