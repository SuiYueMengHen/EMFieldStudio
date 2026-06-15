from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

import numpy as np

from .aperture import BaseAperture


class PropagationModel(Enum):
    FRAUNHOFER = "fraunhofer"
    FRESNEL_ASM = "fresnel_asm"
    FRESNEL_IR = "fresnel_ir"
    RAYLEIGH_SOMMERFELD = "rayleigh_sommerfeld"


@dataclass
class SimulationParams:
    wavelength: float = 532e-9
    grid_size: int = 1024
    physical_size: float = 100e-6
    propagation_distance: float = 0.1
    model: PropagationModel = PropagationModel.FRAUNHOFER
    pad_factor: float = 2.0


@dataclass
class DiffractionResult:
    intensity: np.ndarray = None
    complex_field: np.ndarray = None
    x_freq: np.ndarray = None
    y_freq: np.ndarray = None
    dx_output: float = 0.0
    metadata: dict = field(default_factory=dict)

    def get_cross_section(self, angle: float = 0, center: tuple = None) -> Tuple[np.ndarray, np.ndarray]:
        if self.intensity is None:
            return np.array([]), np.array([])

        ny, nx = self.intensity.shape
        if center is None:
            center = (nx // 2, ny // 2)

        cx, cy = center
        theta = np.radians(angle)
        length = min(cx, cy, nx - cx - 1, ny - cy - 1)
        s = np.arange(-length, length + 1)
        xs = cx + s * np.cos(theta)
        ys = cy + s * np.sin(theta)

        xs = np.clip(xs.astype(int), 0, nx - 1)
        ys = np.clip(ys.astype(int), 0, ny - 1)

        profile = self.intensity[ys, xs]

        if self.x_freq is not None and self.y_freq is not None:
            dx = self.dx_output if self.dx_output > 0 else 1.0
            coords = s * dx
        else:
            coords = s.astype(float)

        return coords, profile

    def get_horizontal_profile(self, row: int = None) -> Tuple[np.ndarray, np.ndarray]:
        if self.intensity is None:
            return np.array([]), np.array([])
        if row is None:
            row = self.intensity.shape[0] // 2
        profile = self.intensity[row, :]
        if self.x_freq is not None:
            coords = self.x_freq
        else:
            coords = np.arange(len(profile), dtype=float)
        return coords, profile

    def get_vertical_profile(self, col: int = None) -> Tuple[np.ndarray, np.ndarray]:
        if self.intensity is None:
            return np.array([]), np.array([])
        if col is None:
            col = self.intensity.shape[1] // 2
        profile = self.intensity[:, col]
        if self.y_freq is not None:
            coords = self.y_freq
        else:
            coords = np.arange(len(profile), dtype=float)
        return coords, profile


class DiffractionEngine:

    def __init__(self, use_gpu: bool = False, fft_precision: str = 'float64'):
        self.use_gpu = use_gpu
        self.fft_precision = fft_precision
        self.xp = np
        self._fft2 = np.fft.fft2
        self._ifft2 = np.fft.ifft2
        self._fftshift = np.fft.fftshift
        self._ifftshift = np.fft.ifftshift
        self._fftfreq = np.fft.fftfreq
        self._use_numba = False
        self._setup_backend()

    def set_fft_precision(self, precision: str):
        """设置FFT精度：'float32', 'float64', 'longdouble'

        注意：NumPy FFT 不原生支持 longdouble，会自动降级为 float64。
        longdouble 仅在输入数据转换阶段生效，FFT计算仍使用 float64。
        """
        valid = ('float32', 'float64', 'longdouble')
        if precision not in valid:
            precision = 'float64'
        if precision == 'longdouble':
            print("[WARN] NumPy FFT 不支持 longdouble，FFT 计算将降级为 float64。"
                  "输入数据仍使用 clongdouble 精度。")
        self.fft_precision = precision

    def _cast_field(self, field: np.ndarray) -> np.ndarray:
        """根据fft_precision设置转换输入场的数据精度"""
        if self.fft_precision == 'float32':
            return field.astype(np.complex64)
        elif self.fft_precision == 'longdouble':
            return field.astype(np.clongdouble)
        return field.astype(np.complex128)

    def _setup_backend(self):
        if self.use_gpu:
            try:
                import cupy as cp
                self.xp = cp
                self._fft2 = cp.fft.fft2
                self._ifft2 = cp.fft.ifft2
                self._fftshift = cp.fft.fftshift
                self._ifftshift = cp.fft.ifftshift
                self._fftfreq = cp.fft.fftfreq
                print("[INFO] GPU backend enabled (CuPy)")
            except ImportError:
                print("[WARN] CuPy not available, falling back to CPU")
                self.use_gpu = False
                self._setup_cpu()
        else:
            self._setup_cpu()

    def _setup_cpu(self):
        self.xp = np
        self._fft2 = np.fft.fft2
        self._ifft2 = np.fft.ifft2
        self._fftshift = np.fft.fftshift
        self._ifftshift = np.fft.ifftshift
        self._fftfreq = np.fft.fftfreq
        try:
            import numba
            self._use_numba = True
            print("[INFO] CPU backend with Numba JIT acceleration")
        except ImportError:
            self._use_numba = False
            print("[INFO] CPU backend (NumPy)")

    def create_grid(self, params: SimulationParams) -> Tuple[np.ndarray, np.ndarray, float]:
        n = params.grid_size
        L = params.physical_size
        dx = L / n

        x = self.xp.linspace(-L / 2, L / 2 - dx, n)
        y = self.xp.linspace(-L / 2, L / 2 - dx, n)
        X, Y = self.xp.meshgrid(x, y)

        return X, Y, dx

    def compute_diffraction(self, aperture: BaseAperture,
                            params: SimulationParams) -> DiffractionResult:
        X, Y, dx = self.create_grid(params)

        mask = aperture.get_mask(X, Y)

        if params.pad_factor > 1:
            mask = self._zero_pad(mask, params.pad_factor)

        field = self._cast_field(mask)

        if params.model == PropagationModel.FRAUNHOFER:
            result = self._fraunhofer(field, dx, params)
        elif params.model == PropagationModel.FRESNEL_ASM:
            result = self._fresnel_asm(field, dx, params)
        elif params.model == PropagationModel.FRESNEL_IR:
            result = self._fresnel_ir(field, dx, params)
        elif params.model == PropagationModel.RAYLEIGH_SOMMERFELD:
            result = self._rayleigh_sommerfeld(field, dx, params)
        else:
            result = self._fraunhofer(field, dx, params)

        result.metadata = {
            'wavelength': params.wavelength,
            'grid_size': params.grid_size,
            'physical_size': params.physical_size,
            'propagation_distance': params.propagation_distance,
            'model': params.model.value,
            'pad_factor': params.pad_factor,
            'use_gpu': self.use_gpu,
        }

        return result

    def _fraunhofer(self, field: np.ndarray, dx: float,
                    params: SimulationParams) -> DiffractionResult:
        N = field.shape[0]

        F = self._fftshift(self._fft2(field))
        intensity = self.xp.abs(F) ** 2

        df = 1.0 / (N * dx)
        fx = self._fftshift(self._fftfreq(N, dx))
        fy = self._fftshift(self._fftfreq(N, dx))

        return DiffractionResult(
            intensity=self._to_numpy(intensity),
            complex_field=self._to_numpy(F),
            x_freq=self._to_numpy(fx),
            y_freq=self._to_numpy(fy),
            dx_output=df,
        )

    def _fresnel_asm(self, field: np.ndarray, dx: float,
                     params: SimulationParams) -> DiffractionResult:
        N = field.shape[0]
        k = 2 * np.pi / params.wavelength
        z = params.propagation_distance

        fx = self._fftfreq(N, dx)
        fy = self._fftfreq(N, dx)
        FX, FY = self.xp.meshgrid(fx, fy)

        arg = 1 - (params.wavelength * FX) ** 2 - (params.wavelength * FY) ** 2
        propagating = arg > 0
        arg = self.xp.where(propagating, arg, 0)

        H = self.xp.exp(1j * k * z * self.xp.sqrt(arg))
        H = self.xp.where(propagating, H, 0)

        A0 = self._fft2(field)
        A1 = A0 * H
        U = self._ifft2(A1)

        intensity = self.xp.abs(U) ** 2

        fx_shifted = self._fftshift(fx)
        fy_shifted = self._fftshift(fy)

        return DiffractionResult(
            intensity=self._to_numpy(intensity),
            complex_field=self._to_numpy(U),
            x_freq=self._to_numpy(fx_shifted),
            y_freq=self._to_numpy(fy_shifted),
            dx_output=dx,
        )

    def _fresnel_ir(self, field: np.ndarray, dx: float,
                    params: SimulationParams) -> DiffractionResult:
        N = field.shape[0]
        k = 2 * np.pi / params.wavelength
        z = params.propagation_distance
        L = N * dx

        x = self.xp.linspace(-L / 2, L / 2 - dx, N)
        y = self.xp.linspace(-L / 2, L / 2 - dx, N)
        X, Y = self.xp.meshgrid(x, y)

        h = self.xp.exp(1j * k * z) / (1j * params.wavelength * z) * \
            self.xp.exp(1j * k * (X ** 2 + Y ** 2) / (2 * z))

        H = self._fft2(self._ifftshift(h)) * (dx ** 2)
        U0_fft = self._fft2(field)
        U = self._ifft2(U0_fft * H)

        intensity = self.xp.abs(U) ** 2

        fx = self._fftshift(self._fftfreq(N, dx))
        fy = self._fftshift(self._fftfreq(N, dx))

        return DiffractionResult(
            intensity=self._to_numpy(intensity),
            complex_field=self._to_numpy(U),
            x_freq=self._to_numpy(fx),
            y_freq=self._to_numpy(fy),
            dx_output=dx,
        )

    def _rayleigh_sommerfeld(self, field: np.ndarray, dx: float,
                             params: SimulationParams) -> DiffractionResult:
        N = field.shape[0]
        k = 2 * np.pi / params.wavelength
        z = params.propagation_distance
        L = N * dx

        x = self.xp.linspace(-L / 2, L / 2 - dx, N)
        y = self.xp.linspace(-L / 2, L / 2 - dx, N)
        X, Y = self.xp.meshgrid(x, y)

        fx = self._fftfreq(N, dx)
        fy = self._fftfreq(N, dx)
        FX, FY = self.xp.meshgrid(fx, fy)

        arg = (params.wavelength * FX) ** 2 + (params.wavelength * FY) ** 2
        propagating = arg < 1
        arg_clamped = self.xp.where(propagating, 1 - arg, 0)
        sqrt_term = self.xp.sqrt(arg_clamped)

        H = self.xp.exp(1j * k * z * sqrt_term)
        H = self.xp.where(propagating, H, 0)

        A0 = self._fft2(field)
        A1 = A0 * H
        U = self._ifft2(A1)

        intensity = self.xp.abs(U) ** 2

        fx_shifted = self._fftshift(fx)
        fy_shifted = self._fftshift(fy)

        return DiffractionResult(
            intensity=self._to_numpy(intensity),
            complex_field=self._to_numpy(U),
            x_freq=self._to_numpy(fx_shifted),
            y_freq=self._to_numpy(fy_shifted),
            dx_output=dx,
        )

    def _zero_pad(self, array: np.ndarray, factor: float) -> np.ndarray:
        N = array.shape[0]
        pad_size = int(N * (factor - 1) / 2)
        if pad_size <= 0:
            return array
        return self.xp.pad(array, pad_size, mode='constant')

    def _to_numpy(self, array) -> np.ndarray:
        if hasattr(array, 'get'):
            return array.get()
        return np.asarray(array)
