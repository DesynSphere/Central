import sys, yaml
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPlainTextEdit, QTabWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, QPushButton, QComboBox
from PySide6.QtGui import QIcon, QTextCursor, QKeySequence, QShortcut
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import Qt, QTimer, QUrl, QUrlQuery
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest

import ArduinoSerial
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

        self.serial_manager = ArduinoSerial.SerialManager()
        self.portal_network_manager = QNetworkAccessManager(self)
        self.portal_pending_replies = set()

        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)

        # Create tab widgets and layout
        self.tab_central = QTabWidget()
        self.tab_central.setMaximumWidth(640)
        self.tab_bar = QTabWidget()
        self.tab1 = QWidget()
        self.tab2 = QWidget()
        # self.tab3 = QWidget()
        self.tab4 = QWidget()
        tab_icon = QIcon('LogoWhite.ico')
        self.tab_central.addTab(self.tab1, tab_icon, " Central")
        self.tab_bar.addTab(self.tab2, "Lab")
        # self.tab_bar.addTab(self.tab3, "Autofactory")
        self.tab_bar.addTab(self.tab4, "Portal")
        self.layout.addWidget(self.tab_central)
        self.layout.addWidget(self.tab_bar)
        self.initTab1()
        self.initTab2()
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
        menu_script = QComboBox()
        menu_script.addItems(["001 - Boot", "002 - Serial", "003 - Actuation"]) 
        play_button = QPushButton("Play")
        play_button.setCheckable(True)
        play_button.setMaximumWidth(60)

        def script():
            with open("CentralCore.yaml", "r") as f:
                script_data = yaml.safe_load(f)
            entries = script_data.get(menu_script.currentText().strip(), [])

            menu_script.setEnabled(False)
            menu_script.setVisible(False)
            play_button.setChecked(True)
            play_button.setEnabled(False)
            play_button.setVisible(False)
            def log(index=0):
                if index >= len(entries):
                    menu_script.setEnabled(True)
                    menu_script.setVisible(True)
                    play_button.setChecked(False)
                    play_button.setEnabled(True)
                    play_button.setVisible(True)
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

                if "command" in entry:
                    # terminal.appendPlainText(str(entry.get("command", "")))
                    if entry.get("command", "").startswith("HEATER:"):
                        temp = entry.get("command", "").split(":")[1]
                        self.serial_manager.sendCommand(f"AMBIENTTEMPERATURESETTING:{temp}")
                    if entry.get("command", "").startswith("LED:"):
                        state = entry.get("command", "").split(":")[1]
                        self.serial_manager.sendCommand(f"LED:{state}")
                    elif entry.get("command", "").startswith("TAB:"):
                        tab = entry.get("command", "").split(":")[1]
                        self.tab_bar.setCurrentIndex(int(tab))
                terminal.moveCursor(QTextCursor.End)
                terminal.verticalScrollBar().setValue(terminal.verticalScrollBar().maximum())

                delay_ms = int(float(entry.get("delay", 0)) * 1000)
                QTimer.singleShot(delay_ms, lambda: log(index + 1))

            log()
        play_button.clicked.connect(script)

        # Layout
        layout.addWidget(terminal)
        layout.addStretch()
        layout.addWidget(menu_script)
        layout.addWidget(play_button)
    
    def initTab2(self):
        layout = QVBoxLayout(self.tab2)
 
        # System widgets
        label_port = QLabel("Port:")
        menu_port = QComboBox()
        menu_port.addItems(self.serial_manager.listPorts())
        # menu_port.addItems(ArduinoSerial.SerialManager.listPorts(self))
        button_refresh = QPushButton("Refresh")
        button_refresh.clicked.connect(menu_port.clear)
        button_refresh.clicked.connect(lambda: menu_port.addItems(self.serial_manager.listPorts()))
        # button_refresh.clicked.connect(lambda: menu_port.addItems(ArduinoSerial.SerialManager.listPorts(self)))

        # label_baud = QLabel("Baud:")
        # menu_baud = QComboBox()
        # menu_baud.addItems(["115200"])
        label_status = QLabel("Status:")
        toggle_connect = QPushButton("Disconnected")
        toggle_connect.setCheckable(True)
        def toggleConnect():
            if toggle_connect.isChecked():
                self.serial_manager.connect(menu_port.currentText(), 115200)
                if self.serial_manager.isConnected():
                    toggle_connect.setText("Connected")
            else:
                self.serial_manager.disconnect()
                if not self.serial_manager.isConnected():
                    toggle_connect.setText("Disconnected")
        toggle_connect.clicked.connect(toggleConnect)
        toggle_connect.click()

        # Data widgets
        label_arduino_reading = QLabel("Device not connected to serial port.")
        label_ambient_temperature = QLabel("Ambient Temperature:")
        label_ambient_humidity = QLabel("Ambient Humidity:")
        label_heater_status = QLabel("Heater Status:")

        # Control widgets
        label_LED = QLabel("LED:")
        toggle_LED = QPushButton("Off")
        toggle_LED.setCheckable(True)
        def toggleLED():
            if toggle_LED.isChecked():
                if not self.serial_manager.isConnected():
                    print("Device not connected to serial port.")
                    toggle_LED.setChecked(False)
                    return
                self.serial_manager.sendCommand("LED:1")
                toggle_LED.setText("On")
            else:
                self.serial_manager.sendCommand("LED:0")
                toggle_LED.setText("Off")
        toggle_LED.clicked.connect(toggleLED)

        label_heat = QLabel("Heat:")
        menu_heat = QComboBox()
        menu_heat.addItems(["5", "10", "18"])
        def setHeat():
            if not self.serial_manager.isConnected():
                print("Device not connected to serial port.")
                return
            selected_heat = menu_heat.currentText()
            self.serial_manager.sendCommand(f"AMBIENTTEMPERATURESETTING:{selected_heat}")
            print(f"Set heat to: {selected_heat}")
        menu_heat.activated.connect(setHeat)

        # Poll the serial queue every 2 seconds and show the latest message
        arduino_timer = QTimer(self)
        arduino_timer.setInterval(2000)
        def updateArduinoReading():
            latest = None
            q = self.serial_manager.getQueue()
            while not q.empty():
                latest = q.get_nowait()
            if latest is not None:
                label_arduino_reading.setText(str(latest))
            elif not self.serial_manager.isConnected():
                label_arduino_reading.setText("Device not connected to serial port.")
        arduino_timer.timeout.connect(updateArduinoReading)
        arduino_timer.start()

        # System layout
        layout.addWidget(QLabel("System"))
        layout_system = QHBoxLayout()
        layout.addLayout(layout_system)
        layout_system.addWidget(label_port)
        layout_system.addWidget(menu_port)
        layout_system.addWidget(button_refresh)
        # layout_system.addWidget(label_baud)
        # layout_system.addWidget(menu_baud)
        layout_system.addWidget(label_status)
        layout_system.addWidget(toggle_connect)
        layout_system.addStretch()

        # Data layout
        layout.addWidget(QLabel("Data"))
        layout_data = QHBoxLayout()
        layout.addLayout(layout_data)
        layout_data.addWidget(label_arduino_reading)
        # layout_data.addWidget(label_ambient_temperature)
        # layout_data.addWidget(label_ambient_humidity)
        # layout_data.addWidget(label_heater_status)

        # Control layout
        layout.addStretch()
        layout.addWidget(QLabel("Control"))
        layout_control = QHBoxLayout()
        layout.addLayout(layout_control)
        layout_control.addWidget(label_LED)
        layout_control.addWidget(toggle_LED)
        layout_control.addWidget(label_heat)
        layout_control.addWidget(menu_heat)
        layout_control.addStretch()

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

        def portalHost():
            return menu_port.currentText().strip()

        def load_stream_url():
            host = portalHost()
            if host:
                web_view.load(QUrl(f"http://{host}:81/stream"))

        load_stream_url()
        menu_port.currentTextChanged.connect(lambda _: load_stream_url())

        # Control widgets
        button_stop = QPushButton("■")
        button_forward = QPushButton("▲")
        button_backward = QPushButton("▼")
        button_left = QPushButton("◄")
        button_right = QPushButton("►")
        controlFixedWidth = 40
        button_backward.setFixedWidth(controlFixedWidth)
        button_left.setFixedWidth(controlFixedWidth)
        button_forward.setFixedWidth(controlFixedWidth)
        button_stop.setFixedWidth(controlFixedWidth)
        button_right.setFixedWidth(controlFixedWidth)

        def sendMotorCommand(command):
            host = portalHost()
            if not host:
                print("Portal IP not set.")
                return

            url = QUrl(f"http://{host}/motor")
            query = QUrlQuery()
            query.addQueryItem("cmd", command)
            url.setQuery(query)

            reply = self.portal_network_manager.get(QNetworkRequest(url))
            self.portal_pending_replies.add(reply)

            def onFinished():
                response = bytes(reply.readAll()).decode(errors="replace").strip()
                if reply.error():
                    print(f"Motor command failed ({command}): {reply.errorString()}")
                elif response:
                    print(response)
                self.portal_pending_replies.discard(reply)
                reply.deleteLater()

            reply.finished.connect(onFinished)

        button_stop.clicked.connect(lambda: sendMotorCommand("STOP"))
        button_forward.clicked.connect(lambda: sendMotorCommand("FORWARD"))
        button_backward.clicked.connect(lambda: sendMotorCommand("BACKWARD"))
        button_left.clicked.connect(lambda: sendMotorCommand("LEFT"))
        button_right.clicked.connect(lambda: sendMotorCommand("RIGHT"))

        self.key_mapping = {
            Qt.Key_Q: button_stop,
            Qt.Key_W: button_forward,
            Qt.Key_S: button_backward,
            Qt.Key_A: button_left,
            Qt.Key_D: button_right,
        }

        # Keep button visuals in sync with actual key hold state.
        for key, button in self.key_mapping.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.WindowShortcut)
            # Keep key behavior in keyPressEvent/keyReleaseEvent only.
            shortcut.activated.connect(button.animateClick)

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
        layout_control = QGridLayout()
        layout.addLayout(layout_control)
        layout_control.addWidget(button_stop, 0, 0)
        layout_control.addWidget(button_forward, 0, 1)
        layout_control.addWidget(button_backward, 1, 1)
        layout_control.addWidget(button_left, 1, 0)
        layout_control.addWidget(button_right, 1, 2)
        layout_control.setColumnStretch(3, 1)

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in self.key_mapping:
            button = self.key_mapping[event.key()]
            button.setDown(True)
            button.setChecked(True)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            return
        if event.key() in self.key_mapping:
            button = self.key_mapping[event.key()]
            button.setDown(False)
            button.setChecked(False)
        super().keyReleaseEvent(event)

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
