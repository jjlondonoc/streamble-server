# UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
NOTIFY_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef1"
COMMAND_CHAR_UUID = "12345678-1234-5678-1234-56789abcdef2"

# Peripheral's name
DEVICE_NAME = "Vital-signs-monitor"

# Max time for BLE scanning [s]
SCAN_TIMEOUT = 10.0

# Protocol
PACKET_HEADER = b'\x00\x00\x00\x02'  # 4 bytes
LENGTH_TAG = 0x03                # Tag byte
SAMPLE_TAG = 0x05                  # Tag byte
LENGTH_FIELD_SIZE= 4                    # 3 bytes length + 1 byte tag
SAMPLE_UNIT_SIZE = 4                    # 3 bytes sample + 1 byte tag
HEADER_SIZE = len(PACKET_HEADER) + LENGTH_FIELD_SIZE

START_COMMAND = "start"
STOP_COMMAND = "stop"

# Parser
QUEUE_PUT_TIMEOUT = 0.1   # s
MAX_BUFFER_SIZE = 65536 # max bytes in buffer

# Named pipe
PIPE_NAME = r'\\.\pipe\streamble_data' # Pipe's name

# Threads
# Events shutdown control
SHUT_DOWN_COMMAND = None
