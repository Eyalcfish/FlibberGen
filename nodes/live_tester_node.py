from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QLineEdit, QPushButton)
from PySide6.QtCore import Qt
from node_engine.node_base import Node
import numpy as np

class LiveTesterNode(Node):
    def __init__(self):
        super().__init__("Live Tester")
        self.height = 240
        self.width = 220
        
        # Input: Model
        self.add_input(0)
        
        self.input_fields = {}  # Dict: feature_name -> QLineEdit
        self.all_input_names = []
        self.sub_model = None
        self.sub_model_input_names = []
        self.direct_feature_names = []
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        self.main_layout = QVBoxLayout(self.widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(3)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻ Load Features")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #555; color: white; border: none; padding: 3px; font-size: 10px; }
            QPushButton:hover { background: #666; }
        """)
        self.refresh_btn.clicked.connect(self.load_features)
        self.main_layout.addWidget(self.refresh_btn)
        
        # Container for dynamic input fields
        self.inputs_container = QWidget()
        self.inputs_layout = QVBoxLayout(self.inputs_container)
        self.inputs_layout.setContentsMargins(0, 0, 0, 0)
        self.inputs_layout.setSpacing(2)
        self.main_layout.addWidget(self.inputs_container)
        
        # Predict button
        self.predict_btn = QPushButton("▶ Predict")
        self.predict_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 5px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.predict_btn.clicked.connect(self.predict)
        self.main_layout.addWidget(self.predict_btn)
        
        # Result display
        self.result_label = QLabel("Result: --")
        self.result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4EC9B0;")
        self.main_layout.addWidget(self.result_label)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(200, 200)
        self.proxy.setZValue(1.0)  # Ensure interactive

    def load_features(self):
        """Load feature info from connected model - shows ALL original inputs"""
        model = self.get_input_value(0)
        if model is None:
            self.result_label.setText("No model connected")
            self.result_label.setStyleSheet("color: #F44747;")
            return
        
        # Clear existing input fields
        for field in self.input_fields.values():
            field.deleteLater()
        self.input_fields.clear()
        
        # Clear layout
        while self.inputs_layout.count():
            item = self.inputs_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    w = item.layout().takeAt(0).widget()
                    if w:
                        w.deleteLater()
        
        # Get all original input names (x, y, z - not _poly_pred)
        self.all_input_names = getattr(model, 'all_input_names', None)
        self.sub_model = getattr(model, 'sub_model', None)
        self.sub_model_input_names = getattr(model, 'sub_model_input_names', [])
        self.direct_feature_names = getattr(model, 'input_feature_names', [])
        
        if not self.all_input_names:
            # Fallback to direct feature names
            self.all_input_names = self.direct_feature_names or [f"X{i+1}" for i in range(
                model.poly_features.n_features_in_ if hasattr(model, 'poly_features') and model.poly_features else 1
            )]
        
        # Create input field for each original input
        for name in self.all_input_names:
            row = QHBoxLayout()
            display = name[:12] + ".." if len(name) > 14 else name
            lbl = QLabel(f"{display}:")
            lbl.setStyleSheet("font-size: 10px;")
            lbl.setFixedWidth(80)
            lbl.setToolTip(name)
            row.addWidget(lbl)
            
            field = QLineEdit("0.0")
            field.setStyleSheet("background: #3c3c3c; color: white; border: 1px solid #555; padding: 2px;")
            field.returnPressed.connect(self.predict)
            row.addWidget(field)
            self.input_fields[name] = field
            
            self.inputs_layout.addLayout(row)
        
        # Adjust height
        new_height = 160 + len(self.all_input_names) * 28
        self.height = max(240, new_height)
        self.proxy.resize(200, new_height - 50)
        
        self.result_label.setText(f"Ready ({len(self.all_input_names)} inputs)")
        self.result_label.setStyleSheet("color: #888;")

    def predict(self):
        model = self.get_input_value(0)
        if model is None:
            self.result_label.setText("No model connected")
            self.result_label.setStyleSheet("font-size: 14px; color: #F44747;")
            return
        
        if not self.input_fields:
            self.load_features()
            if not self.input_fields:
                return
            
        try:
            # Get all input values
            all_values = {}
            for name, field in self.input_fields.items():
                all_values[name] = float(field.text())
            
            # Build the X array for the model
            # If there's a sub-model, compute its prediction first
            x_vals = []
            for feat_name in self.direct_feature_names:
                if feat_name == '_poly_pred' and self.sub_model:
                    # Compute sub-model prediction using its inputs
                    sub_x = [all_values[n] for n in self.sub_model_input_names]
                    sub_X = np.array([sub_x])
                    sub_pred = self.sub_model.predict(sub_X)
                    x_vals.append(sub_pred[0] if hasattr(sub_pred, '__iter__') else sub_pred)
                else:
                    x_vals.append(all_values.get(feat_name, 0.0))
            
            # Create proper 2D array
            X = np.array([x_vals])
            
            if hasattr(model, 'predict'):
                result = model.predict(X)
                if hasattr(result, '__iter__'):
                    result = result[0]
            else:
                result = 0
                    
            self.result_label.setText(f"Y = {result:.6f}")
            self.result_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4EC9B0;")
        except Exception as e:
            self.result_label.setText(f"Error: {str(e)[:20]}")
            self.result_label.setStyleSheet("font-size: 14px; color: #F44747;")
            
    def eval(self):
        return None
