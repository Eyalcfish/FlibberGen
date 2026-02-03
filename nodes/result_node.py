from PySide6.QtWidgets import QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel, QDoubleSpinBox, QPushButton
from PySide6.QtCore import Qt
from node_engine.node_base import Node
from nodes.polyfit_node import PolyFitModel
import numpy as np

class ResultNode(Node):
    def __init__(self):
        super().__init__("Result / Test")
        self.width = 200
        self.height = 200
        
        self.add_input(0) # Model Input
        
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: transparent; color: white;")
        layout = QVBoxLayout(self.widget)
        
        layout.addWidget(QLabel("Test Input (X1):"))
        self.spin_x1 = QDoubleSpinBox()
        self.spin_x1.setRange(-1e9, 1e9)
        layout.addWidget(self.spin_x1)
        
        layout.addWidget(QLabel("Test Input (X2):"))
        self.spin_x2 = QDoubleSpinBox()
        self.spin_x2.setRange(-1e9, 1e9)
        layout.addWidget(self.spin_x2)
        
        self.btn = QPushButton("Predict")
        self.btn.clicked.connect(self.calculate)
        layout.addWidget(self.btn)
        
        self.lbl_res = QLabel("Result: --")
        self.lbl_res.setStyleSheet("font-size: 14px; font-weight: bold; color: #007ACC;")
        layout.addWidget(self.lbl_res)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 35)
        self.proxy.resize(180, 150)
        
    def calculate(self):
        model_obj = self.get_input_value(0)
        if isinstance(model_obj, PolyFitModel):
            x1 = self.spin_x1.value()
            x2 = self.spin_x2.value()
            
            # Prepare input vector (must match model degree/shape ideally, but for MVP assuming 2 features if trained with 2)
            # This is brittle but suffices for MVP demo
            X = np.array([[x1, x2]])
            
            # Handle dimension mismatch gracefully-ish
            try:
                # If model was trained on 1 feature, slice input
                if model_obj.model.n_features_in_ == 1:
                    X = np.array([[x1]])
                    
                X_poly = model_obj.poly.transform(X)
                pred = model_obj.model.predict(X_poly)[0]
                self.lbl_res.setText(f"Result: {pred:.4f}")
            except Exception as e:
                 self.lbl_res.setText("Dim Error")
        else:
            self.lbl_res.setText("No Model")
    
    def eval(self):
        return None
