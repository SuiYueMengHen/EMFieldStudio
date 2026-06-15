import numpy as np
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QColor, QMouseEvent
import pyqtgraph as pg


class ShapeEditorWidget(pg.GraphicsLayoutWidget):

    shape_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._vertices = []
        self._mode = 'polygon'
        self._setup_view()

    def _setup_view(self):
        self.view = self.addViewBox(row=0, col=0)
        self.view.setAspectLocked(True)
        self.view.setBackgroundColor(QColor(20, 20, 30))
        self.view.setRange(xRange=(-1, 1), yRange=(-1, 1))

        self.preview_image = pg.ImageItem()
        self.view.addItem(self.preview_image)

        self.scatter = pg.ScatterPlotItem(
            pen=pg.mkPen('w', width=2),
            brush=pg.mkBrush('#ff6600'),
            size=10
        )
        self.view.addItem(self.scatter)

        self.line_plot = self.plot(pen=pg.mkPen('#00ccff', width=2))

    def set_mode(self, mode: str):
        self._mode = mode
        self._vertices = []
        self._update_display()

    def add_vertex(self, x: float, y: float):
        self._vertices.append((x, y))
        self._update_display()
        self.shape_changed.emit()

    def remove_last_vertex(self):
        if self._vertices:
            self._vertices.pop()
            self._update_display()
            self.shape_changed.emit()

    def clear_vertices(self):
        self._vertices = []
        self._update_display()
        self.shape_changed.emit()

    def get_vertices(self):
        return self._vertices.copy()

    def get_mask(self, grid_size: int = 256) -> np.ndarray:
        if len(self._vertices) < 3:
            return np.zeros((grid_size, grid_size), dtype=np.float32)

        x = np.linspace(-1, 1, grid_size)
        y = np.linspace(-1, 1, grid_size)
        X, Y = np.meshgrid(x, y)

        vx = np.array([v[0] for v in self._vertices])
        vy = np.array([v[1] for v in self._vertices])
        n = len(self._vertices)

        mask = np.zeros(X.shape, dtype=bool)
        j = n - 1
        for i in range(n):
            cond = ((vy[i] > Y) != (vy[j] > Y)) & \
                   (X < (vx[j] - vx[i]) * (Y - vy[i]) / (vy[j] - vy[i] + 1e-30) + vx[i])
            mask = mask ^ cond
            j = i

        return mask.astype(np.float32)

    def _update_display(self):
        if self._vertices:
            xs = [v[0] for v in self._vertices]
            ys = [v[1] for v in self._vertices]

            self.scatter.setData(xs, ys)

            if len(self._vertices) > 1:
                closed_xs = xs + [xs[0]]
                closed_ys = ys + [ys[0]]
                self.line_plot.setData(closed_xs, closed_ys)
            else:
                self.line_plot.setData([], [])
        else:
            self.scatter.setData([], [])
            self.line_plot.setData([], [])


class ShapeEditor(QWidget):

    shape_accepted = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        toolbar = QHBoxLayout()
        self.mode_label = QLabel("模式: 多边形")
        toolbar.addWidget(self.mode_label)

        self.clear_btn = QPushButton("清除")
        self.clear_btn.clicked.connect(self._clear)
        toolbar.addWidget(self.clear_btn)

        self.undo_btn = QPushButton("撤销")
        self.undo_btn.clicked.connect(self._undo)
        toolbar.addWidget(self.undo_btn)

        self.accept_btn = QPushButton("确认")
        self.accept_btn.clicked.connect(self._accept)
        toolbar.addWidget(self.accept_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.editor_widget = ShapeEditorWidget()
        self.editor_widget.setMinimumHeight(300)
        layout.addWidget(self.editor_widget)

    def _clear(self):
        self.editor_widget.clear_vertices()

    def _undo(self):
        self.editor_widget.remove_last_vertex()

    def _accept(self):
        vertices = self.editor_widget.get_vertices()
        if len(vertices) >= 3:
            self.shape_accepted.emit(vertices)
        else:
            QMessageBox.warning(self, "提示", "至少需要3个顶点来定义一个多边形")

    def get_mask(self, grid_size: int = 256) -> np.ndarray:
        return self.editor_widget.get_mask(grid_size)
