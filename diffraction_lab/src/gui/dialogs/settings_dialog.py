from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QFormLayout, QGroupBox, QComboBox,
    QCheckBox, QSpinBox, QDoubleSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QKeySequenceEdit, QLabel, QSlider, QMessageBox,
    QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence as QKeySequenceClass

from utils.preferences import (
    Preferences, DEFAULT_SHORTCUTS, PRECISION_PRESETS,
    DEFAULT_DISPLAY, DEFAULT_ADVANCED
)


class SettingsDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumSize(620, 520)
        self.resize(680, 580)
        self.prefs = Preferences()
        self._shortcut_edits = {}
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_general_tab(), "通用")
        self.tabs.addTab(self._create_shortcuts_tab(), "快捷键")
        self.tabs.addTab(self._create_precision_tab(), "渲染精度")
        self.tabs.addTab(self._create_display_tab(), "显示")
        self.tabs.addTab(self._create_advanced_tab(), "高级")
        layout.addWidget(self.tabs)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        reset_btn = QPushButton("恢复默认")
        reset_btn.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(reset_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("应用")
        apply_btn.setObjectName("applyBtn")
        apply_btn.clicked.connect(self._apply_settings)
        btn_layout.addWidget(apply_btn)

        layout.addLayout(btn_layout)

    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        general_group = QGroupBox("通用设置")
        form = QFormLayout(general_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["暗色", "亮色"])
        form.addRow("主题:", self.theme_combo)

        self.auto_update_check = QCheckBox("自动更新计算结果")
        form.addRow("", self.auto_update_check)

        self.restore_layout_check = QCheckBox("启动时恢复窗口布局")
        form.addRow("", self.restore_layout_check)

        layout.addWidget(general_group)
        layout.addStretch()
        return widget

    def _create_shortcuts_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel("点击快捷键列可修改，按 Esc 清除快捷键")
        info_label.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(info_label)

        self.shortcut_table = QTableWidget()
        self.shortcut_table.setColumnCount(3)
        self.shortcut_table.setHorizontalHeaderLabels(["操作", "快捷键", "默认值"])
        self.shortcut_table.horizontalHeader().setStretchLastSection(True)
        self.shortcut_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.shortcut_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self.shortcut_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self.shortcut_table.setAlternatingRowColors(True)
        self.shortcut_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)

        action_names = {
            'update': '更新计算',
            'reset_view': '重置视图',
            'fit_window': '适应窗口',
            'horizontal_profile': '水平截面',
            'vertical_profile': '垂直截面',
            'fwhm_measure': 'FWHM测量',
            'toggle_theme': '切换主题',
            'export_image': '导出图像',
            'export_data': '导出数据',
            'save_config': '保存配置',
            'help': '帮助',
        }

        self.shortcut_table.setRowCount(len(action_names))
        self._shortcut_edits = {}

        for i, (key, name) in enumerate(action_names.items()):
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.ItemDataRole.UserRole, key)
            self.shortcut_table.setItem(i, 0, name_item)

            seq_edit = QKeySequenceEdit()
            seq_edit.setKeySequence(
                QKeySequenceClass(self.prefs.get_shortcut(key)))
            seq_edit.keySequenceChanged.connect(
                lambda seq, k=key: self._on_shortcut_changed(k, seq))
            self._shortcut_edits[key] = seq_edit
            self.shortcut_table.setCellWidget(i, 1, seq_edit)

            default_item = QTableWidgetItem(DEFAULT_SHORTCUTS.get(key, ''))
            default_item.setFlags(default_item.flags() & ~
                                  Qt.ItemFlag.ItemIsEditable)
            self.shortcut_table.setItem(i, 2, default_item)

        layout.addWidget(self.shortcut_table)

        reset_sc_btn = QPushButton("恢复默认快捷键")
        reset_sc_btn.clicked.connect(self._reset_shortcuts)
        layout.addWidget(reset_sc_btn)

        return widget

    def _create_precision_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        preset_group = QGroupBox("精度预设")
        preset_form = QFormLayout(preset_group)

        self.precision_combo = QComboBox()
        self.precision_combo.addItems(["草稿", "标准", "高精度", "超高精度", "极限精度"])
        self.precision_combo.setCurrentIndex(1)
        self.precision_combo.currentIndexChanged.connect(
            self._on_precision_preset_changed)
        preset_form.addRow("预设等级:", self.precision_combo)

        self.precision_info = QLabel("")
        self.precision_info.setStyleSheet("color: #888; font-size: 11px;")
        preset_form.addRow("", self.precision_info)

        layout.addWidget(preset_group)

        custom_group = QGroupBox("自定义精度")
        custom_form = QFormLayout(custom_group)

        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["256", "512", "1024", "2048", "4096"])
        custom_form.addRow("默认网格大小:", self.grid_size_combo)

        self.fft_precision_combo = QComboBox()
        self.fft_precision_combo.addItems([
            "float32 (快速)", "float64 (标准)", "longdouble (高精度)"])
        custom_form.addRow("FFT计算精度:", self.fft_precision_combo)

        self.interpolation_combo = QComboBox()
        self.interpolation_combo.addItems([
            "最近邻 (快速)", "双线性 (标准)", "高精度 (float64)"])
        custom_form.addRow("图像插值方式:", self.interpolation_combo)

        self.pad_factor_spin = QDoubleSpinBox()
        self.pad_factor_spin.setRange(1.0, 8.0)
        self.pad_factor_spin.setValue(2.0)
        self.pad_factor_spin.setSingleStep(0.5)
        custom_form.addRow("默认零填充因子:", self.pad_factor_spin)

        layout.addWidget(custom_group)

        auto_group = QGroupBox("自动降精度")
        auto_form = QFormLayout(auto_group)

        self.auto_reduce_check = QCheckBox("当计算超时时自动降低精度")
        auto_form.addRow("", self.auto_reduce_check)

        self.reduce_threshold_spin = QSpinBox()
        self.reduce_threshold_spin.setRange(500, 30000)
        self.reduce_threshold_spin.setValue(2000)
        self.reduce_threshold_spin.setSuffix(" ms")
        self.reduce_threshold_spin.setSingleStep(500)
        auto_form.addRow("超时阈值:", self.reduce_threshold_spin)

        layout.addWidget(auto_group)
        layout.addStretch()
        return widget

    def _create_display_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        display_group = QGroupBox("默认显示设置")
        form = QFormLayout(display_group)

        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["热力图", "翠绿色", "灰度", "等离子体", "炼狱"])
        form.addRow("颜色映射:", self.colormap_combo)

        self.log_scale_check = QCheckBox("默认对数显示")
        form.addRow("", self.log_scale_check)

        self.gamma_spin = QDoubleSpinBox()
        self.gamma_spin.setRange(0.1, 3.0)
        self.gamma_spin.setValue(1.0)
        self.gamma_spin.setSingleStep(0.1)
        self.gamma_spin.setDecimals(2)
        form.addRow("默认Gamma值:", self.gamma_spin)

        self.crosshair_check = QCheckBox("显示十字准线")
        form.addRow("", self.crosshair_check)

        layout.addWidget(display_group)

        status_group = QGroupBox("状态栏显示")
        status_form = QFormLayout(status_group)

        self.status_coord_check = QCheckBox("坐标信息")
        self.status_intensity_check = QCheckBox("强度信息")
        self.status_fps_check = QCheckBox("计算时间")
        self.status_strehl_check = QCheckBox("Strehl比")

        status_form.addRow("", self.status_coord_check)
        status_form.addRow("", self.status_intensity_check)
        status_form.addRow("", self.status_fps_check)
        status_form.addRow("", self.status_strehl_check)

        layout.addWidget(status_group)
        layout.addStretch()
        return widget

    def _create_advanced_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        compute_group = QGroupBox("计算设置")
        compute_form = QFormLayout(compute_group)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(5000, 120000)
        self.timeout_spin.setValue(30000)
        self.timeout_spin.setSuffix(" ms")
        self.timeout_spin.setSingleStep(5000)
        compute_form.addRow("计算超时:", self.timeout_spin)

        self.debounce_spin = QSpinBox()
        self.debounce_spin.setRange(50, 1000)
        self.debounce_spin.setValue(150)
        self.debounce_spin.setSuffix(" ms")
        self.debounce_spin.setSingleStep(50)
        compute_form.addRow("防抖延迟:", self.debounce_spin)

        self.gpu_check = QCheckBox("启用GPU加速（实验性）")
        self.gpu_check.setEnabled(False)
        compute_form.addRow("", self.gpu_check)

        layout.addWidget(compute_group)

        render_group = QGroupBox("渲染设置")
        render_form = QFormLayout(render_group)

        self.opengl_check = QCheckBox("启用OpenGL硬件加速")
        render_form.addRow("", self.opengl_check)

        self.antialias_check = QCheckBox("启用抗锯齿")
        render_form.addRow("", self.antialias_check)

        self.hidpi_check = QCheckBox("启用HiDPI缩放支持")
        render_form.addRow("", self.hidpi_check)

        layout.addWidget(render_group)

        log_group = QGroupBox("日志与缓存")
        log_form = QFormLayout(log_group)

        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_form.addRow("日志级别:", self.log_level_combo)

        self.cache_spin = QSpinBox()
        self.cache_spin.setRange(64, 4096)
        self.cache_spin.setValue(512)
        self.cache_spin.setSuffix(" MB")
        self.cache_spin.setSingleStep(64)
        log_form.addRow("缓存大小:", self.cache_spin)

        layout.addWidget(log_group)
        layout.addStretch()
        return widget

    def _load_settings(self):
        theme = self.prefs.get_theme()
        self.theme_combo.setCurrentIndex(0 if theme == 'dark' else 1)

        self.auto_update_check.setChecked(self.prefs.get_auto_update())
        self.restore_layout_check.setChecked(self.prefs.get_restore_layout())

        preset = self.prefs.get_precision_preset()
        preset_map = {'draft': 0, 'normal': 1, 'high': 2, 'ultra': 3, 'extreme': 4}
        self.precision_combo.setCurrentIndex(preset_map.get(preset, 1))
        self._on_precision_preset_changed(preset_map.get(preset, 1))

        precision_params = self.prefs.get_precision_params()
        grid_idx = self.grid_size_combo.findText(
            str(precision_params.get('grid_size', 512)))
        if grid_idx >= 0:
            self.grid_size_combo.setCurrentIndex(grid_idx)
        self.pad_factor_spin.setValue(precision_params.get('pad_factor', 2.0))

        fft_prec = self.prefs.get_advanced_setting('fft_precision', 'float64')
        fft_map = {'float32': 0, 'float64': 1, 'longdouble': 2}
        self.fft_precision_combo.setCurrentIndex(fft_map.get(fft_prec, 1))

        interp = self.prefs.get_advanced_setting('interpolation', 'bilinear')
        interp_map = {'nearest': 0, 'bilinear': 1, 'high_precision': 2}
        self.interpolation_combo.setCurrentIndex(interp_map.get(interp, 1))

        self.auto_reduce_check.setChecked(
            self.prefs.get_advanced_setting('auto_reduce_precision', True))
        self.reduce_threshold_spin.setValue(
            int(self.prefs.get_advanced_setting('auto_reduce_threshold_ms', 2000)))

        cmap_map = {'hot': 0, 'viridis': 1, 'gray': 2, 'plasma': 3, 'inferno': 4}
        cmap = self.prefs.get_display_setting('colormap', 'hot')
        self.colormap_combo.setCurrentIndex(cmap_map.get(cmap, 0))

        self.log_scale_check.setChecked(
            self.prefs.get_display_setting('log_scale', True))
        self.gamma_spin.setValue(
            float(self.prefs.get_display_setting('gamma', 1.0)))
        self.crosshair_check.setChecked(
            self.prefs.get_display_setting('show_crosshair', True))
        self.status_coord_check.setChecked(
            self.prefs.get_display_setting('show_status_coord', True))
        self.status_intensity_check.setChecked(
            self.prefs.get_display_setting('show_status_intensity', True))
        self.status_fps_check.setChecked(
            self.prefs.get_display_setting('show_status_fps', True))
        self.status_strehl_check.setChecked(
            self.prefs.get_display_setting('show_status_strehl', True))

        self.timeout_spin.setValue(
            int(self.prefs.get_advanced_setting('compute_timeout_ms', 30000)))
        self.debounce_spin.setValue(
            int(self.prefs.get_advanced_setting('debounce_ms', 150)))
        self.gpu_check.setChecked(
            self.prefs.get_advanced_setting('use_gpu', False))

        self.opengl_check.setChecked(
            self.prefs.get_advanced_setting('use_opengl', True))
        self.antialias_check.setChecked(
            self.prefs.get_advanced_setting('use_antialias', True))
        self.hidpi_check.setChecked(
            self.prefs.get_advanced_setting('use_hidpi', True))

        log_level = self.prefs.get_advanced_setting('log_level', 'INFO')
        log_idx = self.log_level_combo.findText(log_level)
        if log_idx >= 0:
            self.log_level_combo.setCurrentIndex(log_idx)

        self.cache_spin.setValue(
            int(self.prefs.get_advanced_setting('cache_size_mb', 512)))

    def _on_shortcut_changed(self, action: str, sequence):
        pass

    def _on_precision_preset_changed(self, index: int):
        preset_map = {0: 'draft', 1: 'normal', 2: 'high', 3: 'ultra', 4: 'extreme'}
        preset = preset_map.get(index, 'normal')
        params = PRECISION_PRESETS.get(preset, PRECISION_PRESETS['normal'])
        self.precision_info.setText(
            f"网格: {params['grid_size']}×{params['grid_size']}, "
            f"零填充: {params['pad_factor']}x")

    def _reset_shortcuts(self):
        for key, edit in self._shortcut_edits.items():
            edit.setKeySequence(QKeySequenceClass(DEFAULT_SHORTCUTS.get(key, '')))

    def _reset_defaults(self):
        reply = QMessageBox.question(
            self, "确认", "确定要恢复所有设置为默认值吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.prefs.reset_to_defaults()
            self._load_settings()
            for key, edit in self._shortcut_edits.items():
                edit.setKeySequence(
                    QKeySequenceClass(DEFAULT_SHORTCUTS.get(key, '')))

    def _apply_settings(self):
        theme_map = {0: 'dark', 1: 'light'}
        self.prefs.set_theme(theme_map[self.theme_combo.currentIndex()])

        self.prefs.set_auto_update(self.auto_update_check.isChecked())
        self.prefs.set_restore_layout(self.restore_layout_check.isChecked())

        preset_map = {0: 'draft', 1: 'normal', 2: 'high', 3: 'ultra', 4: 'extreme'}
        self.prefs.set_precision_preset(
            preset_map[self.precision_combo.currentIndex()])
        self.prefs.set_custom_grid_size(
            int(self.grid_size_combo.currentText()))
        self.prefs.set_custom_pad_factor(self.pad_factor_spin.value())

        fft_map = {0: 'float32', 1: 'float64', 2: 'longdouble'}
        self.prefs.set_advanced_setting(
            'fft_precision', fft_map[self.fft_precision_combo.currentIndex()])

        interp_map = {0: 'nearest', 1: 'bilinear', 2: 'high_precision'}
        self.prefs.set_advanced_setting(
            'interpolation', interp_map[self.interpolation_combo.currentIndex()])

        self.prefs.set_advanced_setting(
            'auto_reduce_precision', self.auto_reduce_check.isChecked())
        self.prefs.set_advanced_setting(
            'auto_reduce_threshold_ms', self.reduce_threshold_spin.value())

        cmap_map = {0: 'hot', 1: 'viridis', 2: 'gray', 3: 'plasma', 4: 'inferno'}
        self.prefs.set_display_setting(
            'colormap', cmap_map[self.colormap_combo.currentIndex()])
        self.prefs.set_display_setting(
            'log_scale', self.log_scale_check.isChecked())
        self.prefs.set_display_setting('gamma', self.gamma_spin.value())
        self.prefs.set_display_setting(
            'show_crosshair', self.crosshair_check.isChecked())
        self.prefs.set_display_setting(
            'show_status_coord', self.status_coord_check.isChecked())
        self.prefs.set_display_setting(
            'show_status_intensity', self.status_intensity_check.isChecked())
        self.prefs.set_display_setting(
            'show_status_fps', self.status_fps_check.isChecked())
        self.prefs.set_display_setting(
            'show_status_strehl', self.status_strehl_check.isChecked())

        self.prefs.set_advanced_setting(
            'compute_timeout_ms', self.timeout_spin.value())
        self.prefs.set_advanced_setting(
            'debounce_ms', self.debounce_spin.value())
        self.prefs.set_advanced_setting('use_gpu', self.gpu_check.isChecked())
        self.prefs.set_advanced_setting('use_opengl', self.opengl_check.isChecked())
        self.prefs.set_advanced_setting('use_antialias', self.antialias_check.isChecked())
        self.prefs.set_advanced_setting('use_hidpi', self.hidpi_check.isChecked())
        self.prefs.set_advanced_setting(
            'log_level', self.log_level_combo.currentText())
        self.prefs.set_advanced_setting(
            'cache_size_mb', self.cache_spin.value())

        for key, edit in self._shortcut_edits.items():
            seq = edit.keySequence().toString()
            self.prefs.set_shortcut(key, seq)

        self.prefs.sync()
        self.accept()
