import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QLabel, QSplitter, QWidget, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg

from core.chromatic import (
    ChromaticEngine, LIGHT_SOURCE_PRESETS, GLASS_PRESETS,
    uniform_visible_spectrum
)
from core.diffraction import SimulationParams, PropagationModel
from core.aperture import ApertureType, ApertureFactory
from .dialog_theme import apply_dialog_theme, apply_plot_theme


class ChromaticWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, engine, aperture, wavelengths, weights,
                 sim_params, glass_preset, thickness, log_scale):
        super().__init__()
        self.engine = engine
        self.aperture = aperture
        self.wavelengths = wavelengths
        self.weights = weights
        self.sim_params = sim_params
        self.glass_preset = glass_preset
        self.thickness = thickness
        self.log_scale = log_scale
        self._cancelled = False

    def run(self):
        try:
            if self.glass_preset and self.glass_preset != 'none':
                result = self.engine.compute_chromatic_with_dispersion(
                    self.aperture, self.wavelengths, self.weights,
                    self.sim_params, self.glass_preset, self.thickness,
                    self.log_scale)
            else:
                result = self.engine.compute_chromatic(
                    self.aperture, self.wavelengths, self.weights,
                    self.sim_params, self.log_scale)
            if not self._cancelled:
                self.finished.emit(result)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class ChromaticDiffractionDialog(QDialog):

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("彩色光衍射模拟")
        self.setMinimumSize(1100, 750)
        self.resize(1200, 800)
        self._main_window = main_window
        self._worker = None
        self._is_dark = True
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(8)

        source_group = QGroupBox("光源设置")
        source_form = QFormLayout(source_group)
        self.source_combo = QComboBox()
        self.source_combo.addItems(
            [v['name'] for v in LIGHT_SOURCE_PRESETS.values()])
        self.source_combo.addItem("自定义光谱")
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        source_form.addRow("光源预设:", self.source_combo)
        self.n_wavelengths_spin = QSpinBox()
        self.n_wavelengths_spin.setRange(3, 50)
        self.n_wavelengths_spin.setValue(20)
        source_form.addRow("采样波长数:", self.n_wavelengths_spin)
        left_layout.addWidget(source_group)

        spectrum_group = QGroupBox("光谱分布")
        spectrum_layout = QVBoxLayout(spectrum_group)
        self.spectrum_plot = pg.PlotWidget()
        self.spectrum_plot.setMinimumHeight(120)
        self.spectrum_plot.showGrid(x=True, y=True, alpha=0.3)
        self.spectrum_plot.setLabel('bottom', '波长 (nm)')
        self.spectrum_plot.setLabel('left', '权重')
        self.spectrum_curve = self.spectrum_plot.plot(
            pen=pg.mkPen('#7c8cf8', width=2),
            symbol='o', symbolSize=6, symbolBrush='#7c8cf8')
        bar_x = []
        bar_h = []
        bar_b = []
        preset_keys = list(LIGHT_SOURCE_PRESETS.keys())
        if preset_keys:
            preset = LIGHT_SOURCE_PRESETS[preset_keys[0]]
            wls = np.array(preset['wavelengths'])
            ws = np.array(preset['weights']) if preset['weights'] else np.ones_like(wls)
            bar_x = wls.tolist()
            bar_h = ws.tolist()
            bar_b = [0] * len(wls)
        self.spectrum_bars = pg.BarGraphItem(
            x=bar_x, height=bar_h, width=15,
            brush=pg.mkBrush(124, 140, 248, 80))
        self.spectrum_plot.addItem(self.spectrum_bars)
        spectrum_layout.addWidget(self.spectrum_plot)
        left_layout.addWidget(spectrum_group)

        dispersion_group = QGroupBox("色散模拟")
        dispersion_form = QFormLayout(dispersion_group)
        self.dispersion_check = QCheckBox("启用色散")
        dispersion_form.addRow("", self.dispersion_check)
        self.glass_combo = QComboBox()
        self.glass_combo.addItem("无", "none")
        for key, val in GLASS_PRESETS.items():
            self.glass_combo.addItem(val['name'], key)
        dispersion_form.addRow("玻璃材料:", self.glass_combo)
        self.thickness_spin = QDoubleSpinBox()
        self.thickness_spin.setRange(0.1, 100.0)
        self.thickness_spin.setValue(5.0)
        self.thickness_spin.setSuffix(" mm")
        self.thickness_spin.setSingleStep(0.5)
        dispersion_form.addRow("厚度:", self.thickness_spin)
        left_layout.addWidget(dispersion_group)

        params_group = QGroupBox("孔径与传播参数")
        params_form = QFormLayout(params_group)
        self.aperture_combo = QComboBox()
        self.aperture_combo.addItems([
            "圆形", "矩形", "三角形", "六边形",
            "圆环", "星形", "双缝", "光栅"
        ])
        params_form.addRow("孔径类型:", self.aperture_combo)
        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(0.1, 10000)
        self.size_spin.setValue(50)
        self.size_spin.setSuffix(" μm")
        params_form.addRow("孔径尺寸:", self.size_spin)
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setRange(0.001, 100)
        self.distance_spin.setValue(0.1)
        self.distance_spin.setSuffix(" m")
        self.distance_spin.setDecimals(3)
        params_form.addRow("传播距离:", self.distance_spin)
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "夫琅和费 (远场)", "菲涅尔 (角谱法)",
            "菲涅尔 (脉冲响应)", "瑞利-索末菲"
        ])
        params_form.addRow("传播模型:", self.model_combo)
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(["256", "512", "1024"])
        self.grid_combo.setCurrentText("512")
        params_form.addRow("网格大小:", self.grid_combo)
        self.log_check = QCheckBox("对数显示")
        self.log_check.setChecked(True)
        params_form.addRow("", self.log_check)
        left_layout.addWidget(params_group)

        self.compute_btn = QPushButton("计算彩色衍射")
        self.compute_btn.setObjectName("updateBtn")
        self.compute_btn.setMinimumHeight(36)
        self.compute_btn.clicked.connect(self._start_compute)
        left_layout.addWidget(self.compute_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        left_layout.addStretch()
        scroll.setWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.result_label = QLabel("等待计算...")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(self.result_label)
        self.image_widget = pg.ImageView()
        right_layout.addWidget(self.image_widget, 1)

        splitter.addWidget(scroll)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([320, 780])

        main_layout.addWidget(splitter)
        self._update_spectrum_plot()

    def _on_source_changed(self, index):
        self._update_spectrum_plot()

    def _update_spectrum_plot(self):
        idx = self.source_combo.currentIndex()
        preset_keys = list(LIGHT_SOURCE_PRESETS.keys())
        if idx < len(preset_keys):
            preset = LIGHT_SOURCE_PRESETS[preset_keys[idx]]
            wavelengths = np.array(preset['wavelengths'])
            weights = np.array(preset['weights']) if preset['weights'] else np.ones_like(wavelengths)
        else:
            n = self.n_wavelengths_spin.value()
            wavelengths, weights = uniform_visible_spectrum(n)
        self.spectrum_curve.setData(wavelengths, weights)
        self.spectrum_bars.setOpts(
            x=wavelengths.tolist(),
            height=weights.tolist(),
            width=max(15, (wavelengths[-1] - wavelengths[0]) / len(wavelengths) * 0.8))

    def _create_aperture(self, aperture_type_text: str, size_um: float):
        type_map = {
            "圆形": ApertureType.CIRCLE, "矩形": ApertureType.RECTANGLE,
            "三角形": ApertureType.TRIANGLE, "六边形": ApertureType.HEXAGON,
            "圆环": ApertureType.ANNULUS, "星形": ApertureType.STAR,
            "双缝": ApertureType.DOUBLE_SLIT, "光栅": ApertureType.GRATING,
        }
        at = type_map.get(aperture_type_text, ApertureType.CIRCLE)
        return ApertureFactory.create(at, params={'size': size_um})

    def _start_compute(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)

        idx = self.source_combo.currentIndex()
        preset_keys = list(LIGHT_SOURCE_PRESETS.keys())
        if idx < len(preset_keys):
            preset = LIGHT_SOURCE_PRESETS[preset_keys[idx]]
            wavelengths = np.array(preset['wavelengths'])
            weights = np.array(preset['weights']) if preset['weights'] else np.ones_like(wavelengths)
        else:
            n = self.n_wavelengths_spin.value()
            wavelengths, weights = uniform_visible_spectrum(n)

        aperture = self._create_aperture(
            self.aperture_combo.currentText(), self.size_spin.value())

        model_map = {
            "夫琅和费 (远场)": PropagationModel.FRAUNHOFER,
            "菲涅尔 (角谱法)": PropagationModel.FRESNEL_ASM,
            "菲涅尔 (脉冲响应)": PropagationModel.FRESNEL_IR,
            "瑞利-索末菲": PropagationModel.RAYLEIGH_SOMMERFELD,
        }

        sim_params = SimulationParams(
            wavelength=532e-9,
            grid_size=int(self.grid_combo.currentText()),
            physical_size=200e-6,
            propagation_distance=self.distance_spin.value(),
            model=model_map.get(self.model_combo.currentText(), PropagationModel.FRAUNHOFER),
            pad_factor=2.0,
        )

        glass_preset = 'none'
        if self.dispersion_check.isChecked():
            glass_preset = self.glass_combo.currentData() or 'none'

        engine = ChromaticEngine(use_gpu=False)
        self._worker = ChromaticWorker(
            engine, aperture, wavelengths, weights,
            sim_params, glass_preset, self.thickness_spin.value(),
            self.log_check.isChecked())
        self._worker.finished.connect(self._on_compute_finished)
        self._worker.error.connect(self._on_compute_error)
        self._worker.start()

        self.compute_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.result_label.setText("计算中...")

    def _on_compute_finished(self, rgb_image: np.ndarray):
        self.compute_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        display = (rgb_image * 255).astype(np.uint8)
        self.image_widget.setImage(display)
        self.result_label.setText(
            f"彩色衍射图样 ({rgb_image.shape[1]}×{rgb_image.shape[0]})")

    def _on_compute_error(self, error_msg: str):
        self.compute_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.result_label.setText(f"计算失败: {error_msg}")

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        apply_dialog_theme(self, is_dark)
        apply_plot_theme(self.spectrum_plot, is_dark)
