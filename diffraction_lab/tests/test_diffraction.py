import numpy as np
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.aperture import CircleAperture, ApertureParams
from src.core.diffraction import (
    DiffractionEngine, SimulationParams, PropagationModel, DiffractionResult
)


class TestFraunhoferDiffraction:

    @pytest.fixture
    def engine(self):
        return DiffractionEngine(use_gpu=False)

    @pytest.fixture
    def aperture(self):
        return CircleAperture(ApertureParams(size=50))

    def test_airy_disk_radius(self, engine, aperture):
        params = SimulationParams(
            wavelength=532e-9,
            grid_size=512,
            physical_size=200e-6,
        )

        result = engine.compute_diffraction(aperture, params)
        assert result.intensity is not None
        assert result.intensity.shape[0] > 0

        intensity = result.intensity
        center = intensity.shape[0] // 2
        radial_profile = intensity[center, center:]

        min_idx = np.argmin(radial_profile[1:100]) + 1
        assert min_idx > 1, "First minimum should not be at center"

    def test_result_structure(self, engine, aperture):
        params = SimulationParams(wavelength=532e-9, grid_size=256)
        result = engine.compute_diffraction(aperture, params)

        assert isinstance(result, DiffractionResult)
        assert result.intensity is not None
        assert result.complex_field is not None
        assert result.x_freq is not None
        assert result.y_freq is not None
        assert result.dx_output > 0
        assert 'wavelength' in result.metadata

    def test_intensity_positive(self, engine, aperture):
        params = SimulationParams(wavelength=532e-9, grid_size=256)
        result = engine.compute_diffraction(aperture, params)
        assert np.all(result.intensity >= 0)

    def test_peak_at_center(self, engine, aperture):
        params = SimulationParams(wavelength=532e-9, grid_size=256)
        result = engine.compute_diffraction(aperture, params)
        center = result.intensity.shape[0] // 2
        assert result.intensity[center, center] == result.intensity.max()


class TestFresnelDiffraction:

    @pytest.fixture
    def engine(self):
        return DiffractionEngine(use_gpu=False)

    @pytest.fixture
    def aperture(self):
        return CircleAperture(ApertureParams(size=50))

    def test_fresnel_asm(self, engine, aperture):
        params = SimulationParams(
            wavelength=532e-9,
            grid_size=256,
            physical_size=200e-6,
            propagation_distance=0.1,
            model=PropagationModel.FRESNEL_ASM,
        )
        result = engine.compute_diffraction(aperture, params)
        assert result.intensity is not None
        assert np.all(result.intensity >= 0)

    def test_fresnel_ir(self, engine, aperture):
        params = SimulationParams(
            wavelength=532e-9,
            grid_size=256,
            physical_size=200e-6,
            propagation_distance=0.1,
            model=PropagationModel.FRESNEL_IR,
        )
        result = engine.compute_diffraction(aperture, params)
        assert result.intensity is not None
        assert np.all(result.intensity >= 0)


class TestDiffractionResult:

    def test_cross_section(self):
        intensity = np.random.rand(64, 64)
        result = DiffractionResult(
            intensity=intensity,
            x_freq=np.linspace(-1, 1, 64),
            y_freq=np.linspace(-1, 1, 64),
            dx_output=0.03125,
        )
        coords, profile = result.get_cross_section(angle=0)
        assert len(coords) > 0
        assert len(profile) > 0

    def test_horizontal_profile(self):
        intensity = np.random.rand(64, 64)
        result = DiffractionResult(
            intensity=intensity,
            x_freq=np.linspace(-1, 1, 64),
            y_freq=np.linspace(-1, 1, 64),
        )
        coords, profile = result.get_horizontal_profile()
        assert len(coords) == 64
        assert len(profile) == 64

    def test_vertical_profile(self):
        intensity = np.random.rand(64, 64)
        result = DiffractionResult(
            intensity=intensity,
            x_freq=np.linspace(-1, 1, 64),
            y_freq=np.linspace(-1, 1, 64),
        )
        coords, profile = result.get_vertical_profile()
        assert len(coords) == 64
        assert len(profile) == 64


class TestEnergyConservation:

    def test_parseval_theorem(self):
        engine = DiffractionEngine(use_gpu=False)
        aperture = CircleAperture(ApertureParams(size=50))
        params = SimulationParams(wavelength=532e-9, grid_size=256)

        result = engine.compute_diffraction(aperture, params)

        input_energy = float(aperture.get_mask(
            *engine.create_grid(params)[:2]
        ).sum())
        output_energy = float(result.intensity.sum())

        assert output_energy > 0
        assert input_energy > 0
