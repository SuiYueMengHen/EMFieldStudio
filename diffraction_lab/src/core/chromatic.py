import numpy as np
from core.optics import wavelength_to_rgb
from core.diffraction import DiffractionEngine, SimulationParams, PropagationModel
from core.aperture import BaseAperture


LIGHT_SOURCE_PRESETS = {
    'D65': {
        'name': 'D65 标准白光',
        'wavelengths': np.linspace(380, 780, 20).tolist(),
        'weights': None,
    },
    'sodium': {
        'name': '钠灯',
        'wavelengths': [589.0, 589.6],
        'weights': [1.0, 0.5],
    },
    'mercury': {
        'name': '汞灯',
        'wavelengths': [404.7, 435.8, 546.1, 577.0, 579.1],
        'weights': [0.3, 0.5, 1.0, 0.4, 0.4],
    },
    'led_white': {
        'name': 'LED 白光',
        'wavelengths': [450.0, 530.0, 560.0, 610.0, 650.0],
        'weights': [0.6, 0.4, 0.5, 0.7, 0.8],
    },
    'rgb_laser': {
        'name': 'RGB 激光',
        'wavelengths': [445.0, 532.0, 635.0],
        'weights': [1.0, 1.0, 1.0],
    },
}


def uniform_visible_spectrum(n_wavelengths: int = 20) -> tuple:
    wavelengths = np.linspace(380, 780, n_wavelengths)
    weights = np.ones(n_wavelengths)
    return wavelengths, weights


def cauchy_refractive_index(wavelength_nm: float, A: float, B: float, C: float = 0.0) -> float:
    wl_um = wavelength_nm / 1000.0
    return A + B / (wl_um ** 2) + C / (wl_um ** 4)


def sellmeier_refractive_index(wavelength_nm: float, B1: float, C1: float,
                                B2: float, C2: float, B3: float, C3: float) -> float:
    wl_um = wavelength_nm / 1000.0
    wl2 = wl_um ** 2
    n2 = 1.0 + (B1 * wl2 / (wl2 - C1)) + (B2 * wl2 / (wl2 - C2)) + (B3 * wl2 / (wl2 - C3))
    return np.sqrt(max(n2, 1.0))


BK7_SELLMEIER = {'B1': 1.03961212, 'C1': 0.00600069867,
                 'B2': 0.231792344, 'C2': 0.0200179144,
                 'B3': 1.01046945, 'C3': 103.560653}

SF11_SELLMEIER = {'B1': 1.73759695, 'C1': 0.013188707,
                  'B2': 0.313747346, 'C2': 0.0623068142,
                  'B3': 1.89878101, 'C3': 155.23629}

GLASS_PRESETS = {
    'BK7': {'name': 'BK7 玻璃', 'params': BK7_SELLMEIER, 'type': 'sellmeier'},
    'SF11': {'name': 'SF11 玻璃', 'params': SF11_SELLMEIER, 'type': 'sellmeier'},
    'water': {'name': '水', 'params': {'A': 1.3199, 'B': 0.00454, 'C': 0.0}, 'type': 'cauchy'},
}


class ChromaticEngine:

    def __init__(self, use_gpu: bool = False):
        self.engine = DiffractionEngine(use_gpu=use_gpu)

    def compute_chromatic(self, aperture: BaseAperture,
                          wavelengths_nm: np.ndarray,
                          weights: np.ndarray,
                          sim_params: SimulationParams,
                          log_scale: bool = True) -> np.ndarray:
        if weights is None:
            weights = np.ones_like(wavelengths_nm)

        total_weight = np.sum(weights)
        if total_weight > 0:
            weights = weights / total_weight

        first_result = self.engine.compute_diffraction(aperture, sim_params)
        ny, nx = first_result.intensity.shape
        composite_rgb = np.zeros((ny, nx, 3), dtype=np.float64)

        global_max = 0.0
        displays = []

        for i, wl_nm in enumerate(wavelengths_nm):
            wl_m = wl_nm * 1e-9
            w = weights[i]

            sp = SimulationParams(
                wavelength=wl_m,
                grid_size=sim_params.grid_size,
                physical_size=sim_params.physical_size,
                propagation_distance=sim_params.propagation_distance,
                model=sim_params.model,
                pad_factor=sim_params.pad_factor,
            )

            result = self.engine.compute_diffraction(aperture, sp)
            intensity = result.intensity

            if log_scale:
                display = np.log1p(intensity)
            else:
                display = intensity.copy()

            if display.max() > global_max:
                global_max = display.max()

            r, g, b = wavelength_to_rgb(float(wl_nm))
            weighted = display * w
            composite_rgb[:, :, 0] += weighted * r
            composite_rgb[:, :, 1] += weighted * g
            composite_rgb[:, :, 2] += weighted * b

        if global_max > 0:
            composite_rgb = composite_rgb / composite_rgb.max()

        composite_rgb = np.clip(composite_rgb, 0.0, 1.0)
        return composite_rgb

    def compute_chromatic_with_dispersion(self, aperture: BaseAperture,
                                          wavelengths_nm: np.ndarray,
                                          weights: np.ndarray,
                                          sim_params: SimulationParams,
                                          glass_preset: str = 'BK7',
                                          thickness_mm: float = 5.0,
                                          log_scale: bool = True) -> np.ndarray:
        if weights is None:
            weights = np.ones_like(wavelengths_nm)

        total_weight = np.sum(weights)
        if total_weight > 0:
            weights = weights / total_weight

        glass = GLASS_PRESETS.get(glass_preset, GLASS_PRESETS['BK7'])

        first_result = self.engine.compute_diffraction(aperture, sim_params)
        ny, nx = first_result.intensity.shape
        composite_rgb = np.zeros((ny, nx, 3), dtype=np.float64)

        ref_n = None

        for i, wl_nm in enumerate(wavelengths_nm):
            wl_m = wl_nm * 1e-9
            w = weights[i]

            if glass['type'] == 'sellmeier':
                p = glass['params']
                n = sellmeier_refractive_index(wl_nm, p['B1'], p['C1'],
                                                p['B2'], p['C2'], p['B3'], p['C3'])
            else:
                p = glass['params']
                n = cauchy_refractive_index(wl_nm, p['A'], p['B'], p.get('C', 0.0))

            if ref_n is None:
                ref_n = n

            delta_n = n - ref_n
            chromatic_defocus = thickness_mm * 1e-3 * delta_n

            sp = SimulationParams(
                wavelength=wl_m,
                grid_size=sim_params.grid_size,
                physical_size=sim_params.physical_size,
                propagation_distance=sim_params.propagation_distance + chromatic_defocus,
                model=sim_params.model,
                pad_factor=sim_params.pad_factor,
            )

            result = self.engine.compute_diffraction(aperture, sp)
            intensity = result.intensity

            if log_scale:
                display = np.log1p(intensity)
            else:
                display = intensity.copy()

            r, g, b = wavelength_to_rgb(float(wl_nm))
            weighted = display * w
            composite_rgb[:, :, 0] += weighted * r
            composite_rgb[:, :, 1] += weighted * g
            composite_rgb[:, :, 2] += weighted * b

        max_val = composite_rgb.max()
        if max_val > 0:
            composite_rgb = composite_rgb / max_val

        composite_rgb = np.clip(composite_rgb, 0.0, 1.0)
        return composite_rgb
