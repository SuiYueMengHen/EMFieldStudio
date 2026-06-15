import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QDoubleSpinBox, QPushButton, QLabel, QSplitter,
    QWidget, QScrollArea, QTabWidget, QProgressBar, QSpinBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import pyqtgraph as pg

from core.diffraction import DiffractionEngine, SimulationParams, PropagationModel
from core.aperture import ApertureType, ApertureFactory
from .dialog_theme import apply_dialog_theme, apply_plot_theme


SURFACE_TYPES = {
    'flat': '平面',
    'tilt_x': '倾斜 (X方向)',
    'tilt_y': '倾斜 (Y方向)',
    'cylinder_x': '柱面 (X方向弯曲)',
    'cylinder_y': '柱面 (Y方向弯曲)',
    'sphere': '球面',
    'paraboloid': '抛物面',
    'cone': '锥面',
}


def _compute_surface_height(surface_type, X, Y, curvature, tilt_rad, tilt_rad_y):
    if surface_type == 'flat':
        return np.zeros_like(X)
    elif surface_type == 'tilt_x':
        return X * np.tan(tilt_rad)
    elif surface_type == 'tilt_y':
        return Y * np.tan(tilt_rad_y)
    elif surface_type == 'cylinder_x':
        return curvature * X ** 2
    elif surface_type == 'cylinder_y':
        return curvature * Y ** 2
    elif surface_type == 'sphere':
        return curvature * (X ** 2 + Y ** 2)
    elif surface_type == 'paraboloid':
        return curvature * (X ** 2 + Y ** 2)
    elif surface_type == 'cone':
        return curvature * np.sqrt(X ** 2 + Y ** 2)
    return np.zeros_like(X)


class ReceiverSurfaceWorker(QThread):
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, engine, aperture, sim_params, surface_type,
                 curvature, tilt_angle, tilt_angle_y, n_depth_slices):
        super().__init__()
        self.engine = engine
        self.aperture = aperture
        self.sim_params = sim_params
        self.surface_type = surface_type
        self.curvature = curvature
        self.tilt_angle = tilt_angle
        self.tilt_angle_y = tilt_angle_y
        self.n_depth_slices = max(n_depth_slices, 5)
        self._cancelled = False

    def run(self):
        try:
            z0 = self.sim_params.propagation_distance
            wl = self.sim_params.wavelength
            grid_size = self.sim_params.grid_size
            phys_size = self.sim_params.physical_size

            dx = phys_size / grid_size
            x = np.linspace(-grid_size / 2, grid_size / 2, grid_size) * dx
            y = np.linspace(-grid_size / 2, grid_size / 2, grid_size) * dx
            X, Y = np.meshgrid(x, y)

            tilt_rad = np.radians(self.tilt_angle)
            tilt_rad_y = np.radians(self.tilt_angle_y)
            surface_z = _compute_surface_height(
                self.surface_type, X, Y, self.curvature, tilt_rad, tilt_rad_y)

            z_eff = z0 - surface_z
            z_min = float(z_eff.min())
            z_max = float(z_eff.max())

            if z_min < 1e-10:
                z_min = 1e-10

            if abs(z_max - z_min) < 1e-12:
                result = self.engine.compute_diffraction(self.aperture, self.sim_params)
                if self._cancelled:
                    return
                self.finished.emit({
                    'original_intensity': result.intensity,
                    'shifted_intensity': result.intensity.copy(),
                    'surface_z': surface_z,
                    'x': x, 'y': y,
                })
                return

            n_slices = self.n_depth_slices
            z_slices = np.linspace(z_min, z_max, n_slices)

            slice_intensities = []
            for i, z_val in enumerate(z_slices):
                if self._cancelled:
                    return
                sp = SimulationParams(
                    wavelength=wl,
                    grid_size=grid_size,
                    physical_size=phys_size,
                    propagation_distance=z_val,
                    model=self.sim_params.model,
                    pad_factor=self.sim_params.pad_factor,
                )
                result = self.engine.compute_diffraction(self.aperture, sp)
                slice_intensities.append(result.intensity)
                pct = int((i + 1) / n_slices * 90)
                self.progress.emit(pct, f"计算深度切片 {i+1}/{n_slices}")

            if self._cancelled:
                return

            z_idx = (z_eff - z_min) / (z_max - z_min) * (n_slices - 1)
            z_idx = np.clip(z_idx, 0, n_slices - 1)

            idx_low = np.floor(z_idx).astype(int)
            idx_high = np.minimum(idx_low + 1, n_slices - 1)
            frac = (z_idx - idx_low)[..., np.newaxis]

            stack = np.stack(slice_intensities, axis=0)

            low_data = stack[idx_low, np.arange(grid_size)[:, None], np.arange(grid_size)[None, :]]
            high_data = stack[idx_high, np.arange(grid_size)[:, None], np.arange(grid_size)[None, :]]

            shifted = (1.0 - frac) * low_data + frac * high_data

            self.progress.emit(95, "计算原始参考...")

            sp0 = SimulationParams(
                wavelength=wl, grid_size=grid_size, physical_size=phys_size,
                propagation_distance=z0, model=self.sim_params.model,
                pad_factor=self.sim_params.pad_factor,
            )
            result0 = self.engine.compute_diffraction(self.aperture, sp0)
            original = result0.intensity

            if not self._cancelled:
                self.finished.emit({
                    'original_intensity': original,
                    'shifted_intensity': shifted,
                    'surface_z': surface_z,
                    'x': x, 'y': y,
                })
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class ReceiverSurfaceDialog(QDialog):

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("接收面形状分析")
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

        surface_group = QGroupBox("接收面形状")
        surface_form = QFormLayout(surface_group)
        self.surface_combo = QComboBox()
        for key, name in SURFACE_TYPES.items():
            self.surface_combo.addItem(name, key)
        self.surface_combo.currentIndexChanged.connect(self._update_info)
        surface_form.addRow("面型:", self.surface_combo)

        self.curvature_spin = QDoubleSpinBox()
        self.curvature_spin.setRange(-1e6, 1e6)
        self.curvature_spin.setValue(500.0)
        self.curvature_spin.setDecimals(1)
        self.curvature_spin.setSingleStep(50)
        self.curvature_spin.setSuffix(" 1/m")
        surface_form.addRow("曲率:", self.curvature_spin)

        self.tilt_spin = QDoubleSpinBox()
        self.tilt_spin.setRange(-45, 45)
        self.tilt_spin.setValue(10.0)
        self.tilt_spin.setDecimals(2)
        self.tilt_spin.setSingleStep(1)
        self.tilt_spin.setSuffix(" °")
        surface_form.addRow("倾斜角(X):", self.tilt_spin)

        self.tilt_y_spin = QDoubleSpinBox()
        self.tilt_y_spin.setRange(-45, 45)
        self.tilt_y_spin.setValue(0.0)
        self.tilt_y_spin.setDecimals(2)
        self.tilt_y_spin.setSingleStep(1)
        self.tilt_y_spin.setSuffix(" °")
        surface_form.addRow("倾斜角(Y):", self.tilt_y_spin)

        self.slices_spin = QSpinBox()
        self.slices_spin.setRange(5, 30)
        self.slices_spin.setValue(10)
        self.slices_spin.setToolTip("更多切片=更精确但更慢")
        surface_form.addRow("深度切片数:", self.slices_spin)

        left_layout.addWidget(surface_group)

        info_group = QGroupBox("面型说明")
        info_layout = QVBoxLayout(info_group)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self._update_info()
        info_layout.addWidget(self.info_label)
        left_layout.addWidget(info_group)

        self.compute_btn = QPushButton("计算接收面衍射")
        self.compute_btn.setObjectName("updateBtn")
        self.compute_btn.setMinimumHeight(36)
        self.compute_btn.clicked.connect(self._start_compute)
        left_layout.addWidget(self.compute_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        left_layout.addWidget(self.status_label)

        left_layout.addStretch()
        scroll.setWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()

        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setContentsMargins(4, 4, 4, 4)
        self.surface_image = pg.ImageView()
        tab1_layout.addWidget(self.surface_image, 1)
        tabs.addTab(tab1, "接收面形状")

        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setContentsMargins(4, 4, 4, 4)
        self.original_image = pg.ImageView()
        tab2_layout.addWidget(self.original_image, 1)
        tabs.addTab(tab2, "平面衍射")

        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setContentsMargins(4, 4, 4, 4)
        self.shifted_image = pg.ImageView()
        tab3_layout.addWidget(self.shifted_image, 1)
        tabs.addTab(tab3, "接收面衍射")

        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        tab4_layout.setContentsMargins(4, 4, 4, 4)
        self.diff_image = pg.ImageView()
        tab4_layout.addWidget(self.diff_image, 1)
        tabs.addTab(tab4, "差异对比")

        right_layout.addWidget(tabs, 1)

        self.compare_plot = pg.PlotWidget()
        self.compare_plot.setMaximumHeight(200)
        self.compare_plot.showGrid(x=True, y=True, alpha=0.3)
        self.compare_plot.setLabel('bottom', '位置 (像素)')
        self.compare_plot.setLabel('left', '强度')
        self.compare_plot.addLegend(offset=(10, 10))
        self.original_curve = self.compare_plot.plot(
            pen=pg.mkPen('#7c8cf8', width=2), name='平面')
        self.shifted_curve = self.compare_plot.plot(
            pen=pg.mkPen('#ff6600', width=2), name='接收面')
        right_layout.addWidget(self.compare_plot)

        splitter.addWidget(scroll)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 800])

        main_layout.addWidget(splitter)

    def _update_info(self):
        surface_type = self.surface_combo.currentData()
        descriptions = {
            'flat': '平面接收面，无形状变化。衍射图样与标准计算一致。',
            'tilt_x': '接收面沿X方向倾斜。不同X位置的有效传播距离不同，导致衍射斑在X方向产生非均匀离焦。模拟探测器倾斜放置的情况。',
            'tilt_y': '接收面沿Y方向倾斜。不同Y位置的有效传播距离不同。',
            'cylinder_x': '柱面弯曲（X方向），X方向有效距离呈二次变化。模拟弯曲基底上的探测器，产生X方向渐变离焦。',
            'cylinder_y': '柱面弯曲（Y方向），Y方向有效距离呈二次变化。',
            'sphere': '球面接收面，有效距离从中心向边缘呈二次递减。模拟场曲效应——中心对焦时边缘离焦，反之亦然。',
            'paraboloid': '抛物面接收面，与球面类似但曲率分布不同。常用于反射式聚焦系统。',
            'cone': '锥面接收面，有效距离从中心向边缘线性递减。模拟轴锥镜接收面。',
        }
        self.info_label.setText(descriptions.get(surface_type, ''))

    def _start_compute(self):
        if self._main_window is None:
            return

        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)

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
            grid_size=min(params.get('grid_size', 512), 512),
            physical_size=params.get('physical_size', 200e-6),
            propagation_distance=params.get('distance', 0.1),
            model=model_map.get(params.get('model', 'fresnel_asm'), PropagationModel.FRESNEL_ASM),
            pad_factor=params.get('pad_factor', 2.0),
        )

        engine = DiffractionEngine(use_gpu=False)
        self._worker = ReceiverSurfaceWorker(
            engine, aperture, sim_params,
            self.surface_combo.currentData(),
            self.curvature_spin.value(),
            self.tilt_spin.value(),
            self.tilt_y_spin.value(),
            self.slices_spin.value())
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self.compute_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("计算中...")

    def _on_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_label.setText(msg)

    def _on_finished(self, output: dict):
        self.compute_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("计算完成")

        surface_z = output['surface_z']
        original = output['original_intensity']
        shifted = output['shifted_intensity']

        sz_display = surface_z.copy()
        sz_min, sz_max = sz_display.min(), sz_display.max()
        if sz_max > sz_min:
            sz_display = (sz_display - sz_min) / (sz_max - sz_min)
        self.surface_image.setImage(sz_display.astype(np.float32))

        orig_display = np.log1p(original)
        o_min, o_max = orig_display.min(), orig_display.max()
        if o_max > o_min:
            orig_display = (orig_display - o_min) / (o_max - o_min)
        self.original_image.setImage(orig_display.astype(np.float32))

        shift_display = np.log1p(shifted)
        s_min, s_max = shift_display.min(), shift_display.max()
        if s_max > s_min:
            shift_display = (shift_display - s_min) / (s_max - s_min)
        self.shifted_image.setImage(shift_display.astype(np.float32))

        diff = shifted - original
        diff_display = diff.copy()
        d_abs_max = max(abs(diff_display.min()), abs(diff_display.max()), 1e-30)
        diff_display = (diff_display + d_abs_max) / (2 * d_abs_max)
        self.diff_image.setImage(diff_display.astype(np.float32))

        ny, nx = original.shape
        mid_y = ny // 2
        x_coords = np.arange(nx)
        self.original_curve.setData(x_coords, original[mid_y, :])
        self.shifted_curve.setData(x_coords, shifted[mid_y, :])

    def _on_error(self, error_msg: str):
        self.compute_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"错误: {error_msg}")

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        apply_dialog_theme(self, is_dark)
        apply_plot_theme(self.compare_plot, is_dark)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        super().closeEvent(event)
