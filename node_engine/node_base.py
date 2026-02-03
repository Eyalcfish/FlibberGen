from PySide6.QtWidgets import QGraphicsItem, QGraphicsTextItem
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QBrush, QPen, QFont
from .socket import Socket
from core.signals import Signals

class Node(QGraphicsItem):
    def __init__(self, title="Node"):
        super().__init__()
        self.title = title
        
        # Dimensions
        self.width = 180
        self.height = 100
        self.header_height = 24
        self.edge_roundness = 10.0
        
        # Sockets
        self.inputs = []
        self.outputs = []
        
        # Flags
        # Allow selecting and moving
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        # Allow child widgets to receive events
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges)
        
        # Styling
        self._pen_default = QPen(QColor("#7F000000"))
        self._pen_selected = QPen(QColor("#FFFFA637"))
        self._brush_title = QBrush(QColor("#FF313131"))
        self._brush_background = QBrush(QColor("#E3212121"))
        
        # Title Item
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(self.title)
        self.title_item.setDefaultTextColor(QColor("#FFFFFFFF"))
        self.title_item.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title_item.setPos(5, 0)
        
        # Signals
        self.signals = Signals.get()
        
    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)
        
    def paint(self, painter, option, widget):
        # Body
        painter.setBrush(self._brush_background)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(0, 0, self.width, self.height, self.edge_roundness, self.edge_roundness)
        
        # Header
        painter.setBrush(self._brush_title)
        painter.drawRoundedRect(0, 0, self.width, self.header_height, self.edge_roundness, self.edge_roundness)
        # Fix bottom corners of header to be square
        painter.drawRect(0, self.header_height - self.edge_roundness, self.width, self.edge_roundness)
        
        # Outline
        if self.isSelected():
            painter.setPen(self._pen_selected)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(-1, -1, self.width + 2, self.height + 2, self.edge_roundness, self.edge_roundness)
        else:
            painter.setPen(self._pen_default)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(0, 0, self.width, self.height, self.edge_roundness, self.edge_roundness)

            
    def add_input(self, index=0):
        socket = Socket(self, index, is_input=True)
        socket.setPos(0, self.header_height + 20 + index * 22)
        self.inputs.append(socket)
        return socket
        
    def add_output(self, index=0):
        socket = Socket(self, index, is_input=False)
        socket.setPos(self.width, self.header_height + 20 + index * 22)
        self.outputs.append(socket)
        return socket
        
    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        # Optimize: only update connected edges
        for socket in self.inputs + self.outputs:
            for edge in socket.edges:
                edge.update_positions()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange and value == True:
            self.signals.node_selected.emit(self)
        return super().itemChange(change, value)
    
    # Logic to override
    def eval(self):
        pass
    
    # Helper to get input data
    def get_input_value(self, index=0):
        if index >= len(self.inputs): return None
        socket = self.inputs[index]
        if not socket.edges: return None
        # Get the other socket
        other_socket = socket.edges[0].start_socket
        # Get that socket's node
        other_node = other_socket.node
        return other_node.eval()
        
    def to_dict(self):
        return {
            "title": self.title,
            "x": self.pos().x(),
            "y": self.pos().y()
        }
        
    def from_dict(self, data):
        self.setPos(data.get("x", 0), data.get("y", 0))
