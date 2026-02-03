from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QSlider)
from PySide6.QtCore import Qt
from node_engine.node_base import Node
import numpy as np

class RangeFilterNode(Node):
    def __init__(self):
        super().__init__("Range Filter")
        self.height = 120
        
        # Input: Data
        self.add_input(0)
        # Output: Filtered data
        self.add_output(0)
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Min slider
        self.lbl_min = QLabel("Start: 0%")
        self.lbl_min.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.lbl_min)
        
        self.slider_min = QSlider(Qt.Horizontal)
        self.slider_min.setRange(0, 100)
        self.slider_min.setValue(0)
        self.slider_min.valueChanged.connect(self.update_labels)
        layout.addWidget(self.slider_min)
        
        # Max slider
        self.lbl_max = QLabel("End: 100%")
        self.lbl_max.setStyleSheet("font-size: 10px;")
        layout.addWidget(self.lbl_max)
        
        self.slider_max = QSlider(Qt.Horizontal)
        self.slider_max.setRange(0, 100)
        self.slider_max.setValue(100)
        self.slider_max.valueChanged.connect(self.update_labels)
        layout.addWidget(self.slider_max)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(160, 80)

    def update_labels(self):
        self.lbl_min.setText(f"Start: {self.slider_min.value()}%")
        self.lbl_max.setText(f"End: {self.slider_max.value()}%")
        
    def eval(self):
        data = self.get_input_value(0)
        if data is None or not isinstance(data, dict):
            return None
            
        X, Y = data.get('X'), data.get('Y')
        if X is None or Y is None:
            return None
            
        n = len(Y)
        start_pct = self.slider_min.value() / 100
        end_pct = self.slider_max.value() / 100
        
        start_idx = int(n * start_pct)
        end_idx = int(n * end_pct)
        
        return {
            'X': X[start_idx:end_idx],
            'Y': Y[start_idx:end_idx],
            'feature_names': data.get('feature_names', [])
        }
