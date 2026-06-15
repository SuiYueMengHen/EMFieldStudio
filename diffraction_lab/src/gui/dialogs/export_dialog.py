import os
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QGroupBox, QComboBox, QSpinBox, QCheckBox,
    QPushButton, QLabel, QFileDialog, QLineEdit,
    QDialogButtonBox
)


class ExportDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        file_group = QGroupBox("文件")
        file_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择导出路径...")
        file_layout.addWidget(self.path_edit)

        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.clicked.connect(self._browse)
        file_layout.addWidget(self.browse_btn)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        format_group = QGroupBox("格式设置")
        format_layout = QFormLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "TIFF", "JPEG", "HDF5", "CSV"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        format_layout.addRow("格式:", self.format_combo)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSuffix(" dpi")
        format_layout.addRow("DPI:", self.dpi_spin)

        self.metadata_check = QCheckBox("包含元数据")
        self.metadata_check.setChecked(True)
        format_layout.addRow("", self.metadata_check)

        self.raw_data_check = QCheckBox("导出原始数据（非显示数据）")
        self.raw_data_check.setChecked(True)
        format_layout.addRow("", self.raw_data_check)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        fmt = self.format_combo.currentText().lower()
        ext_map = {
            'png': 'PNG Images (*.png)',
            'tiff': 'TIFF Images (*.tif *.tiff)',
            'jpeg': 'JPEG Images (*.jpg *.jpeg)',
            'hdf5': 'HDF5 Files (*.h5 *.hdf5)',
            'csv': 'CSV Files (*.csv)',
        }
        filter_str = ext_map.get(fmt, 'All Files (*)')

        path, _ = QFileDialog.getSaveFileName(self, "导出文件", "", filter_str)
        if path:
            self.path_edit.setText(path)

    def _on_format_changed(self, fmt: str):
        self.dpi_spin.setEnabled(fmt not in ('HDF5', 'CSV'))

    def get_export_params(self) -> dict:
        return {
            'filepath': self.path_edit.text(),
            'format': self.format_combo.currentText().lower(),
            'dpi': self.dpi_spin.value(),
            'include_metadata': self.metadata_check.isChecked(),
            'raw_data': self.raw_data_check.isChecked(),
        }
