import numpy as np
import pandas as pd

class LogNormaliser:
    """
    Prepare data from luminosity (W/Hz) to log-normalized.
    
    Not sklearn Transformer compatible, since we transform both X and y,
    which is not (yet) supported by scikit-learn.
    """

    def __init__(self, normalise_band='WISE_3.4', ignore_bands=None, copy=True):
        self.normalise_band = normalise_band
        self.copy = copy
        self.ignore_bands = list(ignore_bands) if ignore_bands is not None else []
        if not normalise_band in ignore_bands:
            self.ignore_bands.append(normalise_band)
    
    def transform(self, X, y):
        self._check_dataframes(X, y)
        normalise_flux = X[self.normalise_band].copy()
        X = self._log_normalise_df(X, normalise_flux)
        y = self._log_normalise_df(y, normalise_flux)
        X[self.normalise_band] = np.log10(normalise_flux)
        return X, y

    def inverse_transform(self, X, y):
        self._check_dataframes(X, y)
        normalise_flux = np.power(10, X[self.normalise_band].copy())
        X = self._unnormalise_df(X, normalise_flux)
        y = self._unnormalise_df(y, normalise_flux)
        X[self.normalise_band] = normalise_flux
        return X, y
        
    def _check_dataframes(self, X, y):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X should be pd.DataFrame, was", type(X))
        if not isinstance(y, pd.DataFrame):
            raise TypeError("y should be pd.DataFrame, was", type(y))
        if self.normalise_band not in X.columns:
            raise ValueError(f"Normaliseband ({self.normalise_band}) not in features!")

    def _log_normalise_df(self, df, normalise_flux):
        if self.copy:
            df = df.copy()
        used_bands = ~df.columns.isin(self.ignore_bands)
        df.loc[:, used_bands] = (df.loc[:, used_bands]
                                    .divide(normalise_flux, axis=0)
                                    .apply(np.log10))
        return df

    def _unnormalise_df(self, df, normalise_flux):
        if self.copy:
            df = df.copy()
        used_bands = ~df.columns.isin(self.ignore_bands)
        df.loc[:, used_bands] = (np.power(10, df.loc[:, used_bands])
                                    .multiply(normalise_flux, axis=0))
        return df