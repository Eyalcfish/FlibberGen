import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QDockWidget, QFileDialog
from PySide6.QtCore import Qt

from node_engine.scene import NodeScene
from node_engine.view import NodeView
from ui.styles import VSCodeStyle
from ui.dock_widgets import CSVLoaderWidget, CodePreviewWidget, MetricsWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FlibberGen | Node-Based Poly Tool")
        self.resize(1280, 800)
        
        # Style
        self.setStyle()
        
        # Center: Node Editor
        self.scene = NodeScene()
        self.view = NodeView(self.scene)
        self.setCentralWidget(self.view)
        
        # Left Dock: Data
        self.dock_data = QDockWidget("Data Source", self)
        self.dock_data.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_data.setWidget(CSVLoaderWidget())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_data)
        
        # Right Dock: Code
        self.dock_code = QDockWidget("Generated Code (Horner)", self)
        self.dock_code.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_code.setWidget(CodePreviewWidget())
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_code)
        
        # Bottom Dock: Metrics
        self.dock_metrics = QDockWidget("Test Console & Metrics", self)
        self.dock_metrics.setAllowedAreas(Qt.AllDockWidgetAreas)
        self.dock_metrics.setWidget(MetricsWidget())
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_metrics)
        
        # Dock capabilities
        self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)

        # Menu
        self.createMenu()
        
        # Toolbar
        self.createToolbar()

    def createMenu(self):
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Save Profile...", self.save_profile)
        file_menu.addAction("Load Profile...", self.load_profile)
        
        view_menu = menubar.addMenu("View")
        
        # Add actions to toggle docks
        view_menu.addAction(self.dock_data.toggleViewAction())
        view_menu.addAction(self.dock_code.toggleViewAction())
        view_menu.addAction(self.dock_metrics.toggleViewAction())

    def save_profile(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON (*.json)")
        if filename:
            import json
            data = self.scene.serialize()
            try:
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error saving: {e}")

    def load_profile(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Load Profile", "", "JSON (*.json)")
        if filename:
            import json
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)
                self.scene.deserialize(data, self.view.create_node)
            except Exception as e:
                print(f"Error loading: {e}")

    def createToolbar(self):
        toolbar = self.addToolBar("Nodes")
        # Entry
        toolbar.addAction("CSV Loader", lambda: self.view.add_node("CSV Loader"))
        toolbar.addAction("Col Select", lambda: self.view.add_node("Column Selector"))
        toolbar.addSeparator()
        # Logic
        toolbar.addAction("Splitter", lambda: self.view.add_node("Conditional Splitter"))
        toolbar.addAction("Range", lambda: self.view.add_node("Range Filter"))
        toolbar.addSeparator()
        # Math
        toolbar.addAction("PolyFit", lambda: self.view.add_node("PolyFit"))
        toolbar.addAction("Neural Net", lambda: self.view.add_node("Neural Network"))
        toolbar.addAction("Manual", lambda: self.view.add_node("Manual Coeffs"))
        toolbar.addSeparator()
        # Output
        toolbar.addAction("Code Gen", lambda: self.view.add_node("Code Generator"))
        toolbar.addAction("Inspector", lambda: self.view.add_node("Inspector"))
        toolbar.addAction("Tester", lambda: self.view.add_node("Live Tester"))
        toolbar.addAction("Graph", lambda: self.view.add_node("Graph View"))


    def setStyle(self):
        palette = VSCodeStyle.get_palette()
        self.setPalette(palette)
        QApplication.instance().setPalette(palette)
        self.setStyleSheet(VSCodeStyle.get_stylesheet())

def main():
    # Handle High DPI
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()