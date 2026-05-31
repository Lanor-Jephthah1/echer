import sys
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QLabel, QPushButton, QSizeGrip, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QTextCursor, QColor, QTextBlockFormat
from pynput import keyboard
import threading

from core.vision.screen_capture import ScreenPerceptionEngine
from core.vision.ocr_parser import OCRParser
from core.ai.llm_controller import LLMController

class HistoryLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history = []
        self.history_index = -1
        self.temp_text = ""

    def add_to_history(self, text):
        if text and (not self.history or self.history[-1] != text):
            self.history.append(text)
        self.history_index = len(self.history)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Up:
            if self.history:
                if self.history_index == len(self.history):
                    self.temp_text = self.text()
                if self.history_index > 0:
                    self.history_index -= 1
                    self.setText(self.history[self.history_index])
            event.accept()
        elif event.key() == Qt.Key.Key_Down:
            if self.history:
                if self.history_index < len(self.history) - 1:
                    self.history_index += 1
                    self.setText(self.history[self.history_index])
                elif self.history_index == len(self.history) - 1:
                    self.history_index += 1
                    self.setText(self.temp_text)
            event.accept()
        else:
            super().keyPressEvent(event)

class AITaskThread(QThread):
    status_signal = pyqtSignal(str)
    stream_signal = pyqtSignal(str)

    def __init__(self, query, img_path, active_window_title=None):
        super().__init__()
        self.query = query
        self.img_path = img_path
        self.active_window_title = active_window_title

    def run(self):
        try:
            self.status_signal.emit("Echer-System:\\> Running offline OCR...")
            ocr = OCRParser()
            text = ocr.extract_text(self.img_path)
            
            self.status_signal.emit("Echer-System:\\> Querying local Ollama LLM...")
            llm = LLMController()
            is_loaded, msg = llm.load_model()
            if not is_loaded:
                self.status_signal.emit(f"Echer-Error:\\> {msg}")
                return
                
            app_context = ""
            if self.active_window_title:
                app_context = f"The user is currently working inside the application window titled: '{self.active_window_title}'.\n"
                
            prompt = f"The user asks: {self.query}\n\n{app_context}Here is the raw text currently visible on their screen: {text}\n\nBased on this screen context, answer the user's question directly. Adjust your detail dynamically: if they ask for a detailed, thorough, or step-by-step explanation, be extremely detailed and comprehensive; if they ask for a brief, quick, or concise answer, be extremely concise. Otherwise, provide a balanced, natural, and helpful answer."
            
            self.status_signal.emit("\nEcher:\\> ")
            for chunk in llm.generate_stream(prompt, max_tokens=1024):
                self.stream_signal.emit(chunk)
        except Exception as e:
            self.status_signal.emit(f"Echer-Error:\\> {str(e)}")
class JarvisOverlay(QWidget):
    toggle_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.previously_active_window_info = None
        self.toggle_signal.connect(self.safe_toggle_visibility)
        self.initUI()
        self.setup_hotkey()
        
        # Pre-warm the OCR engine on startup in a silent background thread
        # This completely eliminates the 5-7 second disk-load time on the first query!
        threading.Thread(target=OCRParser, daemon=True).start()

    def initUI(self):
        # Frameless, stay on top (allow taskbar icon so minimizing works normally)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Initial size in Idle State (compact search bar + shadow margins)
        self.resize(730, 150)
        
        # Center on screen
        screen_geometry = self.screen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = int(screen_geometry.height() * 0.2) # 20% down from top
        self.move(x, y)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15) # 15px bleed room for the drop shadow glow
        
        # Main container for rounded corners and styling
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(15, 20, 31, 215); /* Sleek, less transparent luxurious iOS frosted glass */
                border-radius: 28px; /* Ultra-rounded organic corners */
                border: 1.5px solid rgba(255, 255, 255, 30); /* Frosted glass bubble edge */
            }
        """)
        
        # Soft ambient aura backlight shadow (Glowing neon aura backlight)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(99, 179, 237, 95)) # Glowing cyan-blue backlight aura
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        
        # Custom Title Bar
        title_bar_layout = QHBoxLayout()
        title_bar_layout.setContentsMargins(0, 0, 0, 10)
        
        self.title_label = QLabel("Echer OS Layer")
        self.title_label.setStyleSheet("color: #63b3ed; font-size: 14px; font-weight: bold; background: transparent; border: none;")
        title_bar_layout.addWidget(self.title_label)
        
        title_bar_layout.addSpacing(15)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #718096; font-size: 12px; background: transparent; border: none;")
        title_bar_layout.addWidget(self.status_label)
        
        # Capture Mode Toggle Button (Sleek Glassmorphic Pill)
        self.capture_mode = "full" # Default to Full Screen
        self.mode_btn = QPushButton("🖥️ Full Screen")
        self.mode_btn.setFixedSize(110, 24)
        self.mode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_btn.setStyleSheet("""
            QPushButton {
                color: #a0aec0;
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(99, 179, 237, 100);
            }
        """)
        self.mode_btn.clicked.connect(self.toggle_capture_mode)
        title_bar_layout.addWidget(self.mode_btn)
        
        title_bar_layout.addStretch()
        
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(24, 24)
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet("""
            QPushButton {
                color: #a0aec0;
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 12px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(236, 201, 75, 180);
            }
        """)
        self.min_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(self.min_btn)
        
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                color: #a0aec0;
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 12px; /* Perfect circular pill button */
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                background-color: rgba(252, 129, 129, 180); /* Soft red delete glow */
            }
        """)
        self.close_btn.clicked.connect(self.safe_toggle_visibility)
        title_bar_layout.addWidget(self.close_btn)
        
        container_layout.addLayout(title_bar_layout)

        self.input_box = HistoryLineEdit()
        self.input_box.setPlaceholderText("Ask Echer... (e.g. 'What am I looking at?')")
        self.input_box.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 15); /* Pill-shaped transparent container */
                color: white;
                border: 1px solid rgba(255, 255, 255, 10);
                border-radius: 22px; /* Perfect pill-shape */
                padding: 12px 20px;
                font-size: 15px;
            }
            QLineEdit:focus {
                border: 1.5px solid rgba(99, 179, 237, 180); /* Cyan pill focus */
                background-color: rgba(255, 255, 255, 20);
            }
        """)
        self.input_box.returnPressed.connect(self.process_query)
        container_layout.addWidget(self.input_box)

        self.response_area = QTextEdit()
        self.response_area.setReadOnly(True)
        self.response_area.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #edf2f7;
                border: none;
                font-size: 15px;
                margin-top: 15px;
            }
            code {
                background-color: rgba(255, 255, 255, 25);
                color: #63b3ed;
                font-family: 'Consolas', monospace;
                padding: 2px 4px;
                border-radius: 4px;
            }
            pre {
                background-color: rgba(15, 20, 31, 150);
                border: 1px solid rgba(255, 255, 255, 10);
                padding: 10px;
                border-radius: 8px;
                font-family: 'Consolas', monospace;
            }
            strong {
                color: #63b3ed;
                font-weight: bold;
            }
            ul, ol {
                margin-left: 15px;
                padding-left: 0px;
            }
        """)
        self.response_area.setHtml("<span style='color: #a0aec0;'>Ready.<br>Press Ctrl+Space to toggle Echer.<br>Waiting for local Ollama LLM to finish downloading...</span>")
        self.response_area.setVisible(False) # HIDE response area initially in Idle State
        container_layout.addWidget(self.response_area)

        # Resizing grip in the bottom right
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        
        self.sizegrip = QSizeGrip(self)
        self.sizegrip.setFixedSize(16, 16)
        self.sizegrip.setStyleSheet("""
            QSizeGrip {
                background-color: rgba(255, 255, 255, 25);
                border-top-left-radius: 6px;
                border-bottom-right-radius: 24px; /* Curve matching the 28px bubble corner */
            }
            QSizeGrip:hover {
                background-color: rgba(99, 179, 237, 160);
            }
        """)
        bottom_bar.addWidget(self.sizegrip)
        container_layout.addLayout(bottom_bar)

        layout.addWidget(self.container)
        self.setLayout(layout)

        self.show()

    # Mouse events to enable window dragging for frameless window
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if hasattr(self, '_drag_active') and self._drag_active:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_active = False

    def animate_to_state(self, expanded=True):
        if hasattr(self, "anim") and self.anim.state() == QPropertyAnimation.State.Running:
            self.anim.stop()
            
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(350)
        self.anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        current_geom = self.geometry()
        target_geom = self.geometry()
        
        if expanded:
            self.response_area.setVisible(True)
            target_geom.setHeight(510)
        else:
            target_geom.setHeight(150)
            self.anim.finished.connect(self.hide_response_area)
            
        self.anim.setStartValue(current_geom)
        self.anim.setEndValue(target_geom)
        self.anim.start()

    def hide_response_area(self):
        if self.height() <= 160: # Only hide if collapsed
            self.response_area.setVisible(False)

    def process_query(self):
        query = self.input_box.text().strip()
        if not query:
            return
        
        # Add to history
        self.input_box.add_to_history(query)
        
        # Dynamic Island: Fluidly expand window height on submit
        if not self.response_area.isVisible():
            self.animate_to_state(expanded=True)
            
        from PyQt6.QtWidgets import QApplication
        # 1. Hide the overlay temporarily to get Echer out of the way of the screenshot
        self.hide()
        QApplication.processEvents() # Force Windows to update DWM and remove Echer from view
        import time
        time.sleep(0.15) # Wait 150ms for Windows DWM to completely hide Echer and refresh the screen
        
        # 2. Perform a clean capture based on the selected mode (Full Screen or Active Window)
        try:
            vision = ScreenPerceptionEngine()
            target_window_info = getattr(self, "previously_active_window_info", None)
            if self.capture_mode == "full":
                img_path = vision.capture_screen()
            else:
                img_path = vision.capture_active_window(target_window_info=target_window_info)
        except Exception as e:
            img_path = ""
            
        # 3. Restore the overlay immediately (practically invisible flicker)
        self.show()
        self.activateWindow()
        self.input_box.setFocus()
        
        import os
        try:
            username = os.getlogin()
        except Exception:
            username = "User"
            
        # Force a clean new paragraph block to strip previous HTML list/bullet formats
        cursor = self.response_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock(QTextBlockFormat())
        
        prompt_html = f"<span style='color: #a0aec0;'>C:\\Users\\{username}&gt;</span> <span style='color: #ffffff;'>{query}</span>"
        cursor.insertHtml(prompt_html)
        self.input_box.clear()
        
        active_window_title = None
        if hasattr(self, "previously_active_window_info") and self.previously_active_window_info:
            active_window_title = self.previously_active_window_info.get("title")
            
        self.worker = AITaskThread(query, img_path, active_window_title=active_window_title)
        self.worker.status_signal.connect(self.update_status)
        self.worker.stream_signal.connect(self.update_stream)
        self.worker.start()

    from PyQt6 import QtCore
    @QtCore.pyqtSlot(str)
    def update_status(self, text):
        if "Echer-System" in text:
            clean_text = text.replace("Echer-System:\\>", "").strip()
            self.status_label.setStyleSheet("color: #a0aec0; font-size: 12px; background: transparent; border: none;")
            self.status_label.setText(f"• {clean_text}")
        elif "Echer-Error" in text:
            clean_text = text.replace("Echer-Error:\\>", "").strip()
            self.status_label.setStyleSheet("color: #fc8181; font-size: 12px; background: transparent; border: none;")
            self.status_label.setText(f"✕ {clean_text}")
            self.response_area.append(f"<span style='color: #fc8181; font-weight: bold;'>Error:</span> <span style='color: #feb2b2;'>{clean_text}</span>")
        else:
            if "Echer:\\>" in text:
                self.status_label.setText("") # Clear status when streaming starts
                # Force a clean new paragraph block to strip previous HTML list/bullet formats
                cursor = self.response_area.textCursor()
                cursor.movePosition(QTextCursor.MoveOperation.End)
                cursor.insertBlock(QTextBlockFormat())
                cursor.insertHtml("<span style='color: #63b3ed; font-weight: bold;'>Echer:\\&gt;</span> ")
                
                # Move cursor to end and record the starting position of the stream
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.stream_start_pos = cursor.position()
                self.current_stream_buffer = ""
            else:
                self.response_area.append(text)

    @QtCore.pyqtSlot(str)
    def update_stream(self, chunk):
        import markdown
        self.current_stream_buffer += chunk
        
        # Convert the markdown buffer to HTML
        html = markdown.markdown(self.current_stream_buffer)
        
        # Select from start position to the end of the document and replace it cleanly with HTML
        cursor = self.response_area.textCursor()
        cursor.setPosition(self.stream_start_pos)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.insertHtml(html)

    def toggle_capture_mode(self):
        if self.capture_mode == "full":
            self.capture_mode = "window"
            self.mode_btn.setText("🪟 Active Window")
            self.mode_btn.setStyleSheet("""
                QPushButton {
                    color: #63b3ed;
                    background-color: rgba(99, 179, 237, 40);
                    border: 1px solid rgba(99, 179, 237, 100);
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: white;
                    background-color: rgba(99, 179, 237, 80);
                }
            """)
        else:
            self.capture_mode = "full"
            self.mode_btn.setText("🖥️ Full Screen")
            self.mode_btn.setStyleSheet("""
                QPushButton {
                    color: #a0aec0;
                    background-color: rgba(255, 255, 255, 20);
                    border: none;
                    border-radius: 12px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: white;
                    background-color: rgba(99, 179, 237, 100);
                }
            """)

    def setup_hotkey(self):
        # We run the hotkey listener in a separate thread
        self.listener_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
        self.listener_thread.start()

    def hotkey_listener(self):
        # Listen for Ctrl + Space
        with keyboard.GlobalHotKeys({
            '<ctrl>+<space>': self.emit_toggle_signal
        }) as h:
            h.join()

    def emit_toggle_signal(self):
        # Capture the active window before Echer shows up and steals focus!
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active and "Echer" not in active.title and "Echer OS Layer" not in active.title:
                self.previously_active_window_info = {
                    "title": active.title,
                    "left": active.left,
                    "top": active.top,
                    "width": active.width,
                    "height": active.height
                }
        except Exception:
            pass
        self.toggle_signal.emit()

    from PyQt6 import QtCore
    @QtCore.pyqtSlot()
    def safe_toggle_visibility(self):
        if self.isVisible():
            # Collapse back to Dynamic Island state upon hiding
            self.animate_to_state(expanded=False)
            self.hide()
        else:
            self.show_and_focus()

    @QtCore.pyqtSlot()
    def show_and_focus(self):
        # Capture active window before showing (as a fallback)
        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active and "Echer" not in active.title and "Echer OS Layer" not in active.title:
                self.previously_active_window_info = {
                    "title": active.title,
                    "left": active.left,
                    "top": active.top,
                    "width": active.width,
                    "height": active.height
                }
        except Exception:
            pass
            
        self.showNormal() # Unminimize if it was minimized to taskbar
        self.show()
        self.activateWindow()
        self.input_box.setFocus()
