import numpy as np
from typing import Tuple, Optional


def measure_fwhm(coords: np.ndarray, profile: np.ndarray) -> Optional[float]:
    if len(profile) < 3:
        return None

    max_val = np.max(profile)
    baseline = np.min(profile)
    half_max = (max_val - baseline) / 2.0 + baseline

    above = np.where(profile >= half_max)[0]
    if len(above) < 2:
        return None

    left_idx = above[0]
    right_idx = above[-1]

    if left_idx > 0:
        x1, x2 = coords[left_idx - 1], coords[left_idx]
        y1, y2 = profile[left_idx - 1], profile[left_idx]
        if y2 != y1:
            t = (half_max - y1) / (y2 - y1)
            left_x = x1 + t * (x2 - x1)
        else:
            left_x = coords[left_idx]
    else:
        left_x = coords[left_idx]

    if right_idx < len(profile) - 1:
        x1, x2 = coords[right_idx], coords[right_idx + 1]
        y1, y2 = profile[right_idx], profile[right_idx + 1]
        if y2 != y1:
            t = (half_max - y1) / (y2 - y1)
            right_x = x1 + t * (x2 - x1)
        else:
            right_x = coords[right_idx]
    else:
        right_x = coords[right_idx]

    return float(right_x - left_x)


def find_peak_position(coords: np.ndarray, profile: np.ndarray) -> Tuple[float, float]:
    max_idx = np.argmax(profile)
    return float(coords[max_idx]), float(profile[max_idx])


def total_intensity(intensity: np.ndarray) -> float:
    return float(np.sum(intensity))


def peak_intensity(intensity: np.ndarray) -> float:
    return float(np.max(intensity))


def encircled_energy(intensity: np.ndarray, center: tuple = None,
                     max_radius: int = None) -> Tuple[np.ndarray, np.ndarray]:
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
    if total_energy == 0:
        return radii, np.zeros_like(radii, dtype=np.float64)

    ee = np.zeros_like(radii, dtype=np.float64)
    for i, rad in enumerate(radii):
        mask = r <= rad
        ee[i] = intensity[mask].sum() / total_energy

    return radii, ee


def strehl_ratio(intensity: np.ndarray, perfect_intensity: np.ndarray = None) -> float:
    peak = np.max(intensity)
    if perfect_intensity is not None:
        perfect_peak = np.max(perfect_intensity)
        if perfect_peak == 0:
            return 0.0
        return float(peak / perfect_peak)
    return -1.0


def radial_profile(intensity: np.ndarray, center: tuple = None,
                   num_bins: int = 256) -> Tuple[np.ndarray, np.ndarray]:
    if center is None:
        center = (intensity.shape[0] // 2, intensity.shape[1] // 2)

    cy, cx = center
    ny, nx = intensity.shape
    y, x = np.ogrid[:ny, :nx]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    max_r = min(cx, cy, nx - cx - 1, ny - cy - 1)
    bins = np.linspace(0, max_r, num_bins + 1)

    radial_intensity = np.zeros(num_bins)
    bin_counts = np.zeros(num_bins)

    r_flat = r.flatten()
    i_flat = intensity.flatten()

    bin_indices = np.digitize(r_flat, bins) - 1
    valid = (bin_indices >= 0) & (bin_indices < num_bins)

    for idx in range(num_bins):
        mask = bin_indices == idx
        if mask.any():
            radial_intensity[idx] = i_flat[mask].mean()
            bin_counts[idx] = mask.sum()

    bin_centers = (bins[:-1] + bins[1:]) / 2
    return bin_centers, radial_intensity
