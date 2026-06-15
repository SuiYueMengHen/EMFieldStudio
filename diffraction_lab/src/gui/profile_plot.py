import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class ProfilePlot(pg.PlotWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_dark = True
        self._setup_plot()
        self._h_profile_data = None
        self._v_profile_data = None
        self._custom_profile_data = None

    def _setup_plot(self):
        self._apply_dark_style()
        self.showGrid(x=True, y=True, alpha=0.3)
        self.setLabel('left', 'Intensity', units='a.u.')
        self.setLabel('bottom', 'Position', units='m')

        self.h_curve = self.plot(pen=pg.mkPen('#00ccff', width=2), name='Horizontal')
        self.v_curve = self.plot(pen=pg.mkPen('#ff6600', width=2), name='Vertical')
        self.custom_curve = self.plot(pen=pg.mkPen('#00ff66', width=2), name='Custom')

        self.addLegend(offset=(10, 10))

        self.fwhm_line_left = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen('#ffff00', width=1, style=Qt.PenStyle.DashLine))
        self.fwhm_line_right = pg.InfiniteLine(
            angle=90, movable=False,
            pen=pg.mkPen('#ffff00', width=1, style=Qt.PenStyle.DashLine))
        self.fwhm_level_line = pg.InfiniteLine(
            angle=0, movable=False,
            pen=pg.mkPen('#ffff00', width=1, style=Qt.PenStyle.DotLine))
        self.addItem(self.fwhm_line_left, ignoreBounds=True)
        self.addItem(self.fwhm_line_right, ignoreBounds=True)
        self.addItem(self.fwhm_level_line, ignoreBounds=True)

        self.fwhm_label = pg.TextItem(color='#ffff00', anchor=(0, 1))
        self.addItem(self.fwhm_label, ignoreBounds=True)

    def _apply_dark_style(self):
        self.setBackground(QColor(30, 30, 40))
        self.getAxis('left').setPen(pg.mkPen('#8888aa'))
        self.getAxis('bottom').setPen(pg.mkPen('#8888aa'))
        self.getAxis('left').setTextPen(pg.mkPen('#c0c0d0'))
        self.getAxis('bottom').setTextPen(pg.mkPen('#c0c0d0'))

    def _apply_light_style(self):
        self.setBackground(QColor(245, 246, 250))
        self.getAxis('left').setPen(pg.mkPen('#b0b0c0'))
        self.getAxis('bottom').setPen(pg.mkPen('#b0b0c0'))
        self.getAxis('left').setTextPen(pg.mkPen('#2c3e50'))
        self.getAxis('bottom').setTextPen(pg.mkPen('#2c3e50'))

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        if is_dark:
            self._apply_dark_style()
        else:
            self._apply_light_style()

    def update_horizontal_profile(self, coords: np.ndarray, profile: np.ndarray):
        if coords is None or profile is None or len(coords) == 0:
            return
        self._h_profile_data = (coords, profile)
        self.h_curve.setData(coords, profile)

    def update_vertical_profile(self, coords: np.ndarray, profile: np.ndarray):
        if coords is None or profile is None or len(coords) == 0:
            return
        self._v_profile_data = (coords, profile)
        self.v_curve.setData(coords, profile)

    def update_custom_profile(self, coords: np.ndarray, profile: np.ndarray):
        if coords is None or profile is None or len(coords) == 0:
            return
        self._custom_profile_data = (coords, profile)
        self.custom_curve.setData(coords, profile)

    def show_fwhm(self, coords: np.ndarray, profile: np.ndarray):
        if coords is None or profile is None or len(profile) < 3:
            self.hide_fwhm()
            return

        max_val = np.max(profile)
        half_max = max_val / 2.0

        above_half = np.where(profile >= half_max)[0]
        if len(above_half) < 2:
            self.hide_fwhm()
            return

        left_idx = above_half[0]
        right_idx = above_half[-1]

        left_x = coords[left_idx]
        right_x = coords[right_idx]
        fwhm_val = right_x - left_x

        self.fwhm_line_left.setPos(left_x)
        self.fwhm_line_right.setPos(right_x)
        self.fwhm_level_line.setPos(half_max)

        mid_x = (left_x + right_x) / 2
        self.fwhm_label.setPos(mid_x, half_max)
        self.fwhm_label.setText(f'FWHM: {fwhm_val:.4e} m')

        self.fwhm_line_left.show()
        self.fwhm_line_right.show()
        self.fwhm_level_line.show()
        self.fwhm_label.show()

    def hide_fwhm(self):
        self.fwhm_line_left.hide()
        self.fwhm_line_right.hide()
        self.fwhm_level_line.hide()
        self.fwhm_label.hide()

    def clear_profiles(self):
        self.h_curve.setData([], [])
        self.v_curve.setData([], [])
        self.custom_curve.setData([], [])
        self.hide_fwhm()
        self._h_profile_data = None
        self._v_profile_data = None
        self._custom_profile_data = None
