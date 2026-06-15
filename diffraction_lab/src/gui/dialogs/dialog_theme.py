from PyQt6.QtGui import QColor
import pyqtgraph as pg


DARK_DIALOG_CSS = """
QDialog, QWidget { background-color: #1a1b2e; color: #e0e0e0; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 12px; }
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
QCheckBox { spacing: 8px; color: #e0e0e0; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #3a3b5e; background-color: #252640; }
QCheckBox::indicator:checked { background-color: #7c8cf8; border-color: #7c8cf8; }
QLabel { color: #e0e0e0; background: transparent; }
QProgressBar { border: none; border-radius: 4px; text-align: center; background-color: #252640; color: #e0e0e0; height: 8px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #7c8cf8,stop:1 #6c7cf0); border-radius: 4px; }
QSlider::groove:horizontal { border: none; height: 6px; background: #252640; border-radius: 3px; }
QSlider::handle:horizontal { background: #7c8cf8; border: none; width: 18px; margin: -6px 0; border-radius: 9px; }
QTableWidget { background-color: #1a1b2e; color: #e0e0e0; gridline-color: #252640; border: 1px solid #3a3b5e; border-radius: 4px; }
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section { background-color: #252640; color: #7c8cf8; padding: 6px; border: none; border-bottom: 1px solid #3a3b5e; font-weight: 600; }
QListWidget { background-color: #1a1b2e; color: #e0e0e0; border: 1px solid #3a3b5e; border-radius: 4px; }
QListWidget::item { padding: 6px; border-radius: 4px; }
QListWidget::item:selected { background-color: #3a3b5e; color: #7c8cf8; }
QScrollBar:vertical { background: #1a1b2e; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #3a3b5e; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #7c8cf8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

LIGHT_DIALOG_CSS = """
QDialog, QWidget { background-color: #f5f6fa; color: #2c3e50; font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 12px; }
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
QCheckBox { spacing: 8px; color: #2c3e50; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #dcdde1; background-color: #ffffff; }
QCheckBox::indicator:checked { background-color: #5b6abf; border-color: #5b6abf; }
QLabel { color: #2c3e50; background: transparent; }
QProgressBar { border: none; border-radius: 4px; text-align: center; background-color: #e8e9f0; color: #2c3e50; height: 8px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #5b6abf,stop:1 #6c7bd0); border-radius: 4px; }
QSlider::groove:horizontal { border: none; height: 6px; background: #dcdde1; border-radius: 3px; }
QSlider::handle:horizontal { background: #5b6abf; border: none; width: 18px; margin: -6px 0; border-radius: 9px; }
QTableWidget { background-color: #ffffff; color: #2c3e50; gridline-color: #e8e9f0; border: 1px solid #dcdde1; border-radius: 4px; }
QTableWidget::item { padding: 4px 8px; }
QHeaderView::section { background-color: #e8e9f0; color: #5b6abf; padding: 6px; border: none; border-bottom: 1px solid #dcdde1; font-weight: 600; }
QListWidget { background-color: #ffffff; color: #2c3e50; border: 1px solid #dcdde1; border-radius: 4px; }
QListWidget::item { padding: 6px; border-radius: 4px; }
QListWidget::item:selected { background-color: #e8e9f0; color: #5b6abf; }
QScrollBar:vertical { background: #f5f6fa; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: #c0c0d0; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #5b6abf; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""


def apply_dialog_theme(dialog, is_dark: bool):
    if is_dark:
        dialog.setStyleSheet(DARK_DIALOG_CSS)
    else:
        dialog.setStyleSheet(LIGHT_DIALOG_CSS)


def apply_plot_theme(plot_widget, is_dark: bool):
    if is_dark:
        plot_widget.setBackground(QColor(30, 30, 40))
        for axis_name in ['left', 'bottom', 'right', 'top']:
            axis = plot_widget.getAxis(axis_name)
            axis.setPen(pg.mkPen('#8888aa'))
            axis.setTextPen(pg.mkPen('#c0c0d0'))
    else:
        plot_widget.setBackground(QColor(245, 246, 250))
        for axis_name in ['left', 'bottom', 'right', 'top']:
            axis = plot_widget.getAxis(axis_name)
            axis.setPen(pg.mkPen('#b0b0c0'))
            axis.setTextPen(pg.mkPen('#2c3e50'))
