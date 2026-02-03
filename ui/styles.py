from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

class VSCodeStyle:
    BG_MAIN = "#1E1E1E"
    BG_SIDEBAR = "#252526"
    BG_ACTIVITY_BAR = "#333333"
    BG_INPUT = "#3C3C3C"
    BORDER = "#2D2D2D"
    ACCENT = "#007ACC"
    TEXT_MAIN = "#CCCCCC"
    
    @staticmethod
    def get_palette():
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(VSCodeStyle.BG_MAIN))
        palette.setColor(QPalette.WindowText, QColor(VSCodeStyle.TEXT_MAIN))
        palette.setColor(QPalette.Base, QColor(VSCodeStyle.BG_INPUT))
        palette.setColor(QPalette.AlternateBase, QColor(VSCodeStyle.BG_SIDEBAR))
        palette.setColor(QPalette.ToolTipBase, QColor(VSCodeStyle.BG_SIDEBAR))
        palette.setColor(QPalette.ToolTipText, QColor(VSCodeStyle.TEXT_MAIN))
        palette.setColor(QPalette.Text, QColor(VSCodeStyle.TEXT_MAIN))
        palette.setColor(QPalette.Button, QColor(VSCodeStyle.BG_INPUT))
        palette.setColor(QPalette.ButtonText, QColor(VSCodeStyle.TEXT_MAIN))
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(VSCodeStyle.ACCENT))
        palette.setColor(QPalette.Highlight, QColor(VSCodeStyle.ACCENT))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        return palette
        
    @staticmethod
    def get_stylesheet():
        return f"""
        QMainWindow {{
            background-color: {VSCodeStyle.BG_MAIN};
        }}
        QDockWidget {{
            titlebar-close-icon: url(close.png);
            titlebar-normal-icon: url(undock.png);
        }}
        QDockWidget::title {{
            text-align: left;
            background: {VSCodeStyle.BG_SIDEBAR};
            padding-left: 5px;
            padding-top: 4px; 
            padding-bottom: 4px;
        }}
        /* Splitters */
        QSplitter::handle {{
            background: {VSCodeStyle.BG_MAIN};
        }}
        
        /* Inputs */
        QLineEdit, QComboBox, QDoubleSpinBox {{
            background-color: {VSCodeStyle.BG_INPUT};
            border: 1px solid {VSCodeStyle.BORDER};
            color: {VSCodeStyle.TEXT_MAIN};
            padding: 3px;
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {VSCodeStyle.BG_INPUT};
            border: 1px solid {VSCodeStyle.BG_MAIN};
            color: {VSCodeStyle.TEXT_MAIN};
            padding: 5px;
        }}
        QPushButton:hover {{
            background-color: #4C4C4C;
        }}
        
        /* Graphics View */
        QGraphicsView {{
            border: none;
            background: {VSCodeStyle.BG_MAIN};
        }}
        """
