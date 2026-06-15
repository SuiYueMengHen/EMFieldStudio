import numpy as np


def _hot_colormap(data: np.ndarray) -> np.ndarray:
    t = np.clip(data, 0, 1)
    r = np.clip(3 * t, 0, 1)
    g = np.clip(3 * t - 1, 0, 1)
    b = np.clip(3 * t - 2, 0, 1)
    return np.stack([r, g, b], axis=-1)


def _viridis_colormap(data: np.ndarray) -> np.ndarray:
    t = np.clip(data, 0, 1)
    r = np.clip(0.267 + 0.329 * t + 0.429 * t ** 2 - 0.025 * t ** 3, 0, 1)
    g = np.clip(0.004 + 0.839 * t + 0.275 * t ** 2 - 0.118 * t ** 3, 0, 1)
    b = np.clip(0.329 + 0.285 * t - 0.614 * t ** 2 + 0.0 * t ** 3, 0, 1)
    return np.stack([r, g, b], axis=-1)


def _gray_colormap(data: np.ndarray) -> np.ndarray:
    v = np.clip(data, 0, 1)
    return np.stack([v, v, v], axis=-1)


def _plasma_colormap(data: np.ndarray) -> np.ndarray:
    t = np.clip(data, 0, 1)
    r = np.clip(0.050 + 0.867 * t + 0.083 * t ** 2, 0, 1)
    g = np.clip(0.003 + 0.138 * t + 0.859 * t ** 2, 0, 1)
    b = np.clip(0.529 + 0.226 * t - 0.755 * t ** 2 + 0.0 * t ** 3, 0, 1)
    return np.stack([r, g, b], axis=-1)


def _inferno_colormap(data: np.ndarray) -> np.ndarray:
    t = np.clip(data, 0, 1)
    r = np.clip(0.001 + 1.424 * t - 0.425 * t ** 2, 0, 1)
    g = np.clip(0.000 + 0.272 * t + 0.728 * t ** 2, 0, 1)
    b = np.clip(0.015 + 1.470 * t - 2.485 * t ** 2 + 1.0 * t ** 3, 0, 1)
    return np.stack([r, g, b], axis=-1)


_COLORMAP_REGISTRY = {
    'hot': _hot_colormap,
    'viridis': _viridis_colormap,
    'gray': _gray_colormap,
    'plasma': _plasma_colormap,
    'inferno': _inferno_colormap,
}


def get_colormap(name: str):
    if name in _COLORMAP_REGISTRY:
        return _COLORMAP_REGISTRY[name]
    return _hot_colormap


def get_colormap_names():
    return list(_COLORMAP_REGISTRY.keys())


def get_pyqtgraph_lut(name: str) -> np.ndarray:
    cmap_func = get_colormap(name)
    n = 256
    t = np.linspace(0, 1, n)
    rgb = cmap_func(t)
    lut = (rgb * 255).astype(np.uint8)
    return lut
