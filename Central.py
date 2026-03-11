import sys, yaml
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPlainTextEdit, QTabWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QComboBox
from PySide6.QtGui import QIcon, QTextCursor, QKeySequence, QShortcut
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QUrl, QTimer
# pip install pyyaml

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window parameters (title, size, position)
        self.setWindowTitle("Central")
        #self.setWindowIcon(QIcon('Logo - White.png'))
        monitor_size = app.primaryScreen().size()
        monitor_width = monitor_size.width()
        monitor_height = monitor_size.height()
        window_width = 1920
        window_height = 1080
        window_posx = monitor_width - window_width
        window_posy = 0
        self.setGeometry(window_posx, window_posy, window_width, window_height)

        # Set custom title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Create tab widgets and layout
        self.tab_central = QTabWidget()
        self.tab_central.setMaximumWidth(640)
        self.tab_bar = QTabWidget()
        self.tab1 = QWidget()
        # self.tab2 = QWidget()
        # self.tab3 = QWidget()
        self.tab4 = QWidget()
        tab_icon = QIcon('LogoWhite.ico')
        self.tab_central.addTab(self.tab1, tab_icon, " Central")
        # self.tab_bar.addTab(self.tab2, "Lab")
        # self.tab_bar.addTab(self.tab3, "Autofactory")
        self.tab_bar.addTab(self.tab4, "Portal")
        self.layout.addWidget(self.tab_central)
        self.layout.addWidget(self.tab_bar)
        self.initTab1()
        # self.initTab2()
        # self.initTab3()
        self.initTab4()

    def initTab1(self):
        layout = QVBoxLayout(self.tab1)

        # Data widget
        terminal = QPlainTextEdit()
        terminal.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        terminal.setReadOnly(True)
        terminal.setCursorWidth(0)

        # Control widget
        play_button = QPushButton("Play")
        play_button.setCheckable(True)
        play_button.setMaximumWidth(60)
        def script():
            with open("CentralCore.yaml", "r") as f:
                script_data = yaml.safe_load(f)
            entries = script_data.get("boot", [])

            play_button.setChecked(True)
            play_button.setEnabled(False)
            play_button.setVisible(False)


            def log(index=0):
                if index >= len(entries):
                    play_button.setEnabled(True)
                    play_button.setChecked(False)
                    # delay 5 seconds before showing the button again
                    QTimer.singleShot(5000, lambda: play_button.setVisible(True))
                    return

                entry = entries[index]

                if "logclear" in entry:
                    terminal.clear()

                if "logupdate" in entry:
                    current_lines = terminal.toPlainText().splitlines()
                    update_text = str(entry.get("logupdate", ""))
                    if current_lines:
                        current_lines[-1] = update_text
                    else:
                        current_lines.append(update_text)
                    terminal.setPlainText("\n".join(current_lines))

                if "log" in entry:
                    terminal.appendPlainText(str(entry.get("log", "")))

                terminal.moveCursor(QTextCursor.End)
                terminal.verticalScrollBar().setValue(terminal.verticalScrollBar().maximum())

                delay_ms = int(float(entry.get("delay", 0)) * 1000)
                QTimer.singleShot(delay_ms, lambda: log(index + 1))

            log()
        play_button.clicked.connect(script)

        # Layout
        layout.addWidget(terminal)
        layout.addStretch()
        layout.addWidget(play_button)

    def initTab4(self):
        layout = QVBoxLayout(self.tab4)

        # System widgets
        label_IP = QLabel("IP:")
        menu_port = QComboBox()
        menu_port.addItems(["192.168.8.172"])

        label_status = QLabel("Status:")
        toggle_connect = QPushButton("Active")
        toggle_connect.setCheckable(True)
        toggle_connect.setChecked(True)
        def toggleConnect():
            if toggle_connect.isChecked():
                toggle_connect.setText("Active")
            else:
                toggle_connect.setText("Innactive")
        toggle_connect.clicked.connect(toggleConnect)

        # Data widgets
        web_view = QWebEngineView()
        initial_url = QUrl(f"http://{menu_port.currentText().strip()}/")
        stream_url = QUrl(f"http://{menu_port.currentText().strip()}:81/stream")
        web_view.load(stream_url)
        def load_stream_url():
            # stream = QUrl(f"http://{menu_port.currentText().strip()}:81/stream")
            web_view.load(stream_url)
        menu_port.currentTextChanged.connect(lambda _: load_stream_url())

        # Control widgets


        # System layout
        layout.addWidget(QLabel("System"))
        layout_system = QHBoxLayout()
        layout.addLayout(layout_system)
        layout_system.addWidget(label_IP)
        layout_system.addWidget(menu_port)
        layout_system.addWidget(label_status)
        layout_system.addWidget(toggle_connect)
        layout_system.addStretch()

        # Data layout
        layout.addWidget(QLabel("Data"))
        layout.addWidget(QLabel("Optical sensor"))
        layout.addWidget(web_view)

        # Control layout
        layout.addStretch()
        layout.addWidget(QLabel("Control"))
        layout.addWidget(QLabel("Actuation layer: NOT FOUND"))

# Fix/workaround for Windows taskbar icon
import ctypes
myappid = 'origin.program.version.build' # arbitrary string
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

# Run the application
if __name__ == "__main__":
    app = QApplication()
    app.setWindowIcon(QIcon('LogoWhite.ico'))

    window = MainWindow()
    window.show()

    with open("CentralStyle.qss", "r") as f:
        _style = f.read()
        app.setStyleSheet(_style)

    sys.exit(app.exec())
