from PySide6.QtWidgets import QGraphicsScene
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen
from .edge import Edge

class NodeScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor("#212121"))
        self.grid_size = 20
        self.grid_pen_light = QPen(QColor("#2f2f2f"))
        self.grid_pen_light.setWidth(1)
        self.grid_pen_dark = QPen(QColor("#292929"))
        self.grid_pen_dark.setWidth(1.5)
        
        self.setSceneRect(-32000, -32000, 64000, 64000)
        
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        # Grid
        left = int(rect.left())
        top = int(rect.top())
        right = int(rect.right())
        bottom = int(rect.bottom())
        
        first_left = left - (left % self.grid_size)
        first_top = top - (top % self.grid_size)
        
        # Compute lines
        lines_light, lines_dark = [], []
        
        for x in range(first_left, right, self.grid_size):
            if x % (self.grid_size * 5) == 0:
                lines_dark.append(x)
            else:
                lines_light.append(x)
                
        for y in range(first_top, bottom, self.grid_size):
            if y % (self.grid_size * 5) == 0:
                pass # vertical lines logic reused, wait this is horizontal
            # Actually easier to just draw immediately
        
        # Draw light
        painter.setPen(self.grid_pen_light)
        for x in range(first_left, right, self.grid_size):
             painter.drawLine(x, top, x, bottom)
        for y in range(first_top, bottom, self.grid_size):
             painter.drawLine(left, y, right, y)
             
        # Draw dark
        painter.setPen(self.grid_pen_dark)
        for x in range(first_left, right, self.grid_size * 5):
             painter.drawLine(x, top, x, bottom)
        for y in range(first_top, bottom, self.grid_size * 5):
             painter.drawLine(left, y, right, y)
