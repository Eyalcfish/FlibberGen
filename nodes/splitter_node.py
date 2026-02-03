from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QLineEdit)
from PySide6.QtCore import Qt
from node_engine.node_base import Node
from core.signals import Signals
import numpy as np

class ConditionalSplitterNode(Node):
    def __init__(self):
        super().__init__("Conditional Splitter")
        self.height = 140
        self.width = 220
        
        # Input: Data (X, Y)
        self.add_input(0)
        # Outputs: True stream, False stream
        self.add_output(0)  # True
        self.add_output(1)  # False
        
        self.signals = Signals.get()
        self.signals.data_loaded.connect(self.on_data_loaded)
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Column selector
        self.col_combo = QComboBox()
        self.col_combo.setStyleSheet("background: #3c3c3c; color: white; border: 1px solid #555;")
        layout.addWidget(self.col_combo)
        
        # Operator + Value row
        row = QHBoxLayout()
        self.op_combo = QComboBox()
        self.op_combo.addItems([">", "<", ">=", "<=", "==", "!="])
        self.op_combo.setStyleSheet("background: #3c3c3c; color: white; border: 1px solid #555;")
        row.addWidget(self.op_combo)
        
        self.val_input = QLineEdit("0")
        self.val_input.setStyleSheet("background: #3c3c3c; color: white; border: 1px solid #555; padding: 2px;")
        row.addWidget(self.val_input)
        layout.addLayout(row)
        
        # Output labels
        lbl_true = QLabel("→ True (green)")
        lbl_true.setStyleSheet("color: #4EC9B0; font-size: 9px;")
        layout.addWidget(lbl_true)
        
        lbl_false = QLabel("→ False (red)")
        lbl_false.setStyleSheet("color: #F44747; font-size: 9px;")
        layout.addWidget(lbl_false)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(200, 100)

    def on_data_loaded(self, df):
        self.col_combo.clear()
        if df is not None:
            self.col_combo.addItems(list(df.columns))
        
    def eval(self, output_index=0):
        data = self.get_input_value(0)
        if data is None or not isinstance(data, dict):
            return None
            
        X, Y = data.get('X'), data.get('Y')
        feature_names = data.get('feature_names', [])
        
        col = self.col_combo.currentText()
        op = self.op_combo.currentText()
        try:
            val = float(self.val_input.text())
        except:
            return None
        
        # Find column index
        if col in feature_names:
            col_idx = feature_names.index(col)
            col_data = X[:, col_idx] if X.ndim > 1 else X
        else:
            return None
        
        # Apply condition
        ops = {'>': np.greater, '<': np.less, '>=': np.greater_equal, 
               '<=': np.less_equal, '==': np.equal, '!=': np.not_equal}
        mask = ops[op](col_data, val)
        
        if output_index == 0:  # True stream
            return {'X': X[mask], 'Y': Y[mask], 'feature_names': feature_names,
                    'condition': f"{col} {op} {val}"}
        else:  # False stream
            return {'X': X[~mask], 'Y': Y[~mask], 'feature_names': feature_names,
                    'condition': f"NOT ({col} {op} {val})"}
