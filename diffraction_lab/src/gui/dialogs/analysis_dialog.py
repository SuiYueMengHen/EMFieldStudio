import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QPushButton, QLabel, QFileDialog
)
import pyqtgraph as pg
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class AnalysisDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("专业分析")
        self.setMinimumSize(800, 600)
        self._is_dark = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_mtf_tab(), "MTF 曲线")
        self.tabs.addTab(self._create_ee_tab(), "环围能量")
        self.tabs.addTab(self._create_radial_tab(), "径向分布")
        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        self.export_btn = QPushButton("导出数据")
        self.export_btn.clicked.connect(self._export_data)
        btn_layout.addWidget(self.export_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def _apply_dark_style(self, plot: pg.PlotWidget):
        plot.setBackground(QColor(30, 30, 40))
        plot.getAxis('left').setPen(pg.mkPen('#8888aa'))
        plot.getAxis('bottom').setPen(pg.mkPen('#8888aa'))
        plot.getAxis('left').setTextPen(pg.mkPen('#c0c0d0'))
        plot.getAxis('bottom').setTextPen(pg.mkPen('#c0c0d0'))

    def _apply_light_style(self, plot: pg.PlotWidget):
        plot.setBackground(QColor(245, 246, 250))
        plot.getAxis('left').setPen(pg.mkPen('#b0b0c0'))
        plot.getAxis('bottom').setPen(pg.mkPen('#b0b0c0'))
        plot.getAxis('left').setTextPen(pg.mkPen('#2c3e50'))
        plot.getAxis('bottom').setTextPen(pg.mkPen('#2c3e50'))

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        for plot in [self.mtf_plot, self.ee_plot, self.radial_plot]:
            if is_dark:
                self._apply_dark_style(plot)
            else:
                self._apply_light_style(plot)

    def _create_mtf_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.mtf_plot = pg.PlotWidget()
        self._apply_dark_style(self.mtf_plot)
        self.mtf_plot.showGrid(x=True, y=True, alpha=0.3)
        self.mtf_plot.setLabel('left', 'MTF', units='')
        self.mtf_plot.setLabel('bottom', '空间频率', units='cycles/pixel')
        self.mtf_curve = self.mtf_plot.plot(pen=pg.mkPen('#00ccff', width=2))
        self.mtf_diffraction = self.mtf_plot.plot(
            pen=pg.mkPen('#ff6600', width=2, style=Qt.PenStyle.DashLine))
        layout.addWidget(self.mtf_plot)
        return widget

    def _create_ee_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.ee_plot = pg.PlotWidget()
        self._apply_dark_style(self.ee_plot)
        self.ee_plot.showGrid(x=True, y=True, alpha=0.3)
        self.ee_plot.setLabel('left', '归一化能量', units='')
        self.ee_plot.setLabel('bottom', '半径', units='pixels')
        self.ee_curve = self.ee_plot.plot(pen=pg.mkPen('#00ff66', width=2))
        layout.addWidget(self.ee_plot)

        self.ee_info = QLabel("")
        layout.addWidget(self.ee_info)
        return widget

    def _create_radial_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.radial_plot = pg.PlotWidget()
        self._apply_dark_style(self.radial_plot)
        self.radial_plot.showGrid(x=True, y=True, alpha=0.3)
        self.radial_plot.setLabel('left', '平均强度', units='')
        self.radial_plot.setLabel('bottom', '半径', units='pixels')
        self.radial_curve = self.radial_plot.plot(pen=pg.mkPen('#ff66ff', width=2))
        layout.addWidget(self.radial_plot)
        return widget

    def update_mtf(self, spatial_freq: np.ndarray, mtf_values: np.ndarray,
                   diffraction_limit: np.ndarray = None):
        self.mtf_curve.setData(spatial_freq, mtf_values)
        if diffraction_limit is not None:
            self.mtf_diffraction.setData(spatial_freq, diffraction_limit)

    def update_ee(self, radii: np.ndarray, ee_values: np.ndarray):
        self.ee_curve.setData(radii, ee_values)

        ee50_idx = np.searchsorted(ee_values, 0.5)
        ee86_idx = np.searchsorted(ee_values, 0.86)
        ee50_r = radii[min(ee50_idx, len(radii) - 1)] if ee50_idx < len(radii) else 0
        ee86_r = radii[min(ee86_idx, len(radii) - 1)] if ee86_idx < len(radii) else 0

        self.ee_info.setText(
            f"EE50 半径: {ee50_r:.1f} px  |  EE86 半径: {ee86_r:.1f} px"
        )

    def update_radial(self, radii: np.ndarray, radial_intensity: np.ndarray):
        self.radial_curve.setData(radii, radial_intensity)

    def _export_data(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出分析数据", "", "CSV Files (*.csv);;HDF5 Files (*.h5)"
        )
        if path:
            pass
