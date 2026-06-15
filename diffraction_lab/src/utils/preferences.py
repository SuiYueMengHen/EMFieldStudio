from PyQt6.QtCore import QSettings

DEFAULT_SHORTCUTS = {
    'update': 'Ctrl+Return',
    'reset_view': 'R',
    'fit_window': 'F',
    'horizontal_profile': 'H',
    'vertical_profile': 'V',
    'fwhm_measure': 'W',
    'toggle_theme': 'T',
    'export_image': 'Ctrl+E',
    'export_data': 'Ctrl+D',
    'save_config': 'Ctrl+S',
    'help': 'F1',
}

PRECISION_PRESETS = {
    'draft': {'grid_size': 256, 'pad_factor': 1.0},
    'normal': {'grid_size': 512, 'pad_factor': 2.0},
    'high': {'grid_size': 1024, 'pad_factor': 2.0},
    'ultra': {'grid_size': 2048, 'pad_factor': 4.0},
    'extreme': {'grid_size': 4096, 'pad_factor': 4.0},
}

DEFAULT_DISPLAY = {
    'colormap': 'hot',
    'log_scale': True,
    'gamma': 1.0,
    'show_crosshair': True,
    'show_status_coord': True,
    'show_status_intensity': True,
    'show_status_fps': True,
    'show_status_strehl': True,
}

DEFAULT_ADVANCED = {
    'compute_timeout_ms': 30000,
    'use_gpu': False,
    'cache_size_mb': 512,
    'log_level': 'INFO',
    'auto_reduce_precision': True,
    'auto_reduce_threshold_ms': 2000,
    'debounce_ms': 150,
    'use_opengl': True,
    'use_antialias': True,
    'use_hidpi': True,
    'fft_precision': 'float64',
    'interpolation': 'bilinear',
}


class Preferences:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._settings = QSettings('DiffractionLab', 'DiffractionLab')
        self._ensure_defaults()

    def _ensure_defaults(self):
        if not self._settings.contains('shortcuts/update'):
            for key, value in DEFAULT_SHORTCUTS.items():
                self._settings.setValue(f'shortcuts/{key}', value)
        if not self._settings.contains('precision/preset'):
            self._settings.setValue('precision/preset', 'normal')
        if not self._settings.contains('display/colormap'):
            for key, value in DEFAULT_DISPLAY.items():
                self._settings.setValue(f'display/{key}', value)
        if not self._settings.contains('advanced/compute_timeout_ms'):
            for key, value in DEFAULT_ADVANCED.items():
                if not self._settings.contains(f'advanced/{key}'):
                    self._settings.setValue(f'advanced/{key}', value)
        if not self._settings.contains('general/theme'):
            self._settings.setValue('general/theme', 'dark')
        if not self._settings.contains('general/auto_update'):
            self._settings.setValue('general/auto_update', True)
        if not self._settings.contains('general/restore_layout'):
            self._settings.setValue('general/restore_layout', True)

    def get_shortcut(self, action: str) -> str:
        return self._settings.value(
            f'shortcuts/{action}',
            DEFAULT_SHORTCUTS.get(action, ''),
            type=str
        )

    def set_shortcut(self, action: str, key_sequence: str):
        self._settings.setValue(f'shortcuts/{action}', key_sequence)

    def get_all_shortcuts(self) -> dict:
        result = {}
        for key in DEFAULT_SHORTCUTS:
            result[key] = self.get_shortcut(key)
        return result

    def get_precision_preset(self) -> str:
        return self._settings.value('precision/preset', 'normal', type=str)

    def set_precision_preset(self, preset: str):
        self._settings.setValue('precision/preset', preset)

    def get_precision_params(self) -> dict:
        preset = self.get_precision_preset()
        base = PRECISION_PRESETS.get(preset, PRECISION_PRESETS['normal']).copy()
        custom_grid = self._settings.value(
            'precision/custom_grid_size', None, type=int)
        custom_pad = self._settings.value(
            'precision/custom_pad_factor', None, type=float)
        if custom_grid is not None:
            base['grid_size'] = custom_grid
        if custom_pad is not None:
            base['pad_factor'] = custom_pad
        return base

    def set_custom_grid_size(self, size: int):
        self._settings.setValue('precision/custom_grid_size', size)

    def set_custom_pad_factor(self, factor: float):
        self._settings.setValue('precision/custom_pad_factor', factor)

    def get_theme(self) -> str:
        return self._settings.value('general/theme', 'dark', type=str)

    def set_theme(self, theme: str):
        self._settings.setValue('general/theme', theme)

    def get_auto_update(self) -> bool:
        return self._settings.value(
            'general/auto_update', True, type=bool)

    def set_auto_update(self, enabled: bool):
        self._settings.setValue('general/auto_update', enabled)

    def get_restore_layout(self) -> bool:
        return self._settings.value(
            'general/restore_layout', True, type=bool)

    def set_restore_layout(self, enabled: bool):
        self._settings.setValue('general/restore_layout', enabled)

    def get_display_setting(self, key: str, default=None):
        if default is None:
            default = DEFAULT_DISPLAY.get(key)
        if isinstance(default, bool):
            return self._settings.value(f'display/{key}', default, type=bool)
        elif isinstance(default, int):
            return self._settings.value(f'display/{key}', default, type=int)
        elif isinstance(default, float):
            return self._settings.value(f'display/{key}', default, type=float)
        return self._settings.value(f'display/{key}', default)

    def set_display_setting(self, key: str, value):
        self._settings.setValue(f'display/{key}', value)

    def get_advanced_setting(self, key: str, default=None):
        if default is None:
            default = DEFAULT_ADVANCED.get(key)
        if isinstance(default, bool):
            return self._settings.value(f'advanced/{key}', default, type=bool)
        elif isinstance(default, int):
            return self._settings.value(f'advanced/{key}', default, type=int)
        elif isinstance(default, float):
            return self._settings.value(f'advanced/{key}', default, type=float)
        return self._settings.value(f'advanced/{key}', default)

    def set_advanced_setting(self, key: str, value):
        self._settings.setValue(f'advanced/{key}', value)

    def get_debounce_ms(self) -> int:
        return self._settings.value(
            'advanced/debounce_ms', 150, type=int)

    def reset_to_defaults(self):
        self._settings.clear()
        self._ensure_defaults()

    def reset_shortcuts(self):
        for key, value in DEFAULT_SHORTCUTS.items():
            self._settings.setValue(f'shortcuts/{key}', value)

    def sync(self):
        self._settings.sync()
