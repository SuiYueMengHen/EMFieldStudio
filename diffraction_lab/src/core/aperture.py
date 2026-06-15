from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np


class ApertureType(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    TRIANGLE = "triangle"
    HEXAGON = "hexagon"
    ANNULUS = "annulus"
    POLYGON = "polygon"
    STAR = "star"
    DOUBLE_SLIT = "double_slit"
    GRATING = "grating"
    CUSTOM_SVG = "custom_svg"
    CUSTOM_BITMAP = "custom_bitmap"
    COMPOSITE = "composite"


class CompositeOperation(Enum):
    UNION = "union"
    INTERSECTION = "intersection"
    SUBTRACT = "subtract"
    XOR = "xor"


@dataclass
class ApertureParams:
    size: float = 50.0
    center_x: float = 0.0
    center_y: float = 0.0
    rotation: float = 0.0


class BaseAperture(ABC):

    def __init__(self, params: ApertureParams):
        self.params = params
        self._mask_cache = None
        self._cache_grid_key = None

    @abstractmethod
    def generate_mask(self, x_grid: np.ndarray, y_grid: np.ndarray) -> np.ndarray:
        pass

    def get_mask(self, x_grid: np.ndarray, y_grid: np.ndarray) -> np.ndarray:
        grid_key = (x_grid.shape, x_grid.tobytes()[:24])
        if self._mask_cache is not None and self._cache_grid_key == grid_key:
            return self._mask_cache
        mask = self.generate_mask(x_grid, y_grid)
        self._mask_cache = mask
        self._cache_grid_key = grid_key
        return mask

    def clear_cache(self):
        self._mask_cache = None
        self._cache_grid_key = None

    def _rotate_coords(self, x_grid: np.ndarray, y_grid: np.ndarray,
                       cx: float, cy: float, rotation_deg: float):
        if rotation_deg == 0:
            return x_grid, y_grid
        theta = np.radians(rotation_deg)
        dx = x_grid - cx
        dy = y_grid - cy
        x_rot = dx * np.cos(theta) + dy * np.sin(theta) + cx
        y_rot = -dx * np.sin(theta) + dy * np.cos(theta) + cy
        return x_rot, y_rot


class CircleAperture(BaseAperture):

    def generate_mask(self, x_grid, y_grid):
        radius = self.params.size / 2 * 1e-6
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6
        r = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
        return (r <= radius).astype(np.float32)


class RectangleAperture(BaseAperture):

    def __init__(self, params: ApertureParams, aspect_ratio: float = 1.0):
        super().__init__(params)
        self.aspect_ratio = aspect_ratio

    def generate_mask(self, x_grid, y_grid):
        width = self.params.size * 1e-6
        height = self.params.size * self.aspect_ratio * 1e-6
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        mask_x = np.abs(x_rot - cx) <= width / 2
        mask_y = np.abs(y_rot - cy) <= height / 2
        return (mask_x & mask_y).astype(np.float32)


class TriangleAperture(BaseAperture):

    def __init__(self, params: ApertureParams, side_length: float = None):
        super().__init__(params)
        self.side_length = side_length or params.size

    def generate_mask(self, x_grid, y_grid):
        s = self.side_length * 1e-6
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        h = s * np.sqrt(3) / 2
        v1 = np.array([0, 2 * h / 3])
        v2 = np.array([-s / 2, -h / 3])
        v3 = np.array([s / 2, -h / 3])

        def sign(p1x, p1y, p2x, p2y, p3x, p3y):
            return (p1x - p3x) * (p2y - p3y) - (p2x - p3x) * (p1y - p3y)

        dx = x_rot - cx
        dy = y_rot - cy

        d1 = sign(dx, dy, v1[0], v1[1], v2[0], v2[1])
        d2 = sign(dx, dy, v2[0], v2[1], v3[0], v3[1])
        d3 = sign(dx, dy, v3[0], v3[1], v1[0], v1[1])

        has_neg = (d1 < 0) | (d2 < 0) | (d3 < 0)
        has_pos = (d1 > 0) | (d2 > 0) | (d3 > 0)

        return (~(has_neg & has_pos)).astype(np.float32)


class HexagonAperture(BaseAperture):

    def generate_mask(self, x_grid, y_grid):
        radius = self.params.size / 2 * 1e-6
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        dx = np.abs(x_rot - cx)
        dy = np.abs(y_rot - cy)

        mask = (dy <= radius) & (dx <= radius * np.sqrt(3) / 2) & \
               (dx + np.sqrt(3) * dy <= radius * np.sqrt(3))
        return mask.astype(np.float32)


class AnnulusAperture(BaseAperture):

    def __init__(self, params: ApertureParams, inner_ratio: float = 0.5):
        super().__init__(params)
        self.inner_ratio = inner_ratio

    def generate_mask(self, x_grid, y_grid):
        outer_radius = self.params.size / 2 * 1e-6
        inner_radius = outer_radius * self.inner_ratio
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        r = np.sqrt((x_grid - cx) ** 2 + (y_grid - cy) ** 2)
        mask = (r <= outer_radius) & (r >= inner_radius)
        return mask.astype(np.float32)


class PolygonAperture(BaseAperture):

    def __init__(self, params: ApertureParams, vertices: List[Tuple[float, float]] = None):
        super().__init__(params)
        self.vertices = vertices or []

    def generate_mask(self, x_grid, y_grid):
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6
        scale = self.params.size / 2 * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        n = len(self.vertices)
        if n < 3:
            return np.zeros_like(x_grid, dtype=np.float32)

        vx = np.array([v[0] * scale + cx for v in self.vertices])
        vy = np.array([v[1] * scale + cy for v in self.vertices])

        mask = np.zeros(x_grid.shape, dtype=bool)
        j = n - 1
        for i in range(n):
            cond = ((vy[i] > y_rot) != (vy[j] > y_rot)) & \
                   (x_rot < (vx[j] - vx[i]) * (y_rot - vy[i]) / (vy[j] - vy[i] + 1e-30) + vx[i])
            mask = mask ^ cond
            j = i

        return mask.astype(np.float32)


class StarAperture(BaseAperture):

    def __init__(self, params: ApertureParams, num_points: int = 5,
                 inner_ratio: float = 0.4):
        super().__init__(params)
        self.num_points = num_points
        self.inner_ratio = inner_ratio

    def generate_mask(self, x_grid, y_grid):
        outer_r = self.params.size / 2 * 1e-6
        inner_r = outer_r * self.inner_ratio
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        angles = np.linspace(0, 2 * np.pi, 2 * self.num_points, endpoint=False)
        radii = np.array([outer_r if i % 2 == 0 else inner_r for i in range(2 * self.num_points)])

        vx = radii * np.cos(angles) + cx
        vy = radii * np.sin(angles) + cy

        vertices = list(zip(vx, vy))
        n = len(vertices)
        mask = np.zeros(x_grid.shape, dtype=bool)
        j = n - 1
        for i in range(n):
            cond = ((vertices[i][1] > y_rot) != (vertices[j][1] > y_rot)) & \
                   (x_rot < (vertices[j][0] - vertices[i][0]) *
                    (y_rot - vertices[i][1]) / (vertices[j][1] - vertices[i][1] + 1e-30) +
                    vertices[i][0])
            mask = mask ^ cond
            j = i

        return mask.astype(np.float32)


class DoubleSlitAperture(BaseAperture):

    def __init__(self, params: ApertureParams, slit_width: float = None,
                 slit_separation: float = None):
        super().__init__(params)
        self.slit_width = slit_width or params.size * 0.1
        self.slit_separation = slit_separation or params.size * 0.5

    def generate_mask(self, x_grid, y_grid):
        w = self.slit_width * 1e-6
        d = self.slit_separation * 1e-6
        h = self.params.size * 1e-6
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        slit1_x = np.abs(x_rot - (cx - d / 2)) <= w / 2
        slit2_x = np.abs(x_rot - (cx + d / 2)) <= w / 2
        mask_y = np.abs(y_rot - cy) <= h / 2

        mask = (slit1_x | slit2_x) & mask_y
        return mask.astype(np.float32)


class GratingAperture(BaseAperture):

    def __init__(self, params: ApertureParams, num_slits: int = 5,
                 slit_width: float = None, slit_separation: float = None):
        super().__init__(params)
        self.num_slits = num_slits
        self.slit_width = slit_width or params.size * 0.05
        self.slit_separation = slit_separation or params.size * 0.15

    def generate_mask(self, x_grid, y_grid):
        w = self.slit_width * 1e-6
        d = self.slit_separation * 1e-6
        h = self.params.size * 1e-6
        cx = self.params.center_x * 1e-6
        cy = self.params.center_y * 1e-6

        x_rot, y_rot = self._rotate_coords(x_grid, y_grid, cx, cy, self.params.rotation)

        total_width = (self.num_slits - 1) * d
        mask = np.zeros_like(x_grid, dtype=bool)
        mask_y = np.abs(y_rot - cy) <= h / 2

        for i in range(self.num_slits):
            slit_center_x = cx - total_width / 2 + i * d
            slit_mask = np.abs(x_rot - slit_center_x) <= w / 2
            mask = mask | (slit_mask & mask_y)

        return mask.astype(np.float32)


class CompositeAperture(BaseAperture):

    def __init__(self, apertures: List[BaseAperture], operation: CompositeOperation):
        self.apertures = apertures
        self.operation = operation
        super().__init__(ApertureParams(size=0))

    def generate_mask(self, x_grid, y_grid):
        masks = [ap.generate_mask(x_grid, y_grid) for ap in self.apertures]

        if len(masks) == 0:
            return np.zeros_like(x_grid, dtype=np.float32)

        if self.operation == CompositeOperation.UNION:
            result = np.zeros_like(masks[0])
            for m in masks:
                result = np.logical_or(result, m)
        elif self.operation == CompositeOperation.INTERSECTION:
            result = np.ones_like(masks[0])
            for m in masks:
                result = np.logical_and(result, m)
        elif self.operation == CompositeOperation.SUBTRACT:
            result = masks[0].copy().astype(bool)
            for m in masks[1:]:
                result = np.logical_and(result, np.logical_not(m))
        elif self.operation == CompositeOperation.XOR:
            result = masks[0].copy().astype(bool)
            for m in masks[1:]:
                result = np.logical_xor(result, m)
        else:
            result = np.zeros_like(masks[0])

        return result.astype(np.float32)


class CustomBitmapAperture(BaseAperture):

    def __init__(self, params: ApertureParams, bitmap: np.ndarray = None):
        super().__init__(params)
        self.bitmap = bitmap

    def generate_mask(self, x_grid, y_grid):
        if self.bitmap is None:
            return np.zeros_like(x_grid, dtype=np.float32)

        from scipy.ndimage import zoom
        target_shape = x_grid.shape
        if self.bitmap.shape != target_shape:
            zoom_factors = (target_shape[0] / self.bitmap.shape[0],
                            target_shape[1] / self.bitmap.shape[1])
            resized = zoom(self.bitmap, zoom_factors, order=1)
            return (resized > 0.5).astype(np.float32)
        return (self.bitmap > 0.5).astype(np.float32)


class ApertureFactory:

    _registry = {}

    @classmethod
    def register(cls, aperture_type: ApertureType, aperture_class):
        cls._registry[aperture_type] = aperture_class

    @classmethod
    def create(cls, aperture_type: ApertureType, **kwargs) -> BaseAperture:
        params_dict = kwargs.get('params', {})
        params = ApertureParams(**params_dict)

        if aperture_type == ApertureType.CIRCLE:
            return CircleAperture(params)
        elif aperture_type == ApertureType.RECTANGLE:
            return RectangleAperture(params, aspect_ratio=kwargs.get('aspect_ratio', 1.0))
        elif aperture_type == ApertureType.TRIANGLE:
            return TriangleAperture(params, side_length=kwargs.get('side_length'))
        elif aperture_type == ApertureType.HEXAGON:
            return HexagonAperture(params)
        elif aperture_type == ApertureType.ANNULUS:
            return AnnulusAperture(params, inner_ratio=kwargs.get('inner_ratio', 0.5))
        elif aperture_type == ApertureType.POLYGON:
            return PolygonAperture(params, vertices=kwargs.get('vertices', []))
        elif aperture_type == ApertureType.STAR:
            return StarAperture(params, num_points=kwargs.get('num_points', 5),
                                inner_ratio=kwargs.get('inner_ratio', 0.4))
        elif aperture_type == ApertureType.DOUBLE_SLIT:
            return DoubleSlitAperture(params,
                                      slit_width=kwargs.get('slit_width'),
                                      slit_separation=kwargs.get('slit_separation'))
        elif aperture_type == ApertureType.GRATING:
            return GratingAperture(params, num_slits=kwargs.get('num_slits', 5),
                                   slit_width=kwargs.get('slit_width'),
                                   slit_separation=kwargs.get('slit_separation'))
        elif aperture_type == ApertureType.CUSTOM_BITMAP:
            return CustomBitmapAperture(params, bitmap=kwargs.get('bitmap'))
        elif aperture_type == ApertureType.COMPOSITE:
            return CompositeAperture(
                apertures=kwargs.get('apertures', []),
                operation=kwargs.get('operation', CompositeOperation.UNION)
            )
        else:
            if aperture_type in cls._registry:
                return cls._registry[aperture_type](params, **kwargs)
            raise ValueError(f"Unknown aperture type: {aperture_type}")
