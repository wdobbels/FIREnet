from .helpers import combine_grids, interpolate_log, cache_simple_method
import os
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.constants import c

class Filter:
    """Class that represents a single broad-band filter"""

    filterdir = Path(__file__).parent / 'filterdata'

    def __init__(self, filtername):
        self.name = filtername
        filename = self._get_filterfile(filtername)
        self.get_transmission(filename)

    def get_transmission(self, filename):
        '''
        Called from init
        The transmission curve is always considered in bolometer format.
        It matches frequencies (not wavelengths), and is normalized in
        frequency space.
        '''

        filename = Filter.filterdir / filename
        # get type (photon or bolo) and amount of lines to skip
        with open(filename, 'r') as f:
            line = f.readline()
            i = 0
            while line.startswith('#'):
                line = f.readline()
                i += 1
                if i == 1:
                    det_type = line[1:].strip()
        skiplines = i
        df_filter = pd.read_csv(filename, skiprows=skiplines, header=None,
                                sep=r'\s+', 
                                names=['wavelength', 'transmission'],
                                dtype=np.float64)
            
        self.wavelengths = np.array(df_filter['wavelength'] / 1e4)
        self.frequencies = (2.99792458e14 / self.wavelengths)[::-1]
        self._trans_lambda = np.array(df_filter['transmission'])
        if det_type == 'photon':
            self._trans_lambda *= self.wavelengths
        self.transmission = self._trans_lambda[::-1]
        self.transmission /= np.trapz(x=self.frequencies, y=self.transmission)

    def convolve(self, sed_wavelengths, sed_fnu):
        '''
        Apply the filter to the sed
        The wavelengths should be in micron (and are converted to frequencies).
        '''

        # attenuation (all negative): switch sign at beginning and end
        if np.all(sed_fnu <= 0):  
            sed_fnu = -sed_fnu
            signfact = -1
        else:
            signfact = 1
        
        sed_freq = (c*1e6 / sed_wavelengths)[::-1]
        sed_fnu = sed_fnu[::-1]
        freqs = combine_grids(sed_freq, self.frequencies)
        sed = interpolate_log(freqs, sed_freq, sed_fnu)
        transmission = interpolate_log(freqs, self.frequencies, 
                                       self.transmission, logy=False)
        # Normalize again because of finer grid
        return signfact * (np.trapz(x=freqs, y=(sed * transmission)) /
                           np.trapz(x=freqs, y=transmission))

    def convolve_lambda(self, sed_wavelengths, sed_flambda):
        '''
        Input: F_lambda in W/nm/mˆ2
        Output: F_nu_band in Jy ()
        '''

        lambdas = combine_grids(sed_wavelengths, self.wavelengths)
        sed = interpolate_log(lambdas, sed_wavelengths, sed_flambda)
        transmission = interpolate_log(lambdas, self.wavelengths, 
                                       self._trans_lambda, logy=False)
        return 1e23 * (np.trapz(x=lambdas, y=(transmission * sed)) /
                       np.trapz(x=lambdas, y=(c * transmission / 
                                              np.square(lambdas))))

    @cache_simple_method
    def effective_wavelength(self):
        return (np.trapz(x=self.wavelengths, 
                         y=(self._trans_lambda * self.wavelengths)) / 
                np.trapz(x=self.wavelengths, y=self._trans_lambda))

    @cache_simple_method
    def pivot_wavelength(self):
        return np.sqrt(np.trapz(x=self.wavelengths, y=self._trans_lambda) / 
                       np.trapz(x=self.wavelengths,
                                y=(self._trans_lambda / 
                                   np.square(self.wavelengths))))

    def plot_transmission(self, ax=None):
        if ax is None:
            f, ax = plt.subplots()
        else:
            f = ax.get_figure()
        ax.loglog(self.wavelengths, self._trans_lambda)
        ax.set_xlabel('Wavelength (micron)')
        ax.set_ylabel('Transmission')
        ax.set_title(self.name)
        return f

    def _get_filterfile(self, filtername):
        """Resolve filter name to get to the right file"""

        rawnames = os.listdir(Filter.filterdir)
        validnames = list(map(lambda x: x.lower()[:-4], rawnames))
        d_namemap = {validnames[i]: rawnames[i] for i in range(len(rawnames))}
        originalname = filtername
        filtername = filtername.lower()
        if filtername.startswith('sdss_'):
            filtername = filtername[5:] + '_prime'
        elif filtername.endswith('_hipe'):  # plw_s
            filtername = filtername[:-5] + '_s'
        elif filtername.startswith('galex'):  # fuv
            filtername = filtername[-3:]
        elif filtername.startswith('2mass_'):
            filtername = filtername[6:] + '_2mass'
        elif filtername.startswith('wise_'):
            last = filtername[5:]
            if last in ['1', '2', '3', '4']:
                filtername = 'wise' + last
            else:
                dmap = {'3.4': '1', '4.6': '2', '12': '3', '22': '4'}
                if last not in dmap:
                    filtername = 'unresolved'  # will throw error at end
                filtername = 'wise' + dmap[last]
        elif filtername.startswith('pacs_'):
            last = filtername[5:]
            dmap = {'70': 'blue', '100': 'green', '160': 'red'}
            if last in dmap:
                filtername = 'pacs_' + dmap[last]
        elif filtername.startswith('spire_'):
            last = filtername[6:]
            dmap = {'250': 'psw_s', '350': 'pmw_s', '500': 'plw_s'}
            if last in dmap:
                filtername = dmap[last]

        if filtername in validnames:
            return d_namemap[filtername]
        else:
            raise ValueError('Filter {} '.format(originalname) +
                             'was not found!')