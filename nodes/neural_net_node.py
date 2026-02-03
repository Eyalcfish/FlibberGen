from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QSpinBox, QPushButton, QLineEdit)
from ui.graphics_combo import GraphicsComboBox
from PySide6.QtCore import Qt
from node_engine.node_base import Node
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

class NeuralNetModel:
    """Container for Neural Network regression results"""
    def __init__(self, model, r2, mse, input_feature_names, all_input_names=None, 
                 sub_model=None, sub_model_input_names=None, condition=None):
        self.model = model
        self.r2 = r2
        self.mse = mse
        self.input_feature_names = input_feature_names
        self.all_input_names = all_input_names or input_feature_names
        self.sub_model = sub_model
        self.sub_model_input_names = sub_model_input_names
        self.condition = condition
        
        # Mock poly_features for compatibility with GraphNode/LiveTester
        class MockPolyFeatures:
            def __init__(self, n_features):
                self.n_features_in_ = n_features
        
        self.poly_features = MockPolyFeatures(len(input_feature_names) if input_feature_names else 1)
        
    def predict(self, X):
        return self.model.predict(X)

class NeuralNetNode(Node):
    def __init__(self):
        super().__init__("Neural Network")
        self.height = 240
        self.width = 200
        
        # Input: Data (X, Y)
        self.add_input(0)
        # Output: Model
        self.add_output(0)
        
        self.model = None
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Hidden Layers configuration
        self.layer_spinboxes = []
        
        # Num Layers Selector
        row_n = QHBoxLayout()
        row_n.addWidget(QLabel("Num Layers:", styleSheet="font-size: 10px; color: #aaa;"))
        self.num_layers_spin = QSpinBox()
        self.num_layers_spin.setRange(1, 5)
        self.num_layers_spin.setValue(2) # Default
        self.num_layers_spin.setStyleSheet("background: #3c3c3c; color: white;")
        self.num_layers_spin.valueChanged.connect(self.update_layers_ui)
        row_n.addWidget(self.num_layers_spin)
        layout.addLayout(row_n)
        
        # Dynamic Container for Layer Sizes
        self.layers_container = QWidget()
        self.layers_layout = QVBoxLayout(self.layers_container)
        self.layers_layout.setContentsMargins(0,0,0,0)
        self.layers_layout.setSpacing(2)
        layout.addWidget(self.layers_container)
        
        # Initial population
        self.update_layers_ui()
        
        # Activation
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Activ:", styleSheet="font-size: 10px;"))
        self.activation_combo = GraphicsComboBox()
        self.activation_combo.addItems(["relu", "tanh", "logistic", "identity"])
        row1.addWidget(self.activation_combo)
        layout.addLayout(row1)
        
        # Solver
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Solver:", styleSheet="font-size: 10px;"))
        self.solver_combo = GraphicsComboBox()
        self.solver_combo.addItems(["adam", "lbfgs", "sgd"])
        row2.addWidget(self.solver_combo)
        layout.addLayout(row2)
        
        # Max Iters
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Max Iter:", styleSheet="font-size: 10px;"))
        self.iter_spin = QSpinBox()
        self.iter_spin.setRange(100, 10000)
        self.iter_spin.setValue(500)
        self.iter_spin.setStyleSheet("background: #3c3c3c; color: white;")
        row3.addWidget(self.iter_spin)
        layout.addLayout(row3)
        
        # Train Button
        self.train_btn = QPushButton("▶ Train Model")
        self.train_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 5px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.train_btn.clicked.connect(self.run_train)
        layout.addWidget(self.train_btn)
        
        # Status Label
        self.status_lbl = QLabel("Ready")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.status_lbl)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.adjust_height()
        self.proxy.setZValue(1.0) 

    def update_layers_ui(self):
        # Clear existing
        self.layer_spinboxes = []
        while self.layers_layout.count():
            item = self.layers_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        n = self.num_layers_spin.value()
        for i in range(n):
            row = QHBoxLayout()
            row.setContentsMargins(0,0,0,0)
            lbl = QLabel(f"L{i+1} Size:")
            lbl.setStyleSheet("font-size: 9px; color: #888;")
            row.addWidget(lbl)
            
            spin = QSpinBox()
            spin.setRange(1, 2000)
            spin.setValue(100 if i == 0 else 50) # Default taper
            spin.setStyleSheet("background: #3c3c3c; color: white;")
            row.addWidget(spin)
            
            self.layers_layout.addLayout(row)
            self.layer_spinboxes.append(spin)
            
        self.adjust_height()
        
    def adjust_height(self):
        # Base height + space per layer row
        n = self.num_layers_spin.value()
        new_height = 240 + (n * 25)
        self.height = max(240, new_height)
        self.proxy.resize(180, new_height - 30)

    def run_train(self):
        self.eval()

    def fit(self, X, Y, input_feature_names=None):
        try:
            # Parse layers from dynamic list
            layers = []
            for spin in self.layer_spinboxes:
                layers.append(spin.value())
            
            layers = tuple(layers)
                
            activation = self.activation_combo.currentText()
            solver = self.solver_combo.currentText()
            max_iter = self.iter_spin.value()
            
            # Configure and train model
            mlp = MLPRegressor(
                hidden_layer_sizes=layers,
                activation=activation,
                solver=solver,
                max_iter=max_iter,
                random_state=42
            )
            
            mlp.fit(X, Y)
            
            Y_pred = mlp.predict(X)
            r2 = r2_score(Y, Y_pred)
            mse = mean_squared_error(Y, Y_pred)
            
            return NeuralNetModel(
                model=mlp,
                r2=r2,
                mse=mse,
                input_feature_names=input_feature_names
            )
            
        except Exception as e:
            self.status_lbl.setText(f"Error: {str(e)[:20]}")
            self.status_lbl.setStyleSheet("color: #F44747; font-size: 10px;")
            return None

    def eval(self):
        data = self.get_input_value(0)
        if data is None or not isinstance(data, dict):
            self.status_lbl.setText("No data connected")
            self.status_lbl.setStyleSheet("color: #888; font-size: 10px;")
            return None
            
        X, Y = data.get('X'), data.get('Y')
        if X is None or Y is None or len(X) == 0:
            self.status_lbl.setText("Empty data")
            return None
            
        # Get feature names from the data
        input_feature_names = data.get('feature_names', [])
        all_input_names = data.get('all_input_names', input_feature_names)
        sub_model = data.get('sub_model')
        sub_model_input_names = data.get('sub_model_input_names', [])
        
        self.model = self.fit(X, Y, input_feature_names)
        
        if self.model:
            self.model.condition = data.get('condition')
            # Store info for chained models
            self.model.all_input_names = all_input_names
            self.model.sub_model = sub_model
            self.model.sub_model_input_names = sub_model_input_names
            
            self.status_lbl.setText(f"✓ R²={self.model.r2:.4f}")
            self.status_lbl.setStyleSheet("color: #4EC9B0; font-size: 10px;")
            
        return self.model
