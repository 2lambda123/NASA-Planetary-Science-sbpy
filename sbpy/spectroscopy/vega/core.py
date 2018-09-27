# Licensed under a 3-clause BSD style license - see LICENSE.rst
"""
=====================
SBPy Vega Core Module
=====================
"""

import astropy.units as u
from astropy.utils.state import ScienceState
from ..core import SpectralStandard

__doctest_requires__ = {'Sun': 'synphot'}

__all__ = [
    'Vega',
    'default_vega'
]


class Vega(SpectralStandard):
    """Vega spectrum.

    Parameters
    ----------
    wave : `~astropy.units.Quantity`
      The spectral wavelengths.

    fluxd : `~astropy.units.Quantity`
      The solar flux densities, at 1 au.

    description : string, optional
      A brief description of the source spectrum.

    bibcode : string, optional
      Bibliography code for `sbpy.bib.register`.

    meta : dict, optional
      Any additional meta data, passed on to
      `~synphot.SourceSpectrum`.


    Attributes
    ----------
    wave        - Wavelengths of the source spectrum.
    fluxd       - Source spectrum.
    description - Brief description of the source spectrum.
    meta        - Meta data.


    Examples
    --------
    Get the default Vega spectrum:
    >>> vega = Vega.from_default()

    Create Vega from a file:
    >>> vega = Vega.from_file('filename')               # doctest: +SKIP

    Evaluate Vega at 1 μm:
    >>> print(vega(1 * u.um))                   # doctest: +SKIP

    """

    def __repr__(self):
        if self.description is None:
            return '<Vega>'
        else:
            return '<Vega: {}>'.format(self.description)

    @classmethod
    def from_builtin(cls, name):
        """Vega spectrum from a built-in `sbpy` source.

        Parameters
        ----------
        name : string
          The name of a Vega spectrum parameter set in
          `sbpy.spectroscopy.vega.sources`.

        """

        import os
        from . import sources

        try:
            parameters = getattr(sources, name)
            vega = Vega.from_file(**parameters)
        except AttributeError:
            msg = 'Unknown Vega spectrum "{}".  Valid spectra:\n{}'.format(
                name, sources.keys())
            raise ValueError(msg)

        return vega

    @classmethod
    def from_default(cls):
        """Return the `sbpy` default Vega spectrum."""
        return default_vega.get()


class default_vega(ScienceState):
    """Get/set the `sbpy` default Vega spectrum.

    To change it:

    >>> from sbpy.spectroscopy.vega import default_vega
    >>> with default_vega(Vega.from_file(filename))  # doctest: +SKIP
    ...     # Vega from filename in effect

    """
    _value = 'Bohlin2014'

    @classmethod
    def validate(cls, value):
        if isinstance(value, str):
            return Vega.from_builtin(value)
        elif isinstance(value, Vega):
            return value
        else:
            raise TypeError("default_vega must be a string or Vega instance.")
