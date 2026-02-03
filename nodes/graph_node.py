from PySide6.QtWidgets import (QGraphicsProxyWidget, QWidget, QVBoxLayout, QPushButton, QLabel)
from PySide6.QtCore import Qt
from node_engine.node_base import Node
import numpy as np

# Matplotlib with Qt backend
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class GraphNode(Node):
    def __init__(self):
        super().__init__("Graph View")
        self.height = 320
        self.width = 320
        
        # Inputs: Model and Data
        self.add_input(0)  # Model from PolyFit
        self.add_input(1)  # Data from Column Selector (optional)
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #1E1E1E;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Refresh button
        self.refresh_btn = QPushButton("↻ Refresh Graph")
        self.refresh_btn.setStyleSheet("""
            QPushButton { background: #007ACC; color: white; border: none; padding: 4px; font-size: 10px; }
            QPushButton:hover { background: #0098FF; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_graph)
        layout.addWidget(self.refresh_btn)
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(3, 2.5), dpi=80, facecolor='#1E1E1E')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(280, 200)
        layout.addWidget(self.canvas)
        
        # Status
        self.status_lbl = QLabel("Connect Model + Data")
        self.status_lbl.setStyleSheet("color: #888; font-size: 9px;")
        layout.addWidget(self.status_lbl)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(300, 280)
        
        # Initial empty plot
        self.setup_axes()
        
    def setup_axes(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.set_facecolor('#252526')
        self.ax.tick_params(colors='#888')
        self.ax.spines['bottom'].set_color('#555')
        self.ax.spines['top'].set_color('#555')
        self.ax.spines['left'].set_color('#555')
        self.ax.spines['right'].set_color('#555')
        self.ax.set_xlabel('X', color='#888', fontsize=9)
        self.ax.set_ylabel('Y', color='#888', fontsize=9)
        
    def refresh_graph(self):
        """Pull model and data, render graph"""
        model = self.get_input_value(0)
        data = self.get_input_value(1)
        
        self.setup_axes()
        
        if model is None:
            self.status_lbl.setText("No model connected (input 1)")
            self.status_lbl.setStyleSheet("color: #F44747; font-size: 9px;")
            self.canvas.draw()
            return
        
        # Get data points if available
        X_data = None
        Y_data = None
        if data is not None and isinstance(data, dict):
            X_data = data.get('X')
            Y_data = data.get('Y')
        
        # Plot data points
        if X_data is not None and Y_data is not None:
            # For multi-feature, only plot first feature
            if X_data.ndim > 1:
                x_plot = X_data[:, 0]
            else:
                x_plot = X_data
            
            self.ax.scatter(x_plot, Y_data, c='#4EC9B0', s=20, alpha=0.7, label='Data')
            x_min, x_max = x_plot.min(), x_plot.max()
        else:
            # If no data, use default range
            x_min, x_max = 0, 10
        
        # Plot polynomial curve
        if hasattr(model, 'predict') and hasattr(model, 'poly_features'):
            # Generate smooth curve
            x_line = np.linspace(x_min, x_max, 100)
            
            # Need to match feature dimensions
            n_features = model.poly_features.n_features_in_
            if n_features == 1:
                X_line = x_line.reshape(-1, 1)
            else:
                # For multi-feature, plot slice with other features at 0
                X_line = np.zeros((100, n_features))
                X_line[:, 0] = x_line
            
            try:
                y_line = model.predict(X_line)
                self.ax.plot(x_line, y_line, c='#DCDCAA', linewidth=2, label='Fit')
            except Exception as e:
                self.status_lbl.setText(f"Plot error: {str(e)[:20]}")
        
        # Add legend and metrics
        self.ax.legend(loc='upper left', fontsize=8, facecolor='#252526', edgecolor='#555', labelcolor='white')
        
        if hasattr(model, 'r2') and model.r2 is not None:
            self.ax.set_title(f'R² = {model.r2:.4f}', color='#4EC9B0', fontsize=10)
        
        self.canvas.draw()
        self.status_lbl.setText("✓ Graph updated")
        self.status_lbl.setStyleSheet("color: #4EC9B0; font-size: 9px;")
        
    def eval(self):
        return None
