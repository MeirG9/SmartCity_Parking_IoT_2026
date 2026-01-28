# mqtt_client.py
# ---------------------------------------------------------
# Generic MQTT Client Wrapper (Paho MQTT V2 Compliant)
# Provides a robust communication layer for the system.
# ---------------------------------------------------------
from typing import Callable, Optional, Any
from paho.mqtt.enums import CallbackAPIVersion
import paho.mqtt.client as mqtt
from config import BROKER_ADDRESS, BROKER_PORT, KEEPALIVE
from icecream import ic
from datetime import datetime

ic.configureOutput(prefix=lambda: f'{datetime.now().strftime("%H:%M:%S")} | ')

class MqttClient:
    """
    A wrapper class for Paho MQTT Client V2.
    Handles connection, subscription, and message callbacks safely.
    """
    def __init__(self, client_id: str):
        self.client = mqtt.Client(CallbackAPIVersion.VERSION2, client_id=client_id)
        
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        
        self.on_msg_received: Optional[Callable[[str, str], None]] = None
        self.on_connected_callback: Optional[Callable[[], None]] = None
        
        self.connected: bool = False

    def on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: int, properties: Any) -> None:
        """Handle connection events with V2 reason codes."""
        if reason_code == 0:
            ic(f"[{client._client_id.decode()}] Connected to Broker Successfully")
            self.connected = True
            if self.on_connected_callback:
                self.on_connected_callback()
        else:
            ic(f"[{client._client_id.decode()}] Connection Failed. Reason Code: {reason_code}")

    def on_disconnect(self, client: mqtt.Client, userdata: Any, disconnect_flags: Any, reason_code: int, properties: Any) -> None:
        """Handle disconnection events."""
        ic(f"[{client._client_id.decode()}] Disconnected. Reason Code: {reason_code}")
        self.connected = False

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Decode message and forward to the application logic."""
        try:
            payload = str(msg.payload.decode("utf-8"))
            # Delegate to the external handler if defined
            if self.on_msg_received:
                self.on_msg_received(msg.topic, payload)
        except Exception as e:
            ic(f"Error decoding message: {e}")

    def connect(self) -> None:
        """Initiate connection and start the background loop."""
        ic(f"Connecting to {BROKER_ADDRESS}...")
        try:
            self.client.connect(BROKER_ADDRESS, BROKER_PORT, KEEPALIVE)
            self.client.loop_start()  # Non-blocking background thread
        except Exception as e:
            ic(f"Fatal Connection Error: {e}")

    def disconnect(self) -> None:
        """Clean shutdown."""
        self.client.loop_stop()
        self.client.disconnect()

    def subscribe(self, topic: str) -> None:
        """Subscribe to an MQTT topic."""
        if self.connected:
            self.client.subscribe(topic)
            ic(f"Subscribed to: {topic}")
        else:
            ic(f"Warning: Attempted to subscribe to {topic} before connection.")

    def publish(self, topic: str, message: str) -> None:
        """Publish a message to an MQTT topic."""
        if self.connected:
            self.client.publish(topic, message)
            # Log only critical commands to avoid clutter
            if "Command" in topic or "Alerts" in topic:
                ic(f"TX: {topic} -> {message}")