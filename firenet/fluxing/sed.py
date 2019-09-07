from .filters import Filter

import numpy as np
from astropy.io import fits
from scipy.constants import c

class SED:
    """
    Represents an SED
    Wavelength is given in micron,
    Fnu is in Jy.
    """

    def __init__(self, wavelengths, fnu, ferr=None):
        if (ferr is not None) and (len(ferr.shape) > 1) and (ferr.shape[0] != 2):
            raise ValueError('SED ferr should be either 1-dimensional '
                             '(symmetric errors) or shape (2, N) (lower, '
                             'upper error)')
        self.wavelengths = np.array(wavelengths)
        self.fnu = np.array(fnu)
        self.ferr = ferr

    def __mul__(self, other):
        new = self.copy()
        new.fnu = self.fnu * other
        if self.ferr is not None:
            new.ferr = self.ferr * other
        return new

    def __truediv__(self, other):
        new = self.copy()
        new.fnu = self.fnu / other
        if self.ferr is not None:
            new.ferr = self.ferr / other
        return new

    def copy(self):
        """Returns a copy"""

        return type(self)(self.wavelengths.copy(), self.fnu.copy())

class HighresSED(SED):
    """
    Represents an SED that is sampled at high spectral resolution, probably
    originating from a library of models.
    """

    def __init__(self, wavelengths, fnu, ferr=None):
        super().__init__(wavelengths, fnu, ferr)

    @classmethod
    def from_cigale_fits(cls, filename, flux_column='Fnu', fluxfactor=1, 
                         hdu_index=1, combine_column_list=True):
        '''
        Create a full SED from a cigale output (name_best_fit.fits) and convert
        to Jy.

        fluxfactor : float, default: 1. The factor with which we multiply
            the flux to convert it to Jy, on top of the default mJy to Jy 
            conversion. If the CIGALE INPUT was (mistakingly) in Jy, set this 
            to 1e3.

        combine_column_list : bool, default True.
            Only used if flux_column is iterable. If True, return a single
            HighresSED, where the flux is the sum of the given flux columns.
            If False, return an equally large list of HighresSEDs.
        '''

        hdu = fits.open(filename)[hdu_index]
        wavelengths = hdu.data['wavelength'] / 1e3  # from nm to micron

        def get_fnu(fluxcol):
            fnu = hdu.data[fluxcol] * fluxfactor
            if fluxcol == 'Fnu':
                fnu /= 1e3  # From mJy to Jy
            else:  # from W/nm to per W/Hz
                fnu = np.square(wavelengths) * fnu / (c * 1e3)
            return fnu

        if isinstance(flux_column, (list, tuple)):
            if not combine_column_list:
                return [cls(wavelengths, get_fnu(fluxcol)) for fluxcol in flux_column]
            fnu = sum([get_fnu(fluxcol) for fluxcol in flux_column])
        else:
            fnu = get_fnu(flux_column)
        return cls(wavelengths, fnu)

    def to_broadband(self, filters, quick=False):
        '''
        Transforms the full SED to broadband (returns new BroadbandSED).

        Parameters
        ----------

        filters : iterable
            The elements should be either of class `Filter`, or strings from
            which a filter can be created. When calling this function multiple
            times, create the `Filter`s beforehand so you can reuse them.
            If using strings, the `Filter`s will be loaded from disk which is
            slow.

        quick : bool, default False
            If True, take the flux closest to the filters pivot wavelength,
            instead of doing the convolution.
        '''

        ffilters = []  # make sure to copy
        fnu_bands = []
        for filt in filters:
            if not isinstance(filt, Filter):
                filt = Filter(filt)
            ffilters.append(filt)
            if quick:
                best_idx = np.searchsorted(self.wavelengths, filt.pivot_wavelength())
                fnu = self.fnu[best_idx]
            else:
                fnu = filt.convolve(self.wavelengths, self.fnu)
            fnu_bands.append(fnu)
        return BroadbandSED(ffilters, fnu_bands)

    def blueshift(self, z):
        '''
        Blueshift the spectrum (to bring it to restframe), by shifting
        all wavelengths.
        '''

        # Divide by (1+z) becaues fnu (F_nu dnu = F_lambda dlambda stays
        # constant when redshifting). See Hogg 2002 and Hogg 2000 on K-correction.
        self.fnu = self.fnu / (1 + z)
        self.wavelengths = self.wavelengths / (1+z)

    def redshift(self, z):
        '''Redshift the model spectrum, by shifting all wavelengths.'''

        self.fnu = self.fnu * (1 + z)
        self.wavelengths = self.wavelengths * (1 + z)

class BroadbandSED(SED):
    """
    An SED measured over a few broadbands.
    """

    def __init__(self, filters, fnu, ferr=None):
        wavelengths = []
        filter_objs = []  # create new copy so we can modify list
        for filt in filters:
            if not isinstance(filt, Filter):
                filt = Filter(filt)
            filter_objs.append(filt)
            wavelengths.append(filt.pivot_wavelength())
        super().__init__(wavelengths, fnu, ferr)
        self.filters = filter_objs

    def k_correct(self, z, modelSED):
        """Perform a K-correction, assuming an underlying model SED. Returns
        a new BroadbandSED with the corrected values.
        
        For each broadband, the model SED is scaled to the appropriate level,
        so its normalization does not matter. The modelSED is redshifted
        (matching the BroadbandSED before doing the K-correct).
        """

        # isinstance fails due to multiple model imports
        if not 'HighresSED' in str(type(modelSED)):
            raise ValueError('modelSED must be a HighresSED, was', type(modelSED))

        model_broad = modelSED.to_broadband(self.filters)
        fnu_kcorr = []
        for i, filt in enumerate(self.filters):
            scalef = self.fnu[i] / model_broad.fnu[i]
            model_f = modelSED * scalef
            model_f.blueshift(z)
            fnu_band = filt.convolve(model_f.wavelengths, model_f.fnu)
            fnu_kcorr.append(fnu_band)
        return BroadbandSED(self.filters, fnu_kcorr)

    def copy(self):
        """Returns a copy"""

        return type(self)(self.filters, self.fnu.copy(), self.ferr.copy())