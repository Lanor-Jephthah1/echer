import sys
import io
from PyQt6.QtWidgets import QApplication
from core.ui.main_window import JarvisOverlay

# Force console outputs to support UTF-8 (prevents crashes with special block chars like █)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    overlay = JarvisOverlay()
    sys.exit(app.exec())
