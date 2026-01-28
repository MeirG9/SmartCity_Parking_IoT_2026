# parking_gui.py
# ---------------------------------------------------------
# Main Dashboard (Management View)
# Visualization of the entire system state.
# ---------------------------------------------------------
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                             QLabel, QListWidget, QVBoxLayout, QFrame)
from PyQt5.QtCore import pyqtSignal, QObject, Qt, QTimer
from mqtt_client import MqttClient
from config import *
import datetime
from icecream import ic

class MqttWorker(QObject):
    msg_signal = pyqtSignal(str, str)
    def on_connect_success(self):
        ic("GUI Connected! Subscribing to data...")
        self.client.subscribe(TOPIC_SLOT_STATUS)
        self.client.subscribe(TOPIC_ALERTS)
        self.client.subscribe(TOPIC_SIGNAGE)
        self.client.subscribe(TOPIC_GATE_COMMAND)
    def __init__(self):
        super().__init__()
        self.client = MqttClient("GUI_Dashboard_Viewer")

        self.client.on_connected_callback = self.on_connect_success
        self.client.connect()
        self.client.on_msg_received = self.emit_msg
        
    def emit_msg(self, topic: str, payload: str) -> None:
        self.msg_signal.emit(topic, payload)

class ParkingDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart City: Parking Management Dashboard")
        self.setGeometry(600, 100, 600, 500)
        
        self.init_ui()
        
        # Init Background Worker
        self.worker = MqttWorker()
        self.worker.msg_signal.connect(self.update_dashboard)

    def init_ui(self) -> None:
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # 1. Header
        header = QLabel("Real-Time Parking Status")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # 2. Slots Grid
        grid_layout = QGridLayout()
        self.slot_widgets: dict[int, QLabel] = {}
        
        for i in range(1, TOTAL_SLOTS + 1):
            lbl = QLabel(f"Slot {i}\nFREE")
            lbl.setFixedSize(120, 100)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(self.get_style("FREE"))
            
            grid_layout.addWidget(lbl, 0, i-1)
            self.slot_widgets[i] = lbl
            
        main_layout.addLayout(grid_layout)

        # 3. Live Logs
        self.list_logs = QListWidget()
        self.list_logs.setStyleSheet("background-color: #2b2b2b; color: #00FF00; font-family: Consolas;")
        main_layout.addWidget(QLabel("Live System Logs:"))
        main_layout.addWidget(self.list_logs)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def get_style(self, status: str) -> str:
        base = "border: 2px solid gray; border-radius: 10px; font-weight: bold;"
        if status == "FREE":
            return base + "background-color: #C8E6C9; color: green;"
        else: # OCCUPIED
            return base + "background-color: #FFCDD2; color: red;"

    def update_dashboard(self, topic: str, payload: str) -> None:
        """Parses incoming MQTT messages and updates the UI."""
        
        # 1. Slot Status Updates
        if "Slots" in topic:
            try:
                slot_id = int(topic.split("/")[-2])
                is_occupied = int(payload) == 1
                
                lbl = self.slot_widgets.get(slot_id)
                if lbl:
                    if is_occupied:
                        lbl.setText(f"Slot {slot_id}\nOCCUPIED")
                        lbl.setStyleSheet(self.get_style("OCCUPIED"))
                        self.add_log(f"Sensor: Slot {slot_id} Occupied", "orange")
                    else:
                        lbl.setText(f"Slot {slot_id}\nFREE")
                        lbl.setStyleSheet(self.get_style("FREE"))
                        self.add_log(f"Sensor: Slot {slot_id} Freed", "green")
            except ValueError:
                pass

        # 2. System Alerts
        elif topic == TOPIC_ALERTS:
            self.add_log(f"ALERT: {payload}", "red")

        # 3. Gate Activity
        elif topic == TOPIC_GATE_COMMAND:
            if payload == "OPEN":
                self.add_log("GATE OPENING...", "cyan")

    def add_log(self, text: str, color_name: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        item_text = f"[{timestamp}] {text}"
        self.list_logs.addItem(item_text)
        self.list_logs.scrollToBottom()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ParkingDashboard()
    gui.show()
    sys.exit(app.exec_())