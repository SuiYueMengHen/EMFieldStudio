import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class DiffractionCanvas(pg.GraphicsLayoutWidget):

    mouse_moved = pyqtSignal(float, float, float)
    view_changed = pyqtSignal()

    def __init__(self, parent=None):
        self._use_opengl = True
        self._use_antialias = True
        self._interpolation = 'bilinear'
        # pyqtgraph 0.13+ 使用 setConfigOptions(useOpenGL=True) 来启用 OpenGL
        # GraphicsLayoutWidget 的 __init__ 不再接受 useOpenGL 参数
        super().__init__(parent)
        self._intensity_data = None
        self._x_freq = None
        self._y_freq = None
        self._current_rect = None
        self._log_scale = True
        self._gamma = 1.0
        self._current_colormap = 'hot'
        self._is_dark = True
        self._setup_view()
        self._setup_items()
        self._setup_interaction()

    def configure_rendering(self, use_opengl: bool = True,
                            antialias: bool = True,
                            interpolation: str = 'bilinear'):
        self._use_opengl = use_opengl
        self._use_antialias = antialias
        self._interpolation = interpolation

        pg.setConfigOptions(
            antialias=antialias,
            useOpenGL=use_opengl,
            imageAxisOrder='row-major',
        )

        self._refresh_display()

    def _setup_view(self):
        self.view = self.addViewBox(row=0, col=0)
        self.view.setAspectLocked(True)
        self.view.setBackgroundColor(QColor(20, 20, 30))
        self.view.setMouseEnabled(x=True, y=True)
        self.view.setMenuEnabled(False)

    def _setup_items(self):
        self.image_item = pg.ImageItem()
        self.image_item.setOpts(axisOrder='row-major')
        self.view.addItem(self.image_item)
        self._apply_colormap(self._current_colormap)

    def _setup_interaction(self):
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

        self.crosshair_v = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))
        self.crosshair_h = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))
        self.view.addItem(self.crosshair_v, ignoreBounds=True)
        self.view.addItem(self.crosshair_h, ignoreBounds=True)

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        if is_dark:
            self.view.setBackgroundColor(QColor(20, 20, 30))
            self.crosshair_v.setPen(pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))
            self.crosshair_h.setPen(pg.mkPen('#ffffff', width=1, style=Qt.PenStyle.DashLine))
        else:
            self.view.setBackgroundColor(QColor(240, 240, 245))
            self.crosshair_v.setPen(pg.mkPen('#333333', width=1, style=Qt.PenStyle.DashLine))
            self.crosshair_h.setPen(pg.mkPen('#333333', width=1, style=Qt.PenStyle.DashLine))

    def _apply_colormap(self, name: str):
        from .colormaps import get_pyqtgraph_lut
        try:
            lut = get_pyqtgraph_lut(name)
            self.image_item.setLookupTable(lut)
            self._current_colormap = name
        except Exception:
            pass

    def update_diffraction(self, intensity: np.ndarray,
                           x_freq: np.ndarray = None,
                           y_freq: np.ndarray = None):
        self._intensity_data = intensity
        self._x_freq = x_freq
        self._y_freq = y_freq

        display_data = self._prepare_display(intensity)

        if x_freq is not None and y_freq is not None:
            x0, x1 = float(x_freq[0]), float(x_freq[-1])
            y0, y1 = float(y_freq[0]), float(y_freq[-1])
            self._current_rect = (x0, y0, x1 - x0, y1 - y0)
            self.image_item.setImage(
                display_data,
                autoLevels=False,
                levels=[0.0, 1.0],
                rect=pg.QtCore.QRectF(x0, y0, x1 - x0, y1 - y0)
            )
        else:
            self._current_rect = None
            self.image_item.setImage(
                display_data,
                autoLevels=False,
                levels=[0.0, 1.0]
            )

        if x_freq is not None and y_freq is not None:
            x0, x1 = float(x_freq[0]), float(x_freq[-1])
            y0, y1 = float(y_freq[0]), float(y_freq[-1])
            self.view.setRange(xRange=(x0, x1), yRange=(y0, y1), padding=0.02)
        else:
            n = intensity.shape[0]
            self.view.setRange(xRange=(0, n), yRange=(0, n), padding=0.02)

    def _prepare_display(self, intensity: np.ndarray) -> np.ndarray:
        if self._log_scale:
            data = np.log1p(intensity)
        else:
            data = intensity.copy()

        d_min = data.min()
        d_max = data.max()
        if d_max > d_min:
            data = (data - d_min) / (d_max - d_min)
        else:
            data = np.zeros_like(data)

        if self._gamma != 1.0 and self._gamma > 0:
            data = np.power(data, self._gamma)

        # 根据插值设置选择输出精度
        # pyqtgraph推荐float32获得最佳性能，float64提供更高渲染精度
        if self._interpolation == 'high_precision':
            return data.astype(np.float64)
        return data.astype(np.float32)

    def set_log_scale(self, enabled: bool):
        self._log_scale = enabled
        self._refresh_display()

    def set_gamma(self, gamma: float):
        self._gamma = gamma
        self._refresh_display()

    def set_colormap(self, name: str):
        self._apply_colormap(name)

    def _refresh_display(self):
        if self._intensity_data is not None:
            display_data = self._prepare_display(self._intensity_data)
            kwargs = dict(autoLevels=False, levels=[0.0, 1.0])
            if self._current_rect is not None:
                kwargs['rect'] = pg.QtCore.QRectF(*self._current_rect)
            self.image_item.setImage(display_data, **kwargs)

    def reset_view(self):
        if self._x_freq is not None and self._y_freq is not None:
            x0, x1 = float(self._x_freq[0]), float(self._x_freq[-1])
            y0, y1 = float(self._y_freq[0]), float(self._y_freq[-1])
            self.view.setRange(xRange=(x0, x1), yRange=(y0, y1), padding=0.02)
        else:
            self.view.autoRange()

    def fit_to_window(self):
        self.view.autoRange()

    def _on_mouse_moved(self, pos):
        if self._intensity_data is None:
            return

        mouse_point = self.view.mapSceneToView(pos)
        x, y = mouse_point.x(), mouse_point.y()

        self.crosshair_v.setPos(x)
        self.crosshair_h.setPos(y)

        intensity_val = self._get_intensity_at(x, y)
        self.mouse_moved.emit(x, y, intensity_val)

    def _get_intensity_at(self, x: float, y: float) -> float:
        if self._intensity_data is None or self._x_freq is None or self._y_freq is None:
            return 0.0

        ny, nx = self._intensity_data.shape
        ix = np.searchsorted(self._x_freq, x)
        iy = np.searchsorted(self._y_freq, y)

        if 0 <= ix < nx and 0 <= iy < ny:
            return float(self._intensity_data[iy, ix])
        return 0.0

    def _on_view_changed(self, view, range):
        self.view_changed.emit()

    def get_current_intensity(self) -> np.ndarray:
        return self._intensity_data
