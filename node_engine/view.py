from PySide6.QtWidgets import QGraphicsView, QMenu
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPainter, QMouseEvent
from .socket import Socket
from .edge import Edge
# Import all node types
from nodes import csv_loader_node, column_selector_node, splitter_node, range_filter_node
from nodes import polyfit_node, manual_coeff_node, code_generator_node, inspector_node, live_tester_node
from nodes import graph_node, neural_net_node

class NodeView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(parent)
        self.setScene(scene)
        self.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Default to NoDrag to allow widget interaction
        self.setDragMode(QGraphicsView.NoDrag)
        
        # Interaction state
        self.mode = "NO_OP"
        self.drag_start_socket = None
        self.drag_edge = None
        
    def zoom_view(self, factor):
        self.scale(factor, factor)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_out_factor = 1 / 1.25
            zoom_in_factor = 1.25
            
            if event.angleDelta().y() > 0:
                zoom_factor = zoom_in_factor
            else:
                zoom_factor = zoom_out_factor
                
            self.zoom_view(zoom_factor)
            event.accept()
        else:
            super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middleMouseButtonPress(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonPress(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonPress(event)
        else:
            super().mousePressEvent(event)
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.middleMouseButtonRelease(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonRelease(event)
        else:
            super().mouseReleaseEvent(event)
            
    def middleMouseButtonPress(self, event):
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        fake_event = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
        super().mousePressEvent(fake_event)
        
    def middleMouseButtonRelease(self, event):
        fake_event = QMouseEvent(event.type(), event.position(), Qt.LeftButton, Qt.LeftButton, event.modifiers())
        super().mouseReleaseEvent(fake_event)
        self.setDragMode(QGraphicsView.NoDrag)
        
    def leftMouseButtonPress(self, event):
        item = self.itemAt(event.pos())
        
        # 1. Socket Click -> Create Edge
        if isinstance(item, Socket):
            self.mode = "EDGE_DRAG"
            self.drag_start_socket = item
            self.drag_point = DummySocket(item.get_scene_pos())
            self.drag_edge = Edge(self.scene(), item, self.drag_point)
            # Ensure NoDrag so we don't select/pan while wiring
            self.setDragMode(QGraphicsView.NoDrag)
            return
            
        # 2. Background Click -> Enable RubberBand
        if item is None:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
        else:
            # 3. Item Click (Node, Widget, etc)
            self.setDragMode(QGraphicsView.NoDrag)
            
            # Special handling for Proxy Widgets (interactive controls)
            # Walk up to find if we clicked a proxy
            temp = item
            while temp:
                from PySide6.QtWidgets import QGraphicsProxyWidget
                if isinstance(temp, QGraphicsProxyWidget):
                    # Force focus to the proxy widget to ensure it receives input
                    temp.setFocus()
                    break
                temp = temp.parentItem()
            
        super().mousePressEvent(event)
        
    def leftMouseButtonRelease(self, event):
        # Always reset to NoDrag after release to be safe
        # But process Edge Drag logic first
        
        if self.mode == "EDGE_DRAG":
            self.mode = "NO_OP"
            
            if self.drag_edge:
                self.drag_edge.remove()
                self.drag_edge = None
            self.drag_point = None

            item = self.itemAt(event.pos())
            
            if isinstance(item, Socket) and item is not self.drag_start_socket:
                if item.is_input != self.drag_start_socket.is_input:
                    # Determine start/end order
                    start = self.drag_start_socket if not self.drag_start_socket.is_input else item
                    end = item if not self.drag_start_socket.is_input else self.drag_start_socket
                    
                    if end.is_input and end.has_edge():
                        end.remove_all_edges()
                        
                    Edge(self.scene(), start, end)
            
            # Reset and return
            self.setDragMode(QGraphicsView.NoDrag)
            return

        super().mouseReleaseEvent(event)
        
        # Reset to NoDrag for next interaction
        self.setDragMode(QGraphicsView.NoDrag)
        
    def mouseMoveEvent(self, event):
        if self.mode == "EDGE_DRAG" and self.drag_edge and self.drag_point:
            pos = self.mapToScene(event.pos())
            self.drag_point.setPos(pos)
            self.drag_edge.update_positions()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        # Zoom shortcuts
        if event.modifiers() & Qt.ControlModifier:
            if event.key() == Qt.Key_Equal or event.key() == Qt.Key_Plus:
                self.zoom_view(1.25)
                event.accept()
                return
            elif event.key() == Qt.Key_Minus:
                self.zoom_view(1 / 1.25)
                event.accept()
                return

        if event.key() == Qt.Key_Delete or event.key() == Qt.Key_Backspace:
            self.delete_selected()
        else:
            super().keyPressEvent(event)
    
    def delete_selected(self):
        """Delete all selected nodes and their edges"""
        from .node_base import Node
        items = self.scene().selectedItems()
        for item in items:
            if isinstance(item, Node):
                # Remove all edges connected to this node
                for socket in item.inputs + item.outputs:
                    for edge in socket.edges[:]:
                        edge.remove()
                self.scene().removeItem(item)




    def rightMouseButtonPress(self, event):
        from .node_base import Node
        
        # Check if clicking on a node
        item = self.itemAt(event.pos())
        clicked_node = None
        
        # Find parent node if clicking on child item
        while item:
            if isinstance(item, Node):
                clicked_node = item
                break
            item = item.parentItem()
        
        menu = QMenu(self)
        pos = event.globalPos()
        
        # If clicking on a node, show node-specific menu
        if clicked_node:
            delete_action = menu.addAction("🗑 Delete Node")
            menu.addSeparator()
        
        # Entry nodes
        entry_menu = menu.addMenu("Add Entry")
        entry_menu.addAction("CSV Loader")
        entry_menu.addAction("Column Selector")
        
        # Logic nodes
        logic_menu = menu.addMenu("Add Logic")
        logic_menu.addAction("Conditional Splitter")
        logic_menu.addAction("Range Filter")
        
        # Math nodes
        math_menu = menu.addMenu("Add Math")
        math_menu.addAction("PolyFit")
        math_menu.addAction("Neural Network")
        math_menu.addAction("Manual Coeffs")
        
        # Output nodes
        output_menu = menu.addMenu("Add Output")
        output_menu.addAction("Code Generator")
        output_menu.addAction("Inspector")
        output_menu.addAction("Live Tester")
        output_menu.addAction("Graph View")
        
        action = menu.exec(pos)
        if action:
            if clicked_node and action.text() == "🗑 Delete Node":
                # Delete the node
                for socket in clicked_node.inputs + clicked_node.outputs:
                    for edge in socket.edges[:]:
                        edge.remove()
                self.scene().removeItem(clicked_node)
            else:
                self.add_node_by_name(action.text(), event.pos())

    def create_node(self, name):
        node_map = {
            "CSV Loader": csv_loader_node.CSVLoaderNode,
            "Column Selector": column_selector_node.ColumnSelectorNode,
            "Conditional Splitter": splitter_node.ConditionalSplitterNode,
            "Range Filter": range_filter_node.RangeFilterNode,
            "PolyFit": polyfit_node.PolyFitNode,
            "Neural Network": neural_net_node.NeuralNetNode,
            "Manual Coeffs": manual_coeff_node.ManualCoeffNode,
            "Code Generator": code_generator_node.CodeGeneratorNode,
            "Inspector": inspector_node.InspectorNode,
            "Live Tester": live_tester_node.LiveTesterNode,
            "Graph View": graph_node.GraphNode,
        }
        cls = node_map.get(name)
        return cls() if cls else None

    def add_node_by_name(self, name, pos_point):
        scene_pos = self.mapToScene(pos_point)
        node = self.create_node(name)
        if node:
            self.scene().addItem(node)
            node.setPos(scene_pos)
            
    def add_node(self, node_type_str):
        # Helper for external toolbars
        center_pt = self.viewport().rect().center()
        scene_pos = self.mapToScene(center_pt)
        node = self.create_node(node_type_str)
        if node:
            self.scene().addItem(node)
            node.setPos(scene_pos)

class DummySocket:
    def __init__(self, pos):
        self.pos = pos
        self.node = None # Mock
        
    def get_scene_pos(self):
        return self.pos
        
    def setPos(self, pos):
        self.pos = pos
        
    def add_edge(self, edge): pass
    def remove_edge(self, edge): pass
