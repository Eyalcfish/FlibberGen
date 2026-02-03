from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QHBoxLayout,
                               QLabel, QComboBox, QCheckBox, QPushButton, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QClipboard, QGuiApplication
from node_engine.node_base import Node
import numpy as np

class CodeGeneratorNode(Node):
    def __init__(self):
        super().__init__("Code Generator")
        self.height = 250
        self.width = 280
        
        # Multiple model inputs
        for i in range(4):  # Support up to 4 connected models
            self.add_input(i)
        
        # No outputs (final display)
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Options row
        row = QHBoxLayout()
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Python", "C", "Java"])
        self.lang_combo.setStyleSheet("background: #3c3c3c; color: white;")
        self.lang_combo.currentIndexChanged.connect(self.generate)
        row.addWidget(self.lang_combo)
        
        self.horner_cb = QCheckBox("Horner's")
        self.horner_cb.setStyleSheet("color: white; font-size: 10px;")
        self.horner_cb.stateChanged.connect(self.generate)
        row.addWidget(self.horner_cb)
        layout.addLayout(row)
        
        # Code display
        self.code_edit = QTextEdit()
        self.code_edit.setReadOnly(True)
        self.code_edit.setStyleSheet("""
            QTextEdit {
                background: #1E1E1E;
                color: #D4D4D4;
                font-family: 'Consolas', monospace;
                font-size: 10px;
                border: 1px solid #555;
            }
        """)
        layout.addWidget(self.code_edit)
        
        # Copy button
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 4px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.copy_btn.clicked.connect(self.copy_code)
        layout.addWidget(self.copy_btn)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(260, 210)

    def generate(self):
        models = []
        for i in range(4):
            model = self.get_input_value(i)
            if model is not None:
                models.append(model)
        
        if not models:
            self.code_edit.setText("// Connect model(s) to generate code")
            return
            
        lang = self.lang_combo.currentText()
        use_horner = self.horner_cb.isChecked()
        
        code = self.generate_code(models, lang, use_horner)
        self.code_edit.setText(code)
        
    def generate_code(self, models, lang, use_horner):
        lines = []
        
        # Language-specific syntax
        if lang == "Python":
            func_def = "def predict(x):"
            ret = "return"
            cmt = "#"
        elif lang == "C":
            func_def = "double predict(double x) {"
            ret = "return"
            cmt = "//"
            lines.append(func_def)
        else:  # Java
            func_def = "public static double predict(double x) {"
            ret = "return"
            cmt = "//"
            lines.append(func_def)
            
        if lang == "Python":
            lines.append(func_def)
        
        # Generate if/else for multiple models
        for i, model in enumerate(models):
            indent = "    " if lang == "Python" else "    "
            
            if len(models) > 1 and hasattr(model, 'condition') and model.condition:
                if i == 0:
                    lines.append(f"{indent}if ({model.condition}) {{" if lang != "Python" else f"{indent}if {model.condition}:")
                else:
                    lines.append(f"{indent}}} else {{" if lang != "Python" else f"{indent}else:")
            
            # Generate polynomial expression
            expr = self.poly_to_expr(model, use_horner)
            inner_indent = indent + ("    " if len(models) > 1 else "")
            lines.append(f"{inner_indent}{ret} {expr};")
            
        if lang != "Python" and len(models) > 1:
            lines.append("    }")
        if lang != "Python":
            lines.append("}")
            
        return "\n".join(lines)
    
    def poly_to_expr(self, model, use_horner):
        """Convert model coefficients to expression string"""
        if not hasattr(model, 'coeffs'):
            return "0"
            
        coeffs = model.coeffs if hasattr(model.coeffs, '__iter__') else [model.coeffs]
        intercept = model.intercept if hasattr(model, 'intercept') else 0
        
        if use_horner and len(coeffs) > 1:
            # Horner's method: a0 + x*(a1 + x*(a2 + ...))
            expr = f"{coeffs[-1]:.6f}"
            for c in reversed(coeffs[:-1]):
                expr = f"({c:.6f} + x * {expr})"
            return f"({intercept:.6f} + x * {expr})"
        else:
            # Standard form
            terms = [f"{intercept:.6f}"]
            for i, c in enumerate(coeffs):
                if i == 0:
                    terms.append(f"({c:.6f} * x)")
                else:
                    terms.append(f"({c:.6f} * pow(x, {i+1}))")
            return " + ".join(terms)
    
    def copy_code(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.code_edit.toPlainText())
        
    def eval(self):
        self.generate()
        return None
