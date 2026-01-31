# Smart City: Autonomous Parking System (IoT Final Project)

> **Course:** IoT Systems Development | **Year:** 2026
> **Student:** Meir Garada

##  Project Overview
This project simulates a **Smart Parking Management System** for a Smart City environment.
It is designed to solve the problem of parking congestion by automating access control, monitoring occupancy in real-time, and providing live data visualization to operators.

The system is built using a fully decoupled **Microservices Architecture**, communicating asynchronously over the **MQTT Protocol**.

---

##  Key Features & Technical Highlights

* **Modern MQTT Architecture:** Utilizes `paho-mqtt` **Client V2** (Callback API Version 2) for strict compliance and zero deprecation warnings.
* **Intelligent Logic Controller:** Autonomous decision-making engine that prevents overcrowding and manages gate access based on real-time sensor data.
* **Thread-Safe GUI:** A responsive Dashboard built with **PyQt5**, utilizing `Signals` and `Slots` to separate network logic from UI rendering.
* **Robust Data Persistence:** **SQLite** database implementing **WAL (Write-Ahead Logging) Mode** to ensure high concurrency and stability (prevents "database locked" errors).

---

##  System Architecture

The system consists of 4 main independent modules:

1.  **Parking Emulators (Hardware Sim):**
    * **Producers:** 4x Ultrasonic Sensors (simulate car presence per slot).
    * **Input Actuator:** Entry Request Button (Driver).
    * **Output Actuators:** Gate Barrier (Motor) & Digital Signage (LED Display).
2.  **Logic Controller (The Brain):**
    * Orchestrates the system. Listens to sensors, processes logic (If `Occupied < Total` -> `Open Gate`), and commands actuators.
3.  **Database Manager:**
    * Logs all events (Entries, Alerts, Commands) to a local SQLite DB for auditing.
4.  **GUI Dashboard:**
    * Visualizes the parking lot status (Red/Green slots), displays system alerts, and shows a live log feed.

---

##  Prerequisites

* Python 3.9 or higher
* Internet connection (for HiveMQ public broker)

### Dependencies
Install the required libraries using `pip`:

```bash
pip install -r requirements.txt

```

*Content of `requirements.txt`:*

* `paho-mqtt` (Communication)
* `PyQt5` (User Interface)
* `icecream` (Professional Debugging/Logging)
* `pandas` (Data handling)

---

##  How to Run the System

Since this is a distributed system, you need to run the components in specific order.
Open **3 separate Terminal** windows:

### Step 1: Start the Logic Controller (The Brain)

This script initializes the DB and starts listening for sensors.

```bash
python logic_controller.py

```

### Step 2: Start the GUI Dashboard (The View)

This opens the management screen.

```bash
python parking_gui.py

```

### Step 3: Start the Hardware Emulators (The Simulation)

This opens the control panel to simulate cars and buttons.

```bash
python parking_emulators.py

```

---

## Project Structure

```text
📦 SmartCity_Parking_IoT
 ┣ 📜 config.py              # Global Configuration (Topics, Broker, Constants)
 ┣ 📜 mqtt_client.py         # Generic MQTT Wrapper Class (Paho V2)
 ┣ 📜 database_manager.py    # SQLite Manager (WAL Mode)
 ┣ 📜 logic_controller.py    # Main Business Logic (Manager App)
 ┣ 📜 parking_emulators.py   # Hardware Simulation (Sensors/Actuators)
 ┣ 📜 parking_gui.py         # Operator Dashboard (PyQt5)
 ┣ 📜 requirements.txt       # Project Dependencies
 ┗ 📜 README.md              # Project Documentation

```

---

## Usage Scenario (Demo)

1. **Entry Request:** User clicks "PRESS FOR TICKET" on the Emulator.
2. **Processing:** `logic_controller` checks availability.
3. **Action:**
* If **Free**: Gate opens, Signage shows "FREE".
* If **Full**: Gate remains closed, System alerts "Parking Full".


4. **Feedback:** The GUI Dashboard updates the slot color (Green -> Red) and logs the event.

![alt text](<Screenshot 2026-01-28 095635.png>)
---

## License

This project was developed for educational purposes at HIT (Holon Institute of Technology).