import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QDoubleSpinBox, QPushButton, QLabel, QSlider, QSplitter, QWidget,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import pyqtgraph as pg

from core.diffraction import DiffractionEngine, SimulationParams, PropagationModel
from core.aperture import ApertureType, ApertureFactory
from .dialog_theme import apply_dialog_theme


class PropagationWorker(QThread):
    progress = pyqtSignal(int, float, np.ndarray)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, engine, aperture, params, distances):
        super().__init__()
        self.engine = engine
        self.aperture = aperture
        self.params = params
        self.distances = distances
        self._cancelled = False

    def run(self):
        try:
            frames = []
            model_map = {
                'fraunhofer': PropagationModel.FRAUNHOFER,
                'fresnel_asm': PropagationModel.FRESNEL_ASM,
                'fresnel_ir': PropagationModel.FRESNEL_IR,
                'rayleigh_sommerfeld': PropagationModel.RAYLEIGH_SOMMERFELD,
            }

            for i, d in enumerate(self.distances):
                if self._cancelled:
                    break

                sp = SimulationParams(
                    wavelength=self.params.get('wavelength', 532e-9),
                    grid_size=min(self.params.get('grid_size', 512), 512),
                    physical_size=self.params.get('physical_size', 200e-6),
                    propagation_distance=d,
                    model=model_map.get(
                        self.params.get('model', 'fresnel_asm'),
                        PropagationModel.FRESNEL_ASM),
                    pad_factor=self.params.get('pad_factor', 2.0),
                )
                result = self.engine.compute_diffraction(self.aperture, sp)
                intensity = result.intensity
                display = np.log1p(intensity)
                d_min, d_max = display.min(), display.max()
                if d_max > d_min:
                    display = (display - d_min) / (d_max - d_min)
                frames.append((d, display.astype(np.float32)))

                pct = int((i + 1) / len(self.distances) * 100)
                self.progress.emit(pct, d, display.astype(np.float32))

            if not self._cancelled:
                self.finished.emit(frames)
        except Exception as e:
            if not self._cancelled:
                self.error.emit(str(e))

    def cancel(self):
        self._cancelled = True


class PropagationDialog(QDialog):

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("传播动画")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        self._main_window = main_window
        self._is_dark = True
        self._frames = []
        self._current_frame = 0
        self._playing = False
        self._worker = None
        self._timer = QTimer()
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._next_frame)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        controls = QHBoxLayout()

        dist_group = QGroupBox("距离范围")
        dist_form = QFormLayout(dist_group)

        self.start_dist = QDoubleSpinBox()
        self.start_dist.setRange(0.0001, 100)
        self.start_dist.setValue(0.001)
        self.start_dist.setDecimals(4)
        self.start_dist.setSuffix(" m")
        dist_form.addRow("起始距离:", self.start_dist)

        self.end_dist = QDoubleSpinBox()
        self.end_dist.setRange(0.0001, 100)
        self.end_dist.setValue(1.0)
        self.end_dist.setDecimals(4)
        self.end_dist.setSuffix(" m")
        dist_form.addRow("结束距离:", self.end_dist)

        self.n_frames_spin = QDoubleSpinBox()
        self.n_frames_spin.setRange(5, 200)
        self.n_frames_spin.setValue(30)
        self.n_frames_spin.setDecimals(0)
        dist_form.addRow("帧数:", self.n_frames_spin)

        controls.addWidget(dist_group)

        btn_group = QGroupBox("控制")
        btn_layout = QVBoxLayout(btn_group)

        self.compute_btn = QPushButton("生成动画")
        self.compute_btn.setObjectName("updateBtn")
        self.compute_btn.clicked.connect(self._generate_frames)
        btn_layout.addWidget(self.compute_btn)

        self.cancel_btn = QPushButton("取消生成")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_generation)
        btn_layout.addWidget(self.cancel_btn)

        play_layout = QHBoxLayout()
        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self._toggle_play)
        play_layout.addWidget(self.play_btn)

        self.prev_btn = QPushButton("<")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.clicked.connect(self._prev_frame)
        play_layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton(">")
        self.next_btn.setFixedWidth(40)
        self.next_btn.clicked.connect(self._next_frame)
        play_layout.addWidget(self.next_btn)

        btn_layout.addLayout(play_layout)

        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(20, 500)
        self.speed_slider.setValue(100)
        self.speed_label = QLabel("100 ms/帧")
        self.speed_slider.valueChanged.connect(
            lambda v: (self._timer.setInterval(v), self.speed_label.setText(f"{v} ms/帧")))
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("速度:"))
        speed_layout.addWidget(self.speed_slider, 1)
        speed_layout.addWidget(self.speed_label)
        btn_layout.addLayout(speed_layout)

        controls.addWidget(btn_group)

        layout.addLayout(controls)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.frame_slider = QSlider(Qt.Orientation.Horizontal)
        self.frame_slider.setRange(0, 0)
        self.frame_slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.frame_slider)

        self.dist_label = QLabel("距离: --")
        layout.addWidget(self.dist_label)

        self.image_widget = pg.ImageView()
        layout.addWidget(self.image_widget, 1)

    def _generate_frames(self):
        if self._main_window is None:
            return

        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)

        cp = self._main_window.control_panel
        params = cp.get_params()
        aperture = self._main_window._create_aperture(params)

        distances = np.linspace(
            self.start_dist.value(), self.end_dist.value(),
            int(self.n_frames_spin.value()))

        engine = DiffractionEngine(use_gpu=False)

        self._worker = PropagationWorker(engine, aperture, params, distances)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

        self.compute_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.dist_label.setText("生成中...")

    def _cancel_generation(self):
        if self._worker:
            self._worker.cancel()
        self.compute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.dist_label.setText("已取消")

    def _on_progress(self, pct: int, dist: float, img: np.ndarray):
        self.progress_bar.setValue(pct)
        self.image_widget.setImage(img)
        self.dist_label.setText(f"距离: {dist:.4f} m  (生成中 {pct}%)")

    def _on_finished(self, frames: list):
        self._frames = frames
        self.compute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

        self.frame_slider.setRange(0, max(len(self._frames) - 1, 0))
        self.frame_slider.setValue(0)
        if self._frames:
            self._show_frame(0)

    def _on_error(self, error_msg: str):
        self.compute_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.dist_label.setText(f"错误: {error_msg}")

    def _show_frame(self, idx: int):
        if 0 <= idx < len(self._frames):
            d, img = self._frames[idx]
            self.image_widget.setImage(img)
            self.dist_label.setText(f"距离: {d:.4f} m  (帧 {idx+1}/{len(self._frames)})")

    def _on_slider_changed(self, val: int):
        self._current_frame = val
        self._show_frame(val)

    def _toggle_play(self):
        if self._playing:
            self._timer.stop()
            self._playing = False
            self.play_btn.setText("播放")
        else:
            if not self._frames:
                return
            self._timer.start()
            self._playing = True
            self.play_btn.setText("暂停")

    def _next_frame(self):
        if not self._frames:
            return
        self._current_frame = (self._current_frame + 1) % len(self._frames)
        self.frame_slider.setValue(self._current_frame)

    def _prev_frame(self):
        if not self._frames:
            return
        self._current_frame = (self._current_frame - 1) % len(self._frames)
        self.frame_slider.setValue(self._current_frame)

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        apply_dialog_theme(self, is_dark)

    def closeEvent(self, event):
        self._timer.stop()
        self._playing = False
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)
        super().closeEvent(event)
