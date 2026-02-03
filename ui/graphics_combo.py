from PySide6.QtWidgets import QPushButton, QMenu
from PySide6.QtCore import Signal, Qt

class GraphicsComboBox(QPushButton):
    """
    A fake ComboBox implemented as a QPushButton + QMenu.
    This bypasses QGraphicsProxyWidget/QComboBox popup issues entirely
    by using QMenu which is known to work in GraphicsScenes.
    """
    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self._current_index = -1
        
        self.clicked.connect(self.show_menu)
        
        # Style to look like a ComboBox
        self.setStyleSheet("""
            QPushButton {
                background-color: #3C3C3C;
                border: 1px solid #2D2D2D;
                color: #CCCCCC;
                padding: 3px;
                padding-right: 15px; /* Space for arrow */
                text-align: left;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
            }
        """)
        
    def addItems(self, items):
        self.items.extend(items)
        if self._current_index == -1 and items:
            self.setCurrentIndex(0)
            
    def setCurrentIndex(self, index):
        if 0 <= index < len(self.items):
            self._current_index = index
            text = self.items[index]
            self.setText(text + " ▼") # Fake arrow
            self.currentIndexChanged.emit(index)
            self.currentTextChanged.emit(text)
            
    def currentText(self):
        if 0 <= self._current_index < len(self.items):
            return self.items[self._current_index]
        return ""
        
    def currentIndex(self):
        return self._current_index
        
    def show_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #CCCCCC;
                border: 1px solid #333333;
            }
            QMenu::item {
                padding: 4px 20px 4px 10px;
            }
            QMenu::item:selected {
                background-color: #007ACC;
                color: white;
            }
        """)
        
        for i, item_text in enumerate(self.items):
            action = menu.addAction(item_text)
            # Use default arguments to capture loop variable 'i'
            action.triggered.connect(lambda checked=False, idx=i: self.setCurrentIndex(idx))
            
        # Show below the button
        pos = self.mapToGlobal(self.rect().bottomLeft())
        menu.exec(pos)
