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

    def serialize(self):
        from .node_base import Node
        
        nodes = []
        edges = []
        
        # Temp ID map
        node_to_id = {}
        
        # 1. Serialize Nodes
        all_items = self.items()
        current_id = 0
        
        # Filter nodes first
        scene_nodes = [i for i in all_items if isinstance(i, Node)]
        
        for node in scene_nodes:
            node_id = current_id
            current_id += 1
            node_to_id[node] = node_id
            
            node_data = node.to_dict()
            node_data['id'] = node_id
            # title is already in to_dict but we use it for creation type too usually
            # In our case 'title' maps to the node type string in create_node?
            # actually node.title is "CSV Loader" etc. which matches the map keys.
            nodes.append(node_data)
            
        # 2. Serialize Edges
        # We can iterate nodes and their outputs to find edges to avoid duplicates?
        # Or just iterate all items and filter edges.
        
        scene_edges = [i for i in all_items if isinstance(i, Edge)]
        for edge in scene_edges:
            start_node = edge.start_socket.node
            end_node = edge.end_socket.node
            
            if start_node in node_to_id and end_node in node_to_id:
                edge_data = {
                    "start_node_id": node_to_id[start_node],
                    "end_node_id": node_to_id[end_node],
                    "start_socket_index": edge.start_socket.index,
                    "end_socket_index": edge.end_socket.index
                }
                edges.append(edge_data)
                
        return {
            "nodes": nodes,
            "edges": edges
        }

    def deserialize(self, data, create_node_func):
        self.clear()
        
        nodes_data = data.get("nodes", [])
        edges_data = data.get("edges", [])
        
        # ID map for reconstruction
        id_to_node = {}
        
        # 1. Create Nodes
        for n_data in nodes_data:
            title = n_data.get("title", "Node")
            node = create_node_func(title)
            if node:
                self.addItem(node)
                node.from_dict(n_data)
                id_to_node[n_data['id']] = node
        
        # 2. Create Edges
        for e_data in edges_data:
            start_id = e_data["start_node_id"]
            end_id = e_data["end_node_id"]
            
            if start_id in id_to_node and end_id in id_to_node:
                start_node = id_to_node[start_id]
                end_node = id_to_node[end_id]
                
                start_idx = e_data["start_socket_index"]
                end_idx = e_data["end_socket_index"]
                
                # Verify indices
                if start_idx < len(start_node.outputs) and end_idx < len(end_node.inputs):
                    start_socket = start_node.outputs[start_idx]
                    end_socket = end_node.inputs[end_idx]
                    
                    Edge(self, start_socket, end_socket)
