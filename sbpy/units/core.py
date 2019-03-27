# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""sbpy units core module

This package defines Vega-based magnitude systems, and a units
equivalency function for converting to/from flux density.

To use these units in the top-level `astropy.units` namespace::

    >>> import sbpy.units
    >>> sbpy.units.enable()    # doctest: +SKIP

"""

__all__ = [
    'spectral_density_vega',
    'enable',
    'VEGA',
    'VEGAmag',
    'JM',
    'JMmag',
    'magnitude_reflectance',
    'magnitude_xsection'
]

from warnings import warn
import numpy as np
import astropy.units as u
from astropy.utils.exceptions import AstropyWarning
from ..spectroscopy.vega import Vega
from ..spectroscopy.sun import Sun


VEGA = u.def_unit(['VEGA', 'VEGAflux'], doc='Spectral flux density of Vega.')

VEGAmag = u.MagUnit(VEGA)
VEGAmag.__doc__ = "Vega-based magnitude: Vega is 0 mag at all wavelengths"

JM = u.def_unit(['JM', 'JMflux'], represents=VEGA * 10**(0.4 * 0.03),
                doc=('Johnson-Morgan magnitude system flux density '
                     'zeropoint (Johnson et al. 1966; Bessell & Murphy '
                     '2012).'))

JMmag = u.MagUnit(JM)
JMmag.__doc__ = ("Johnson-Morgan magnitude system: Vega is 0.03 mag at "
                 "all wavelengths (Johnson et al. 1966; Bessell & Murphy "
                 "2012).")


def enable():
    """Enable `sbpy` units in the top-level `~astropy.units` namespace.

    Allows the use in `~astropy.units.UnitBase.find_equivalent_units` and
    `~astropy.units.UnitBase.compose`.

    May be used with the ``with`` statement to enable them temporarily.

    """
    import inspect
    return u.add_enabled_units(inspect.getmodule(enable))


def spectral_density_vega(wfb):
    """Flux density equivalencies with Vega-based magnitude systems.

    Requires `~synphot`.

    Uses the default `sbpy` Vega spectrum.

    Vega is assumed to have an apparent magnitude of 0 in the
    ``VEGAmag`` system, and 0.03 in the Johnson-Morgan, ``JMmag``,
    system [Joh66, BM12]_.


    Parameters
    ----------
    wfb : `~astropy.units.Quantity`, `~synphot.SpectralElement`, string
        Wavelength, frequency, or a bandpass of the corresponding flux
        density being converted.  See
        :func:`~synphot.SpectralElement.from_filter()` for possible
        bandpass names.


    Returns
    -------
    eqv : list
        List of equivalencies.


    Examples
    --------
    >>> import astropy.units as u
    >>> from sbpy.units import spectral_density_vega, VEGAmag
    >>> m = 0 * VEGAmag
    >>> fluxd = m.to(u.Jy, spectral_density_vega(5500 * u.AA))
    >>> fluxd.value   # doctest: +FLOAT_CMP
    3578.9571538333985


    References
    ----------
    [Joh66] Johnson et al. 1966, Commun. Lunar Planet. Lab. 4, 99

    [BM12] Bessell & Murphy 2012, PASP 124, 140-157

    """

    # warn rather than raise an exception so that code that uses
    # spectral_density_vega when it doesn't need it will still run.
    try:
        import synphot
    except ImportError:
        warn(AstropyWarning('synphot required for Vega-based magnitude'
                            ' conversions.'))
        return []

    vega = Vega.from_default()
    if isinstance(wfb, u.Quantity):
        wav = wfb
        fnu0 = vega(wfb, unit='W/(m2 Hz)')
        flam0 = vega(wfb, unit='W/(m2 um)')
    elif isinstance(wfb, (synphot.SpectralElement, str)):
        fnu0 = vega.filt(wfb, unit='W/(m2 Hz)')[1]
        flam0 = vega.filt(wfb, unit='W/(m2 um)')[1]

    return [
        (fnu0.unit, VEGA, lambda x: x / fnu0.value,
         lambda x: x * fnu0.value),
        (flam0.unit, VEGA, lambda x: x / flam0.value,
         lambda x: x * flam0.value)
    ]


def magnitude_reflectance(xsec, wfb=None, M_sun=None):
    """Magnitude - reflectance equivalencies to convert between magnitude and
    average reflectance for given scattering cross-section.

    The default magnitude system is ``VEGAmag``, where the apparent magnitude
    of Vega is assumed to be 0 in all and any wavelengths and bands.  If other
    magnitude system is used, then it is implicitly inferred from the solar
    magnitude passed by keyword 'M_sun'.

    Parameters
    ----------
    xsec : `~astropy.units.Quantity`
        Scattering cross-section of the object of interest
    wfb : `~astropy.units.Quantity`, `~synphot.SpectralElement`, string
        Wavelength, frequency, or a bandpass of the corresponding flux
        density being converted.  See
        :func:`~synphot.SpectralElement.from_filter()` for possible
        bandpass names.  If provided, then this parameter overrides `M_sun`.
    M_sun : `~astropy.units.Quantity`
        Solar magnitude in the same magnitude system as the quantity to be
        converted.  If `wfb` is not provided, then `M_sun` will be used
        in the conversion.  If neither `wfb` nor `M_sun` is present, then
        the default V-band solar magnitude, -26.775 VEGAmag will be used.

    Returns
    -------
    eqv : list
        List of equivalencies

    Examples
    --------
    >>> import numpy as np
    >>> from astropy import units as u
    >>> from sbpy.units import magnitude_reflectance, VEGAmag
    >>> m = 3.4 * VEGAmag
    >>> xsec = np.pi * (460 * u.km)**2
    >>> ref = m.to('1/sr', magnitude_reflectance(xsec))
    >>> print('{0:.4f}'.format(ref))
    0.0287 1 / sr
    >>>
    >>> m1 = ref.to(VEGAmag, magnitude_reflectance(xsec))
    >>> print('{0:.2f}'.format(m1))
    3.40 mag(VEGA)
    """
    if wfb is not None:
        try:
            import synphot
        except ImportError:
            warn(AstropyWarning('synphot required for Vega-based magnitude'
                            ' conversions.'))
            return []
        sun = Sun.from_default()
        if isinstance(wfb, u.Quantity):
            f_sun = sun(wfb).to(VEGA, spectral_density_vega(wfb))
        elif isinstance(wfb, (synphot.SpectralElement, str)):
            f_sun = sun.filt(wfb)[1].to(VEGA, spectral_density_vega(wfb))
        else:
            raise ValueError('unrecognized type for `wfb`')
        M_sun = f_sun.to(VEGAmag)
        f_sun = f_sun.value
    else:
        if M_sun is None:
            M_sun = -26.77471503 * VEGAmag
        if not hasattr(M_sun.unit, 'physical_unit'):
            raise u.UnitTypeError('the magnitude system must be based on a physical unit')
        f_sun = M_sun.to(M_sun.unit.physical_unit).value
    return [(M_sun.unit.physical_unit,
             u.sr**-1,
             lambda mag: mag/(f_sun*xsec.to('au2').value),
             lambda ref: ref*f_sun*xsec.to('au2').value)]


def magnitude_xsection(ref, wfb=None, M_sun=None):
    """Magnitude - cross-section equivalencies to convert between magnitude
    and scattering cross-section for given average reflectance.

    The default magnitude system is ``VEGAmag``, where the apparent magnitude
    of Vega is assumed to be 0 in all and any wavelengths and bands.  If other
    magnitude system is used, then it is implicitly inferred from the solar
    magnitude passed by keyword 'M_sun'.

    Parameters
    ----------
    ref : `~astropy.units.Quantity`
        Average reflectance of the object of interest
    wfb : `~astropy.units.Quantity`, `~synphot.SpectralElement`, string
        Wavelength, frequency, or a bandpass of the corresponding flux
        density being converted.  See
        :func:`~synphot.SpectralElement.from_filter()` for possible
        bandpass names.  If provided, then this parameter overrides `M_sun`.
    M_sun : `~astropy.units.Quantity`
        Solar magnitude in the same magnitude system as the quantity to be
        converted.  If `wfb` is not provided, then `M_sun` will be used
        in the conversion.  If neither `wfb` nor `M_sun` is present, then
        the default V-band solar magnitude, -26.775 VEGAmag will be used.

    Returns
    -------
    eqv : list
        List of equivalencies

    Examples
    --------
    >>> from astropy import units as u
    >>> from sbpy.units import magnitude_xsection, VEGAmag
    >>> m = 3.4 * VEGAmag
    >>> ref = 0.0287 / u.sr
    >>> xsec = m.to('km2', magnitude_xsection(ref))
    >>> radius = np.sqrt(xsec/np.pi)
    >>> print('{0:.2f}'.format(radius))
    459.69 km
    >>>
    >>> m1 = xsec.to(VEGAmag, magnitude_xsection(ref))
    >>> print('{0:.2f}'.format(m1))
    3.40 mag(VEGA)
    """
    if wfb is not None:
        try:
            import synphot
        except ImportError:
            warn(AstropyWarning('synphot required for Vega-based magnitude'
                            ' conversions.'))
            return []
        sun = Sun.from_default()
        if isinstance(wfb, u.Quantity):
            f_sun = sun(wfb).to(VEGA, spectral_density_vega(wfb))
        elif isinstance(wfb, (synphot.SpectralElement, str)):
            f_sun = sun.filt(wfb)[1].to(VEGA, spectral_density_vega(wfb))
        else:
            raise ValueError('unrecognized type for `wfb`')
        M_sun = f_sun.to(VEGAmag)
        f_sun = f_sun.value
    else:
        if M_sun is None:
            M_sun = -26.77471503 * VEGAmag
        if not hasattr(M_sun.unit, 'physical_unit'):
            raise u.UnitTypeError('the magnitude system must be based on a physical unit')
        f_sun = M_sun.to(M_sun.unit.physical_unit).value
    ref = ref.to('1/sr').value
    return [(M_sun.unit.physical_unit,
             u.km**2,
             lambda mag: mag/(f_sun*ref)*u.au.to('km')**2,
             lambda xsec: f_sun*ref*xsec*u.km.to('au')**2)]
