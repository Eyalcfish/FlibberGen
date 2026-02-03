from PySide6.QtWidgets import QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog
from PySide6.QtCore import Qt
from node_engine.node_base import Node
from core.data_manager import DataManager
from core.signals import Signals
import pandas as pd

class CSVLoaderNode(Node):
    def __init__(self):
        super().__init__("CSV Loader")
        self.height = 100
        
        # Output: DataFrame
        self.add_output(0)
        
        # Data
        self.df = None
        
        # UI
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.btn = QPushButton("Browse CSV...")
        self.btn.setStyleSheet("""
            QPushButton {
                background: #007ACC;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover { background: #0098FF; }
        """)
        self.btn.clicked.connect(self.browse)
        layout.addWidget(self.btn)
        
        self.lbl = QLabel("No file loaded")
        self.lbl.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self.lbl)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(160, 60)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(None, "Open CSV", "", "CSV (*.csv)")
        if path:
            try:
                self.df = pd.read_csv(path)
                filename = path.split('/')[-1].split('\\')[-1]
                self.lbl.setText(f"✓ {filename}")
                self.lbl.setStyleSheet("color: #4EC9B0; font-size: 10px;")
                # Also update global manager
                DataManager.get().set_dataframe(self.df)
                Signals.get().data_loaded.emit(self.df)
            except Exception as e:
                self.lbl.setText(f"Error: {e}")
                self.lbl.setStyleSheet("color: #F44747; font-size: 10px;")
        
    def eval(self):
        return self.df
