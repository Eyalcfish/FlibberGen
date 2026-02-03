from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel, QPushButton)
from PySide6.QtCore import Qt
from node_engine.node_base import Node

class InspectorNode(Node):
    def __init__(self):
        super().__init__("Inspector")
        self.height = 180
        self.width = 200
        
        # Input: Model
        self.add_input(0)
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(4)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻ Refresh Stats")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 4px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.refresh_btn.clicked.connect(self.refresh)
        layout.addWidget(self.refresh_btn)
        
        # Metrics display
        self.r2_label = QLabel("R²: --")
        self.r2_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4EC9B0;")
        layout.addWidget(self.r2_label)
        
        self.mse_label = QLabel("MSE: --")
        self.mse_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #DCDCAA;")
        layout.addWidget(self.mse_label)
        
        self.degree_label = QLabel("Degree: --")
        self.degree_label.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(self.degree_label)
        
        self.terms_label = QLabel("Terms: --")
        self.terms_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.terms_label)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(180, 140)

    def refresh(self):
        """Button to trigger evaluation"""
        self.eval()

    def eval(self):
        model = self.get_input_value(0)
        if model is None:
            self.r2_label.setText("R²: -- (no model)")
            self.mse_label.setText("MSE: --")
            self.degree_label.setText("Degree: --")
            self.terms_label.setText("Connect a PolyFit node")
            return None
            
        # Update displays
        r2 = getattr(model, 'r2', None)
        mse = getattr(model, 'mse', None)
        degree = getattr(model, 'degree', None)
        coeffs = getattr(model, 'coeffs', [])
        
        self.r2_label.setText(f"R²: {r2:.6f}" if r2 is not None else "R²: N/A")
        self.mse_label.setText(f"MSE: {mse:.6f}" if mse is not None else "MSE: N/A")
        self.degree_label.setText(f"Degree: {degree}" if degree else "Degree: --")
        self.terms_label.setText(f"Terms: {len(coeffs) if hasattr(coeffs, '__len__') else 'N/A'}")
        
        return model
