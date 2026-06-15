SPEED_OF_LIGHT = 2.99792458e8
PLANCK_CONSTANT = 6.62607015e-34
BOLTZMANN_CONSTANT = 1.380649e-23

UM_TO_M = 1e-6
NM_TO_M = 1e-9
MM_TO_M = 1e-3
CM_TO_M = 1e-2


def nm_to_m(nm: float) -> float:
    return nm * NM_TO_M


def um_to_m(um: float) -> float:
    return um * UM_TO_M


def mm_to_m(mm: float) -> float:
    return mm * MM_TO_M


def m_to_nm(m: float) -> float:
    return m / NM_TO_M


def m_to_um(m: float) -> float:
    return m / UM_TO_M


def m_to_mm(m: float) -> float:
    return m / MM_TO_M


def degrees_to_radians(deg: float) -> float:
    import math
    return deg * math.pi / 180.0


def radians_to_degrees(rad: float) -> float:
    import math
    return rad * 180.0 / math.pi


def wavelength_to_frequency(wavelength_m: float) -> float:
    return SPEED_OF_LIGHT / wavelength_m


def frequency_to_wavelength(freq_hz: float) -> float:
    return SPEED_OF_LIGHT / freq_hz


def wavelength_to_energy(wavelength_m: float) -> float:
    return PLANCK_CONSTANT * SPEED_OF_LIGHT / wavelength_m
