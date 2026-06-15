import numpy as np
from scipy.ndimage import center_of_mass


def compute_psf(intensity: np.ndarray) -> dict:
    if intensity is None or intensity.size == 0:
        return {}

    peak = float(np.max(intensity))
    total = float(np.sum(intensity))
    center = center_of_mass(intensity)
    cy, cx = int(round(center[0])), int(round(center[1]))

    ny, nx = intensity.shape
    y, x = np.ogrid[:ny, :nx]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    max_r = min(cx, cy, nx - cx - 1, ny - cy - 1)
    if max_r < 1:
        return {'peak': peak, 'total': total}

    r_flat = r.ravel()
    i_flat = intensity.ravel()

    sort_idx = np.argsort(r_flat)
    r_sorted = r_flat[sort_idx]
    i_sorted = i_flat[sort_idx]

    cumsum = np.cumsum(i_sorted)
    ee = cumsum / total if total > 0 else cumsum

    ee_50_idx = np.searchsorted(ee, 0.5)
    ee_86_idx = np.searchsorted(ee, 0.86)
    ee_50_radius = float(r_sorted[min(ee_50_idx, len(r_sorted) - 1)]) if ee_50_idx < len(r_sorted) else 0
    ee_86_radius = float(r_sorted[min(ee_86_idx, len(r_sorted) - 1)]) if ee_86_idx < len(r_sorted) else 0

    h_profile = intensity[cy, :]
    v_profile = intensity[:, cx]

    def measure_fwhm_1d(profile, coords=None):
        max_val = np.max(profile)
        baseline = np.min(profile)
        half_max = (max_val - baseline) / 2.0 + baseline
        above = np.where(profile >= half_max)[0]
        if len(above) < 2:
            return 0.0
        left_idx = above[0]
        right_idx = above[-1]
        if coords is not None:
            left_x = coords[left_idx]
            right_x = coords[right_idx]
            if left_idx > 0 and profile[left_idx - 1] < half_max:
                y1, y2 = profile[left_idx - 1], profile[left_idx]
                if y2 != y1:
                    t = (half_max - y1) / (y2 - y1)
                    left_x = coords[left_idx - 1] + t * (coords[left_idx] - coords[left_idx - 1])
            if right_idx < len(profile) - 1 and profile[right_idx + 1] < half_max:
                y1, y2 = profile[right_idx], profile[right_idx + 1]
                if y2 != y1:
                    t = (half_max - y1) / (y2 - y1)
                    right_x = coords[right_idx] + t * (coords[right_idx + 1] - coords[right_idx])
            return float(right_x - left_x)
        return float(right_idx - left_idx)

    fwhm_h = measure_fwhm_1d(h_profile)
    fwhm_v = measure_fwhm_1d(v_profile)

    num_bins = min(256, max_r)
    bin_edges = np.linspace(0, max_r, num_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    bin_idx = np.digitize(r_flat, bin_edges) - 1

    ee_binned = np.zeros(num_bins)
    for i in range(num_bins):
        mask = bin_idx == i
        if mask.any():
            ee_binned[i] = i_flat[mask].sum() / total if total > 0 else 0
    ee_cumulative = np.cumsum(ee_binned)

    return {
        'peak': peak,
        'total': total,
        'center': (float(cx), float(cy)),
        'fwhm_h': fwhm_h,
        'fwhm_v': fwhm_v,
        'ee_50_radius': ee_50_radius,
        'ee_86_radius': ee_86_radius,
        'ee_radii': bin_centers,
        'ee_values': ee_cumulative,
        'h_profile': h_profile,
        'v_profile': v_profile,
    }


def compute_otf(psf_intensity: np.ndarray) -> np.ndarray:
    """计算OTF，返回居中排列（零频在中心）用于显示"""
    psf_shifted = np.fft.ifftshift(psf_intensity)
    F = np.fft.fft2(psf_shifted)
    if F[0, 0] != 0:
        F = F / F[0, 0]
    return np.fft.fftshift(F)


def compute_mtf(psf_intensity: np.ndarray) -> np.ndarray:
    otf = compute_otf(psf_intensity)
    return np.abs(otf)


def compute_ctf(psf_intensity: np.ndarray) -> np.ndarray:
    otf = compute_otf(psf_intensity)
    return np.real(otf)


def radial_mtf(mtf: np.ndarray, num_bins: int = 128) -> tuple:
    ny, nx = mtf.shape
    cy, cx = ny // 2, nx // 2
    y, x = np.ogrid[:ny, :nx]
    r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)

    max_r = min(cx, cy)
    bins = np.linspace(0, max_r, num_bins + 1)
    bin_centers = (bins[:-1] + bins[1:]) / 2

    r_flat = r.ravel()
    mtf_flat = mtf.ravel()
    bin_indices = np.digitize(r_flat, bins) - 1

    radial_vals = np.zeros(num_bins)
    counts = np.zeros(num_bins)
    valid = (bin_indices >= 0) & (bin_indices < num_bins)
    for i in range(num_bins):
        mask = bin_indices == i
        if mask.any():
            radial_vals[i] = mtf_flat[mask].mean()

    return bin_centers, radial_vals


def strehl_ratio(intensity: np.ndarray, perfect_peak: float = None) -> float:
    peak = float(np.max(intensity))
    if perfect_peak is not None and perfect_peak > 0:
        return peak / perfect_peak
    return -1.0
