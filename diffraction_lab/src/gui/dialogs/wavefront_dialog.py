import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QDoubleSpinBox, QPushButton, QLabel, QSplitter, QWidget,
    QCheckBox, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

from core.zernike import compute_wavefront, zernike_names, ZERNIKE_INDICES
from .dialog_theme import apply_dialog_theme


ZERNIKE_ITEMS = [
    ('piston', 'Z₀ 平移'),
    ('tip', 'Z₁ 倾斜X'),
    ('tilt', 'Z₂ 倾斜Y'),
    ('defocus', 'Z₄ 离焦'),
    ('astigmatism_0', 'Z₅ 像散0°'),
    ('astigmatism_45', 'Z₆ 像散45°'),
    ('coma_x', 'Z₇ 彗差X'),
    ('coma_y', 'Z₈ 彗差Y'),
    ('trefoil_x', 'Z₉ 三叶X'),
    ('trefoil_y', 'Z₁₀ 三叶Y'),
    ('spherical', 'Z₁₁ 球差'),
    ('sec_astig_0', 'Z₁₂ 二级像散0°'),
    ('sec_astig_45', 'Z₁₃ 二级像散45°'),
    ('quadrafoil_x', 'Z₁₄ 四叶X'),
    ('quadrafoil_y', 'Z₁₅ 四叶Y'),
]


class WavefrontDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("波前分析")
        self.setMinimumSize(1050, 700)
        self.resize(1150, 750)
        self._is_dark = True
        self._spinboxes = {}
        self._setup_ui()
        self._update_wavefront()

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

        zernike_group = QGroupBox("Zernike 系数编辑器")
        zernike_grid = QGridLayout(zernike_group)
        zernike_grid.setSpacing(4)

        for i, (key, label) in enumerate(ZERNIKE_ITEMS):
            row, col = divmod(i, 2)
            lbl = QLabel(label)
            spin = QDoubleSpinBox()
            spin.setRange(-10.0, 10.0)
            spin.setValue(0.0)
            spin.setSingleStep(0.05)
            spin.setDecimals(3)
            spin.setSuffix(" λ")
            spin.valueChanged.connect(self._update_wavefront)
            zernike_grid.addWidget(lbl, row, col * 2)
            zernike_grid.addWidget(spin, row, col * 2 + 1)
            self._spinboxes[key] = spin

        left_layout.addWidget(zernike_group)

        ctrl_group = QGroupBox("干涉图控制")
        ctrl_form = QFormLayout(ctrl_group)
        self.interferogram_check = QCheckBox("显示干涉图")
        self.interferogram_check.setChecked(True)
        self.interferogram_check.stateChanged.connect(self._update_wavefront)
        ctrl_form.addRow("", self.interferogram_check)
        self.tilt_spin = QDoubleSpinBox()
        self.tilt_spin.setRange(0, 30)
        self.tilt_spin.setValue(5)
        self.tilt_spin.setSingleStep(1)
        self.tilt_spin.setSuffix(" 条纹")
        self.tilt_spin.valueChanged.connect(self._update_wavefront)
        ctrl_form.addRow("参考倾斜:", self.tilt_spin)
        left_layout.addWidget(ctrl_group)

        self.reset_btn = QPushButton("重置所有系数")
        self.reset_btn.clicked.connect(self._reset_coefficients)
        left_layout.addWidget(self.reset_btn)

        left_layout.addStretch()
        scroll.setWidget(left_panel)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        wf_label = QLabel("波前相位图")
        wf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(wf_label)
        self.wavefront_image = pg.ImageView()
        right_layout.addWidget(self.wavefront_image, 1)

        igram_label = QLabel("干涉图模拟")
        igram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(igram_label)
        self.interferogram_image = pg.ImageView()
        right_layout.addWidget(self.interferogram_image, 1)

        splitter.addWidget(scroll)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([300, 750])

        main_layout.addWidget(splitter)

    def _get_coefficients(self) -> dict:
        return {key: spin.value() for key, spin in self._spinboxes.items()}

    def _update_wavefront(self, *_):
        coefficients = self._get_coefficients()

        n = 256
        x = np.linspace(-1, 1, n)
        y = np.linspace(-1, 1, n)
        X, Y = np.meshgrid(x, y)
        rho = np.sqrt(X**2 + Y**2)

        if any(v != 0 for v in coefficients.values()):
            wavefront, _ = compute_wavefront(X, Y, 1.0, coefficients)
        else:
            wavefront = np.zeros((n, n), dtype=np.float64)

        display = wavefront.copy()
        display[rho > 1] = np.nan
        self.wavefront_image.setImage(display.astype(np.float32))

        if self.interferogram_check.isChecked():
            tilt = self.tilt_spin.value()
            reference = tilt * X
            phase_diff = 2 * np.pi * (wavefront + reference)
            intensity = 0.5 * (1 + np.cos(phase_diff))
            intensity[rho > 1] = 0
            self.interferogram_image.setImage(intensity.astype(np.float32))

    def _reset_coefficients(self):
        for spin in self._spinboxes.values():
            spin.blockSignals(True)
            spin.setValue(0.0)
            spin.blockSignals(False)
        self._update_wavefront()

    def set_theme(self, is_dark: bool):
        self._is_dark = is_dark
        apply_dialog_theme(self, is_dark)
