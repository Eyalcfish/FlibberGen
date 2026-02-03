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
                code = self.generate_horner(model)
                self.editor.setText(code)
            else:
                self.editor.setText("// Please connect inputs and calculate first.")
        else:
             self.editor.setText("// Select a PolyFit Node to see generated code.")

    def generate_horner(self, model):
        # Generate Horner's form code from PolyFitModel
        lines = ["def predict(x):"]
        lines.append(f"    # Degree: {model.degree}")
        lines.append(f"    # R2: {model.r2:.4f}")
        
        # Get coefficients
        coeffs = model.coeffs
        intercept = model.intercept
        
        if coeffs is None or len(coeffs) == 0:
            lines.append("    return 0  # No coefficients")
        else:
            # Build Horner's nested form
            # P(x) = intercept + c0*x + c1*x^2 + ... = intercept + x*(c0 + x*(c1 + ...))
            coef_list = coeffs.tolist() if hasattr(coeffs, 'tolist') else list(coeffs)
            
            if len(coef_list) == 1:
                lines.append(f"    return {intercept:.6f} + {coef_list[0]:.6f} * x")
            else:
                # Build from innermost out
                expr = f"{coef_list[-1]:.6f}"
                for c in reversed(coef_list[:-1]):
                    expr = f"({c:.6f} + x * {expr})"
                lines.append(f"    return {intercept:.6f} + x * {expr}")
        
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
