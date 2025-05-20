import logging
import time
import queue
import threading
import win32pipe, win32file, pywintypes

from .state import event_queue, data_queue

logger = logging.getLogger(__name__)

def create_pipe_connection(pipe_name: str):
    pipe = win32pipe.CreateNamedPipe(
        pipe_name,
        win32pipe.PIPE_ACCESS_OUTBOUND,
        win32pipe.PIPE_TYPE_BYTE | win32pipe.PIPE_WAIT,
        1, 65536, 65536, 0, None
    )
    logger.info(f"Server ready. Waiting pipe connection: {pipe_name}")
    win32pipe.ConnectNamedPipe(pipe, None)
    return pipe

def close_pipe(pipe: pywintypes.HANDLE):
    try:
        win32file.CloseHandle(pipe)
        logger.info("Pipe closed correctly, resources dispossed succesfully")
    except:
        pass

# Thread

def pipe_writer(pipe: pywintypes.HANDLE, shutdown_event: threading.Event):
    try:
        while not shutdown_event.is_set():
            # Consumes data from data_queue (queue with packets already parsed)
            try:
                data = data_queue.get(timeout=0.5)
            except queue.Empty:
                time.sleep(0.01)
                continue  # Check shutdown again
            # Try write in pipe. 
            # If fails, finish connection server.
            try:
                win32file.WriteFile(pipe, data)
            except (BrokenPipeError, pywintypes.error) as e:
                event_queue.put("pipe_disconnected")
                break

    except Exception as e:
        logger.exception(f"Unexpected error in pipe_writer: {e}")
        event_queue.put("pipe_disconnected")
        
