import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.aperture import (
    CircleAperture, RectangleAperture, TriangleAperture,
    HexagonAperture, AnnulusAperture, StarAperture,
    DoubleSlitAperture, GratingAperture, CompositeAperture,
    CustomBitmapAperture, ApertureFactory, ApertureType,
    ApertureParams, CompositeOperation
)


class TestCircleAperture:

    def test_mask_shape(self):
        aperture = CircleAperture(ApertureParams(size=50))
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = aperture.generate_mask(X, Y)
        assert mask.shape == (256, 256)

    def test_mask_values(self):
        aperture = CircleAperture(ApertureParams(size=50))
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = aperture.generate_mask(X, Y)
        assert mask.dtype == np.float32
        assert set(np.unique(mask)).issubset({0.0, 1.0})

    def test_center_is_transparent(self):
        aperture = CircleAperture(ApertureParams(size=50))
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = aperture.generate_mask(X, Y)
        center = mask[128, 128]
        assert center == 1.0


class TestRectangleAperture:

    def test_mask_shape(self):
        aperture = RectangleAperture(ApertureParams(size=50), aspect_ratio=2.0)
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = aperture.generate_mask(X, Y)
        assert mask.shape == (256, 256)

    def test_rotation(self):
        aperture = RectangleAperture(ApertureParams(size=50, rotation=45))
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = aperture.generate_mask(X, Y)
        assert mask.shape == (256, 256)


class TestCompositeAperture:

    def test_union(self):
        c1 = CircleAperture(ApertureParams(size=30, center_x=-10))
        c2 = CircleAperture(ApertureParams(size=30, center_x=10))
        composite = CompositeAperture([c1, c2], CompositeOperation.UNION)
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = composite.generate_mask(X, Y)
        assert mask.shape == (256, 256)
        assert mask.max() == 1.0

    def test_subtract(self):
        c1 = CircleAperture(ApertureParams(size=50))
        c2 = CircleAperture(ApertureParams(size=20))
        composite = CompositeAperture([c1, c2], CompositeOperation.SUBTRACT)
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)
        mask = composite.generate_mask(X, Y)
        center = mask[128, 128]
        assert center == 0.0


class TestApertureFactory:

    def test_create_circle(self):
        aperture = ApertureFactory.create(ApertureType.CIRCLE, params={'size': 50})
        assert isinstance(aperture, CircleAperture)

    def test_create_rectangle(self):
        aperture = ApertureFactory.create(ApertureType.RECTANGLE,
                                           params={'size': 50},
                                           aspect_ratio=2.0)
        assert isinstance(aperture, RectangleAperture)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError):
            ApertureFactory.create("unknown_type")


class TestCaching:

    def test_cache_hit(self):
        aperture = CircleAperture(ApertureParams(size=50))
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)

        mask1 = aperture.get_mask(X, Y)
        mask2 = aperture.get_mask(X, Y)
        assert mask1 is mask2

    def test_cache_invalidation(self):
        aperture = CircleAperture(ApertureParams(size=50))
        x = np.linspace(-100e-6, 100e-6, 256)
        y = np.linspace(-100e-6, 100e-6, 256)
        X, Y = np.meshgrid(x, y)

        mask1 = aperture.get_mask(X, Y)
        aperture.clear_cache()
        mask2 = aperture.get_mask(X, Y)
        assert mask1 is not mask2
        np.testing.assert_array_equal(mask1, mask2)
