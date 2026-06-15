import numpy as np
from math import factorial


def zernike_radial(n: int, m: int, rho: np.ndarray) -> np.ndarray:
    m_abs = abs(m)
    result = np.zeros_like(rho, dtype=np.float64)
    for k in range((n - m_abs) // 2 + 1):
        coeff = ((-1) ** k * factorial(n - k) /
                 (factorial(k) *
                  factorial((n + m_abs) // 2 - k) *
                  factorial((n - m_abs) // 2 - k)))
        result += coeff * rho ** (n - 2 * k)
    return result


def zernike_polynomial(n: int, m: int, rho: np.ndarray,
                       theta: np.ndarray) -> np.ndarray:
    R = zernike_radial(n, abs(m), rho)
    if m > 0:
        return R * np.cos(m * theta)
    elif m < 0:
        return R * np.sin(abs(m) * theta)
    else:
        return R


ZERNIKE_INDICES = {
    'piston': (0, 0),
    'tip': (1, 1),
    'tilt': (1, -1),
    'defocus': (2, 0),
    'astigmatism_0': (2, 2),
    'astigmatism_45': (2, -2),
    'coma_x': (3, 1),
    'coma_y': (3, -1),
    'trefoil_x': (3, 3),
    'trefoil_y': (3, -3),
    'spherical': (4, 0),
    'secondary_astigmatism_0': (4, 2),
    'secondary_astigmatism_45': (4, -2),
    'quadrafoil_x': (4, 4),
    'quadrafoil_y': (4, -4),
}


def compute_wavefront(x_grid: np.ndarray, y_grid: np.ndarray,
                      aperture_radius: float,
                      coefficients: dict) -> tuple:
    rho = np.sqrt(x_grid ** 2 + y_grid ** 2) / aperture_radius
    theta = np.arctan2(y_grid, x_grid)

    aperture_mask = rho <= 1.0
    rho_safe = np.where(aperture_mask, rho, 0.0)
    wavefront = np.zeros_like(rho, dtype=np.float64)

    for name, coeff in coefficients.items():
        if coeff == 0:
            continue
        if name in ZERNIKE_INDICES:
            n, m = ZERNIKE_INDICES[name]
            Z = zernike_polynomial(n, m, rho_safe, theta)
            wavefront += coeff * Z

    wavefront[~aperture_mask] = 0.0

    return wavefront, aperture_mask


def apply_aberration(field: np.ndarray, wavefront: np.ndarray,
                     wavelength: float,
                     aperture_mask: np.ndarray = None) -> np.ndarray:
    phase = 2 * np.pi * wavefront / wavelength
    result = field * np.exp(1j * phase)
    if aperture_mask is not None:
        result[~aperture_mask] = 0.0
    return result


def zernike_names() -> list:
    return list(ZERNIKE_INDICES.keys())
