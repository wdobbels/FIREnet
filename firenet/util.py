import numpy as np

def add_uncertainty_features(d_data):
    """Add flux error ratio and flux ratio to d_data"""

    d_data['obserr_to_short'] = ((d_data['observederr'] / d_data['shortbay'])
                                .copy()
                                .replace([np.inf, -np.inf], np.nan)
                                .apply(np.log10)
                                .fillna(6))
    d_data['obs_to_short'] = ((d_data['observed'] / d_data['shortbay'])
                                .copy()
                                .replace([np.inf, -np.inf], np.nan)
                                .apply(np.log10)
                                .fillna(6))
    return d_data