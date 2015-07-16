
'''Differential Atmospheric Refraction'''

import numpy
from scipy.interpolate import RectBivariateSpline

class DAR(object):
    '''Null DAR correction (always 0.0).'''
    def value(self, airmass, wl, temp=11.5, rh=44.2, press=772.2):
        # FIXME: Not counting here a possible array in airmass
        return numpy.zeros_like(wl)

class DARFromLUT(DAR):
    '''DAR correction obtained from a look-up table.

        The table is obtained from 
          `http://www.eso.org/gen-fac/pubs/astclim/lasilla/diffrefr.html`

        The temperature, relative humidity and pressure are fixed to
         
         * La Silla (T=11.5 C, RH=44.2%, P=772.2mbar)

    '''
    def __init__(self, fileobj):
        matrix = numpy.loadtxt(fileobj)
        # column-0 is the airmass
        # column-1 to the end are DAR correction referred to 5000AA
        # wavelengths are [3000, 3500, ..., 10000]

        # bivariate interpolator
        x = matrix[:,0 ]
        y = numpy.linspace(3000, 10000, num=15)
        z = matrix[:,1:]
        self.interpolator = RectBivariateSpline(x, y, z)

    def value(self, airmass, wl, **kwds):
        # temperature, relative humidity and pressure are ignored
        return self.interpolator(airmass, wl)

