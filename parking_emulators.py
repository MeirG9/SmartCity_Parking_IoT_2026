# parking_emulators.py
# ---------------------------------------------------------
# Hardware Emulators (GUI)
# Simulates Sensors (Slots) and Actuators (Gate, Signage).
# Includes Automatic Traffic Simulation Mode.
# ---------------------------------------------------------
import sys
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QCheckBox, QGroupBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from mqtt_client import MqttClient
from config import *
from icecream import ic

class ParkingEmulator(QMainWindow):
    # Signals ensure Thread-Safety between MQTT thread and GUI thread
    update_gate_signal = pyqtSignal(str)
    update_signage_signal = pyqtSignal(str)
    
    def on_connect_success(self):
        ic("Emulator Connected! Subscribing to actuators...")
        self.mqtt.subscribe(TOPIC_GATE_COMMAND)
        self.mqtt.subscribe(TOPIC_SIGNAGE)
        
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IOT Emulators (Hardware Sim + Auto Traffic)")
        self.setGeometry(100, 100, 420, 550)
        
        # Setup UI
        self.init_ui()

        # Setup MQTT
        self.client_id: str = f"Emulator_Client_{random.randint(1000,9999)}"
        self.mqtt = MqttClient(self.client_id)
        self.mqtt.on_connected_callback = self.on_connect_success
        self.mqtt.connect()
        self.mqtt.on_msg_received = self.on_actuator_command
        
        # Hook signals to local slots
        self.update_gate_signal.connect(self._handle_gate_ui)
        self.update_signage_signal.connect(self._handle_signage_ui)

        # Traffic Simulation Timer
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulate_random_traffic)

    def init_ui(self) -> None:
        main_widget = QWidget()
        layout = QVBoxLayout()

        # --- Traffic Simulation Control ---
        grp_sim = QGroupBox("🚦 Traffic Simulation (Auto Mode)")
        sim_layout = QHBoxLayout()
        self.btn_sim = QPushButton("Start Auto-Traffic")
        self.btn_sim.setCheckable(True)
        self.btn_sim.setStyleSheet("background-color: #90CAF9; font-weight: bold; padding: 8px;")
        self.btn_sim.clicked.connect(self.toggle_simulation)
        sim_layout.addWidget(self.btn_sim)
        grp_sim.setLayout(sim_layout)
        layout.addWidget(grp_sim)
        
        # 1. Sensors (Producers)
        grp_sensors = QGroupBox("🅿️ Parking Slots (Ultrasonic Sensors)")
        sensor_layout = QVBoxLayout()
        
        self.slot_checkboxes = {} # Store reference for simulation access
        
        for i in range(1, TOTAL_SLOTS + 1):
            cb = QCheckBox(f"Slot {i} Occupied")
            cb.stateChanged.connect(lambda state, slot=i: self.publish_slot_status(slot, state))
            sensor_layout.addWidget(cb)
            self.slot_checkboxes[i] = cb
            
        grp_sensors.setLayout(sensor_layout)
        layout.addWidget(grp_sensors)
        
        # 2. Input (Button)
        grp_entry = QGroupBox("🎟️ Entrance Gate Control")
        entry_layout = QHBoxLayout()
        self.btn_entry = QPushButton("PRESS FOR TICKET")
        self.btn_entry.clicked.connect(self.request_entry)
        self.btn_entry.setStyleSheet("background-color: #A5D6A7; font-weight: bold; padding: 10px;")
        entry_layout.addWidget(self.btn_entry)
        grp_entry.setLayout(entry_layout)
        layout.addWidget(grp_entry)
        
        # 3. Output (Actuators)
        grp_gate = QGroupBox("🚧 Actuators Status")
        gate_layout = QVBoxLayout()
        
        self.lbl_gate_status = QLabel("Gate Status: CLOSED")
        self.lbl_gate_status.setAlignment(Qt.AlignCenter)
        self.lbl_gate_status.setStyleSheet("background: #FFCDD2; padding: 10px; border: 1px solid gray; font-weight: bold;") 
        
        self.lbl_signage = QLabel("Signage: FREE")
        self.lbl_signage.setAlignment(Qt.AlignCenter)
        self.lbl_signage.setStyleSheet("background: #C8E6C9; padding: 10px; border: 1px solid gray; font-weight: bold;") 
        
        gate_layout.addWidget(self.lbl_gate_status)
        gate_layout.addWidget(self.lbl_signage)
        grp_gate.setLayout(gate_layout)
        layout.addWidget(grp_gate)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    # --- Simulation Logic ---
    def toggle_simulation(self) -> None:
        """Starts or stops the random traffic generator."""
        if self.btn_sim.isChecked():
            self.btn_sim.setText("Stop Auto-Traffic")
            self.btn_sim.setStyleSheet("background-color: #FFAB91; font-weight: bold; padding: 8px;")
            self.sim_timer.start(3000) # Event every 3 seconds
            ic("Auto-Traffic Simulation: STARTED")
        else:
            self.btn_sim.setText("Start Auto-Traffic")
            self.btn_sim.setStyleSheet("background-color: #90CAF9; font-weight: bold; padding: 8px;")
            self.sim_timer.stop()
            ic("Auto-Traffic Simulation: STOPPED")

    def simulate_random_traffic(self) -> None:
        """Randomly toggles slots or requests entry."""
        action = random.choice(['slot', 'slot', 'entry']) # 66% chance for slot change
        
        if action == 'slot':
            slot_id = random.randint(1, TOTAL_SLOTS)
            cb = self.slot_checkboxes.get(slot_id)
            if cb:
                # Toggle state (This triggers the existing publish logic automatically)
                cb.setChecked(not cb.isChecked())
                ic(f"Simulating: Car {'Arrived at' if cb.isChecked() else 'Left'} Slot {slot_id}")
                
        elif action == 'entry':
            # Visual click effect
            self.btn_entry.setDown(True)
            QTimer.singleShot(200, lambda: self.btn_entry.setDown(False))
            self.request_entry()
            ic("Simulating: Driver pressed ticket button")

    # --- Producer Logic ---
    def publish_slot_status(self, slot_id: int, state: int) -> None:
        status = 1 if state == Qt.Checked else 0
        topic = TOPIC_SLOT_STATUS.replace("+", str(slot_id))
        ic(f"Sensor Trigger: Slot {slot_id} -> {status}")
        self.mqtt.publish(topic, str(status))

    def request_entry(self) -> None:
        ic("Driver Action: Requested Entry")
        self.mqtt.publish(TOPIC_ENTRY_BUTTON, "REQUEST")

    # --- Consumer Logic (Thread Safe) ---
    def on_actuator_command(self, topic: str, payload: str) -> None:
        """Receives MQTT data and emits Signal to GUI thread."""
        if topic == TOPIC_GATE_COMMAND:
            self.update_gate_signal.emit(payload)
        elif topic == TOPIC_SIGNAGE:
            self.update_signage_signal.emit(payload)

    def _handle_signage_ui(self, payload: str) -> None:
        self.lbl_signage.setText(f"Signage: {payload}")
        if payload == "FULL":
            self.lbl_signage.setStyleSheet("background: #FFCDD2; padding: 10px; border: 1px solid gray; font-weight: bold;") # Red
        else:
            self.lbl_signage.setStyleSheet("background: #C8E6C9; padding: 10px; border: 1px solid gray; font-weight: bold;") # Green

    def _handle_gate_ui(self, payload: str) -> None:
        if payload == "OPEN":
            self.lbl_gate_status.setText("Gate: OPENING...")
            self.lbl_gate_status.setStyleSheet("background: #FFF9C4; padding: 10px; border: 1px solid gray; font-weight: bold;") # Yellow
            # Simulate mechanical delay of 3 seconds
            QTimer.singleShot(GATE_OPEN_DURATION, self._gate_fully_open)
        elif payload == "CLOSE":
            # Only used if system forces close
            self.lbl_gate_status.setText("Gate: CLOSED")
            self.lbl_gate_status.setStyleSheet("background: #FFCDD2; padding: 10px; border: 1px solid gray; font-weight: bold;")

    def _gate_fully_open(self) -> None:
        self.lbl_gate_status.setText("Gate: OPEN (Car Entering)")
        self.lbl_gate_status.setStyleSheet("background: #C8E6C9; padding: 10px; border: 1px solid gray; font-weight: bold;")
        self.mqtt.publish(TOPIC_GATE_FEEDBACK, "OPEN")
        
        # Gate Auto-Close Mechanism (Mechanical Timer)
        QTimer.singleShot(2000, self._internal_gate_close)

    def _internal_gate_close(self) -> None:
        self.lbl_gate_status.setText("Gate: CLOSED")
        self.lbl_gate_status.setStyleSheet("background: #FFCDD2; padding: 10px; border: 1px solid gray; font-weight: bold;")
        self.mqtt.publish(TOPIC_GATE_FEEDBACK, "CLOSED")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    emulator = ParkingEmulator()
    emulator.show()
    sys.exit(app.exec_())