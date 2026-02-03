from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from node_engine.node_base import Node
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import numpy as np

class PolyFitModel:
    """Container for polynomial regression results"""
    def __init__(self, coeffs, intercept, degree, feature_names, r2, mse, poly_features, 
                 input_feature_names=None, condition=None):
        self.coeffs = coeffs
        self.intercept = intercept
        self.degree = degree
        self.feature_names = feature_names  # Polynomial term names (x0^2, x0*x1, etc.)
        self.input_feature_names = input_feature_names  # Original column names (e.g., ['speed', 'angle'])
        self.r2 = r2
        self.mse = mse
        self.poly_features = poly_features
        self.condition = condition  # For conditional splits
        
    def predict(self, X):
        X_poly = self.poly_features.transform(X)
        return X_poly @ self.coeffs + self.intercept

class PolyFitNode(Node):
    def __init__(self):
        super().__init__("PolyFit")
        self.height = 160  # Taller for button
        
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
        
        # Degree row
        row = QHBoxLayout()
        row.addWidget(QLabel("Degree:"))
        self.degree_spin = QSpinBox()
        self.degree_spin.setRange(1, 5)
        self.degree_spin.setValue(2)
        self.degree_spin.setStyleSheet("background: #3c3c3c; color: white;")
        row.addWidget(self.degree_spin)
        layout.addLayout(row)
        
        # Interaction checkbox
        self.interact_cb = QCheckBox("Include interactions")
        self.interact_cb.setChecked(True)
        self.interact_cb.setStyleSheet("color: white; font-size: 10px;")
        layout.addWidget(self.interact_cb)
        
        # Fit button
        from PySide6.QtWidgets import QPushButton
        self.fit_btn = QPushButton("▶ Fit Model")
        self.fit_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 5px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.fit_btn.clicked.connect(self.run_fit)
        layout.addWidget(self.fit_btn)
        
        # Status label
        self.status_lbl = QLabel("Click Fit after connecting")
        self.status_lbl.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.status_lbl)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(160, 120)
    
    def run_fit(self):
        """Button callback to trigger evaluation"""
        self.eval()

    def fit(self, X, Y, input_feature_names=None):
        """Perform polynomial regression"""
        degree = self.degree_spin.value()
        interaction_only = not self.interact_cb.isChecked()
        
        try:
            poly = PolynomialFeatures(degree=degree, interaction_only=interaction_only, include_bias=False)
            X_poly = poly.fit_transform(X.reshape(-1, 1) if X.ndim == 1 else X)
            
            reg = LinearRegression(fit_intercept=True)
            reg.fit(X_poly, Y)
            
            Y_pred = reg.predict(X_poly)
            r2 = r2_score(Y, Y_pred)
            mse = mean_squared_error(Y, Y_pred)
            
            return PolyFitModel(
                coeffs=reg.coef_,
                intercept=reg.intercept_,
                degree=degree,
                feature_names=poly.get_feature_names_out() if hasattr(poly, 'get_feature_names_out') else None,
                r2=r2,
                mse=mse,
                poly_features=poly,
                input_feature_names=input_feature_names  # Store original column names
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
