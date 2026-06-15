import os
import time
import hashlib
import json

import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QDockWidget,
    QToolBar, QStatusBar, QPushButton, QLabel,
    QComboBox, QFileDialog, QMessageBox, QProgressBar,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QKeySequence

from .canvas import DiffractionCanvas
from .control_panel import ControlPanel
from .profile_plot import ProfilePlot
from .data_panel import DataPanel
from .dialogs.export_dialog import ExportDialog
from .dialogs.parameter_scan_dialog import ParameterScanDialog
from .dialogs.about_dialog import AboutDialog
from .dialogs.analysis_dialog import AnalysisDialog
from .dialogs.help_dialog import HelpDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.chromatic_diffraction_dialog import ChromaticDiffractionDialog
from .dialogs.fitting_dialog import FittingDialog
from .dialogs.wavefront_dialog import WavefrontDialog
from .dialogs.propagation_dialog import PropagationDialog
from .dialogs.optical_scene_dialog import OpticalSceneDialog
from .dialogs.receiver_surface_dialog import ReceiverSurfaceDialog
from core.aperture import (
    ApertureType, ApertureParams, ApertureFactory,
    CircleAperture, RectangleAperture, TriangleAperture,
    HexagonAperture, AnnulusAperture, StarAperture,
    DoubleSlitAperture, GratingAperture, CompositeAperture,
    CompositeOperation
)
from core.diffraction import DiffractionEngine, SimulationParams, PropagationModel
from core.zernike import compute_wavefront, apply_aberration, ZERNIKE_INDICES
from core.optics import fresnel_number, wavelength_to_rgb
from analysis.psf_mtf import compute_psf, compute_mtf, radial_mtf, strehl_ratio
from analysis.measurements import radial_profile, encircled_energy
from utils.config import ConfigManager
from utils.preferences import Preferences
from utils.io_handler import IOHandler
from utils.logger import get_logger

logger = get_logger()

DARK_THEME = """
QMainWindow, QWidget { background-color: #1a1b2e; color: #e0e0e0; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 12px; }
QGroupBox { border: 1px solid #3a3b5e; border-radius: 8px; margin-top: 12px; padding-top: 18px; font-weight: 600; color: #7c8cf8; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit { background-color: #252640; border: 1px solid #3a3b5e; border-radius: 6px; padding: 5px 10px; color: #e0e0e0; min-height: 26px; }
QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QLineEdit:focus { border-color: #7c8cf8; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #252640; color: #e0e0e0; selection-background-color: #3a3b5e; border-radius: 4px; }
QPushButton { background-color: #2d2e4a; border: 1px solid #3a3b5e; border-radius: 6px; padding: 7px 18px; color: #e0e0e0; min-height: 26px; }
QPushButton:hover { background-color: #3a3b5e; border-color: #7c8cf8; }
QPushButton:pressed { background-color: #252640; }
QPushButton#updateBtn { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c8cf8,stop:1 #6c7cf0); color: #1a1b2e; font-weight: 700; border: none; }
QPushButton#updateBtn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8c9cff,stop:1 #7c8cf8); }
QPushButton#applyBtn { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c8cf8,stop:1 #6c7cf0); color: #1a1b2e; font-weight: 700; border: none; }
QPushButton#applyBtn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #8c9cff,stop:1 #7c8cf8); }
QSlider::groove:horizontal { border: none; height: 6px; background: #252640; border-radius: 3px; }
QSlider::handle:horizontal { background: #7c8cf8; border: none; width: 18px; margin: -6px 0; border-radius: 9px; }
QSlider::handle:horizontal:hover { background: #8c9cff; }
QCheckBox { spacing: 8px; color: #e0e0e0; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #3a3b5e; background-color: #252640; }
QCheckBox::indicator:checked { background-color: #7c8cf8; border-color: #7c8cf8; }
QDockWidget { color: #e0e0e0; }
QDockWidget::title { background-color: #252640; padding: 8px; border-bottom: 1px solid #3a3b5e; border-radius: 2px; }
QMenuBar { background-color: #15162a; color: #e0e0e0; border-bottom: 1px solid #252640; padding: 2px; }
QMenuBar::item { padding: 6px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #3a3b5e; }
QMenu { background-color: #252640; color: #e0e0e0; border: 1px solid #3a3b5e; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 4px; }
QMenu::item:selected { background-color: #3a3b5e; }
QToolBar { background-color: #15162a; border-bottom: 1px solid #252640; spacing: 6px; padding: 4px 8px; }
QToolBar QToolButton { background-color: transparent; border: 1px solid transparent; border-radius: 6px; padding: 5px 10px; color: #e0e0e0; }
QToolBar QToolButton:hover { background-color: #3a3b5e; border-color: #7c8cf8; }
QStatusBar { background-color: #15162a; color: #8888aa; border-top: 1px solid #252640; font-size: 11px; }
QLabel { color: #e0e0e0; background: transparent; }
QScrollArea { border: none; background: transparent; }
QTabWidget::pane { border: 1px solid #3a3b5e; background-color: #1a1b2e; border-radius: 4px; }
QTabBar::tab { background-color: #252640; color: #8888aa; padding: 8px 16px; border: 1px solid #3a3b5e; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
QTabBar::tab:selected { background-color: #1a1b2e; color: #7c8cf8; border-bottom: 2px solid #7c8cf8; }
QTableWidget { background-color: #1a1b2e; color: #e0e0e0; gridline-color: #252640; border: 1px solid #3a3b5e; border-radius: 4px; }
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:alternate { background-color: #20213a; }
QHeaderView::section { background-color: #252640; color: #7c8cf8; padding: 6px; border: none; border-bottom: 1px solid #3a3b5e; font-weight: 600; }
QProgressBar { border: none; border-radius: 4px; text-align: center; background-color: #252640; color: #e0e0e0; height: 8px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c8cf8,stop:1 #6c7cf0); border-radius: 4px; }
QScrollBar:vertical { background: #1a1b2e; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #3a3b5e; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #7c8cf8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #1a1b2e; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #3a3b5e; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #7c8cf8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QKeySequenceEdit { background-color: #252640; border: 1px solid #3a3b5e; border-radius: 6px; padding: 4px 8px; color: #e0e0e0; min-height: 26px; }
"""

LIGHT_THEME = """
QMainWindow, QWidget { background-color: #f5f6fa; color: #2c3e50; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 12px; }
QGroupBox { border: 1px solid #dcdde1; border-radius: 8px; margin-top: 12px; padding-top: 18px; font-weight: 600; color: #5b6abf; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QDoubleSpinBox, QSpinBox, QComboBox, QLineEdit { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 5px 10px; color: #2c3e50; min-height: 26px; }
QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus, QLineEdit:focus { border-color: #5b6abf; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView { background-color: #ffffff; color: #2c3e50; selection-background-color: #e8e9f0; border-radius: 4px; }
QPushButton { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 7px 18px; color: #2c3e50; min-height: 26px; }
QPushButton:hover { background-color: #e8e9f0; border-color: #5b6abf; }
QPushButton:pressed { background-color: #dcdde1; }
QPushButton#updateBtn { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5b6abf,stop:1 #6c7bd0); color: #ffffff; font-weight: 700; border: none; }
QPushButton#updateBtn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c7bd0,stop:1 #7c8ce0); }
QPushButton#applyBtn { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5b6abf,stop:1 #6c7bd0); color: #ffffff; font-weight: 700; border: none; }
QPushButton#applyBtn:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #6c7bd0,stop:1 #7c8ce0); }
QSlider::groove:horizontal { border: none; height: 6px; background: #dcdde1; border-radius: 3px; }
QSlider::handle:horizontal { background: #5b6abf; border: none; width: 18px; margin: -6px 0; border-radius: 9px; }
QSlider::handle:horizontal:hover { background: #6c7bd0; }
QCheckBox { spacing: 8px; color: #2c3e50; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #dcdde1; background-color: #ffffff; }
QCheckBox::indicator:checked { background-color: #5b6abf; border-color: #5b6abf; }
QDockWidget { color: #2c3e50; }
QDockWidget::title { background-color: #e8e9f0; padding: 8px; border-bottom: 1px solid #dcdde1; }
QMenuBar { background-color: #ffffff; color: #2c3e50; border-bottom: 1px solid #e8e9f0; padding: 2px; }
QMenuBar::item { padding: 6px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #e8e9f0; }
QMenu { background-color: #ffffff; color: #2c3e50; border: 1px solid #dcdde1; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 6px 24px; border-radius: 4px; }
QMenu::item:selected { background-color: #e8e9f0; }
QToolBar { background-color: #ffffff; border-bottom: 1px solid #e8e9f0; spacing: 6px; padding: 4px 8px; }
QStatusBar { background-color: #ffffff; color: #7f8c8d; border-top: 1px solid #e8e9f0; font-size: 11px; }
QLabel { color: #2c3e50; background: transparent; }
QScrollArea { border: none; background: transparent; }
QTabWidget::pane { border: 1px solid #dcdde1; background-color: #f5f6fa; border-radius: 4px; }
QTabBar::tab { background-color: #e8e9f0; color: #7f8c8d; padding: 8px 16px; border: 1px solid #dcdde1; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 2px; }
QTabBar::tab:selected { background-color: #f5f6fa; color: #5b6abf; border-bottom: 2px solid #5b6abf; }
QTableWidget { background-color: #ffffff; color: #2c3e50; gridline-color: #e8e9f0; border: 1px solid #dcdde1; border-radius: 4px; }
QTableWidget::item { padding: 4px 8px; }
QTableWidget::item:alternate { background-color: #f5f6fa; }
QHeaderView::section { background-color: #e8e9f0; color: #5b6abf; padding: 6px; border: none; border-bottom: 1px solid #dcdde1; font-weight: 600; }
QScrollBar:vertical { background: #f5f6fa; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #c0c0d0; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #5b6abf; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: #f5f6fa; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: #c0c0d0; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background: #5b6abf; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QKeySequenceEdit { background-color: #ffffff; border: 1px solid #dcdde1; border-radius: 6px; padding: 4px 8px; color: #2c3e50; min-height: 26px; }
"""


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DiffractionLab v1.0 — 衍射仿真软件")
        self.setMinimumSize(1400, 900)

        self.engine = DiffractionEngine(use_gpu=False)
        self.config_manager = ConfigManager()
        self.prefs = Preferences()
        self._current_result = None
        self._current_aperture = None
        self._last_compute_time = 0
        self._analysis_dialog = None
        self._help_dialog = None
        self._chromatic_dialog = None
        self._wavefront_dialog = None
        self._propagation_dialog = None
        self._receiver_dialog = None
        self._is_dark_theme = self.prefs.get_theme() == 'dark'

        self._result_cache = {}
        self._computing = False

        debounce_ms = self.prefs.get_debounce_ms()
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(debounce_ms)
        self._debounce_timer.timeout.connect(self._do_compute)

        self._pending_params = None

        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._apply_rendering_settings()
        self._apply_theme()
        self._apply_shortcuts()

        self._initial_compute()

    def _setup_ui(self):
        self.canvas = DiffractionCanvas()
        self.setCentralWidget(self.canvas)

        self.control_panel = ControlPanel()
        dock_right = QDockWidget("参数控制", self)
        dock_right.setWidget(self.control_panel)
        dock_right.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        dock_right.setMinimumWidth(280)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_right)

        self.data_panel = DataPanel()
        dock_data = QDockWidget("测量数据", self)
        dock_data.setWidget(self.data_panel)
        dock_data.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        dock_data.setMinimumWidth(260)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_data)

        self.profile_plot = ProfilePlot()
        dock_bottom = QDockWidget("截面分析", self)
        dock_bottom.setWidget(self.profile_plot)
        dock_bottom.setMinimumHeight(200)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock_bottom)

    def _setup_menu(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("文件")
        self._add_action(file_menu, "打开配置...", self._load_config, 'save_config')
        self._add_action(file_menu, "保存配置...", self._save_config, 'save_config')
        file_menu.addSeparator()
        self._add_action(file_menu, "导出图像...", self._export_image, 'export_image')
        self._add_action(file_menu, "导出数据...", self._export_data, 'export_data')
        file_menu.addSeparator()
        self._add_action(file_menu, "退出", self.close, None)

        view_menu = menubar.addMenu("视图")
        self._add_action(view_menu, "重置视图", self._reset_view, 'reset_view')
        self._add_action(view_menu, "适应窗口", self._fit_to_window, 'fit_window')
        view_menu.addSeparator()
        self._theme_action = QAction("切换亮色模式", self)
        self._theme_action.triggered.connect(self._toggle_theme)
        view_menu.addAction(self._theme_action)
        view_menu.addSeparator()
        colormap_menu = view_menu.addMenu("颜色映射")
        cmap_names = {'热力图': 'hot', '翠绿色': 'viridis', '灰度': 'gray',
                      '等离子体': 'plasma', '炼狱': 'inferno'}
        for cn_name, en_name in cmap_names.items():
            self._add_action(colormap_menu, cn_name,
                             lambda checked, n=en_name: self._set_colormap(n))

        analysis_menu = menubar.addMenu("分析")
        self._add_action(analysis_menu, "水平截面", self._show_horizontal_profile, 'horizontal_profile')
        self._add_action(analysis_menu, "垂直截面", self._show_vertical_profile, 'vertical_profile')
        self._add_action(analysis_menu, "FWHM测量", self._measure_fwhm, 'fwhm_measure')
        analysis_menu.addSeparator()
        self._add_action(analysis_menu, "MTF/PSF分析...", self._show_analysis_dialog)
        self._add_action(analysis_menu, "曲线拟合...", self._show_fitting_dialog)

        sim_menu = menubar.addMenu("仿真")
        self._add_action(sim_menu, "参数扫描...", self._parameter_scan)
        self._add_action(sim_menu, "传播动画...", self._show_propagation_dialog)
        self._add_action(sim_menu, "彩色光衍射模拟...", self._show_chromatic_dialog)
        sim_menu.addSeparator()
        self._add_action(sim_menu, "波前分析...", self._show_wavefront_dialog)
        self._add_action(sim_menu, "接收面形状分析...", self._show_receiver_surface_dialog)

        scene_menu = menubar.addMenu("场景")
        self._add_action(scene_menu, "光学场景预设...", self._show_optical_scene_dialog)
        scene_menu.addSeparator()
        self._add_action(scene_menu, "艾里斑 (圆形远场)", self._preset_airy)
        self._add_action(scene_menu, "杨氏双缝干涉", self._preset_double_slit)
        self._add_action(scene_menu, "光栅衍射", self._preset_grating)
        self._add_action(scene_menu, "圆环衍射", self._preset_annulus)
        self._add_action(scene_menu, "六边形衍射", self._preset_hexagon)
        self._add_action(scene_menu, "星形衍射", self._preset_star)
        scene_menu.addSeparator()
        self._add_action(scene_menu, "菲涅尔传播 (近距离)", self._preset_fresnel)

        settings_menu = menubar.addMenu("设置")
        self._add_action(settings_menu, "首选项...", self._show_settings_dialog)

        help_menu = menubar.addMenu("帮助")
        self._add_action(help_menu, "使用指南", self._show_help, 'help')
        self._add_action(help_menu, "关于", self._show_about)

    def _add_action(self, menu, text, callback, shortcut_key=None):
        act = QAction(text, self)
        if shortcut_key:
            sc = self.prefs.get_shortcut(shortcut_key)
            if sc:
                act.setShortcut(sc)
        act.triggered.connect(callback)
        menu.addAction(act)
        return act

    def _apply_shortcuts(self):
        update_sc = self.prefs.get_shortcut('update')
        if update_sc:
            self.control_panel.update_btn.setShortcut(update_sc)

    def _setup_toolbar(self):
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)

        toolbar.addWidget(QLabel(" 孔径: "))
        self.aperture_combo = QComboBox()
        self.aperture_combo.addItems([
            "圆形", "矩形", "三角形", "六边形",
            "圆环", "星形", "双缝", "光栅"
        ])
        self.aperture_combo.currentTextChanged.connect(self._on_toolbar_aperture_changed)
        toolbar.addWidget(self.aperture_combo)

        toolbar.addSeparator()

        for name, callback in [
            ("艾里斑", self._preset_airy),
            ("双缝干涉", self._preset_double_slit),
            ("光栅衍射", self._preset_grating),
        ]:
            btn = QPushButton(name)
            btn.clicked.connect(callback)
            toolbar.addWidget(btn)

        toolbar.addSeparator()

        btn_analysis = QPushButton("MTF分析")
        btn_analysis.clicked.connect(self._show_analysis_dialog)
        toolbar.addWidget(btn_analysis)

        btn_fitting = QPushButton("曲线拟合")
        btn_fitting.clicked.connect(self._show_fitting_dialog)
        toolbar.addWidget(btn_fitting)

        toolbar.addSeparator()

        btn_scan = QPushButton("参数扫描")
        btn_scan.clicked.connect(self._parameter_scan)
        toolbar.addWidget(btn_scan)

        btn_chromatic = QPushButton("彩色衍射")
        btn_chromatic.clicked.connect(self._show_chromatic_dialog)
        toolbar.addWidget(btn_chromatic)

        btn_wavefront = QPushButton("波前分析")
        btn_wavefront.clicked.connect(self._show_wavefront_dialog)
        toolbar.addWidget(btn_wavefront)

        btn_receiver = QPushButton("接收面分析")
        btn_receiver.clicked.connect(self._show_receiver_surface_dialog)
        toolbar.addWidget(btn_receiver)

        toolbar.addSeparator()

        self.theme_btn = QPushButton("亮色模式")
        self.theme_btn.clicked.connect(self._toggle_theme)
        toolbar.addWidget(self.theme_btn)

        btn_settings = QPushButton("设置")
        btn_settings.clicked.connect(self._show_settings_dialog)
        toolbar.addWidget(btn_settings)

        toolbar.addSeparator()

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setFixedHeight(16)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        toolbar.addWidget(self.progress_bar)

    def _setup_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.status_coord = QLabel("坐标: --")
        self.status_intensity = QLabel("强度: --")
        self.status_fps = QLabel("计算: --")
        self.status_backend = QLabel("后端: CPU")
        self.status_strehl = QLabel("Strehl: --")
        for w in [self.status_coord, self.status_intensity,
                  self.status_fps, self.status_strehl, self.status_backend]:
            self.statusbar.addPermanentWidget(w)

    def _connect_signals(self):
        self.control_panel.params_changed.connect(self._on_params_changed)
        self.canvas.mouse_moved.connect(self._update_statusbar)
        self.data_panel.refresh_btn.clicked.connect(self._refresh_data_panel)

    def _apply_theme(self):
        if self._is_dark_theme:
            self.setStyleSheet(DARK_THEME)
        else:
            self.setStyleSheet(LIGHT_THEME)
        self.canvas.set_theme(self._is_dark_theme)
        self.profile_plot.set_theme(self._is_dark_theme)

    def _apply_rendering_settings(self):
        use_opengl = self.prefs.get_advanced_setting('use_opengl', True)
        use_antialias = self.prefs.get_advanced_setting('use_antialias', True)
        interpolation = self.prefs.get_advanced_setting('interpolation', 'bilinear')
        fft_precision = self.prefs.get_advanced_setting('fft_precision', 'float64')
        use_hidpi = self.prefs.get_advanced_setting('use_hidpi', True)

        self.canvas.configure_rendering(
            use_opengl=use_opengl,
            antialias=use_antialias,
            interpolation=interpolation,
        )
        self.engine.set_fft_precision(fft_precision)

        if use_hidpi:
            try:
                import pyqtgraph as pg
                pg.setConfigOption('enableExperimental', True)
            except Exception:
                pass

    def _toggle_theme(self):
        self._is_dark_theme = not self._is_dark_theme
        self.prefs.set_theme('dark' if self._is_dark_theme else 'light')
        self._apply_theme()
        if self._is_dark_theme:
            self._theme_action.setText("切换亮色模式")
            self.theme_btn.setText("亮色模式")
        else:
            self._theme_action.setText("切换暗色模式")
            self.theme_btn.setText("暗色模式")
        if self._help_dialog and self._help_dialog.isVisible():
            self._help_dialog.set_theme(self._is_dark_theme)
        if self._analysis_dialog and self._analysis_dialog.isVisible():
            self._analysis_dialog.set_theme(self._is_dark_theme)
        if self._chromatic_dialog and self._chromatic_dialog.isVisible():
            self._chromatic_dialog.set_theme(self._is_dark_theme)
        if self._wavefront_dialog and self._wavefront_dialog.isVisible():
            self._wavefront_dialog.set_theme(self._is_dark_theme)
        if self._propagation_dialog and self._propagation_dialog.isVisible():
            self._propagation_dialog.set_theme(self._is_dark_theme)
        if self._receiver_dialog and self._receiver_dialog.isVisible():
            self._receiver_dialog.set_theme(self._is_dark_theme)

    def _initial_compute(self):
        self._on_params_changed(self._get_default_params())

    def _get_default_params(self) -> dict:
        return {
            'wavelength': 532e-9,
            'aperture_size': 50e-6,
            'distance': 0.1,
            'physical_size': 200e-6,
            'grid_size': 512,
            'model': 'fraunhofer',
            'pad_factor': 2.0,
            'gamma': 1.0,
            'log_scale': True,
            'colormap': 'hot',
            'aperture_type': 'circle',
            'center_x': 0, 'center_y': 0, 'rotation': 0,
            'aspect_ratio': 1.0, 'inner_ratio': 0.5,
            'num_points': 5, 'num_slits': 5,
            'slit_width': 5.0, 'slit_separation': 25.0,
            'aberration_enabled': False,
            'defocus': 0, 'astigmatism': 0, 'coma': 0,
            'spherical': 0, 'trefoil': 0,
            'multi_wl_enabled': False,
            'wavelengths': [450, 532, 633],
        }

    def _create_aperture(self, params: dict):
        aperture_type = params.get('aperture_type', 'circle')
        size_um = params.get('aperture_size', 50e-6) / 1e-6

        type_map = {
            'circle': ApertureType.CIRCLE,
            'rectangle': ApertureType.RECTANGLE,
            'triangle': ApertureType.TRIANGLE,
            'hexagon': ApertureType.HEXAGON,
            'annulus': ApertureType.ANNULUS,
            'star': ApertureType.STAR,
            'double_slit': ApertureType.DOUBLE_SLIT,
            'grating': ApertureType.GRATING,
        }

        at = type_map.get(aperture_type, ApertureType.CIRCLE)
        kwargs = {'params': {
            'size': size_um,
            'center_x': params.get('center_x', 0),
            'center_y': params.get('center_y', 0),
            'rotation': params.get('rotation', 0),
        }}

        if at == ApertureType.RECTANGLE:
            kwargs['aspect_ratio'] = params.get('aspect_ratio', 1.0)
        elif at == ApertureType.ANNULUS:
            kwargs['inner_ratio'] = params.get('inner_ratio', 0.5)
        elif at == ApertureType.STAR:
            kwargs['num_points'] = params.get('num_points', 5)
            kwargs['inner_ratio'] = params.get('inner_ratio', 0.4)
        elif at == ApertureType.DOUBLE_SLIT:
            kwargs['slit_width'] = params.get('slit_width', 5.0)
            kwargs['slit_separation'] = params.get('slit_separation', 25.0)
        elif at == ApertureType.GRATING:
            kwargs['num_slits'] = params.get('num_slits', 5)
            kwargs['slit_width'] = params.get('slit_width', 5.0)
            kwargs['slit_separation'] = params.get('slit_separation', 25.0)

        return ApertureFactory.create(at, **kwargs)

    def _params_cache_key(self, params: dict) -> str:
        try:
            serialized = json.dumps(params, sort_keys=True, default=str)
            return hashlib.md5(serialized.encode()).hexdigest()
        except Exception:
            return ''

    def _on_params_changed(self, params: dict):
        self._pending_params = params
        if self.control_panel.auto_update_check.isChecked():
            self._debounce_timer.start()

    def _cancel_computation(self):
        self._computing = False
        self.progress_bar.setVisible(False)

    def _do_compute(self):
        params = self._pending_params
        if params is None:
            return

        cache_key = self._params_cache_key(params)
        if cache_key in self._result_cache:
            result, elapsed = self._result_cache[cache_key]
            self._current_result = result
            self._last_compute_time = elapsed
            self._display_result(result, params, elapsed)
            return

        if self._computing:
            return

        try:
            self._computing = True
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.statusbar.showMessage("计算中...")
            QApplication.processEvents()

            aperture = self._create_aperture(params)
            self._current_aperture = aperture

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
                model=model_map.get(params.get('model', 'fraunhofer'),
                                    PropagationModel.FRAUNHOFER),
                pad_factor=params.get('pad_factor', 2.0),
            )

            t0 = time.time()
            result = self.engine.compute_diffraction(aperture, sim_params)
            elapsed = (time.time() - t0) * 1000

            if not self._computing:
                return

            self._on_compute_finished(result, elapsed)

        except Exception as e:
            self._on_compute_error(str(e))

    def _on_compute_finished(self, result, elapsed):
        self._computing = False
        self.progress_bar.setVisible(False)
        self._current_result = result
        self._last_compute_time = elapsed

        params = self._pending_params or self._get_default_params()
        cache_key = self._params_cache_key(params)
        self._result_cache[cache_key] = (result, elapsed)

        if len(self._result_cache) > 20:
            oldest_key = next(iter(self._result_cache))
            del self._result_cache[oldest_key]

        self._display_result(result, params, elapsed)

    def _on_compute_error(self, error_msg):
        self._computing = False
        self.progress_bar.setVisible(False)
        logger.error(f"Computation failed: {error_msg}")
        self.statusbar.showMessage(f"计算失败: {error_msg}", 5000)

    def _display_result(self, result, params, elapsed):
        try:
            self.canvas._log_scale = params.get('log_scale', True)
            self.canvas._gamma = params.get('gamma', 1.0)
            self.canvas.set_colormap(params.get('colormap', 'hot'))
            self.canvas.update_diffraction(
                result.intensity, result.x_freq, result.y_freq
            )

            self.status_fps.setText(f"计算: {elapsed:.0f} ms")
            self.status_backend.setText(
                f"后端: {'GPU' if self.engine.use_gpu else 'CPU'}")

            self._update_profiles()

            sr = strehl_ratio(result.intensity)
            self.status_strehl.setText(f"Strehl: {sr:.4f}" if sr >= 0 else "Strehl: N/A")

            self.statusbar.showMessage("计算完成", 2000)

            QTimer.singleShot(50, lambda: self._update_data_panel_async(params))
        except Exception as e:
            logger.error(f"Display update failed: {e}")

    def _update_profiles(self):
        if self._current_result is None:
            return
        coords_h, profile_h = self._current_result.get_horizontal_profile()
        coords_v, profile_v = self._current_result.get_vertical_profile()
        self.profile_plot.update_horizontal_profile(coords_h, profile_h)
        self.profile_plot.update_vertical_profile(coords_v, profile_v)

    def _update_data_panel_async(self, params: dict):
        if self._current_result is None:
            return

        intensity = self._current_result.intensity
        psf_info = compute_psf(intensity)

        aperture_radius = params.get('aperture_size', 50e-6) / 2
        fn = fresnel_number(
            params.get('wavelength', 532e-9),
            aperture_radius,
            params.get('distance', 0.1)
        )

        sr = strehl_ratio(intensity)
        if sr < 0:
            sr = 0.0

        data = {
            'peak': psf_info.get('peak', 0),
            'total': psf_info.get('total', 0),
            'center': psf_info.get('center', (0, 0)),
            'fwhm_h': psf_info.get('fwhm_h', 0),
            'fwhm_v': psf_info.get('fwhm_v', 0),
            'ee_50_radius': psf_info.get('ee_50_radius', 0),
            'ee_86_radius': psf_info.get('ee_86_radius', 0),
            'strehl': sr,
            'fresnel_number': fn,
            'model': params.get('model', 'fraunhofer'),
            'wavelength': params.get('wavelength', 532e-9),
            'aperture_size': params.get('aperture_size', 50e-6),
            'distance': params.get('distance', 0.1),
            'grid_size': params.get('grid_size', 512),
            'compute_time': self._last_compute_time,
            'backend': 'GPU' if self.engine.use_gpu else 'CPU',
        }

        self.data_panel.update_measurements(data)

    def _refresh_data_panel(self):
        if self._current_result is not None and self._pending_params:
            self._update_data_panel_async(self._pending_params)

    def _update_statusbar(self, x: float, y: float, intensity: float):
        self.status_coord.setText(f"({x:.3e}, {y:.3e})")
        self.status_intensity.setText(f"I={intensity:.3e}")

    def _on_toolbar_aperture_changed(self, text: str):
        idx = self.control_panel.aperture_type_combo.findText(text)
        if idx >= 0:
            self.control_panel.aperture_type_combo.setCurrentIndex(idx)

    def _reset_view(self):
        self.canvas.reset_view()

    def _fit_to_window(self):
        self.canvas.fit_to_window()

    def _set_colormap(self, name: str):
        self.canvas.set_colormap(name)

    def _show_horizontal_profile(self):
        if self._current_result:
            coords, profile = self._current_result.get_horizontal_profile()
            self.profile_plot.update_horizontal_profile(coords, profile)
            self.profile_plot.show_fwhm(coords, profile)

    def _show_vertical_profile(self):
        if self._current_result:
            coords, profile = self._current_result.get_vertical_profile()
            self.profile_plot.update_vertical_profile(coords, profile)
            self.profile_plot.show_fwhm(coords, profile)

    def _measure_fwhm(self):
        if self._current_result:
            coords, profile = self._current_result.get_horizontal_profile()
            self.profile_plot.show_fwhm(coords, profile)

    def _show_analysis_dialog(self):
        if self._current_result is None:
            QMessageBox.warning(self, "提示", "请先进行衍射计算")
            return

        if self._analysis_dialog is None or not self._analysis_dialog.isVisible():
            self._analysis_dialog = AnalysisDialog(self)
            self._analysis_dialog.set_theme(self._is_dark_theme)

        intensity = self._current_result.intensity

        mtf_data = compute_mtf(intensity)
        freq, mtf_radial = radial_mtf(mtf_data)
        self._analysis_dialog.update_mtf(freq, mtf_radial)

        psf_info = compute_psf(intensity)
        if 'ee_radii' in psf_info and 'ee_values' in psf_info:
            self._analysis_dialog.update_ee(
                psf_info['ee_radii'].astype(float),
                psf_info['ee_values']
            )

        radii, rad_profile = radial_profile(intensity)
        self._analysis_dialog.update_radial(radii, rad_profile)

        self._analysis_dialog.show()

    def _load_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开配置文件", "", "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if path:
            self.config_manager.load(path)

    def _save_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "保存配置文件", "", "YAML Files (*.yaml);;All Files (*)"
        )
        if path:
            self.config_manager.save(path)

    def _export_image(self):
        if self._current_result is None:
            QMessageBox.warning(self, "提示", "请先进行衍射计算")
            return
        dialog = ExportDialog(self)
        if dialog.exec() == ExportDialog.DialogCode.Accepted:
            export_params = dialog.get_export_params()
            filepath = export_params['filepath']
            if not filepath:
                return
            intensity = self._current_result.intensity
            IOHandler.export_image(
                filepath, intensity,
                colormap_name=export_params.get('colormap', 'hot'),
                dpi=export_params.get('dpi', 300),
                metadata=self._current_result.metadata if export_params.get('include_metadata') else None
            )
            self.statusbar.showMessage(f"图像已导出至 {filepath}", 3000)

    def _export_data(self):
        if self._current_result is None:
            QMessageBox.warning(self, "提示", "请先进行衍射计算")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "", "CSV Files (*.csv);;HDF5 Files (*.h5);;All Files (*)"
        )
        if path:
            coords, profile = self._current_result.get_horizontal_profile()
            IOHandler.export_data(path, coords, profile, 'position_m', 'intensity')
            self.statusbar.showMessage(f"数据已导出至 {path}", 3000)

    def _parameter_scan(self):
        dialog = ParameterScanDialog(self, main_window=self)
        dialog.set_theme(self._is_dark_theme)
        dialog.exec()

    def _show_chromatic_dialog(self):
        if self._chromatic_dialog is None or not self._chromatic_dialog.isVisible():
            self._chromatic_dialog = ChromaticDiffractionDialog(self, main_window=self)
            self._chromatic_dialog.set_theme(self._is_dark_theme)
        self._chromatic_dialog.show()
        self._chromatic_dialog.raise_()
        self._chromatic_dialog.activateWindow()

    def _show_fitting_dialog(self):
        coords, profile = None, None
        if self._current_result is not None:
            coords, profile = self._current_result.get_horizontal_profile()
        dialog = FittingDialog(self, coords=coords, profile=profile)
        dialog.set_theme(self._is_dark_theme)
        dialog.exec()

    def _show_wavefront_dialog(self):
        if self._wavefront_dialog is None or not self._wavefront_dialog.isVisible():
            self._wavefront_dialog = WavefrontDialog(self)
            self._wavefront_dialog.set_theme(self._is_dark_theme)
        self._wavefront_dialog.show()
        self._wavefront_dialog.raise_()
        self._wavefront_dialog.activateWindow()

    def _show_propagation_dialog(self):
        if self._propagation_dialog is None or not self._propagation_dialog.isVisible():
            self._propagation_dialog = PropagationDialog(self, main_window=self)
            self._propagation_dialog.set_theme(self._is_dark_theme)
        self._propagation_dialog.show()
        self._propagation_dialog.raise_()
        self._propagation_dialog.activateWindow()

    def _show_optical_scene_dialog(self):
        dialog = OpticalSceneDialog(self, main_window=self)
        dialog.set_theme(self._is_dark_theme)
        dialog.exec()

    def _show_receiver_surface_dialog(self):
        if self._receiver_dialog is None or not self._receiver_dialog.isVisible():
            self._receiver_dialog = ReceiverSurfaceDialog(self, main_window=self)
            self._receiver_dialog.set_theme(self._is_dark_theme)
        self._receiver_dialog.show()
        self._receiver_dialog.raise_()
        self._receiver_dialog.activateWindow()

    def _show_help(self):
        if self._help_dialog is None or not self._help_dialog.isVisible():
            self._help_dialog = HelpDialog(self, is_dark=self._is_dark_theme)
        self._help_dialog.show()
        self._help_dialog.raise_()
        self._help_dialog.activateWindow()

    def _show_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == SettingsDialog.DialogCode.Accepted:
            self._apply_shortcuts()
            debounce_ms = self.prefs.get_debounce_ms()
            self._debounce_timer.setInterval(debounce_ms)
            theme = self.prefs.get_theme()
            is_dark = theme == 'dark'
            if is_dark != self._is_dark_theme:
                self._toggle_theme()
            self._apply_rendering_settings()
            self.statusbar.showMessage("设置已更新", 2000)

    def _show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def _preset_airy(self):
        self.control_panel.aperture_type_combo.setCurrentText("圆形")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(50)
        self.control_panel.model_combo.setCurrentText("夫琅和费 (远场)")
        self.control_panel._emit_params()

    def _preset_double_slit(self):
        self.control_panel.aperture_type_combo.setCurrentText("双缝")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(100)
        self.control_panel.slit_width_spin.setValue(5)
        self.control_panel.slit_separation_spin.setValue(25)
        self.control_panel.model_combo.setCurrentText("夫琅和费 (远场)")
        self.control_panel._emit_params()

    def _preset_grating(self):
        self.control_panel.aperture_type_combo.setCurrentText("光栅")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(200)
        self.control_panel.num_slits_spin.setValue(7)
        self.control_panel.slit_width_spin.setValue(5)
        self.control_panel.slit_separation_spin.setValue(20)
        self.control_panel.model_combo.setCurrentText("夫琅和费 (远场)")
        self.control_panel._emit_params()

    def _preset_annulus(self):
        self.control_panel.aperture_type_combo.setCurrentText("圆环")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(60)
        self.control_panel.inner_ratio_spin.setValue(0.5)
        self.control_panel.model_combo.setCurrentText("夫琅和费 (远场)")
        self.control_panel._emit_params()

    def _preset_hexagon(self):
        self.control_panel.aperture_type_combo.setCurrentText("六边形")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(50)
        self.control_panel.model_combo.setCurrentText("夫琅和费 (远场)")
        self.control_panel._emit_params()

    def _preset_star(self):
        self.control_panel.aperture_type_combo.setCurrentText("星形")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(50)
        self.control_panel.num_points_spin.setValue(6)
        self.control_panel.inner_ratio_spin.setValue(0.4)
        self.control_panel.model_combo.setCurrentText("夫琅和费 (远场)")
        self.control_panel._emit_params()

    def _preset_fresnel(self):
        self.control_panel.aperture_type_combo.setCurrentText("圆形")
        self.control_panel.wavelength_spin.setValue(532)
        self.control_panel.size_spin.setValue(100)
        self.control_panel.distance_spin.setValue(0.005)
        self.control_panel.model_combo.setCurrentText("菲涅尔 (角谱法)")
        self.control_panel._emit_params()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            self._cancel_computation()
            self.statusbar.showMessage("计算已取消", 2000)
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self._computing = False
        self.prefs.sync()
        super().closeEvent(event)
