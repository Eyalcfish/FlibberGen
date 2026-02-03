from PySide6.QtWidgets import QGraphicsPathItem
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QColor, QPen, QPainterPath

class Edge(QGraphicsPathItem):
    def __init__(self, scene, start_socket, end_socket):
        super().__init__()
        self.scene = scene
        self.start_socket = start_socket
        self.end_socket = end_socket
        
        self.start_socket.add_edge(self)
        self.end_socket.add_edge(self)
        
        self.scene.addItem(self)
        self.setZValue(-1)
        
        self.color = QColor("#FFFFFFFF")
        self.pen = QPen(self.color)
        self.pen.setWidthF(2.0)
        self.setPen(self.pen)
        
        self.update_positions()

    def update_positions(self):
        source_pos = self.start_socket.get_scene_pos()
        target_pos = self.end_socket.get_scene_pos()
        
        path = QPainterPath(source_pos)
        
        # Cubic Bezier Logic
        dist_x = abs(target_pos.x() - source_pos.x())
        control_offset = min(dist_x * 0.5, 150.0)
        
        cp1 = source_pos + QPointF(control_offset, 0)
        cp2 = target_pos + QPointF(-control_offset, 0)
        
        path.cubicTo(cp1, cp2, target_pos)
        self.setPath(path)
        
    def remove(self):
        if self.start_socket:
            self.start_socket.remove_edge(self)
        if self.end_socket:
            self.end_socket.remove_edge(self)
        self.scene.removeItem(self)
        self.start_socket = None
        self.end_socket = None
