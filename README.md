# CBMS BLE Streaming Server

This repository provides a modular, multithreaded **backend server** designed to interface with BLE devices that implement the **CBMS protocol** (Continuous Biometric Monitoring Service). It acts as a standardized middleware between the Bluetooth Low Energy (BLE) layer and your client applications, abstracting all BLE logic and exposing signal data through a **named pipe**.

## What is this project?

This is a **Python package** that includes a standalone server for real-time streaming of biomedical signal data—such as ECG, PPG, EMG—from a CBMS-compatible BLE peripheral. The server is built following a client-server architectural model, where the backend manages all BLE communication and packet parsing logic in background threads, while any frontend or data consumer simply reads clean packets from a named pipe.

This project:
- Connects to a BLE peripheral using a custom service
- Parses incoming CBMS-formatted packets (Section 4 of the CBMS specification)
- Streams the parsed binary packets to a named pipe: `\\.\pipe\streamble_data`

## Server Execution Flow

1. The server creates a **named pipe** at `\\.\pipe\streamble_data`.
2. It **blocks** and waits for a client to connect to the pipe.
3. Once a client connects, a **new session** starts:
   - The server connects to the BLE peripheral
   - Parses and manages CBMS protocol packets in real time
   - Transmits the parsed packets to the connected client via the pipe
   - All of this happens **non-blocking and concurrently** using multithreading.
4. If the client disconnects from the pipe, the session ends.
5. If the BLE peripheral disconnects unexpectedly, the session also ends.
6. The server continues waiting for a new client to reconnect and start a new session.

> Logs are printed to the **console** throughout the process for monitoring the state and errors.

---

## Configuration

The BLE device name can be configured in `streamble/config.py`:
```python
DEVICE_NAME = "Vital-signs-monitor"  # <- Change this to match your peripheral's advertised name
```

Other configuration options such as pipe name, timeouts, and logging levels can also be modified in the same file.

---

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/jjlondonoc/streamble-server.git
cd streamble-server
```

### 2. Set up a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the server
```bash
python -m streamble.main
```

This will launch the BLE backend server. It will remain blocked until a client connects to the named pipe.

---

## Consuming the Pipe Stream
Any application can read data from the pipe `\\.\pipe\streamble_data`. Here's an example in Python:

```python
pipe_path = r"\\.\pipe\streamble_data"
with open(pipe_path, "rb") as pipe:
    while True:
        packet = pipe.read(256)  # Adjust to your packet size
        process(packet)          # Your logic here
```

You can also connect with a basic terminal reader for debugging:
```bash
type \\.\pipe\streamble_data
```

---

## Notes
- Server is multithreaded to ensure high responsiveness
- It supports real-time CBMS packet parsing (including header, sample count, and 24-bit samples)
- Sessions are **client-controlled** via pipe connection lifecycle

---

## License
MIT License

---

For more about the CBMS protocol and BLE service structure, see the technical documentation of CBMS Bluetooth service standard, for get it contact us in juan.londono47@eia.edu.co
