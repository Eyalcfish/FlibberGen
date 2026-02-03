from PySide6.QtWidgets import QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QGraphicsItem
from PySide6.QtCore import Qt
from node_engine.node_base import Node
from core.data_manager import DataManager
from core.signals import Signals
import pandas as pd

class InputNode(Node):
    def __init__(self):
        super().__init__("Input Column")
        self.height = 150  # Taller to fit list
        
        # Output only
        self.add_output(0)
        
        # Data
        self.dm = DataManager.get()
        self.signals = Signals.get()
        self.signals.data_loaded.connect(self.on_data_loaded)
        
        # UI inside Node - using QListWidget instead of QComboBox
        self.proxy = QGraphicsProxyWidget(self)
        self.widget = QWidget()
        self.widget.setStyleSheet("background: #2d2d2d; color: white;")
        
        layout = QVBoxLayout(self.widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        self.lbl = QLabel("Select Column:")
        self.lbl.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: #3c3c3c;
                color: white;
                border: 1px solid #555;
            }
            QListWidget::item:selected {
                background: #007ACC;
            }
            QListWidget::item:hover {
                background: #4a4a4a;
            }
        """)
        self.list_widget.setMaximumHeight(80)
        self.list_widget.currentItemChanged.connect(self.on_change)
        layout.addWidget(self.list_widget)
        
        self.proxy.setWidget(self.widget)
        self.proxy.setPos(10, 30)
        self.proxy.resize(160, 110)
        
        # Populate if data exists
        self.on_data_loaded(self.dm.get_dataframe())

    def on_data_loaded(self, df):
        self.list_widget.clear()
        if df is not None:
            for col in df.columns:
                self.list_widget.addItem(QListWidgetItem(col))
            self.lbl.setText(f"Select ({len(df.columns)} cols):")
            if self.list_widget.count() > 0:
                self.list_widget.setCurrentRow(0)
        else:
            self.lbl.setText("Load CSV first...")
            
    def on_change(self, current, previous):
        pass  # Selection changed
        
    def eval(self):
        df = self.dm.get_dataframe()
        if df is not None:
            item = self.list_widget.currentItem()
            if item:
                col = item.text()
                if col in df.columns:
                    return df[col].values
        return None
