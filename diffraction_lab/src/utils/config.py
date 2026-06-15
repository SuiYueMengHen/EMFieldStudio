import os
from typing import Any, Dict, Optional

import yaml

from .logger import get_logger

logger = get_logger()


class SimulationConfig:
    def __init__(self):
        self.wavelength: float = 532e-9
        self.grid_size: int = 1024
        self.physical_size: float = 200e-6
        self.propagation_distance: float = 0.1
        self.pad_factor: float = 2.0
        self.model: str = "fraunhofer"

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


class ApertureConfig:
    def __init__(self):
        self.type: str = "circle"
        self.size: float = 50.0
        self.center_x: float = 0.0
        self.center_y: float = 0.0
        self.rotation: float = 0.0
        self.aspect_ratio: float = 1.0
        self.inner_ratio: float = 0.5
        self.num_points: int = 5
        self.num_slits: int = 5
        self.slit_width: Optional[float] = None
        self.slit_separation: Optional[float] = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


class DisplayConfig:
    def __init__(self):
        self.colormap: str = "hot"
        self.log_scale: bool = True
        self.gamma: float = 1.0
        self.auto_levels: bool = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


class AnalysisConfig:
    def __init__(self):
        self.cross_section_enabled: bool = False
        self.cross_section_angle: float = 0.0
        self.cross_section_width: int = 5
        self.show_psf: bool = False
        self.show_mtf: bool = False
        self.show_encircled_energy: bool = False

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


class AberrationConfig:
    def __init__(self):
        self.enabled: bool = False
        self.defocus: float = 0.0
        self.astigmatism: float = 0.0
        self.coma: float = 0.0
        self.spherical: float = 0.0
        self.trefoil: float = 0.0

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


class MultiWavelengthConfig:
    def __init__(self):
        self.enabled: bool = False
        self.wavelengths: list = [450, 532, 633]
        self.weights: list = [1.0, 1.0, 1.0]

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg


class AppConfig:
    def __init__(self):
        self.simulation = SimulationConfig()
        self.aperture = ApertureConfig()
        self.display = DisplayConfig()
        self.analysis = AnalysisConfig()
        self.aberration = AberrationConfig()
        self.multi_wavelength = MultiWavelengthConfig()

    def to_dict(self) -> dict:
        return {
            'simulation': self.simulation.to_dict(),
            'aperture': self.aperture.to_dict(),
            'display': self.display.to_dict(),
            'analysis': self.analysis.to_dict(),
            'aberration': self.aberration.to_dict(),
            'multi_wavelength': self.multi_wavelength.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict):
        cfg = cls()
        if 'simulation' in data:
            cfg.simulation = SimulationConfig.from_dict(data['simulation'])
        if 'aperture' in data:
            cfg.aperture = ApertureConfig.from_dict(data['aperture'])
        if 'display' in data:
            cfg.display = DisplayConfig.from_dict(data['display'])
        if 'analysis' in data:
            cfg.analysis = AnalysisConfig.from_dict(data['analysis'])
        if 'aberration' in data:
            cfg.aberration = AberrationConfig.from_dict(data['aberration'])
        if 'multi_wavelength' in data:
            cfg.multi_wavelength = MultiWavelengthConfig.from_dict(data['multi_wavelength'])
        return cfg


class ConfigManager:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = None):
        if self._initialized:
            return
        self._initialized = True
        self._config = AppConfig()
        self._config_path = config_path
        if config_path and os.path.exists(config_path):
            self.load(config_path)

    @property
    def config(self) -> AppConfig:
        return self._config

    def load(self, path: str):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            if data:
                self._config = AppConfig.from_dict(data)
                logger.info(f"Configuration loaded from {path}")
        except Exception as e:
            logger.error(f"Failed to load config from {path}: {e}")

    def save(self, path: str = None):
        save_path = path or self._config_path
        if not save_path:
            save_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'config', 'default_config.yaml'
            )
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            data = self._config.to_dict()
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {save_path}: {e}")

    def update(self, section: str, key: str, value: Any):
        try:
            config_section = getattr(self._config, section)
            setattr(config_section, key, value)
            logger.debug(f"Config updated: {section}.{key} = {value}")
        except Exception as e:
            logger.error(f"Failed to update config {section}.{key}: {e}")

    def reset(self):
        self._config = AppConfig()
        logger.info("Configuration reset to defaults")

    @classmethod
    def reset_instance(cls):
        cls._instance = None
