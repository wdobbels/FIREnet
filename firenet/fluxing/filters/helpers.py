from functools import wraps
import numpy as np

def combine_grids(ga, gb):
    '''Combines 2 grids into one (all points of both are preserved)'''

    if (ga[-1] < gb[0]) or (gb[-1] < ga[0]):
        raise ValueError('Grid a and b are incompatible!')
    ga = np.array(ga)
    gb = np.array(gb)
    g1 = ga[(ga >= gb[0]) & (ga <= gb[-1])]
    g2 = gb[(gb >= ga[0]) & (gb <= ga[-1])]
    return np.sort(np.unique(np.hstack((g1, g2))))

def interpolate_log(x, xp, yp, logx=True, logy=True, **kwargs):
    '''Interpolate in logspace (useful for SEDs)'''

    if logx:
        x = np.log(x)
        xp = np.log(xp)
    if logy:
        yp = log(yp)
    interp = np.interp(x, xp, yp, **kwargs)
    if logy:
        interp = np.exp(interp)
    return interp

def log(x):
    '''Takes log, making invalid values a very small number'''

    zeromask = x<=0
    logx = np.empty(x.shape)
    # the largest negative value for which np.exp(x) returns zero
    logx[zeromask] = -750.
    logx[~zeromask] = np.log(x[~zeromask])
    return logx

def cache_simple_method(func):
    """Cache a method that takes no arguments to its return value"""

    @wraps(func)
    def execute_method(self):
        if not hasattr(self, '_cache'):
            self._cache = {}
        key = func.__name__
        if key not in self._cache:
            self._cache[key] = func(self)
        return self._cache[key]
    return execute_method