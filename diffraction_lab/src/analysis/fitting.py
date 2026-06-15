import numpy as np
from scipy.optimize import curve_fit
from typing import Tuple, Optional, Dict


def gaussian(x: np.ndarray, amplitude: float, center: float,
             sigma: float, offset: float = 0) -> np.ndarray:
    return amplitude * np.exp(-(x - center) ** 2 / (2 * sigma ** 2)) + offset


def fit_gaussian(coords: np.ndarray, profile: np.ndarray) -> Optional[Dict]:
    try:
        max_idx = np.argmax(profile)
        amplitude_guess = profile[max_idx]
        center_guess = coords[max_idx]
        offset_guess = np.min(profile)

        half_max = (amplitude_guess - offset_guess) / 2.0 + offset_guess
        above_half = np.where(profile >= half_max)[0]
        if len(above_half) < 2:
            return None

        fwhm_guess = coords[above_half[-1]] - coords[above_half[0]]
        sigma_guess = fwhm_guess / (2 * np.sqrt(2 * np.log(2))) if fwhm_guess > 0 else 1.0

        p0 = [amplitude_guess, center_guess, sigma_guess, offset_guess]
        bounds = (
            [0, coords.min(), 0, -np.inf],
            [np.inf, coords.max(), (coords.max() - coords.min()), np.inf]
        )

        popt, pcov = curve_fit(gaussian, coords, profile, p0=p0, bounds=bounds,
                                maxfev=5000)

        amplitude, center, sigma, offset = popt
        fwhm = 2 * np.sqrt(2 * np.log(2)) * sigma

        y_pred = gaussian(coords, *popt)
        ss_res = np.sum((profile - y_pred) ** 2)
        ss_tot = np.sum((profile - np.mean(profile)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        perr = np.sqrt(np.diag(pcov))

        return {
            'amplitude': amplitude,
            'center': center,
            'sigma': sigma,
            'offset': offset,
            'fwhm': fwhm,
            'r_squared': r_squared,
            'params': popt,
            'errors': perr,
            'fit_func': lambda x: gaussian(x, *popt),
        }
    except Exception:
        return None


def airy_function(x: np.ndarray, amplitude: float, center: float,
                  scale: float, offset: float = 0) -> np.ndarray:
    from scipy.special import j1
    r = np.abs(x - center) * scale
    result = np.ones_like(r) * amplitude
    mask = r > 1e-10
    result[mask] = amplitude * (2 * j1(r[mask]) / r[mask]) ** 2
    return result + offset


def fit_airy(coords: np.ndarray, profile: np.ndarray) -> Optional[Dict]:
    try:
        max_idx = np.argmax(profile)
        amplitude_guess = profile[max_idx]
        center_guess = coords[max_idx]
        offset_guess = np.min(profile)

        half_max = (amplitude_guess - offset_guess) / 2.0 + offset_guess
        above_half = np.where(profile >= half_max)[0]
        if len(above_half) < 2:
            return None

        fwhm_guess = coords[above_half[-1]] - coords[above_half[0]]
        # Airy函数FWHM对应 r ≈ 1.61634（数值求解 [2*J1(r)/r]^2 = 0.5 的根）
        scale_guess = 1.61634 / (fwhm_guess / 2) if fwhm_guess > 0 else 1.0

        p0 = [amplitude_guess, center_guess, scale_guess, offset_guess]
        bounds = (
            [0, coords.min(), 0, -np.inf],
            [np.inf, coords.max(), np.inf, np.inf]
        )

        popt, pcov = curve_fit(airy_function, coords, profile, p0=p0,
                                bounds=bounds, maxfev=5000)

        amplitude, center, scale, offset = popt
        from scipy.special import jn_zeros
        airy_radius = jn_zeros(1, 1)[0] / scale if scale > 0 else 0

        y_pred = airy_function(coords, *popt)
        ss_res = np.sum((profile - y_pred) ** 2)
        ss_tot = np.sum((profile - np.mean(profile)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        perr = np.sqrt(np.diag(pcov))

        return {
            'amplitude': amplitude,
            'center': center,
            'scale': scale,
            'offset': offset,
            'airy_radius': airy_radius,
            'r_squared': r_squared,
            'params': popt,
            'errors': perr,
            'fit_func': lambda x: airy_function(x, *popt),
        }
    except Exception:
        return None


def multi_peak_gaussian(x: np.ndarray, *params) -> np.ndarray:
    n_peaks = (len(params) - 1) // 3
    offset = params[-1]
    result = np.full_like(x, offset, dtype=np.float64)
    for i in range(n_peaks):
        amplitude = params[i * 3]
        center = params[i * 3 + 1]
        sigma = params[i * 3 + 2]
        result += amplitude * np.exp(-(x - center) ** 2 / (2 * sigma ** 2))
    return result


def fit_multi_peak(coords: np.ndarray, profile: np.ndarray,
                   n_peaks: int = 2) -> Optional[Dict]:
    try:
        from scipy.signal import find_peaks

        peaks, properties = find_peaks(profile, height=np.max(profile) * 0.1,
                                        distance=len(profile) // (n_peaks * 2))

        if len(peaks) < n_peaks:
            sorted_indices = np.argsort(profile[peaks])[::-1]
            peaks = peaks[sorted_indices]

        p0 = []
        bounds_low = []
        bounds_high = []

        for i in range(n_peaks):
            if i < len(peaks):
                amp = profile[peaks[i]]
                cen = coords[peaks[i]]
            else:
                amp = np.max(profile) / (i + 2)
                cen = coords[len(coords) // (i + 2)]

            sigma = (coords[-1] - coords[0]) / (n_peaks * 4)
            p0.extend([amp, cen, sigma])
            bounds_low.extend([0, coords.min(), 0])
            bounds_high.extend([np.inf, coords.max(), (coords.max() - coords.min())])

        offset_guess = np.min(profile)
        p0.append(offset_guess)
        bounds_low.append(-np.inf)
        bounds_high.append(np.inf)

        popt, pcov = curve_fit(multi_peak_gaussian, coords, profile,
                                p0=p0, bounds=(bounds_low, bounds_high),
                                maxfev=10000)

        y_pred = multi_peak_gaussian(coords, *popt)
        ss_res = np.sum((profile - y_pred) ** 2)
        ss_tot = np.sum((profile - np.mean(profile)) ** 2)
        r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        peaks_info = []
        for i in range(n_peaks):
            amplitude = popt[i * 3]
            center = popt[i * 3 + 1]
            sigma = popt[i * 3 + 2]
            fwhm = 2 * np.sqrt(2 * np.log(2)) * sigma
            peaks_info.append({
                'amplitude': amplitude,
                'center': center,
                'sigma': sigma,
                'fwhm': fwhm,
            })

        return {
            'peaks': peaks_info,
            'r_squared': r_squared,
            'params': popt,
            'fit_func': lambda x: multi_peak_gaussian(x, *popt),
        }
    except Exception:
        return None
