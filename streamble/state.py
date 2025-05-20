import queue
import threading

# Data structures
data_queue_raw = queue.Queue(maxsize=200) 
data_queue = queue.Queue(maxsize=100)

# Events queues
event_queue = queue.Queue(maxsize=50)

# Threads control
shutdown_event = threading.Event()