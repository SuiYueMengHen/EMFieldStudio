from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于")
        self.setFixedSize(420, 320)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("衍射仿真软件")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00ccff; margin: 10px;")
        layout.addWidget(title)

        subtitle = QLabel("DiffractionLab")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 14px; color: #888; margin-bottom: 15px;")
        layout.addWidget(subtitle)

        info_text = """
        <p style='color: #ccc;'>
        版本: 1.0.0<br><br>
        一款高度可定制的衍射仿真软件，支持多种孔径形状、<br>
        实时参数调整、高性能渲染和专业级定量分析。<br><br>
        支持的传播模型：<br>
        &nbsp;&nbsp;• 夫琅和费衍射（远场）<br>
        &nbsp;&nbsp;• 菲涅尔衍射（角谱法）<br>
        &nbsp;&nbsp;• 菲涅尔衍射（脉冲响应）<br>
        &nbsp;&nbsp;• 瑞利-索末菲衍射<br><br>
        技术栈：Python / PyQt6 / NumPy / SciPy
        </p>
        """
        info = QLabel(info_text)
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addStretch()

        close_btn = QPushButton("确定")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
