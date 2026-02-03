from PySide6.QtCore import QObject, Signal
import pandas as pd

class Signals(QObject):
    # Data Events
    data_loaded = Signal(pd.DataFrame)
    
    # Node Events
    node_selected = Signal(object)  # Emits the selected Node object
    
    # Global singleton instance
    _instance = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
