import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestConfigManager:

    def test_default_config(self):
        from src.utils.config import ConfigManager, AppConfig
        ConfigManager.reset_instance()
        manager = ConfigManager()
        config = manager.config
        assert isinstance(config, AppConfig)
        assert config.simulation.wavelength == 532e-9
        assert config.aperture.type == "circle"

    def test_singleton(self):
        from src.utils.config import ConfigManager
        ConfigManager.reset_instance()
        m1 = ConfigManager()
        m2 = ConfigManager()
        assert m1 is m2

    def test_update_config(self):
        from src.utils.config import ConfigManager
        ConfigManager.reset_instance()
        manager = ConfigManager()
        manager.update('simulation', 'wavelength', 632e-9)
        assert manager.config.simulation.wavelength == 632e-9

    def test_reset_config(self):
        from src.utils.config import ConfigManager
        ConfigManager.reset_instance()
        manager = ConfigManager()
        manager.update('simulation', 'wavelength', 632e-9)
        manager.reset()
        assert manager.config.simulation.wavelength == 532e-9

    def test_aberration_config(self):
        from src.utils.config import ConfigManager
        ConfigManager.reset_instance()
        manager = ConfigManager()
        assert hasattr(manager.config, 'aberration')
        assert manager.config.aberration.enabled == False

    def test_multi_wavelength_config(self):
        from src.utils.config import ConfigManager
        ConfigManager.reset_instance()
        manager = ConfigManager()
        assert hasattr(manager.config, 'multi_wavelength')
        assert manager.config.multi_wavelength.enabled == False

    def test_to_dict_from_dict(self):
        from src.utils.config import AppConfig
        cfg = AppConfig()
        d = cfg.to_dict()
        cfg2 = AppConfig.from_dict(d)
        assert cfg2.simulation.wavelength == cfg.simulation.wavelength


class TestUnits:

    def test_nm_to_m(self):
        from src.core.units import nm_to_m
        assert nm_to_m(532) == 532e-9

    def test_um_to_m(self):
        from src.core.units import um_to_m
        assert abs(um_to_m(50) - 50e-6) < 1e-15

    def test_m_to_nm(self):
        from src.core.units import m_to_nm
        assert abs(m_to_nm(532e-9) - 532) < 1e-6

    def test_degrees_to_radians(self):
        from src.core.units import degrees_to_radians
        import math
        assert abs(degrees_to_radians(180) - math.pi) < 1e-10


class TestOptics:

    def test_airy_disk_angular_radius(self):
        from src.core.optics import airy_disk_angular_radius
        radius = airy_disk_angular_radius(532e-9, 50e-6)
        expected = 1.22 * 532e-9 / 50e-6
        assert abs(radius - expected) < 1e-15

    def test_fresnel_number(self):
        from src.core.optics import fresnel_number
        N = fresnel_number(532e-9, 25e-6, 0.1)
        expected = (25e-6) ** 2 / (532e-9 * 0.1)
        assert abs(N - expected) / expected < 1e-10

    def test_wavelength_to_rgb(self):
        from src.core.optics import wavelength_to_rgb
        r, g, b = wavelength_to_rgb(532)
        assert 0 <= r <= 1
        assert 0 <= g <= 1
        assert 0 <= b <= 1


class TestZernike:

    def test_zernike_names(self):
        from src.core.zernike import zernike_names
        names = zernike_names()
        assert 'defocus' in names
        assert 'spherical' in names
        assert 'coma_x' in names

    def test_compute_wavefront(self):
        import numpy as np
        from src.core.zernike import compute_wavefront
        x = np.linspace(-1, 1, 64)
        y = np.linspace(-1, 1, 64)
        X, Y = np.meshgrid(x, y)
        wf = compute_wavefront(X, Y, 1.0, {'defocus': 1.0})
        assert wf.shape == (64, 64)
        assert wf[32, 32] != 0

    def test_apply_aberration(self):
        import numpy as np
        from src.core.zernike import compute_wavefront, apply_aberration
        x = np.linspace(-1, 1, 64)
        y = np.linspace(-1, 1, 64)
        X, Y = np.meshgrid(x, y)
        field = np.ones((64, 64), dtype=np.complex128)
        wf = compute_wavefront(X, Y, 1.0, {'defocus': 0.5})
        result = apply_aberration(field, wf, 532e-9)
        assert result.shape == (64, 64)
        assert np.abs(result[32, 32]) > 0


class TestPSFMTF:

    def test_compute_psf(self):
        import numpy as np
        from src.analysis.psf_mtf import compute_psf
        intensity = np.random.rand(64, 64)
        intensity[32, 32] = 10.0
        result = compute_psf(intensity)
        assert 'peak' in result
        assert 'total' in result
        assert 'fwhm_h' in result
        assert 'fwhm_v' in result

    def test_compute_mtf(self):
        import numpy as np
        from src.analysis.psf_mtf import compute_mtf
        intensity = np.random.rand(64, 64)
        intensity[32, 32] = 10.0
        mtf = compute_mtf(intensity)
        assert mtf.shape == (64, 64)
        assert mtf[32, 32] == mtf.max()
        assert mtf[32, 32] == 1.0

    def test_radial_mtf(self):
        import numpy as np
        from src.analysis.psf_mtf import compute_mtf, radial_mtf
        intensity = np.random.rand(64, 64)
        intensity[32, 32] = 10.0
        mtf = compute_mtf(intensity)
        freq, mtf_r = radial_mtf(mtf, num_bins=32)
        assert len(freq) == 32
        assert len(mtf_r) == 32

    def test_strehl_ratio(self):
        import numpy as np
        from src.analysis.psf_mtf import strehl_ratio
        intensity = np.random.rand(64, 64)
        sr = strehl_ratio(intensity)
        assert isinstance(sr, float)
        assert sr >= 0
