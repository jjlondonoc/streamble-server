import logging
import queue
import struct

from .state import data_queue, data_queue_raw, event_queue
from . import config

logger = logging.getLogger(__name__)
_unpack_from = struct.unpack_from

def parser():
    """
    Thread for read chunks from data_queue_raw, assemble complete packets
    according with protocol and enqueue in data_queue.
    """
    buffer = bytearray()
    state = 0 # 0: Searching header, 1: Wait length
    idx = None
    read_idx = 0 # Pointer for memory handle
    num_samples = None
    total_size = None

    # Constants
    shutdown_cmd = config.SHUT_DOWN_COMMAND
    max_buffer_size = config.MAX_BUFFER_SIZE
    packet_header = config.PACKET_HEADER # 00 00 00 02
    header_size = config.HEADER_SIZE # 4 + 4 = 8 bytes
    length_tag = config.LENGTH_TAG # 03
    sample_tag = config.SAMPLE_TAG # 05
    sample_unit_size = config.SAMPLE_UNIT_SIZE # 4 bytes
    queue_timeout = config.QUEUE_PUT_TIMEOUT


    # For validate sample tags
    step = sample_unit_size
    start = header_size
    tag_offset = step - 1

    while True:
        # 1) Get next chunk, block until receive it
        chunk = data_queue_raw.get()
        if chunk is shutdown_cmd:
            logger.info(f"Shutdown signal received: {shutdown_cmd}. Exiting from parser.")
            break
        
        buffer.extend(chunk)

        # Delete buffer only when size is more than buffer size / 2
        if read_idx > max_buffer_size // 2:
            del buffer[:read_idx]
            read_idx = 0

        # 2) Prevent buffer growing without control
        if len(buffer) > max_buffer_size:
            logger.warning("Buffer too big. Cleaning previous data.")
            buffer = buffer[-max_buffer_size:]

        # 3) Try extract all complete packets
        while True:
            if state == 0:
                if len(buffer) - read_idx < len(packet_header):
                    break  # Wait for more data

                idx = buffer.find(packet_header, read_idx)
                if idx == -1:
                    # No header in buffer
                    break
                state = 1
            elif state == 1:
                # We have HEADER_SIZE bytes next to header?
                if len(buffer) < idx + header_size:
                    # Wait next chunk
                    break
                
                # Unpack 4 bytes little-endian and calculate number of samples
                value32, = _unpack_from('<I', buffer, idx + len(packet_header))
                tag = (value32 >> 24) & 0xFF
                length = value32 & 0xFFFFFF

                if tag != length_tag:
                    logger.warning("Invalid length-tag; discarting header")
                    read_idx = idx + len(packet_header)
                    state = 0
                    idx = None
                    continue

                num_samples = length + 1
                total_size = header_size + num_samples * sample_unit_size
                state = 2

            elif state == 2:
                # We have complete packet?
                if len(buffer) < idx + total_size:
                    # Wait for more notifications
                    break

                # Extract complete packet
                packet = bytes(buffer[idx: idx + total_size])

                # Validate sample tag byte
                tag_slice = buffer[
                    idx + start + tag_offset 
                    : idx + start + step * num_samples 
                    : step
                ]

                if tag_slice != bytes([sample_tag] * num_samples):
                    logger.warning("Invalid sample tag. Discarting packet")
                    read_idx = idx + total_size
                    state = 0
                    idx = None
                    num_samples = None
                    total_size = None
                    continue

                read_idx = idx + total_size
                # Enqueue complete packet
                try:
                    data_queue.put(packet, timeout=queue_timeout)
                except queue.Full:
                    event_queue.put("data_queue_full")
                except Exception as e:
                    logger.exception(f"Error in enqueue complete packet: {e}")

                # Reset state after enqueue one complete an valid packet
                state = 0
                idx = None
                num_samples = None
                total_size = None


    logger.info("Parser thread finished succesfully")