import matplotlib.pyplot as plt
from ..fluxing.sed import BroadbandSED, HighresSED

class SEDPlotter:
    """
    Class to plot multiple SEDs on top. Can work with broadband SEDs,
    model SEDs, with and without errors.
    """

    def __init__(self, ax=None, **kwargs):
        # Prepare axes
        style = kwargs.get('style', None)
        if style is not None:
            plt.style.use(style)
        if ax is None:
            if not kwargs.get('avoid_close', False):
                plt.close('all')
            figsize = kwargs.get('figsize', None)
            _, ax = plt.subplots(figsize=figsize)

        plt.sca(ax)
        ax.set_xscale('log')
        ax.set_yscale('log', nonposy='clip')
        ax.set_xlabel(r'wavelength ($\mu$m)')
        ax.set_ylabel('flux')
        self.ax = ax
        # Label positions
        self.d_labelpos = {'top left': 0.97, 'top right': 0.97,
                           'bottom left': 0.03, 'bottom right': 0.03}

    def add_broadband_series(self, s_fluxes, s_fluxerrs=None, **kwargs):
        err = s_fluxerrs.values if s_fluxerrs is not None else None
        self.add_broadband(s_fluxes.index, s_fluxes.values, err,
                           **kwargs)

    def add_broadband(self, filters, fluxes, fluxerrs=None, **kwargs):
        sed = BroadbandSED(filters, fluxes, fluxerrs)
        kwargs.setdefault('linestyle', 'None')
        kwargs.setdefault('marker', '+')
        kwargs.setdefault('markeredgewidth', 2.)
        self.add(sed, **kwargs)

    def add_model(self, wavelengths, fluxes, **kwargs):
        sed = HighresSED(wavelengths, fluxes)
        self.add(sed, **kwargs)

    def add(self, sed, **kwargs):
        has_errors = sed.ferr is not None
        ax = self.ax
        if has_errors:
            fill = kwargs.pop('fill', False)
            fill_kwargs = kwargs.pop('fill_kwargs', {})
            fill_kwargs.setdefault('alpha', 0.3)
            if fill:
                if len(sed.ferr.shape) == 2:
                    low, upp = sed.fnu - sed.ferr[0, :], sed.fnu + sed.ferr[1, :]
                else:
                    low, upp = sed.fnu - sed.ferr, sed.fnu + sed.ferr
                ax.plot(sed.wavelengths, sed.fnu, **kwargs)
                ax.fill_between(sed.wavelengths, low, upp, **fill_kwargs)
            else:
                ax.errorbar(sed.wavelengths, sed.fnu, yerr=sed.ferr, **kwargs)
        else:
            ax.plot(sed.wavelengths, sed.fnu, **kwargs)

    def fix_limits(self, which='both'):
        ax = self.ax
        if (which == 'x') or (which == 'both'):
            ax.set_xlim(ax.get_xlim())
        if (which == 'y') or (which == 'both'):
            ax.set_ylim(ax.get_ylim())
        
    def save(self, path):
        plt.savefig(path, bbox_inches='tight')
    
    def show(self):
        plt.show()

    def add_text(self, text, position='top left', vertical_offset=0, height=None,
                 **kwargs):
        if height is None:
            fontsize = kwargs.get('fontsize', plt.rcParams['font.size'])
            height = 0.05 * fontsize / 18.
        x = 0.03 if 'left' in position else 0.97
        ha = 'left' if 'left' in position else 'right'
        va = 'top' if 'top' in position else 'bottom'
        kwargs.setdefault('ha', ha)
        kwargs.setdefault('va', va)
        self.d_labelpos[position] += vertical_offset
        y = self.d_labelpos[position]
        # Subtract height if starting from top
        if 'top' in position:
            height *= -1
        self.d_labelpos[position] += height
        self.ax.text(x, y, text, transform=self.ax.transAxes, **kwargs)