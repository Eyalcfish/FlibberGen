from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QCheckBox, QRadioButton, QButtonGroup, QPushButton)
from PySide6.QtCore import Qt
from node_engine.node_base import Node
import pandas as pd
import numpy as np

class ColumnSelectorNode(Node):
    def __init__(self):
        super().__init__("Column Selector")
        self.height = 280
        self.width = 200
        
        # Inputs: DataFrame (required), Model (optional - adds prediction column)
        self.add_input(0)  # CSV Data
        self.add_input(1)  # PolyFit Model (optional)
        # Output: Combined data
        self.add_output(0)
        
        self.columns = []
        self.feature_checks = []
        self.target_radios = []
        self.target_group = QButtonGroup()
        self.merged_df = None  # Store merged DataFrame
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        self.main_layout = QVBoxLayout(self.widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(2)
        
        # Info label
        info = QLabel("In1: CSV | In2: Model (opt)")
        info.setStyleSheet("font-size: 9px; color: #888;")
        self.main_layout.addWidget(info)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻ Refresh Columns")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 4px; font-size: 10px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_columns)
        self.main_layout.addWidget(self.refresh_btn)
        
        # Header row
        header = QHBoxLayout()
        lbl_col = QLabel("Column")
        lbl_col.setStyleSheet("font-weight: bold; font-size: 10px;")
        lbl_feat = QLabel("X")
        lbl_feat.setStyleSheet("font-weight: bold; color: #4EC9B0; font-size: 10px;")
        lbl_feat.setFixedWidth(25)
        lbl_tgt = QLabel("Y")
        lbl_tgt.setStyleSheet("font-weight: bold; color: #DCDCAA; font-size: 10px;")
        lbl_tgt.setFixedWidth(25)
        header.addWidget(lbl_col)
        header.addWidget(lbl_feat)
        header.addWidget(lbl_tgt)
        self.main_layout.addLayout(header)
        
        # Container for dynamic column rows
        self.cols_container = QWidget()
        self.cols_layout = QVBoxLayout(self.cols_container)
        self.cols_layout.setContentsMargins(0, 0, 0, 0)
        self.cols_layout.setSpacing(1)
        self.main_layout.addWidget(self.cols_container)
        
        # Status
        self.status_lbl = QLabel("Connect CSV Loader")
        self.status_lbl.setStyleSheet("color: #888; font-size: 9px;")
        self.main_layout.addWidget(self.status_lbl)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(180, 240)
        self.proxy.setZValue(1.0)  # Ensure widget is above node body

    def refresh_columns(self):
        df = self.get_input_value(0)
        if df is None or not isinstance(df, pd.DataFrame):
            self.status_lbl.setText("No DataFrame connected!")
            self.status_lbl.setStyleSheet("color: #F44747; font-size: 9px;")
            return
        
        # Start with a copy of the CSV data
        self.merged_df = df.copy()
        
        # Check for optional Model input
        model = self.get_input_value(1)
        if model is not None and hasattr(model, 'predict'):
            try:
                # Get features that the model expects
                if hasattr(model, 'poly_features') and model.poly_features:
                    n_features = model.poly_features.n_features_in_
                    # Use first n numeric columns as features
                    numeric_cols = self.merged_df.select_dtypes(include=[np.number]).columns.tolist()
                    if len(numeric_cols) >= n_features:
                        X = self.merged_df[numeric_cols[:n_features]].values
                        predictions = model.predict(X)
                        # Add prediction as new column
                        self.merged_df['_poly_pred'] = predictions
                        self.status_lbl.setText("✓ Added _poly_pred column")
            except Exception as e:
                self.status_lbl.setText(f"Model err: {str(e)[:15]}")
        
        self.populate_columns(self.merged_df)
        
    def populate_columns(self, df):
        # Clear existing
        for cb in self.feature_checks:
            cb.deleteLater()
        for rb in self.target_radios:
            self.target_group.removeButton(rb)
            rb.deleteLater()
        self.feature_checks.clear()
        self.target_radios.clear()
        
        # Clear layout
        while self.cols_layout.count():
            item = self.cols_layout.takeAt(0)
            if item.layout():
                while item.layout().count():
                    item.layout().takeAt(0)
        
        self.columns = list(df.columns)
        
        # Create row for each column
        for i, col in enumerate(self.columns):
            row = QHBoxLayout()
            row.setSpacing(2)
            
            # Column name (truncated if long), highlight prediction column
            display_name = col[:12] + ".." if len(col) > 14 else col
            lbl = QLabel(display_name)
            if col == '_poly_pred':
                lbl.setStyleSheet("font-size: 10px; color: #CE9178; font-weight: bold;")
            else:
                lbl.setStyleSheet("font-size: 10px;")
            lbl.setToolTip(col)
            row.addWidget(lbl)
            
            # Feature checkbox
            cb = QCheckBox()
            cb.setStyleSheet("margin-left: 5px;")
            cb.setFixedWidth(25)
            row.addWidget(cb)
            self.feature_checks.append(cb)
            
            # Target radio
            rb = QRadioButton()
            rb.setStyleSheet("margin-left: 5px;")
            rb.setFixedWidth(25)
            row.addWidget(rb)
            self.target_group.addButton(rb, i)
            self.target_radios.append(rb)
            
            # Default: last column as target
            if i == len(self.columns) - 1:
                rb.setChecked(True)
            
            self.cols_layout.addLayout(row)
        
        # Adjust node height based on columns
        new_height = 140 + len(self.columns) * 22
        self.height = max(280, new_height)
        self.proxy.resize(180, new_height - 50)
        
        if '_poly_pred' in self.columns:
            self.status_lbl.setText(f"✓ {len(self.columns)} cols (+poly)")
        else:
            self.status_lbl.setText(f"✓ {len(self.columns)} columns")
        self.status_lbl.setStyleSheet("color: #4EC9B0; font-size: 9px;")
        
    def get_features(self):
        features = []
        for i, cb in enumerate(self.feature_checks):
            if cb.isChecked():
                features.append(self.columns[i])
        return features
    
    def get_target(self):
        btn = self.target_group.checkedButton()
        if btn:
            idx = self.target_group.id(btn)
            return self.columns[idx] if idx < len(self.columns) else None
        return None
        
    def eval(self):
        if self.merged_df is None:
            return None
        
        features = self.get_features()
        target = self.get_target()
        
        if not features or not target:
            return None
        
        # Get the sub-model if _poly_pred is selected as a feature
        sub_model = None
        sub_model_input_names = []
        if '_poly_pred' in features:
            model = self.get_input_value(1)
            if model is not None:
                sub_model = model
                sub_model_input_names = getattr(model, 'input_feature_names', [])
        
        # Build list of all original input names needed
        all_input_names = []
        for f in features:
            if f == '_poly_pred' and sub_model_input_names:
                # Replace _poly_pred with the sub-model's inputs
                for name in sub_model_input_names:
                    if name not in all_input_names:
                        all_input_names.append(name)
            else:
                if f not in all_input_names:
                    all_input_names.append(f)
            
        return {
            'X': self.merged_df[features].values,
            'Y': self.merged_df[target].values,
            'feature_names': features,  # What this node uses directly
            'all_input_names': all_input_names,  # All original inputs needed
            'target_name': target,
            'sub_model': sub_model,  # Reference to chained model
            'sub_model_input_names': sub_model_input_names
        }
