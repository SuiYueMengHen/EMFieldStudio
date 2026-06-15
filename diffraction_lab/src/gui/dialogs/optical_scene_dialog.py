from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QSplitter, QWidget
)
from PyQt6.QtCore import Qt
from .dialog_theme import apply_dialog_theme


OPTICAL_SCENES = [
    {
        'name': '望远镜衍射',
        'desc': '大口径圆形孔径 + 远场衍射，模拟天文望远镜的艾里斑',
        'params': {
            'aperture_type': 'circle', 'wavelength': 550, 'size': 5000,
            'distance': 100, 'model': 'fraunhofer', 'grid_size': '1024',
            'physical_size': 20000,
        },
    },
    {
        'name': '反射望远镜（六边形+遮挡）',
        'desc': '六边形孔径模拟主镜，星形遮挡模拟副镜支架',
        'params': {
            'aperture_type': 'hexagon', 'wavelength': 550, 'size': 8000,
            'distance': 100, 'model': 'fraunhofer', 'grid_size': '1024',
            'physical_size': 30000,
        },
    },
    {
        'name': '显微镜成像',
        'desc': '小孔径 + 菲涅尔近场传播 + 球差',
        'params': {
            'aperture_type': 'circle', 'wavelength': 532, 'size': 5,
            'distance': 0.001, 'model': 'fresnel_asm', 'grid_size': '512',
            'physical_size': 20, 'spherical': 0.5,
        },
    },
    {
        'name': '光纤模式',
        'desc': '圆形孔径 + 菲涅尔传播，模拟光纤中的模式分布',
        'params': {
            'aperture_type': 'circle', 'wavelength': 1550, 'size': 62.5,
            'distance': 0.01, 'model': 'fresnel_asm', 'grid_size': '512',
            'physical_size': 200,
        },
    },
    {
        'name': '光谱仪光栅',
        'desc': '光栅 + 多波长，模拟光谱仪的分光效果',
        'params': {
            'aperture_type': 'grating', 'wavelength': 532, 'size': 200,
            'distance': 0.5, 'model': 'fraunhofer', 'grid_size': '1024',
            'physical_size': 500, 'num_slits': 10, 'slit_width': 3,
            'slit_separation': 15, 'multi_wl': True,
        },
    },
    {
        'name': '杨氏双缝干涉',
        'desc': '经典双缝干涉实验，观察干涉条纹',
        'params': {
            'aperture_type': 'double_slit', 'wavelength': 532, 'size': 100,
            'distance': 1.0, 'model': 'fraunhofer', 'grid_size': '512',
            'physical_size': 500, 'slit_width': 5, 'slit_separation': 25,
        },
    },
    {
        'name': '单缝衍射教学',
        'desc': '单缝夫琅和费衍射，观察sinc²包络',
        'params': {
            'aperture_type': 'rectangle', 'wavelength': 633, 'size': 50,
            'distance': 1.0, 'model': 'fraunhofer', 'grid_size': '512',
            'physical_size': 500, 'aspect_ratio': 0.05,
        },
    },
    {
        'name': '圆环衍射',
        'desc': '环形孔径衍射，观察中央凹陷和衍射环',
        'params': {
            'aperture_type': 'annulus', 'wavelength': 532, 'size': 100,
            'distance': 0.5, 'model': 'fraunhofer', 'grid_size': '512',
            'physical_size': 500, 'inner_ratio': 0.5,
        },
    },
]


class OpticalSceneDialog(QDialog):

    def __init__(self, parent=None, main_window=None):
        super().__init__(parent)
        self.setWindowTitle("光学场景预设")
        self.setMinimumSize(700, 500)
        self.resize(800, 550)
        self._main_window = main_window
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.scene_list = QListWidget()
        for scene in OPTICAL_SCENES:
            item = QListWidgetItem(scene['name'])
            item.setData(Qt.ItemDataRole.UserRole, scene)
            self.scene_list.addItem(item)
        self.scene_list.currentRowChanged.connect(self._on_scene_selected)
        splitter.addWidget(self.scene_list)

        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)

        self.name_label = QLabel("")
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        info_layout.addWidget(self.name_label)

        self.desc_label = QLabel("")
        self.desc_label.setWordWrap(True)
        info_layout.addWidget(self.desc_label)

        self.params_label = QLabel("")
        self.params_label.setWordWrap(True)
        info_layout.addWidget(self.params_label)

        info_layout.addStretch()

        self.load_btn = QPushButton("加载此场景")
        self.load_btn.setObjectName("updateBtn")
        self.load_btn.setMinimumHeight(40)
        self.load_btn.setEnabled(False)
        self.load_btn.clicked.connect(self._load_scene)
        info_layout.addWidget(self.load_btn)

        splitter.addWidget(info_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

    def _on_scene_selected(self, row: int):
        if row < 0 or row >= len(OPTICAL_SCENES):
            return

        scene = OPTICAL_SCENES[row]
        self.name_label.setText(scene['name'])
        self.desc_label.setText(scene['desc'])

        params_text = "参数配置:\n"
        for key, val in scene['params'].items():
            params_text += f"  {key}: {val}\n"
        self.params_label.setText(params_text)

        self.load_btn.setEnabled(True)

    def _load_scene(self):
        row = self.scene_list.currentRow()
        if row < 0 or row >= len(OPTICAL_SCENES):
            return

        scene = OPTICAL_SCENES[row]
        p = scene['params']

        if self._main_window is None:
            return

        cp = self._main_window.control_panel

        type_map = {
            'circle': '圆形', 'rectangle': '矩形', 'triangle': '三角形',
            'hexagon': '六边形', 'annulus': '圆环', 'star': '星形',
            'double_slit': '双缝', 'grating': '光栅',
        }
        model_map = {
            'fraunhofer': '夫琅和费 (远场)',
            'fresnel_asm': '菲涅尔 (角谱法)',
            'fresnel_ir': '菲涅尔 (脉冲响应)',
            'rayleigh_sommerfeld': '瑞利-索末菲',
        }

        if 'aperture_type' in p:
            cp.aperture_type_combo.setCurrentText(
                type_map.get(p['aperture_type'], '圆形'))
        if 'wavelength' in p:
            cp.wavelength_spin.setValue(p['wavelength'])
        if 'size' in p:
            cp.size_spin.setValue(p['size'])
        if 'distance' in p:
            cp.distance_spin.setValue(p['distance'])
        if 'model' in p:
            cp.model_combo.setCurrentText(
                model_map.get(p['model'], '夫琅和费 (远场)'))
        if 'grid_size' in p:
            cp.grid_combo.setCurrentText(str(p['grid_size']))
        if 'physical_size' in p:
            cp.physical_size_spin.setValue(p['physical_size'])
        if 'inner_ratio' in p:
            cp.inner_ratio_spin.setValue(p['inner_ratio'])
        if 'num_slits' in p:
            cp.num_slits_spin.setValue(p['num_slits'])
        if 'slit_width' in p:
            cp.slit_width_spin.setValue(p['slit_width'])
        if 'slit_separation' in p:
            cp.slit_separation_spin.setValue(p['slit_separation'])
        if 'aspect_ratio' in p:
            cp.aspect_ratio_spin.setValue(p['aspect_ratio'])
        if 'spherical' in p:
            cp.aberration_check.setChecked(True)
            cp.spherical_spin.setValue(p['spherical'])

        cp._emit_params()
        self.accept()

    def set_theme(self, is_dark: bool):
        apply_dialog_theme(self, is_dark)
