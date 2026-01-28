# logic_controller.py
# ---------------------------------------------------------
# Business Logic Controller (The "Manager")
# Coordinates Sensors, Actuators, and Database.
# ---------------------------------------------------------
import time
from mqtt_client import MqttClient
from database_manager import DatabaseManager
from config import *
from icecream import ic

class ParkingManager:
    def __init__(self):
        self.client_id: str = "Manager_App_v1"
        self.mqtt = MqttClient(self.client_id)
        self.db = DatabaseManager()
        
        # State Tracking
        self.slots_status: dict[int, int] = {i: 0 for i in range(1, TOTAL_SLOTS + 1)}
        self.occupied_count: int = 0

    def on_connect_success(self):
        ic("Connected! Subscribing now...")
        self.mqtt.subscribe(TOPIC_SLOT_STATUS)
        self.mqtt.subscribe(TOPIC_ENTRY_BUTTON)
        self.mqtt.subscribe(TOPIC_GATE_COMMAND)
        self.mqtt.subscribe(TOPIC_GATE_FEEDBACK)

    def start(self) -> None:
        """Main entry point."""
        self.mqtt.on_connected_callback = self.on_connect_success
        self.mqtt.connect()
        self.mqtt.on_msg_received = self.process_message
        
        ic("Parking Manager Running... (Press Ctrl+C to stop)")
        try:
            while True:
                time.sleep(1) # Keep main thread alive
        except KeyboardInterrupt:
            self.mqtt.disconnect()
            ic("Manager Stopped.")

    def process_message(self, topic: str, payload: str) -> None:
        """Routing logic for incoming MQTT messages."""
        
        # 1. Sensor Data (Slots)
        if topic.startswith(TOPIC_SLOT_BASE):
            try:
                # Extract Slot ID from topic "SmartCity/.../Slots/1/Status"
                slot_id = int(topic.split("/")[-2])
                status = int(payload)
                
                # Logic Update
                self.slots_status[slot_id] = status
                self.update_occupancy()
                
            except (ValueError, IndexError) as e:
                ic(f"Error parsing slot data: {e}")

        # 2. Input Actuator (Entry Button)
        elif topic == TOPIC_ENTRY_BUTTON:
            ic(f"Button Press Detected: {payload}")
            self.handle_entry_request()

        # 3. Logging Actuator Actions
        elif topic == TOPIC_GATE_COMMAND:
            self.db.insert_log(topic, f"Command: {payload}", "ACTUATOR_CMD")

    def update_occupancy(self) -> None:
        """Recalculate occupancy and update signage."""
        self.occupied_count = sum(self.slots_status.values())
        ic(f"Occupancy Updated: {self.occupied_count}/{TOTAL_SLOTS}")
        
        # Business Logic: Signage Control
        if self.occupied_count >= TOTAL_SLOTS:
            self.mqtt.publish(TOPIC_SIGNAGE, "FULL")
            self.mqtt.publish(TOPIC_ALERTS, f"Parking Full! ({self.occupied_count}/{TOTAL_SLOTS})")
        else:
            self.mqtt.publish(TOPIC_SIGNAGE, "FREE")

    def handle_entry_request(self) -> None:
        """Core Business Logic: Gate Control."""
        if self.occupied_count < TOTAL_SLOTS:
            ic(f"Access Granted. Gate Opening. ({self.occupied_count}/{TOTAL_SLOTS} Occupied)")
            self.mqtt.publish(TOPIC_GATE_COMMAND, "OPEN")
            self.db.insert_log(TOPIC_ENTRY_BUTTON, "Entry Granted", "ACCESS_LOG")
        else:
            ic("Access Denied. Parking is Full.")
            self.mqtt.publish(TOPIC_ALERTS, "Entry Denied: Parking Full")
            self.db.insert_log(TOPIC_ENTRY_BUTTON, "Entry Denied (Full)", "ACCESS_LOG")

if __name__ == "__main__":
    manager = ParkingManager()
    manager.start()