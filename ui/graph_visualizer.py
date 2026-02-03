import numpy as np
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QComboBox, QSlider, QWidget, QScrollArea)
from PySide6.QtCore import Qt
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar

class GraphSlicerDialog(QDialog):
    def __init__(self, model, data=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multivariate Graph Slicer")
        self.resize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        self.model = model
        self.data = data
        
        # Analyze model to get feature info
        self.features = self._get_feature_names()
        self.n_features = len(self.features)
        
        # Determine ranges for each feature
        self.ranges = self._calculate_ranges()
        
        # State: which feature is on X axis
        self.x_axis_idx = 0 
        # State: discrete values for all features (sliders)
        # Initialize to mean of range
        self.current_values = [(r[0] + r[1])/2 for r in self.ranges]
        
        self._init_ui()
        self._update_plot()
        
    def _get_feature_names(self):
        # Try to get names from model metadata (PolyFitNode provides these)
        names = getattr(self.model, 'all_input_names', []) or getattr(self.model, 'input_feature_names', [])
        
        # If missing, try sklearn poly attributes
        if not names and hasattr(self.model, 'poly_features'):
             n = self.model.poly_features.n_features_in_
             names = [f"x{i+1}" for i in range(n)]
             
        # Fallback
        if not names:
            names = ["x"]
            
        return names
        
    def _calculate_ranges(self):
        ranges = [] # List of (min, max)
        
        # If we have real data, use its bounds
        X_data = None
        if self.data and 'X' in self.data:
            X_data = self.data['X']
            
        for i in range(self.n_features):
            if X_data is not None and i < X_data.shape[1]:
                col_data = X_data[:, i]
                d_min, d_max = col_data.min(), col_data.max()
                # Add padding
                pad = (d_max - d_min) * 0.1 if d_max != d_min else 1.0
                ranges.append((d_min - pad, d_max + pad))
            else:
                # Default range
                ranges.append((-10.0, 10.0))
        return ranges

    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Top Controls
        top_layout = QHBoxLayout()
        
        # X-Axis Selector
        top_layout.addWidget(QLabel("Horizontal Axis:"))
        self.xaxis_combo = QComboBox()
        self.xaxis_combo.addItems(self.features)
        self.xaxis_combo.currentIndexChanged.connect(self._on_axis_changed)
        top_layout.addWidget(self.xaxis_combo)
        
        top_layout.addStretch()
        layout.addLayout(top_layout)
        
        # Main Split: Canvas (Left/Center) vs Sliders (Right)
        content_layout = QHBoxLayout()
        
        # 1. Matplotlib Canvas
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        self.figure = Figure(facecolor='#1E1E1E')
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        content_layout.addWidget(plot_container, stretch=2)
        
        # 2. Sliders Panel
        sliders_container = QWidget()
        self.sliders_layout = QVBoxLayout(sliders_container)
        self.sliders_layout.setContentsMargins(0,0,0,0)
        
        lbl = QLabel("Variable Slices (Fixed Values):")
        lbl.setStyleSheet("font-weight: bold; font-size: 12px; margin-bottom: 10px;")
        self.sliders_layout.addWidget(lbl)
        
        # Scroll area for sliders in case of many variables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(sliders_container)
        scroll.setFixedWidth(250)
        
        self.slider_widgets = [] # Keep track to update visibility
        
        for i, name in enumerate(self.features):
            w = QWidget()
            row = QVBoxLayout(w)
            row.setContentsMargins(0,5,0,5)
            
            # Label with value
            head_row = QHBoxLayout()
            head_row.addWidget(QLabel(f"{name}:"))
            val_lbl = QLabel(f"{self.current_values[i]:.2f}")
            val_lbl.setStyleSheet("color: #4EC9B0; font-weight: bold;")
            head_row.addWidget(val_lbl)
            row.addLayout(head_row)
            
            # Slider
            slider = QSlider(Qt.Horizontal)
            slider.setRange(0, 1000)
            slider.setValue(500) # Center
            
            # Store metadata on the slider
            slider.idx = i
            slider.val_label = val_lbl
            
            slider.valueChanged.connect(lambda val, s=slider: self._on_slider_change(s, val))
            row.addWidget(slider)
            
            self.sliders_layout.addWidget(w)
            self.slider_widgets.append(w)
            
        
        # Tolerance Slider
        tol_container = QWidget()
        tol_layout = QVBoxLayout(tol_container)
        tol_layout.setContentsMargins(0, 10, 0, 10)
        
        row = QHBoxLayout()
        row.addWidget(QLabel("Slice Width (Tolerance):"))
        self.tol_val_lbl = QLabel("1.0")
        self.tol_val_lbl.setStyleSheet("color: #4EC9B0; font-weight: bold;")
        row.addWidget(self.tol_val_lbl)
        tol_layout.addLayout(row)
        
        self.tol_slider = QSlider(Qt.Horizontal)
        self.tol_slider.setRange(0, 100) # 0 to 10.0
        self.tol_slider.setValue(10) # Default 1.0
        self.tol_slider.valueChanged.connect(self._on_tol_change)
        tol_layout.addWidget(self.tol_slider)
        
        self.sliders_layout.addWidget(tol_container)

        self.sliders_layout.addStretch()
        content_layout.addWidget(scroll)
        
        layout.addLayout(content_layout)
        
        self.xaxis_combo.setCurrentIndex(0)
        self._update_slider_visibility()

    def _on_tol_change(self, val):
        real_val = val / 10.0
        self.tol_val_lbl.setText(f"{real_val:.1f}")
        self._update_plot()

    def _update_slider_visibility(self):
        # Hide the slider for the currently selected X-axis
        for i, w in enumerate(self.slider_widgets):
            if i == self.x_axis_idx:
                w.setVisible(False)
            else:
                w.setVisible(True)

    def _on_axis_changed(self, index):
        self.x_axis_idx = index
        self._update_slider_visibility()
        self._update_plot()
        
    def _on_slider_change(self, slider_obj, int_val):
        idx = slider_obj.idx
        # Map 0-1000 to min-max
        r_min, r_max = self.ranges[idx]
        val = r_min + (int_val / 1000.0) * (r_max - r_min)
        
        self.current_values[idx] = val
        slider_obj.val_label.setText(f"{val:.2f}")
        self._update_plot()

    def _update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#252526')
        ax.tick_params(colors='#AAAAAA')
        for spine in ax.spines.values():
            spine.set_color('#555555')
            
        # 1. Plot the Model Curve (Slice)
        idx_main = self.x_axis_idx
        r_min, r_max = self.ranges[idx_main]
        x_steps = np.linspace(r_min, r_max, 200)
        
        X_pred = np.zeros((200, self.n_features))
        for i in range(self.n_features):
            X_pred[:, i] = self.current_values[i]
        X_pred[:, idx_main] = x_steps
        
        try:
            if hasattr(self.model, 'predict'):
                y_pred = self.model.predict(X_pred)
                ax.plot(x_steps, y_pred, color='#DCDCAA', linewidth=2, label='Model Slice')
        except Exception as e:
            ax.text(0.5, 0.5, f"Prediction Error: {e}", color='red')
            
        # 2. Plot Real Data (Filtered by Slice)
        if self.data and 'X' in self.data and 'Y' in self.data:
            X_real = self.data['X']
            Y_real = self.data['Y']
            
            # Filter condition: Keep points where ALL non-active dimensions are within tolerance
            tolerance = self.tol_slider.value() / 10.0
            mask = np.ones(len(X_real), dtype=bool)
            
            if X_real.ndim > 1:
                for i in range(self.n_features):
                    if i == idx_main: continue 
                    # Use provided ranges for scale-independent tolerance?
                    # For now using absolute tolerance as requested: "if its(2,2) and my x=1 [don't show]"
                    dist = np.abs(X_real[:, i] - self.current_values[i])
                    mask = mask & (dist <= tolerance)
                
                x_real_filtered = X_real[mask, idx_main]
                y_real_filtered = Y_real[mask]
                
                # Show ghost points (faded) for context? User asked for filtering.
                # Let's just show filtered points clearly.
                ax.scatter(x_real_filtered, y_real_filtered, color='#4EC9B0', s=25, alpha=0.9, label='Nearby Data')
                
                # Show stats about filtering
                total_pts = len(X_real)
                shown_pts = len(x_real_filtered)
                self.setWindowTitle(f"Multivariate Graph Slicer - Showing {shown_pts}/{total_pts} points (Tol={tolerance:.1f})")
            else:
                # 1D case, show all
                ax.scatter(X_real, Y_real, color='#4EC9B0', s=20, alpha=0.7, label='Data')
            
        feat_name = self.features[idx_main]
        ax.set_xlabel(f"{feat_name} (Variable)", color='#CCCCCC')
        ax.set_ylabel("Output", color='#CCCCCC')
        
        title = f"Model Slice: {feat_name} vs Output"
        if self.n_features > 1:
            title += f"\nNon-axis vars within ±{tolerance:.1f} of slider"
            
        ax.set_title(title, color='#CCCCCC', fontsize=9)
        ax.legend()
        ax.grid(True, color='#444444', linestyle='--')
        
        self.canvas.draw()
