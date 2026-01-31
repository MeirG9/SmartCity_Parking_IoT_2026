# config.py
# ---------------------------------------------------------
# Global Configuration for Smart Parking IoT System
# ---------------------------------------------------------

# MQTT Broker Settings
BROKER_ADDRESS: str = "broker.hivemq.com"
BROKER_PORT: int = 1883
KEEPALIVE: int = 60

# Topic Structure & Isolation
UNIQUE_ID: str = "Meir_Final_Project_2026"
TOPIC_ROOT: str = f"SmartCity/Parking/{UNIQUE_ID}/"

# Sensors (Producers - Information Flow)
TOPIC_SLOT_STATUS: str = TOPIC_ROOT + "Slots/+/Status"  # Wildcard subscription
TOPIC_SLOT_BASE: str = TOPIC_ROOT + "Slots/"

# Actuators (Input - User Actions)
TOPIC_ENTRY_BUTTON: str = TOPIC_ROOT + "Entrance/Button"

# Actuators (Output - System Reactions)
TOPIC_GATE_COMMAND: str = TOPIC_ROOT + "Gate/Command"    # Commands: OPEN/CLOSE
TOPIC_GATE_FEEDBACK: str = TOPIC_ROOT + "Gate/Feedback"  # Status: OPEN/CLOSED
TOPIC_SIGNAGE: str = TOPIC_ROOT + "Signage/Text"         # Display: FREE/FULL

# System Alerts (Management Reporting)
TOPIC_ALERTS: str = TOPIC_ROOT + "System/Alerts"

# Database Configuration
DB_NAME: str = "smart_parking.db"
TABLE_LOGS: str = "system_logs"

# Logic Constants
TOTAL_SLOTS: int = 4
GATE_OPEN_DURATION: int = 3000  # milliseconds