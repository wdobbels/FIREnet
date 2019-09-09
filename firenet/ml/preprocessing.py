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
    
    def transform(self, X, y=None):
        self._check_dataframes(X, y)
        normalise_flux = X[self.normalise_band].copy()
        X = self._log_normalise_df(X, normalise_flux)
        X[self.normalise_band] = np.log10(normalise_flux)
        if y is not None:
            y = self._log_normalise_df(y, normalise_flux)
            return X, y
        return X

    def inverse_transform(self, X, y=None):
        self._check_dataframes(X, y)
        normalise_flux = np.power(10, X[self.normalise_band].copy())
        X = self._unnormalise_df(X, normalise_flux)
        X[self.normalise_band] = normalise_flux
        if y is not None:
            y = self._unnormalise_df(y, normalise_flux)
            return X, y
        return X
        
    def _check_dataframes(self, X, y):
        if not isinstance(X, pd.DataFrame):
            raise TypeError("X should be pd.DataFrame, was", type(X))
        if (y is not None) and (not isinstance(y, pd.DataFrame)):
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

class FeatureSelect:
    uvmir_bands = ['GALEX_FUV', 'GALEX_NUV', 'SDSS_u', 'SDSS_g', 'SDSS_r', 
                   'SDSS_i', 'SDSS_z', '2MASS_J', '2MASS_H', '2MASS_Ks', 
                   'WISE_3.4', 'WISE_4.6', 'WISE_12', 'WISE_22']
    fir_bands = ['PACS_70', 'PACS_100', 'PACS_160', 
                 'SPIRE_250', 'SPIRE_350', 'SPIRE_500']

    @classmethod
    def select_xreg(cls, d_data):
        """Select 14 UV-MIR Bayesian fluxes"""

        return cls.add_features(None, d_data, cls.uvmir_bands, 'shortbay')

    @classmethod
    def select_xunc(cls, d_data):
        """
        Select 14 UV-MIR Bayesian fluxes + 14 UV-MIR log(F_obs / F_bay)
        + 14 UV-MIR log(F_obserr / F_bay)
        """

        df = cls.add_features(None, d_data, cls.uvmir_bands, 'shortbay')
        df = cls.add_features(df, d_data, cls.uvmir_bands, 'obs_to_short')
        return cls.add_features(df, d_data, cls.uvmir_bands, 'obserr_to_short')

    @classmethod
    def select_y(cls, d_data):
        """
        Select 6 FIR Bayesian fluxes.
        """

        return cls.add_features(None, d_data, cls.fir_bands, 'fullbay')

    @staticmethod
    def add_features(df, d_data, li_features, simname):
        """
        Extract the features or target from d_data and add to dataframe `df`.

        Parameters
        ----------
        li_features : list
            List of features/targets to extract from d_data[`simname`]. 

        simname : string
            The features are taken from this CIGALE fit. If you need features from
            different simulations, call this function multiple times.

        Notes
        -----
        `df` is modified (not copied), and returned again.
        """

        if df is None:
            df = pd.DataFrame()
        # Select features
        for featurename in li_features:
            featureval = d_data[simname][featurename].copy()
            if featurename in df.columns:
                featurename = f'{simname}_{featurename}'
            df[featurename] = featureval
        return df