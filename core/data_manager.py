import pandas as pd
from typing import Optional

class DataManager:
    _instance = None
    
    def __init__(self):
        self._df: Optional[pd.DataFrame] = None
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_dataframe(self, df: pd.DataFrame):
        self._df = df
        
    def get_dataframe(self) -> Optional[pd.DataFrame]:
        return self._df
