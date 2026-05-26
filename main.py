import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import PyRomHackApp

def main():
    app = QApplication(sys.argv)
    
    # Definir ícone global e outras configs se necessário
    app.setApplicationName("pyROMHACK")
    app.setApplicationVersion("1.0.0")
    
    window = PyRomHackApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
