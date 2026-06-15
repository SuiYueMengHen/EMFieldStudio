import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QDoubleSpinBox, QSpinBox, QPushButton,
    QLabel, QProgressBar, QSplitter, QWidget, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg
from PyQt6.QtGui import QColor

from core.diffraction import DiffractionEngine, SimulationParams, PropagationModel
from core.aperture import ApertureType, ApertureFactory
from analysis.psf_mtf import compute_psf, strehl_ratio
from .dialog_theme import apply_dialog_theme, apply_plot_theme


class ScanWorker(QThread):
    progress = pyqtSignal(int, float, object)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, engine, aperture, sim_params, param_name,
                 start_val, end_val, steps):
        super().__init__()
        self.engine = engine
        self.aperture = aperture
        self.sim_params = sim_params
        self.param_name = param_name
        self.start_val = start_val
        self.end_val = end_val
        self.steps = steps
        self._cancelled = False

    def run(self):
        try:
            results = []
            values = np.linspace(self.start_val, self.end_val, self.steps)

            for i, val in enumerate(values):
                if self._cancelled:
                    break

                sp = SimulationParams(
                    wavelength=self.sim_params.wavelength,
                    grid_size=self.sim_params.grid_size,
                    physical_size=self.sim_params.physical_size,
                    propagation_distance=self.sim_params.propagation_distance,
                    model=self.sim_params.model,
                    pad_factor=self.sim_params.pad_factor,
                )

                if self.param_name == 'wavelength':
                    sp.wavelength = val
                elif self.param_name == 'aperture_size':
                    self.aperture = ApertureFactory.create(
                        ApertureType.CIRCLE, params={'size': val * 1e6})
                elif self.param_name == 'distance':
                    sp.propagation_distance = val

                result = self.engine.compute_diffraction(self.aperture, sp)
                intensity = result.intensity
                sr = strehl_ratio(intensity)
                psf_info = compute_psf(intensity)

                results.append((val, intensity, sr, psf_info))
                pct = int((i + 1) / self.steps * 100)
                self.progress.emit(pct, val, intensity)

            if not self._cancelled:
                self.finished.emit(results)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class ParameterScanDialog(QDialog):

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("参数扫描")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        self._main_window = main_window
        self._worker = None
        self._scan_results = []
        self._is_dark = True
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        scan_group = QGroupBox("扫描参数")
        scan_form = QFormLayout(scan_group)

        self.param_combo = QComboBox()
        self.param_combo.addItems([
            "波长", "孔径尺寸", "传播距离"
        ])
        scan_form.addRow("扫描参数:", self.param_combo)

        self.start_spin = QDoubleSpinBox()
        self.start_spin.setRange(0.001, 100000)
        self.start_spin.setValue(400)
        self.start_spin.setSuffix(" nm")
        scan_form.addRow("起始值:", self.start_spin)

        self.end_spin = QDoubleSpinBox()
        self.end_spin.setRange(0.001, 100000)
        self.end_spin.setValue(700)
        self.end_spin.setSuffix(" nm")
        scan_form.addRow("结束值:", self.end_spin)

        self.steps_spin = QSpinBox()
        self.steps_spin.setRange(2, 100)
        self.steps_spin.setValue(20)
        scan_form.addRow("步数:", self.steps_spin)

        left_layout.addWidget(scan_group)

        self.start_btn = QPushButton("开始扫描")
        self.start_btn.setObjectName("updateBtn")
        self.start_btn.setMinimumHeight(36)
        self.start_btn.clicked.connect(self._start_scan)
        left_layout.addWidget(self.start_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_scan)
        left_layout.addWidget(self.cancel_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        left_layout.addWidget(self.status_label)

        self.export_btn = QPushButton("导出数据")
        self.export_btn.setEnabled(False)
        self.export_btn.clicked.connect(self._export_data)
        left_layout.addWidget(self.export_btn)

        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.image_widget = pg.ImageView()
        self.image_widget.setMaximumHeight(300)
        right_layout.addWidget(self.image_widget)

        metrics_group = QGroupBox("指标曲线")
        metrics_layout = QVBoxLayout(metrics_group)
        self.metrics_plot = pg.PlotWidget()
        self.metrics_plot.showGrid(x=True, y=True, alpha=0.3)
        self.metrics_plot.addLegend(offset=(10, 10))
        self.strehl_curve = self.metrics_plot.plot(
            pen=pg.mkPen('#7c8cf8', width=2), name='Strehl')
        self.fwhm_curve = self.metrics_plot.plot(
            pen=pg.mkPen('#ff6600', width=2), name='FWHM')
        metrics_layout.addWidget(self.metrics_plot)
        right_layout.addWidget(metrics_group)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 720])

        main_layout.addWidget(splitter)

    def _start_scan(self):
        if self._worker and self._worker.isRunning():
            return

        if self._main_window is None:
            return

        cp = self._main_window.control_panel
        params = cp.get_params()

        aperture = self._main_window._create_aperture(params)

        model_map = {
            'fraunhofer': PropagationModel.FRAUNHOFER,
            'fresnel_asm': PropagationModel.FRESNEL_ASM,
            'fresnel_ir': PropagationModel.FRESNEL_IR,
            'rayleigh_sommerfeld': PropagationModel.RAYLEIGH_SOMMERFELD,
        }

        sim_params = SimulationParams(
            wavelength=params.get('wavelength', 532e-9),
            grid_size=params.get('grid_size', 512),
            physical_size=params.get('physical_size', 200e-6),
            propagation_distance=params.get('distance', 0.1),
            model=model_map.get(params.get('model', 'fraunhofer'), PropagationModel.FRAUNHOFER),
            pad_factor=params.get('pad_factor', 2.0),
        )

        param_idx = self.param_combo.currentIndex()
        param_names = ['wavelength', 'aperture_size', 'distance']
        param_name = param_names[param_idx]

        start_val = self.start_spin.value()
        end_val = self.end_spin.value()

        if param_name == 'wavelength':
            start_val *= 1e-9
            end_val *= 1e-9
        elif param_name == 'aperture_size':
            start_val *= 1e-6
            end_val *= 1e-6

        engine = DiffractionEngine(use_gpu=False)

        self._worker = ScanWorker(
            engine, aperture, sim_params, param_name,
            start_val, end_val, self.steps_spin.value())
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("扫描中...")

    def _cancel_scan(self):
        if self._worker:
            self._worker.cancel()
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("已取消")

    def _on_progress(self, pct: int, val: float, intensity):
        self.progress_bar.setValue(pct)
        if intensity is not None:
            display = np.log1p(intensity)
            d_min, d_max = display.min(), display.max()
            if d_max > d_min:
                display = (display - d_min) / (d_max - d_min)
            self.image_widget.setImage(display.astype(np.float32))

    def _on_finished(self, results: list):
        self._scan_results = results
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.status_label.setText(f"扫描完成，共 {len(results)} 步")

        if not results:
            return

        values = [r[0] for r in results]
        strehls = [r[2] for r in results]
        fwhms = [r[3].get('fwhm_h', 0) for r in results]

        self.strehl_curve.setData(values, strehls)

        fwhm_normalized = [f / max(fwhms) if max(fwhms) > 0 else 0 for f in fwhms]
        self.fwhm_curve.setData(values, fwhm_normalized)

    def _on_error(self, error_msg: str):
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText(f"错误: {error_msg}")

    def _export_data(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出扫描数据", "", "CSV Files (*.csv)")
        if path and self._scan_results:
            import csv
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['参数值', 'Strehl比', 'FWHM_h', '峰值强度'])
                for val, _, sr, psf in self._scan_results:
                    writer.writerow([val, sr, psf.get('fwhm_h', 0), psf.get('peak', 0)])

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        apply_dialog_theme(self, is_dark)
        apply_plot_theme(self.metrics_plot, is_dark)
