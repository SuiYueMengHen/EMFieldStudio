from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QDoubleSpinBox, QSpinBox, QComboBox,
    QSlider, QCheckBox, QPushButton, QLabel, QScrollArea,
    QTabWidget, QSizePolicy, QToolTip, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal


HELP_TEXTS = {
    'wavelength': '<b>波长 (Wavelength)</b><br>入射光的波长 λ，单位 nm。<br>衍射角与波长成正比：<br>θ ≈ 1.22 λ / D<br>可见光范围：380-780 nm',
    'aperture_size': '<b>孔径尺寸 (Aperture Size)</b><br>孔径的有效直径 D，单位 μm。<br>艾里斑半径：<br>r = 1.22 λ / D<br>增大孔径 → 衍射斑缩小',
    'distance': '<b>传播距离 (Propagation Distance)</b><br>观察面到孔径的距离 z，单位 m。<br>菲涅尔数：<br>N = a² / (λ·z)<br>N≫1 近场，N≪1 远场',
    'physical_size': '<b>物理尺寸 (Physical Size)</b><br>计算网格的物理边长，单位 μm。<br>决定频率域的采样范围：<br>Δf = 1 / L<br>增大 → 频率分辨率提高',
    'aperture_type': '<b>孔径类型 (Aperture Type)</b><br>选择衍射孔径的几何形状。<br>不同形状产生不同的衍射图样：<br>• 圆形 → 艾里斑<br>• 矩形 → sinc函数<br>• 双缝 → 干涉条纹',
    'center_x': '<b>中心X偏移</b><br>孔径中心在X方向的偏移，单位 μm。<br>偏移会导致衍射图样相位变化。',
    'center_y': '<b>中心Y偏移</b><br>孔径中心在Y方向的偏移，单位 μm。',
    'rotation': '<b>旋转角度</b><br>孔径绕中心的旋转角度，单位 °。<br>旋转会相应旋转衍射图样。',
    'aspect_ratio': '<b>宽高比 (Aspect Ratio)</b><br>矩形孔径的宽度与高度之比。<br>=1 为正方形，>1 为横向矩形。<br>影响sinc函数的宽窄比。',
    'inner_ratio': '<b>内径比 (Inner Ratio)</b><br>圆环/星形孔径的内径与外径之比。<br>范围 0-1。<br>=0 退化为圆形，接近1为细环。',
    'num_points': '<b>星形角数</b><br>星形孔径的尖角数量。<br>角数越多，衍射图样越接近圆环。',
    'num_slits': '<b>缝数</b><br>光栅的狭缝数量。<br>缝数越多，主极大越尖锐。<br>光栅分辨力 R = m·N',
    'slit_width': '<b>缝宽</b><br>单个狭缝的宽度，单位 μm。<br>决定单缝衍射包络：<br>sin(πa/λ) / (πa/λ)',
    'slit_separation': '<b>缝距</b><br>相邻狭缝的间距，单位 μm。<br>决定干涉条纹间距：<br>Δθ = λ / d',
    'model': '<b>传播模型 (Propagation Model)</b><br>• 夫琅和费：远场近似，FFT直接计算<br>• 菲涅尔(角谱法)：近场，适合 N>1<br>• 菲涅尔(脉冲响应)：近场，卷积法<br>• 瑞利-索末菲：最严格，计算最慢',
    'grid_size': '<b>网格大小 (Grid Size)</b><br>FFT计算网格的采样点数 N×N。<br>越大 → 结果越精细，计算越慢。<br>建议：预览用512，最终用1024+',
    'pad_factor': '<b>零填充因子 (Zero Padding)</b><br>FFT前对孔径进行零填充的倍数。<br>提高频率域插值精度。<br>=2 表示网格扩大2倍。',
    'gamma': '<b>对比度 γ (Gamma)</b><br>显示gamma校正值。<br>γ &lt; 1 增强暗部细节<br>γ = 1 线性显示<br>γ &gt; 1 增强亮部细节',
    'log_scale': '<b>对数显示</b><br>使用 log(1+I) 显示强度。<br>增强弱信号可见性。<br>适合观察衍射次极大。',
    'colormap': '<b>颜色映射</b><br>将强度值映射为颜色的方案。<br>• 热力图：黑→红→黄→白<br>• 翠绿色：感知均匀<br>• 灰度：经典黑白',
    'defocus': '<b>离焦 Z₄ (Defocus)</b><br>Zernike多项式第4项，单位 λ。<br>波前离焦量，正值为远焦。<br>W = Z₄·(2ρ²-1)',
    'astigmatism': '<b>像散 Z₅/Z₆ (Astigmatism)</b><br>Zernike像散系数，单位 λ。<br>导致不同方向焦点不同。<br>W = Z₅·ρ²cos2θ + Z₆·ρ²sin2θ',
    'coma': '<b>彗差 Z₇/Z₈ (Coma)</b><br>Zernike彗差系数，单位 λ。<br>导致点源呈彗星状拖尾。<br>W = Z₇·(3ρ³-2ρ)cosθ',
    'spherical': '<b>球差 Z₁₁ (Spherical)</b><br>Zernike球差系数，单位 λ。<br>边缘光线与近轴光线焦点不同。<br>W = Z₁₁·(6ρ⁴-6ρ²+1)',
    'trefoil': '<b>三叶差 Z₉/Z₁₀ (Trefoil)</b><br>Zernike三叶差系数，单位 λ。<br>三重对称像差。<br>W = Z₉·ρ³cos3θ',
    'multi_wl': '<b>多波长合成</b><br>同时计算多个波长的衍射图样，<br>按RGB颜色通道合成真彩色图像。<br>模拟白光衍射效果。',
}


class HelpButton(QPushButton):

    def __init__(self, help_key: str, parent=None):
        super().__init__("?", parent)
        self.setFixedSize(18, 18)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7c8cf8;
                border: 1px solid #5a5b7e;
                border-radius: 9px;
                font-size: 11px;
                font-weight: bold;
                padding: 0;
            }
            QPushButton:hover {
                background-color: #7c8cf8;
                color: white;
            }
        """)
        self._help_text = HELP_TEXTS.get(help_key, "")
        self.setToolTip(self._help_text)
        self.clicked.connect(self._show_help)

    def _show_help(self):
        QToolTip.showText(
            self.mapToGlobal(self.rect().bottomLeft()),
            self._help_text,
            self
        )


class ParamRow(QWidget):

    def __init__(self, label: str, widget: QWidget, help_key: str = "",
                 parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)

        lbl = QLabel(label)
        lbl.setMinimumWidth(72)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl)

        if help_key:
            layout.addWidget(HelpButton(help_key))

        layout.addWidget(widget, 1)

        self._widget = widget

    def get_widget(self):
        return self._widget


def _make_scroll_area(content: QWidget) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    scroll.setMinimumHeight(200)
    return scroll


class ControlPanel(QWidget):

    params_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_aperture_type = 'circle'
        self._aperture_rows = {}
        self._setup_ui()
        self._connect_auto_update()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        top_bar = QHBoxLayout()
        self.update_btn = QPushButton("▶  更新计算")
        self.update_btn.setObjectName("updateBtn")
        self.update_btn.setMinimumHeight(36)
        self.update_btn.clicked.connect(self._emit_params)
        top_bar.addWidget(self.update_btn, 1)

        self.auto_update_check = QCheckBox("自动")
        self.auto_update_check.setChecked(True)
        top_bar.addWidget(self.auto_update_check)
        layout.addLayout(top_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_optics_tab(), "光学")
        self.tabs.addTab(self._create_aperture_tab(), "孔径")
        self.tabs.addTab(self._create_advanced_tab(), "高级")
        self.tabs.addTab(self._create_display_tab(), "显示")
        layout.addWidget(self.tabs)

    def _connect_auto_update(self):
        self.wavelength_spin.valueChanged.connect(self._auto_emit)
        self.size_spin.valueChanged.connect(self._auto_emit)
        self.distance_spin.valueChanged.connect(self._auto_emit)
        self.physical_size_spin.valueChanged.connect(self._auto_emit)
        self.aperture_type_combo.currentTextChanged.connect(self._auto_emit)
        self.center_x_spin.valueChanged.connect(self._auto_emit)
        self.center_y_spin.valueChanged.connect(self._auto_emit)
        self.rotation_spin.valueChanged.connect(self._auto_emit)
        self.aspect_ratio_spin.valueChanged.connect(self._auto_emit)
        self.inner_ratio_spin.valueChanged.connect(self._auto_emit)
        self.num_points_spin.valueChanged.connect(self._auto_emit)
        self.num_slits_spin.valueChanged.connect(self._auto_emit)
        self.slit_width_spin.valueChanged.connect(self._auto_emit)
        self.slit_separation_spin.valueChanged.connect(self._auto_emit)
        self.model_combo.currentTextChanged.connect(self._auto_emit)
        self.grid_combo.currentTextChanged.connect(self._auto_emit)
        self.pad_spin.valueChanged.connect(self._auto_emit)
        self.aberration_check.stateChanged.connect(self._auto_emit)
        self.defocus_spin.valueChanged.connect(self._auto_emit)
        self.astigmatism_spin.valueChanged.connect(self._auto_emit)
        self.coma_spin.valueChanged.connect(self._auto_emit)
        self.spherical_spin.valueChanged.connect(self._auto_emit)
        self.trefoil_spin.valueChanged.connect(self._auto_emit)
        self.multi_wl_check.stateChanged.connect(self._auto_emit)
        self.wl1_spin.valueChanged.connect(self._auto_emit)
        self.wl2_spin.valueChanged.connect(self._auto_emit)
        self.wl3_spin.valueChanged.connect(self._auto_emit)
        self.colormap_combo.currentTextChanged.connect(self._auto_emit)
        self.log_check.stateChanged.connect(self._auto_emit)
        self.gamma_slider.valueChanged.connect(self._auto_emit)

    def _auto_emit(self, *_):
        if self.auto_update_check.isChecked():
            self._emit_params()

    def _create_optics_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(4)

        optics_group = QGroupBox("光学参数")
        optics_layout = QVBoxLayout(optics_group)
        optics_layout.setSpacing(2)

        self.wavelength_spin = self._make_double_spin(200, 2000, 532, 1, 10, " nm")
        optics_layout.addWidget(ParamRow("波长:", self.wavelength_spin, "wavelength"))

        self.size_spin = self._make_double_spin(0.1, 10000, 50, 1, 5, " μm")
        optics_layout.addWidget(ParamRow("孔径尺寸:", self.size_spin, "aperture_size"))

        self.distance_spin = self._make_double_spin(0.001, 100, 0.1, 3, 0.01, " m")
        optics_layout.addWidget(ParamRow("传播距离:", self.distance_spin, "distance"))

        self.physical_size_spin = self._make_double_spin(1, 10000, 200, 1, 10, " μm")
        optics_layout.addWidget(ParamRow("物理尺寸:", self.physical_size_spin, "physical_size"))

        layout.addWidget(optics_group)
        layout.addStretch()
        return _make_scroll_area(content)

    def _create_aperture_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(4)

        type_group = QGroupBox("孔径类型")
        type_layout = QVBoxLayout(type_group)
        type_layout.setSpacing(2)

        self.aperture_type_combo = QComboBox()
        self.aperture_type_combo.addItems([
            "圆形", "矩形", "三角形", "六边形",
            "圆环", "星形", "双缝", "光栅"
        ])
        self.aperture_type_combo.currentTextChanged.connect(self._on_aperture_type_changed)
        type_layout.addWidget(ParamRow("类型:", self.aperture_type_combo, "aperture_type"))

        self.center_x_spin = self._make_double_spin(-500, 500, 0, 1, 1, " μm")
        type_layout.addWidget(ParamRow("中心X:", self.center_x_spin, "center_x"))

        self.center_y_spin = self._make_double_spin(-500, 500, 0, 1, 1, " μm")
        type_layout.addWidget(ParamRow("中心Y:", self.center_y_spin, "center_y"))

        self.rotation_spin = self._make_double_spin(0, 360, 0, 1, 5, " °")
        type_layout.addWidget(ParamRow("旋转:", self.rotation_spin, "rotation"))

        layout.addWidget(type_group)

        shape_group = QGroupBox("形状参数")
        shape_layout = QVBoxLayout(shape_group)
        shape_layout.setSpacing(2)

        self.aspect_ratio_spin = self._make_double_spin(0.1, 10, 1.0, 2, 0.1)
        row = ParamRow("宽高比:", self.aspect_ratio_spin, "aspect_ratio")
        self._aperture_rows['aspect_ratio'] = row
        shape_layout.addWidget(row)

        self.inner_ratio_spin = self._make_double_spin(0.01, 0.99, 0.5, 2, 0.05)
        row = ParamRow("内径比:", self.inner_ratio_spin, "inner_ratio")
        self._aperture_rows['inner_ratio'] = row
        shape_layout.addWidget(row)

        self.num_points_spin = QSpinBox()
        self.num_points_spin.setRange(3, 20)
        self.num_points_spin.setValue(5)
        row = ParamRow("星形角数:", self.num_points_spin, "num_points")
        self._aperture_rows['num_points'] = row
        shape_layout.addWidget(row)

        self.num_slits_spin = QSpinBox()
        self.num_slits_spin.setRange(2, 50)
        self.num_slits_spin.setValue(5)
        row = ParamRow("缝数:", self.num_slits_spin, "num_slits")
        self._aperture_rows['num_slits'] = row
        shape_layout.addWidget(row)

        self.slit_width_spin = self._make_double_spin(0.1, 1000, 5, 1, 1, " μm")
        row = ParamRow("缝宽:", self.slit_width_spin, "slit_width")
        self._aperture_rows['slit_width'] = row
        shape_layout.addWidget(row)

        self.slit_separation_spin = self._make_double_spin(0.1, 1000, 25, 1, 1, " μm")
        row = ParamRow("缝距:", self.slit_separation_spin, "slit_separation")
        self._aperture_rows['slit_separation'] = row
        shape_layout.addWidget(row)

        layout.addWidget(shape_group)
        layout.addStretch()

        self._update_aperture_params_visibility()
        return _make_scroll_area(content)

    def _create_advanced_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(4)

        compute_group = QGroupBox("计算参数")
        compute_layout = QVBoxLayout(compute_group)
        compute_layout.setSpacing(2)

        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "夫琅和费 (远场)", "菲涅尔 (角谱法)",
            "菲涅尔 (脉冲响应)", "瑞利-索末菲"
        ])
        compute_layout.addWidget(ParamRow("传播模型:", self.model_combo, "model"))

        self.grid_combo = QComboBox()
        self.grid_combo.addItems(["256", "512", "1024", "2048"])
        self.grid_combo.setCurrentText("512")
        compute_layout.addWidget(ParamRow("网格大小:", self.grid_combo, "grid_size"))

        self.pad_spin = self._make_double_spin(1.0, 8.0, 2.0, 1, 0.5)
        compute_layout.addWidget(ParamRow("零填充:", self.pad_spin, "pad_factor"))

        layout.addWidget(compute_group)

        aberr_group = QGroupBox("像差控制 (Zernike)")
        aberr_layout = QVBoxLayout(aberr_group)
        aberr_layout.setSpacing(2)

        self.aberration_check = QCheckBox("启用像差")
        aberr_layout.addWidget(self.aberration_check)

        self.defocus_spin = self._make_double_spin(-10, 10, 0, 3, 0.1, " λ")
        aberr_layout.addWidget(ParamRow("离焦 Z₄:", self.defocus_spin, "defocus"))

        self.astigmatism_spin = self._make_double_spin(-10, 10, 0, 3, 0.1, " λ")
        aberr_layout.addWidget(ParamRow("像散 Z₅₊₆:", self.astigmatism_spin, "astigmatism"))

        self.coma_spin = self._make_double_spin(-10, 10, 0, 3, 0.1, " λ")
        aberr_layout.addWidget(ParamRow("彗差 Z₇₊₈:", self.coma_spin, "coma"))

        self.spherical_spin = self._make_double_spin(-10, 10, 0, 3, 0.1, " λ")
        aberr_layout.addWidget(ParamRow("球差 Z₁₁:", self.spherical_spin, "spherical"))

        self.trefoil_spin = self._make_double_spin(-10, 10, 0, 3, 0.1, " λ")
        aberr_layout.addWidget(ParamRow("三叶 Z₉₊₁₀:", self.trefoil_spin, "trefoil"))

        layout.addWidget(aberr_group)

        mwl_group = QGroupBox("多波长合成")
        mwl_layout = QVBoxLayout(mwl_group)
        mwl_layout.setSpacing(2)

        self.multi_wl_check = QCheckBox("启用多波长")
        mwl_layout.addWidget(self.multi_wl_check)

        self.wl1_spin = self._make_double_spin(380, 780, 450, 0, 10, " nm")
        mwl_layout.addWidget(ParamRow("波长1:", self.wl1_spin, "multi_wl"))

        self.wl2_spin = self._make_double_spin(380, 780, 532, 0, 10, " nm")
        mwl_layout.addWidget(ParamRow("波长2:", self.wl2_spin, "multi_wl"))

        self.wl3_spin = self._make_double_spin(380, 780, 633, 0, 10, " nm")
        mwl_layout.addWidget(ParamRow("波长3:", self.wl3_spin, "multi_wl"))

        layout.addWidget(mwl_group)
        layout.addStretch()
        return _make_scroll_area(content)

    def _create_display_tab(self) -> QWidget:
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(4)

        display_group = QGroupBox("显示参数")
        display_layout = QVBoxLayout(display_group)
        display_layout.setSpacing(2)

        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["热力图", "翠绿色", "灰度", "等离子体", "炼狱"])
        display_layout.addWidget(ParamRow("颜色映射:", self.colormap_combo, "colormap"))

        self.log_check = QCheckBox("对数显示")
        self.log_check.setChecked(True)
        display_layout.addWidget(ParamRow("", self.log_check, "log_scale"))

        self.gamma_slider = QSlider(Qt.Orientation.Horizontal)
        self.gamma_slider.setRange(10, 300)
        self.gamma_slider.setValue(100)
        self.gamma_label = QLabel("1.00")
        self.gamma_label.setFixedWidth(40)
        self.gamma_slider.valueChanged.connect(
            lambda v: self.gamma_label.setText(f"{v / 100:.2f}"))
        gamma_row = QWidget()
        gamma_layout = QHBoxLayout(gamma_row)
        gamma_layout.setContentsMargins(0, 0, 0, 0)
        gamma_layout.addWidget(self.gamma_slider, 1)
        gamma_layout.addWidget(self.gamma_label)
        display_layout.addWidget(ParamRow("对比度γ:", gamma_row, "gamma"))

        layout.addWidget(display_group)
        layout.addStretch()
        return _make_scroll_area(content)

    def _make_double_spin(self, min_val, max_val, default, decimals,
                          step, suffix="") -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        if suffix:
            spin.setSuffix(suffix)
        return spin

    def _on_aperture_type_changed(self, text: str):
        type_map = {
            "圆形": "circle", "矩形": "rectangle", "三角形": "triangle",
            "六边形": "hexagon", "圆环": "annulus",
            "星形": "star", "双缝": "double_slit", "光栅": "grating"
        }
        self._current_aperture_type = type_map.get(text, "circle")
        self._update_aperture_params_visibility()

    def _update_aperture_params_visibility(self):
        t = self._current_aperture_type
        self._aperture_rows.get('aspect_ratio', QWidget()).setVisible(t == 'rectangle')
        self._aperture_rows.get('inner_ratio', QWidget()).setVisible(t in ('annulus', 'star'))
        self._aperture_rows.get('num_points', QWidget()).setVisible(t == 'star')
        self._aperture_rows.get('num_slits', QWidget()).setVisible(t == 'grating')
        self._aperture_rows.get('slit_width', QWidget()).setVisible(t in ('double_slit', 'grating'))
        self._aperture_rows.get('slit_separation', QWidget()).setVisible(t in ('double_slit', 'grating'))

    def _emit_params(self):
        model_map = {
            "夫琅和费 (远场)": "fraunhofer",
            "菲涅尔 (角谱法)": "fresnel_asm",
            "菲涅尔 (脉冲响应)": "fresnel_ir",
            "瑞利-索末菲": "rayleigh_sommerfeld"
        }
        colormap_map = {
            "热力图": "hot", "翠绿色": "viridis", "灰度": "gray",
            "等离子体": "plasma", "炼狱": "inferno"
        }

        params = {
            'wavelength': self.wavelength_spin.value() * 1e-9,
            'aperture_size': self.size_spin.value() * 1e-6,
            'distance': self.distance_spin.value(),
            'physical_size': self.physical_size_spin.value() * 1e-6,
            'grid_size': int(self.grid_combo.currentText()),
            'model': model_map.get(self.model_combo.currentText(), 'fraunhofer'),
            'pad_factor': self.pad_spin.value(),
            'gamma': self.gamma_slider.value() / 100.0,
            'log_scale': self.log_check.isChecked(),
            'colormap': colormap_map.get(self.colormap_combo.currentText(), 'hot'),
            'aperture_type': self._current_aperture_type,
            'center_x': self.center_x_spin.value(),
            'center_y': self.center_y_spin.value(),
            'rotation': self.rotation_spin.value(),
            'aspect_ratio': self.aspect_ratio_spin.value(),
            'inner_ratio': self.inner_ratio_spin.value(),
            'num_points': self.num_points_spin.value(),
            'num_slits': self.num_slits_spin.value(),
            'slit_width': self.slit_width_spin.value(),
            'slit_separation': self.slit_separation_spin.value(),
            'aberration_enabled': self.aberration_check.isChecked(),
            'defocus': self.defocus_spin.value(),
            'astigmatism': self.astigmatism_spin.value(),
            'coma': self.coma_spin.value(),
            'spherical': self.spherical_spin.value(),
            'trefoil': self.trefoil_spin.value(),
            'multi_wl_enabled': self.multi_wl_check.isChecked(),
            'wavelengths': [self.wl1_spin.value(), self.wl2_spin.value(), self.wl3_spin.value()],
        }
        self.params_changed.emit(params)
        self._last_params = params

    def get_params(self) -> dict:
        self._emit_params()
        return self._last_params

    def get_aberration_params(self) -> dict:
        return {
            'enabled': self.aberration_check.isChecked(),
            'defocus': self.defocus_spin.value(),
            'astigmatism': self.astigmatism_spin.value(),
            'coma': self.coma_spin.value(),
            'spherical': self.spherical_spin.value(),
            'trefoil': self.trefoil_spin.value(),
        }

    def get_multi_wl_params(self) -> dict:
        return {
            'enabled': self.multi_wl_check.isChecked(),
            'wavelengths': [self.wl1_spin.value(), self.wl2_spin.value(), self.wl3_spin.value()],
        }
