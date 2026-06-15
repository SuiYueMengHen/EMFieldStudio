import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QGroupBox, QLabel, QPushButton,
    QHeaderView
)
from PyQt6.QtCore import Qt


class DataPanel(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._psf_data = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self.measure_table = QTableWidget()
        self.measure_table.setColumnCount(2)
        self.measure_table.setHorizontalHeaderLabels(["参数", "值"])
        self.measure_table.horizontalHeader().setStretchLastSection(True)
        self.measure_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.measure_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.measure_table.setAlternatingRowColors(True)
        layout.addWidget(self.measure_table)

        self.refresh_btn = QPushButton("刷新测量")
        layout.addWidget(self.refresh_btn)

    def update_measurements(self, data: dict):
        self._psf_data = data
        self.measure_table.setRowCount(0)

        rows = [
            ("峰值强度", f"{data.get('peak', 0):.4e}"),
            ("总能量", f"{data.get('total', 0):.4e}"),
            ("峰值位置", f"({data.get('center', (0,0))[0]:.0f}, {data.get('center', (0,0))[1]:.0f})"),
            ("FWHM (水平)", f"{data.get('fwhm_h', 0):.2f} px"),
            ("FWHM (垂直)", f"{data.get('fwhm_v', 0):.2f} px"),
            ("EE50 半径", f"{data.get('ee_50_radius', 0):.2f} px"),
            ("EE86 半径", f"{data.get('ee_86_radius', 0):.2f} px"),
            ("斯特列尔比", f"{data.get('strehl', 0):.4f}"),
            ("菲涅尔数", f"{data.get('fresnel_number', 0):.4f}"),
            ("传播模型", f"{data.get('model', 'N/A')}"),
            ("波长", f"{data.get('wavelength', 0) * 1e9:.1f} nm"),
            ("孔径尺寸", f"{data.get('aperture_size', 0) * 1e6:.1f} μm"),
            ("传播距离", f"{data.get('distance', 0):.3f} m"),
            ("网格大小", f"{data.get('grid_size', 0)}"),
            ("计算时间", f"{data.get('compute_time', 0):.1f} ms"),
            ("后端", f"{data.get('backend', 'CPU')}"),
        ]

        self.measure_table.setRowCount(len(rows))
        for i, (name, value) in enumerate(rows):
            name_item = QTableWidgetItem(name)
            value_item = QTableWidgetItem(value)
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.measure_table.setItem(i, 0, name_item)
            self.measure_table.setItem(i, 1, value_item)
