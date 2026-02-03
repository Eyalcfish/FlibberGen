from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QLabel, QPushButton, QFileDialog
from core.signals import Signals
from core.data_manager import DataManager
from nodes.polyfit_node import PolyFitNode, PolyFitModel
import pandas as pd

class CodePreviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.editor = QTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setStyleSheet("font-family: Consolas; font-size: 12px; border: none;")
        layout.addWidget(self.editor)
        
        # Connect
        Signals.get().node_selected.connect(self.on_node_selected)
        
    def on_node_selected(self, node):
        if isinstance(node, PolyFitNode):
            # Evaluate to get the model
            model = node.eval() 
            if isinstance(model, PolyFitModel):
                code = self.generate_code(model)
                self.editor.setText(code)
            else:
                self.editor.setText("// Please connect inputs and calculate first.")
        else:
             self.editor.setText("// Select a PolyFit Node to see generated code.")

    def generate_code(self, model):
        # Get input names
        input_names = getattr(model, 'all_input_names', None) or getattr(model, 'input_feature_names', None)
        if not input_names and hasattr(model, 'poly_features'):
             n_features = model.poly_features.n_features_in_
             input_names = [f"x{i+1}" for i in range(n_features)]
        if not input_names:
            input_names = ["x"]

        # Python function definition
        safe_names = []
        for name in input_names:
            safe = "".join(c for c in name if c.isalnum() or c == '_')
            if not safe or safe[0].isdigit(): safe = "v_" + safe
            safe_names.append(safe)
            
        lines = [f"def predict({', '.join(safe_names)}):"]
        lines.append(f"    # Degree: {model.degree}")
        lines.append(f"    # R2: {model.r2:.4f}")
        
        coeffs = model.coeffs
        intercept = getattr(model, 'intercept', 0)
        
        # Check for multivariate
        powers = None
        if hasattr(model, 'poly_features') and hasattr(model.poly_features, 'powers_'):
            powers = model.poly_features.powers_
            
        if powers is None or len(input_names) == 1:
            # Univariate Horner
            coeffs_list = coeffs.tolist() if hasattr(coeffs, 'tolist') else list(coeffs)
            x_var = safe_names[0]
            
            if len(coeffs_list) > 1:
                expr = f"{coeffs_list[-1]:.6f}"
                for c in reversed(coeffs_list[:-1]):
                    expr = f"({c:.6f} + {x_var} * {expr})"
                lines.append(f"    return {intercept:.6f} + {x_var} * {expr}")
            else:
                lines.append(f"    return {intercept:.6f} + {coeffs_list[0]:.6f} * {x_var}")
        else:
            # Multivariate Standard
            terms = [f"{intercept:.6f}"]
            for i, c in enumerate(coeffs):
                if abs(c) < 1e-9: continue
                
                term_parts = []
                if i < len(powers):
                    p_row = powers[i]
                    for feat_idx, p in enumerate(p_row):
                        if p == 0: continue
                        var_name = safe_names[feat_idx] if feat_idx < len(safe_names) else f"x{feat_idx}"
                        if p == 1:
                            term_parts.append(var_name)
                        else:
                            term_parts.append(f"{var_name}**{p}")
                
                if term_parts:
                    terms.append(f"({c:.6f} * {' * '.join(term_parts)})")
                else:
                    terms.append(f"{c:.6f}")
                    
            lines.append(f"    return {' + '.join(terms)}")
        
        return "\n".join(lines)


class CSVLoaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        self.btn = QPushButton("Load CSV")
        self.btn.clicked.connect(self.load_csv)
        layout.addWidget(self.btn)
        
        self.lbl = QLabel("No file loaded")
        layout.addWidget(self.lbl)
        
        # Preview Table
        from PySide6.QtWidgets import QTableView, QHeaderView
        from PySide6.QtCore import QAbstractTableModel
        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("border: 1px solid #444;")
        layout.addWidget(self.table)
        
        layout.addStretch()
        
    def load_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV (*.csv)")
        if path:
            try:
                df = pd.read_csv(path)
                DataManager.get().set_dataframe(df)
                Signals.get().data_loaded.emit(df)
                self.lbl.setText(path.split('/')[-1])
                
                # Update Table Model
                self.model = DataFrameModel(df.head(50)) # Preview top 50
                self.table.setModel(self.model)
            except Exception as e:
                self.lbl.setText(f"Error: {e}")

from PySide6.QtCore import QAbstractTableModel, Qt
class DataFrameModel(QAbstractTableModel):
    def __init__(self, df):
        super().__init__()
        self._df = df
        
    def rowCount(self, parent=None):
        return self._df.shape[0]
        
    def columnCount(self, parent=None):
        return self._df.shape[1]
        
    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        return None
        
    def headerData(self, col, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._df.columns[col]
        return None

class MetricsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.lbl_r2 = QLabel("R²: --")
        self.lbl_mse = QLabel("MSE: --")
        layout.addWidget(self.lbl_r2)
        layout.addWidget(self.lbl_mse)
        layout.addStretch()
        
        Signals.get().node_selected.connect(self.update)
        
    def update(self, node):
        if isinstance(node, PolyFitNode):
            model = node.eval()
            if isinstance(model, PolyFitModel):
                self.lbl_r2.setText(f"R²: {model.r2:.5f}")
                self.lbl_mse.setText(f"MSE: {model.mse:.5f}")
