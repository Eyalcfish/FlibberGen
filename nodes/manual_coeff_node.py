from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit)
from PySide6.QtCore import Qt
from node_engine.node_base import Node
from nodes.polyfit_node import PolyFitModel
import numpy as np

class ManualCoeffNode(Node):
    def __init__(self):
        super().__init__("Manual Coeffs")
        self.height = 150
        
        # No inputs
        # Output: Model
        self.add_output(0)
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Coefficient inputs
        lbl = QLabel("Coefficients (comma sep):")
        lbl.setStyleSheet("font-size: 10px;")
        layout.addWidget(lbl)
        
        self.coeff_input = QLineEdit("1.0, 0.5, 0.1")
        self.coeff_input.setStyleSheet("background: #3c3c3c; color: white; border: 1px solid #555; padding: 2px;")
        layout.addWidget(self.coeff_input)
        
        # Intercept
        row = QHBoxLayout()
        row.addWidget(QLabel("Intercept:"))
        self.intercept_input = QLineEdit("0.0")
        self.intercept_input.setStyleSheet("background: #3c3c3c; color: white; border: 1px solid #555; padding: 2px;")
        self.intercept_input.setMaximumWidth(60)
        row.addWidget(self.intercept_input)
        layout.addLayout(row)
        
        # Info
        self.info_lbl = QLabel("Format: a₀, a₁, a₂...")
        self.info_lbl.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self.info_lbl)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(160, 110)
        
    def eval(self):
        try:
            coeffs = [float(c.strip()) for c in self.coeff_input.text().split(',')]
            intercept = float(self.intercept_input.text())
            
            # Create a simple model (no poly_features transform)
            class SimpleModel:
                def __init__(self, coeffs, intercept):
                    self.coeffs = np.array(coeffs)
                    self.intercept = intercept
                    self.r2 = None
                    self.mse = None
                    self.degree = len(coeffs)
                    self.condition = None
                    
                def predict(self, X):
                    # Assume polynomial: a0 + a1*x + a2*x^2 + ...
                    result = self.intercept
                    for i, c in enumerate(self.coeffs):
                        result = result + c * (X ** i)
                    return result
                    
            return SimpleModel(coeffs, intercept)
        except Exception as e:
            self.info_lbl.setText(f"Error: {str(e)[:20]}")
            self.info_lbl.setStyleSheet("color: #F44747; font-size: 9px;")
            return None
