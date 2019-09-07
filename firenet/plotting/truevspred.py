import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patheffects as path_effects
from sklearn.metrics import r2_score
from .preparation import estimate_density

class TrueVSPredPlotter:
    '''
    Creates the outer hierarchy of a true vs predicted figure, allowing for
    different panels, each with their own cells. Each panel can be used for
    a different predictor.
    '''
    def __init__(self, figsize=None, **fig_kwargs):
        self.fig = plt.figure(figsize=figsize, **fig_kwargs)
        self.grid = None
        self.grid_panels = None
        self.instanciated = False
        self.nrows, self.ncols = None, None

    def create_panels(self, nrows, ncols=1, **kwargs):
        '''
        Create the panels (without instantiating the cells) on a gridspec
        layout.
        '''
        self.instanciated = True
        self.nrows, self.ncols = nrows, ncols
        self.grid = gridspec.GridSpec(nrows, ncols, figure=self.fig, **kwargs)
        self.grid_panels = []
        for i_row in range(nrows):
            for j_col in range(ncols):
                panel = TrueVSPredPanel(self.grid[i_row, j_col], fig=self.fig)
                self.grid_panels.append(panel)

    def get_panel(self, i_row, j_col=0):
        '''Access a single TrueVSPredPanel '''
        if not self.instanciated:
            raise ValueError("Trying to access panel before instantiation!")
        idx = (i_row * self.ncols) + j_col
        return self.grid_panels[idx]    

class TrueVSPredPanel:
    '''
    A panel in a particular true vs pred plot. Each panel stands on its
    own and can contain a grid of properties to show.
    '''
    def __init__(self, gridspec_panel, fig):
        self.panel = gridspec_panel
        self.fig = fig
        self.grid = None
        self.grid_cells = []
        self.instanciated = False
        self.nrows, self.ncols, self.ncells = None, None, None
        self.data = {}
        self.bands = None

    def stylized_plot(self, y_t, y_p, y_terr=None, y_perr=None, style='firflux',
                      **kwargs):
        '''Create the full plot, high level interface'''

        style_kwargs = kwargs.get('style_kwargs', {})
        extras_kwargs = kwargs.get('extras_kwargs', {})
        d_stylefunc = {'firflux': self.firflux_style, 'property': self.property_style}

        if style not in d_stylefunc:
            raise ValueError(f"Invalid style {style}")

        self.setup_default(y_t, y_p, y_terr, y_perr)

        if style == 'firflux' and self.ncells != 6:
            raise ValueError("Style is firflux, but number of cells is not "
                             f"6, but {self.ncells}!")

        d_stylefunc[style](**style_kwargs)
        self.task_on_cells('plot')
        self.add_extras(**extras_kwargs)

    
    def setup_default(self, y_t, y_p, y_terr=None, y_perr=None):
        '''Sets up the layout and data, using the default standards'''

        ncells = y_t.shape[1]
        if ncells > 4:
            shape = (2, 3)
        else:
            shape = (1, ncells)
        self.create_layout(*shape, wspace=0.13, hspace=0.13)
        self.set_data(y_t, y_p, y_terr=y_terr, y_perr=y_perr)
    
    def firflux_style(self, **kwargs):
        '''Styles the axis (limits, ticks and labels) for 6 fir bands'''

        xlim = kwargs.get('xlim', [-1.4, 3.4])
        ylim = kwargs.get('ylim', 'same')
        xlabel = kwargs.get('xlabel', r'$\log (F_{\mathrm{true}} / F_{3.4\, \mathrm{µm}})$')
        ylabel = kwargs.get('ylabel', r'$\log (F_{\mathrm{pred}} / F_{3.4\, \mathrm{µm}})$')
        labelkwargs = kwargs.get('labelkwargs', {})
        title_kwargs = kwargs.get('title', {})
        title_kwargs.setdefault('suffix', ' µm')
        title_kwargs.setdefault('part', -1)
        category_kwargs = kwargs.get('category', {})
        category_kwargs.setdefault('part', 0)
        category_kwargs.setdefault('y', 0.125)
        category_kwargs.setdefault('fontsize', 17)

        self.task_on_cells('axislimits', xlim=xlim, ylim=ylim)
        self.task_on_cells('axislocator', locator=plt.MultipleLocator(1.))
        self.set_largelabels(xlabel, ylabel, **labelkwargs)
        # Category + title
        self.task_on_cells('title', **category_kwargs)
        self.task_on_cells('title', **title_kwargs)

    def property_style(self, **kwargs):
        '''Create plots for dust lum, dust mass and dust temp'''

        limits = kwargs.get('limits', [[2e4, 2e12], [1e2, 9e8], [7, 42]])
        title_kwargs = kwargs.get('title', {})
        title_kwargs.setdefault('part', -1)
        category_kwargs = kwargs.get('category', {})
        category_kwargs.setdefault('part', 0)
        category_kwargs.setdefault('y', 0.11)
        category_kwargs.setdefault('fontsize', 17)

        self.grid_cells[0].logscale()
        self.grid_cells[1].logscale()
        # Set limits and labels
        xlabels = [r'True $L_d$ [$L_\odot$]', r'True $M_d$ [$M_\odot$]', 
                   r'True $T_d$ [K]']
        for i in range(3):
            self.grid_cells[i].ax.set_xlabel(xlabels[i])
            self.grid_cells[i].set_axislimits(limits[i])
        # Extras
        for i in range(2):  # log axis
            self.grid_cells[i].set_axislocator(locator=plt.LogLocator(numticks=5))
            self.grid_cells[i].set_axislocator(which='minor', formatter=plt.NullFormatter(),
                                                locator=plt.LogLocator(numticks=10))
        self.grid_cells[2].set_axislocator(locator=plt.MultipleLocator(10.))
        self.grid_cells[2].set_axislocator(which='minor', formatter=plt.NullFormatter(),
                                            locator=plt.MultipleLocator(5.))
        self.grid_cells[0].ax.set_ylabel('Predicted')
        # Category + title
        self.task_on_cells('title', **category_kwargs)
        self.task_on_cells('title', **title_kwargs)

    def add_extras(self, **kwargs):
        '''Adds one-to-one line and two metrics'''

        self.task_on_cells('one-to-one', alpha=1, zorder=3.95)
        self.task_on_cells('one-to-one', zorder=3.9, alpha=0.4, color='w', linewidth=4)
        metrics = kwargs.get('metrics', ['rmse', 'r2'])
        metric_kwargs = kwargs.get('metric_kwargs', {})
        for metric in metrics:
            self.task_on_cells('metric', metric=metric, **metric_kwargs)

    def create_layout(self, nrows, ncols, **kwargs):
        '''Creates the cells of the panel (as a gridspec layout)'''

        self.instanciated = True
        self.nrows, self.ncols = nrows, ncols
        self.grid = gridspec.GridSpecFromSubplotSpec(
                     nrows, ncols, subplot_spec=self.panel, **kwargs
                    )
        self._create_fullspan_ax()
        self.grid_cells = []
        for i_row in range(nrows):
            for j_col in range(ncols):
                ax = self.fig.add_subplot(self.grid[i_row, j_col])
                cell = TrueVSPredCell(ax)
                self.grid_cells.append(cell)
        self.ncells = len(self.grid_cells)

    def _create_fullspan_ax(self):
        self.fullspan_ax = self.fig.add_subplot(self.grid[:, :])
        directions = ['left', 'right', 'bottom', 'top']
        for direction in directions:
            self.fullspan_ax.spines[direction].set_visible(False)
        param_kwargs1 = {direction: False for direction in directions}
        # param_kwargs2 = {'label'+direction: False for direction in directions}
        self.fullspan_ax.tick_params(labelcolor='w', **param_kwargs1)

    def set_data(self, y_t, y_p, y_terr=None, y_perr=None):
        '''
        Sets the true, predicted, true error and predicted error of this
        panel. Each of these must be either a DataFrame or dictionary, indexed
        on the band (or property).
        '''

        self.data = {'y_t': y_t, 'y_p': y_p, 'y_terr': y_terr, 'y_perr': y_perr}
        self.ncells = y_t.shape[1]
        self.bands = y_t.columns

    def task_on_cells(self, task='plot', which_cells=None, **kwargs):
        '''Do a particular task on each of the cells.
        
        Parameters
        ----------

        task : 'plot', 'one-to-one', 'axislimits', 'axislocator'
            The task with the equivalent TrueVSPredCell function.

        which_cells : list or None
            The list of indices of the cells (bands/properties) that will
            execute the task. If None, use all cells.

        kwargs : keyword arguments
            Arguments passed to the TrueVSPredCell function.
        '''

        if which_cells is None:
            which_cells = list(range(len(self.grid_cells)))
        start_kwargs = kwargs.copy()
        for i_cell in which_cells:
            kwargs = start_kwargs.copy()  # reset kwargs for new defaults
            cell = self.grid_cells[i_cell]
            band = self.bands[i_cell]
            d_func = {'plot': cell.plot, 'one-to-one': cell.one_to_one,
                      'axislimits': cell.set_axislimits,
                      'axislocator': cell.set_axislocator,
                      'title': cell.set_title, 'metric': cell.add_metric,
                      'mark': cell.mark}
            if task == 'plot':
                y_tb = self._get_band_value('y_t', band)
                y_pb = self._get_band_value('y_p', band)
                y_terrb = self._get_band_value('y_terr', band)
                y_perrb = self._get_band_value('y_perr', band)
                kwargs = _set_default(kwargs, y_t=y_tb, y_p=y_pb,
                                      y_terr=y_terrb, y_perr=y_perrb)
            elif task == 'title':
                # Which part of a multi-word band? None: all.
                part = kwargs.pop('part', None)
                if part is None:
                    default_name = band
                else:
                    separator = '_' if '_' in band else ' '
                    splt = band.split(separator)
                    default_name = splt[part]
                suff = kwargs.pop('suffix', '')
                default_name += suff
                kwargs.setdefault('title', default_name)
            elif task == 'metric':
                y_tb = self._get_band_value('y_t', band)
                y_pb = self._get_band_value('y_p', band)
                kwargs = _set_default(kwargs, y_t=y_tb, y_p=y_pb)
            elif task not in d_func:
                valid_tasks = ', '.join(d_func.keys())
                raise ValueError(f"Invalid task {task}. Valid tasks:",
                                 valid_tasks)
            d_func[task](**kwargs)

    def _get_band_value(self, name, band):
        if self.data[name] is None:
            return None
        return self.data[name][band]

    def set_largelabels(self, xlabel='', ylabel='', **kwargs):
        '''Set 'axis'labels for the whole panel.
        
        Uses a fullspan_ax, which is hidden but spans the whole panel.
        '''

        self.fullspan_ax.set_xlabel(xlabel, **kwargs)
        self.fullspan_ax.set_ylabel(ylabel, **kwargs)

class TrueVSPredCell:
    '''One cell in a truevspred plot, corresponding to one band/property'''

    def __init__(self, ax):
        self.ax = ax
        self.metric_ypos = 0.95
        self.should_log = False
        self.idx_marked = None  # array of booleans (True for highlighted points)

    def logscale(self):
        '''Sets both scales to logarthmic'''

        self.should_log = True
        self.ax.set_xscale('log')
        self.ax.set_yscale('log')

    def plot(self, y_t, y_p, y_terr=None, y_perr=None, marked=False,
             error_kwargs=None, **scatter_kwargs):
        '''
        Creates the true vs predicted scatter, with errorbars and coloured
        by density.
        '''

        # Defaults
        error_kwargs = _set_default(error_kwargs, marker='None', linestyle='None',
                                    alpha=0.1, zorder=1)
        scatter_kwargs.setdefault('zorder', 2)
        if marked:
            cidx = np.zeros(len(y_t), dtype=bool) if self.idx_marked is None else self.idx_marked
            default_color = '#de5849'
            error_kwargs.setdefault('ecolor', default_color)
            scatter_kwargs = _set_default(scatter_kwargs, alpha=0.3, color=default_color,
                                          x=y_t[cidx], y=y_p[cidx])
        else:
            cidx = np.ones(len(y_t), dtype=bool) if self.idx_marked is None else ~self.idx_marked
            error_kwargs.setdefault('ecolor', '#7f8691')
            xc, yc, c = estimate_density(y_t[cidx], y_p[cidx], logspace=self.should_log)
            scatter_kwargs = _set_default(scatter_kwargs, alpha=0.2, cmap='inferno',
                                          x=xc, y=yc, c=c)
        # Plot
        ax = self.ax
        cidx_terr = cidx if len(y_terr.shape) == 1 else (slice(None), cidx)
        cidx_perr = cidx if len(y_perr.shape) == 1 else (slice(None), cidx)
        ax.errorbar(y_t[cidx], y_p[cidx], xerr=y_terr[cidx_terr], 
                    yerr=y_perr[cidx_perr], **error_kwargs)
        ax.scatter(**scatter_kwargs)

    def one_to_one(self, **kwargs):
        '''
        Creates a single one to one line, based on current axislimits.
        Best to set axislimits before.
        '''
        kwargs.setdefault('color', 'k')
        kwargs.setdefault('alpha', 1.)
        kwargs.setdefault('zorder', 3)

        ax = self.ax
        vminx, vmaxx = ax.get_xlim()
        vminy, vmaxy = ax.get_ylim()
        vmin, vmax = min(vminx, vminy), max(vmaxx, vmaxy)
        ax.plot([vmin, vmax], [vmin, vmax], **kwargs)
        ax.set_xlim(vminx, vmaxx)
        ax.set_ylim(vminy, vmaxy)

    def set_axislimits(self, xlim=None, ylim='same'):
        '''Sets the axislimits for both axis'''

        if ylim == 'same':
            ylim = xlim
        if xlim is not None:
            self.ax.set_xlim(xlim)
        if ylim is not None:
            self.ax.set_ylim(ylim)

    def set_axislocator(self, axis='both', which='major', locator=None,
                        formatter=None):
        '''Sets the locator and formatter for x,y or both axis'''

        li_axis = []
        if (axis == 'x') or (axis == 'both'):
            li_axis.append(self.ax.xaxis)
        if (axis == 'y') or (axis == 'both'):
            li_axis.append(self.ax.yaxis)
        for axx in li_axis:
            if (which == 'major') or (which == 'both'):
                if locator is not None:
                    axx.set_major_locator(locator)
                if formatter is not None:
                    axx.set_major_formatter(formatter)
            if (which == 'minor') or (which == 'both'):
                if locator is not None:
                    axx.set_minor_locator(locator)
                if formatter is not None:
                    axx.set_minor_formatter(formatter)

    def set_title(self, title, **kwargs):
        '''Sets the band/property titel in bottom right corner.'''
        outline = [path_effects.withStroke(linewidth=3, foreground='white')]
        kwargs = _set_default(
                kwargs, x=0.98, y=0.02, s=title, horizontalalignment='right',
                verticalalignment='bottom', transform=self.ax.transAxes,
                zorder=10, fontweight='bold', fontsize=20,
                path_effects=outline)
        self.ax.text(**kwargs)

    def add_metric(self, y_t, y_p, metric='rmse', **kwargs):
        '''Adds a metric to the top left corenr.'''

        # Calculate metric
        def rmse(yt, yp): return np.sqrt(np.mean(np.square(yt - yp)))
        def me(yt, yp): return np.mean(yp - yt)
        metric = metric.lower()
        d_metric = {'rmse': rmse, 'r2': r2_score, 'me': me}
        if self.should_log:
            y_t, y_p = np.log10(y_t), np.log10(y_p)
        metric_val = d_metric[metric](y_t, y_p)
        # Text styling
        d_metricname = {'rmse': 'RMSE', 'r2': r'$R^2$', 'me': 'ME'}
        metric_string = f'{d_metricname[metric]} = {metric_val:.2f}'
        outline = [path_effects.withStroke(linewidth=2, foreground='white')]
        kwargs = _set_default(
                kwargs, x=0.05, y=self.metric_ypos, s=metric_string,
                horizontalalignment='left', verticalalignment='top',
                transform=self.ax.transAxes, zorder=10,
                path_effects=outline)
        self.ax.text(**kwargs)
        self.metric_ypos -= 0.11

    def mark(self, idx_marked):
        self.idx_marked = idx_marked

def _set_default(dictionary, **kwargs):
    new_dict = {} if dictionary is None else dictionary.copy()
    for key, val in kwargs.items():
        new_dict.setdefault(key, val)
    return new_dict