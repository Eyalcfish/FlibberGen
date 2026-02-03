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
        
        # Determine inputs from the first model (assuming consistent inputs if multiple models)
        if not models:
            return "// No models"
            
        model = models[0]
        input_names = getattr(model, 'all_input_names', None) or getattr(model, 'input_feature_names', None)
        
        if not input_names and hasattr(model, 'poly_features'):
             n_features = model.poly_features.n_features_in_
             input_names = [f"x{i+1}" for i in range(n_features)]
             
        if not input_names:
            input_names = ["x"]
            
        # Sanitize names for code (simple alphanumeric)
        safe_names = []
        for name in input_names:
            safe = "".join(c for c in name if c.isalnum() or c == '_')
            if not safe or safe[0].isdigit():
                safe = "v_" + safe
            safe_names.append(safe)
            
        # Generate function signature
        args_str = ""
        if lang == "Python":
            args_str = ", ".join(safe_names)
            func_def = f"def predict({args_str}):"
            ret = "return"
        elif lang == "C":
            args_str = ", ".join([f"double {n}" for n in safe_names])
            func_def = f"double predict({args_str}) {{"
            ret = "return"
        else:  # Java
            args_str = ", ".join([f"double {n}" for n in safe_names])
            func_def = f"public static double predict({args_str}) {{"
            ret = "return"
            
        lines.append(func_def)
        
        # Generate if/else for multiple models
        for i, model in enumerate(models):
            indent = "    "
            
            if len(models) > 1 and hasattr(model, 'condition') and model.condition:
                cond = str(model.condition) 
                # Basic replacements for condition syntax if needed
                if i == 0:
                    lines.append(f"{indent}if ({cond}) {{" if lang != "Python" else f"{indent}if {cond}:")
                else:
                    lines.append(f"{indent}}} else {{" if lang != "Python" else f"{indent}else:")
            
            # Generate polynomial expression
            expr = self.poly_to_expr(model, safe_names, use_horner, lang)
            inner_indent = indent + ("    " if len(models) > 1 else "")
            lines.append(f"{inner_indent}{ret} {expr};")
            
        if lang != "Python" and len(models) > 1:
            lines.append("    }")
        if lang != "Python":
            lines.append("}")
            
        return "\n".join(lines)
    
    def poly_to_expr(self, model, input_names, use_horner, lang):
        """Convert model coefficients to expression string handling multivariate"""
        if not hasattr(model, 'coeffs'):
            return "0"
            
        coeffs = model.coeffs
        intercept = getattr(model, 'intercept', 0)
        
        # Check if we have powers_ for multivariate
        powers = None
        if hasattr(model, 'poly_features') and hasattr(model.poly_features, 'powers_'):
            powers = model.poly_features.powers_
            
        # Fallback to univariate if no powers or only 1 feature
        if powers is None or (len(input_names) == 1 and use_horner):
            # Univariate Horner / Standard
            coeffs_list = coeffs.tolist() if hasattr(coeffs, 'tolist') else list(coeffs)
            x_var = input_names[0]
            
            if use_horner and len(coeffs_list) > 1:
                expr = f"{coeffs_list[-1]:.6f}"
                for c in reversed(coeffs_list[:-1]):
                    expr = f"({c:.6f} + {x_var} * {expr})"
                return f"({intercept:.6f} + {x_var} * {expr})"
            else:
                terms = [f"{intercept:.6f}"]
                for i, c in enumerate(coeffs_list):
                    if abs(c) < 1e-9: continue
                    pow_func = f"pow({x_var}, {i+1})" if lang != "Python" else f"{x_var}**{i+1}"
                    if i == 0: pow_func = x_var # Optimization for x^1
                    terms.append(f"({c:.6f} * {pow_func})")
                return " + ".join(terms) if terms else "0"
        
        # Multivariate Standard Form (Horner is hard for multivariate)
        terms = [f"{intercept:.6f}"]
        
        for i, c in enumerate(coeffs):
            if abs(c) < 1e-9: continue
            
            term_parts = []
            if powers is not None and i < len(powers):
                p_row = powers[i]
                for feat_idx, p in enumerate(p_row):
                    if p == 0: continue
                    var_name = input_names[feat_idx] if feat_idx < len(input_names) else f"x{feat_idx}"
                    
                    if p == 1:
                        term_parts.append(var_name)
                    else:
                        pow_str = f"pow({var_name}, {p})" if lang != "Python" else f"{var_name}**{p}"
                        term_parts.append(pow_str)
            
            if term_parts:
                term_expr = " * ".join(term_parts)
                terms.append(f"({c:.6f} * {term_expr})")
            else:
                 # Constant term (shouldn't happen in coefs usually if include_bias=False)
                 terms.append(f"{c:.6f}")
                 
        return " + ".join(terms)
    
    def copy_code(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.code_edit.toPlainText())
        
    def eval(self):
        self.generate()
        return None
