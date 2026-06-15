import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QPushButton, QLabel, QSplitter, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

from analysis.fitting import fit_gaussian, fit_airy, fit_multi_peak
from .dialog_theme import apply_dialog_theme, apply_plot_theme


class FittingDialog(QDialog):

    def __init__(self, parent=None, coords=None, profile=None):
        super().__init__(parent)
        self.setWindowTitle("曲线拟合")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)
        self._coords = coords
        self._profile = profile
        self._fit_result = None
        self._is_dark = True
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        model_group = QGroupBox("拟合模型")
        model_form = QFormLayout(model_group)

        self.model_combo = QComboBox()
        self.model_combo.addItems(["Gaussian", "Airy", "双峰Gaussian"])
        model_form.addRow("模型:", self.model_combo)

        self.n_peaks_spin = None

        self.fit_btn = QPushButton("执行拟合")
        self.fit_btn.setObjectName("updateBtn")
        self.fit_btn.clicked.connect(self._do_fit)
        model_form.addRow("", self.fit_btn)

        self.export_btn = QPushButton("导出结果")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export)
        model_form.addRow("", self.export_btn)

        top_layout.addWidget(model_group)

        result_group = QGroupBox("拟合结果")
        result_layout = QVBoxLayout(result_group)
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["参数", "值"])
        self.result_table.horizontalHeader().setStretchLastSection(True)
        self.result_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        result_layout.addWidget(self.result_table)
        top_layout.addWidget(result_group, 1)

        layout.addLayout(top_layout)

        plot_group = QGroupBox("拟合曲线")
        plot_layout = QVBoxLayout(plot_group)
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend(offset=(10, 10))
        self.data_curve = self.plot_widget.plot(
            pen=pg.mkPen('#7c8cf8', width=2), name='原始数据')
        self.fit_curve = self.plot_widget.plot(
            pen=pg.mkPen('#ff6600', width=2, style=Qt.PenStyle.DashLine), name='拟合曲线')
        plot_layout.addWidget(self.plot_widget)
        layout.addWidget(plot_group, 1)

        if self._coords is not None and self._profile is not None:
            self.data_curve.setData(self._coords, self._profile)

    def _do_fit(self):
        if self._coords is None or self._profile is None:
            return

        model = self.model_combo.currentText()
        if model == "Gaussian":
            self._fit_result = fit_gaussian(self._coords, self._profile)
        elif model == "Airy":
            self._fit_result = fit_airy(self._coords, self._profile)
        elif model == "双峰Gaussian":
            self._fit_result = fit_multi_peak(self._coords, self._profile, n_peaks=2)

        if self._fit_result is None:
            self.result_table.setRowCount(1)
            self.result_table.setItem(0, 0, QTableWidgetItem("状态"))
            self.result_table.setItem(0, 1, QTableWidgetItem("拟合失败"))
            return

        self._display_result()
        self.export_btn.setEnabled(True)

    def _display_result(self):
        r = self._fit_result
        rows = []

        if 'amplitude' in r:
            rows.append(("振幅", f"{r['amplitude']:.6e}"))
        if 'center' in r:
            rows.append(("中心位置", f"{r['center']:.6e}"))
        if 'sigma' in r:
            rows.append(("σ", f"{r['sigma']:.6e}"))
            rows.append(("FWHM", f"{r.get('fwhm', 0):.6e}"))
        if 'scale' in r:
            rows.append(("尺度参数", f"{r['scale']:.6e}"))
            if 'airy_radius' in r:
                rows.append(("艾里斑半径", f"{r['airy_radius']:.6e}"))
        if 'offset' in r:
            rows.append(("偏移量", f"{r['offset']:.6e}"))
        if 'r_squared' in r:
            rows.append(("R²", f"{r['r_squared']:.6f}"))
        if 'peaks' in r:
            for i, peak in enumerate(r['peaks']):
                rows.append((f"峰{i+1} 振幅", f"{peak['amplitude']:.6e}"))
                rows.append((f"峰{i+1} 中心", f"{peak['center']:.6e}"))
                rows.append((f"峰{i+1} FWHM", f"{peak['fwhm']:.6e}"))

        self.result_table.setRowCount(len(rows))
        for i, (name, value) in enumerate(rows):
            self.result_table.setItem(i, 0, QTableWidgetItem(name))
            self.result_table.setItem(i, 1, QTableWidgetItem(value))

        if 'fit_func' in r and self._coords is not None:
            fit_y = r['fit_func'](self._coords)
            self.fit_curve.setData(self._coords, fit_y)

    def _export(self):
        if self._fit_result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出拟合数据", "", "CSV Files (*.csv)")
        if path:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['坐标', '原始值', '拟合值'])
                if self._coords is not None and self._fit_result.get('fit_func'):
                    fit_y = self._fit_result['fit_func'](self._coords)
                    for x, y_orig, y_fit in zip(self._coords, self._profile, fit_y):
                        writer.writerow([x, y_orig, y_fit])

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        apply_dialog_theme(self, is_dark)
        apply_plot_theme(self.plot_widget, is_dark)
