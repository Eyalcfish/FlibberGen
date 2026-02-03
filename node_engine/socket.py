from PySide6.QtWidgets import QGraphicsItem
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPen

class Socket(QGraphicsItem):
    RADIUS = 6.0
    
    def __init__(self, node, index=0, is_input=False):
        super().__init__(parent=node)
        self.node = node
        self.index = index
        self.is_input = is_input
        self.edges = []
        
        # Style
        self.color_outline = QColor("#FF000000")
        self.color_bg = QColor("#FF99AA00") if is_input else QColor("#FF00AA99")
        self.pen = QPen(self.color_outline)
        self.pen.setWidthF(1.0)
        self.brush = QBrush(self.color_bg)
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        
    def boundingRect(self):
        return QRectF(
            -self.RADIUS,
            -self.RADIUS,
            2 * self.RADIUS,
            2 * self.RADIUS
        )
        
    def paint(self, painter, option, widget):
        painter.setBrush(self.brush)
        painter.setPen(self.pen)
        painter.drawEllipse(
            -self.RADIUS,
            -self.RADIUS,
            2 * self.RADIUS,
            2 * self.RADIUS
        )
        
    def get_scene_pos(self):
        return self.scenePos()
    
    def add_edge(self, edge):
        self.edges.append(edge)
        
    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)

    def remove_all_edges(self):
        # Create a copy to avoid modification during iteration
        for edge in self.edges[:]:
             edge.remove()
        self.edges.clear()
    
    def has_edge(self):
        return len(self.edges) > 0
