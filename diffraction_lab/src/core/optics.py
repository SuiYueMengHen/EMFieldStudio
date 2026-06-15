import numpy as np
from .units import SPEED_OF_LIGHT


def airy_disk_angular_radius(wavelength: float, aperture_diameter: float) -> float:
    """Airy 斑角半径（弧度）"""
    return 1.22 * wavelength / aperture_diameter


def rayleigh_criterion(wavelength: float, aperture_diameter: float) -> float:
    """瑞利判据最小可分辨角距离（弧度）"""
    return 1.22 * wavelength / aperture_diameter


def fresnel_number(wavelength: float, aperture_radius: float, distance: float) -> float:
    return aperture_radius ** 2 / (wavelength * distance)


def is_far_field(wavelength: float, aperture_radius: float, distance: float) -> bool:
    """远场判据：菲涅尔数 <= 0.25（与 far_field_distance 一致）"""
    return fresnel_number(wavelength, aperture_radius, distance) <= 0.25


def far_field_distance(wavelength: float, aperture_diameter: float) -> float:
    return aperture_diameter ** 2 / wavelength


def wavelength_to_rgb(wavelength_nm: float) -> tuple:
    if wavelength_nm < 380:
        r, g, b = 0.0, 0.0, 0.0
    elif wavelength_nm < 440:
        r = -(wavelength_nm - 440) / (440 - 380)
        g = 0.0
        b = 1.0
    elif wavelength_nm < 490:
        r = 0.0
        g = (wavelength_nm - 440) / (490 - 440)
        b = 1.0
    elif wavelength_nm < 510:
        r = 0.0
        g = 1.0
        b = -(wavelength_nm - 510) / (510 - 490)
    elif wavelength_nm < 580:
        r = (wavelength_nm - 510) / (580 - 510)
        g = 1.0
        b = 0.0
    elif wavelength_nm < 645:
        r = 1.0
        g = -(wavelength_nm - 645) / (645 - 580)
        b = 0.0
    elif wavelength_nm <= 780:
        r = 1.0
        g = 0.0
        b = 0.0
    else:
        r, g, b = 0.0, 0.0, 0.0

    if 380 <= wavelength_nm < 420:
        factor = 0.3 + 0.7 * (wavelength_nm - 380) / (420 - 380)
    elif 420 <= wavelength_nm <= 700:
        factor = 1.0
    elif 700 < wavelength_nm <= 780:
        factor = 0.3 + 0.7 * (780 - wavelength_nm) / (780 - 700)
    else:
        factor = 0.0

    return (r * factor, g * factor, b * factor)


def strehl_ratio(peak_aberrant: float, peak_perfect: float) -> float:
    return peak_aberrant / peak_perfect


def optical_transfer_function(psf: np.ndarray) -> np.ndarray:
    """光学传递函数 (OTF)，返回标准FFT排列（零频在[0,0]）"""
    psf_shifted = np.fft.ifftshift(psf)
    otf = np.fft.fft2(psf_shifted)
    otf = otf / otf[0, 0]
    return otf


def modulation_transfer_function(psf: np.ndarray) -> np.ndarray:
    otf = optical_transfer_function(psf)
    mtf = np.abs(otf)
    return mtf


def encircled_energy(intensity: np.ndarray, center: tuple = None, max_radius: int = None) -> tuple:
    if center is None:
        center = (intensity.shape[0] // 2, intensity.shape[1] // 2)

    cy, cx = center
    ny, nx = intensity.shape
    y, x = np.ogrid[:ny, :nx]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    if max_radius is None:
        max_radius = min(cx, cy, nx - cx - 1, ny - cy - 1)

    radii = np.arange(0, max_radius + 1)
    total_energy = intensity.sum()
    ee = np.zeros_like(radii, dtype=np.float64)

    for i, rad in enumerate(radii):
        mask = r <= rad
        ee[i] = intensity[mask].sum() / total_energy

    return radii, ee
