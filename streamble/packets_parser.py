import logging
import queue

from .state import data_queue, data_queue_raw, event_queue
from . import config

logger = logging.getLogger(__name__)

def parser():
    """
    Thread for read chunks from data_queue_raw, assemble complete packets
    according with protocol and enqueue in data_queue.
    """
    buffer = bytearray()

    while True:
        # 1) Get next chunk, block until receive it
        chunk = data_queue_raw.get()
        if chunk is config.SHUT_DOWN_COMMAND:
            logger.info(f"Shutdown signal received: {config.SHUT_DOWN_COMMAND}. Exiting from parser.")
            break

        buffer.extend(chunk)

        # 2) Prevent buffer growing without control
        if len(buffer) > config.MAX_BUFFER_SIZE:
            logger.warning("Buffer too big. Cleaning previous data.")
            buffer = buffer[-config.MAX_BUFFER_SIZE:]

        # 3) Try extract all complete packets
        while True:
            idx = buffer.find(config.PACKET_HEADER)
            if idx == -1:
                # No header in buffer
                break

            # We have HEADER_SIZE bytes next to header?
            if len(buffer) < idx + config.HEADER_SIZE:
                # Wait next chunk
                break

            # Validate length tag byte
            tag_byte = buffer[idx + len(config.PACKET_HEADER) + 3]
            if tag_byte != config.LENGTH_TAG:
                logger.warning("Invalid length-tag in parser; deleting one byte.")
                del buffer[idx]
                continue

            # Exctract number of samples (3 bytes LSB)
            num_samples = int.from_bytes(
                buffer[idx + len(config.PACKET_HEADER): idx + len(config.PACKET_HEADER) + 3],
                byteorder='little'
            ) + 1 # Numero de muestras mas 1
            total_size = config.HEADER_SIZE + num_samples * config.SAMPLE_UNIT_SIZE

            # We have complete packet?
            if len(buffer) < idx + total_size:
                # Wait for more notifications
                break

            # Extract complete packet
            packet = bytes(buffer[idx: idx + total_size])
            # Remove processed data
            del buffer[: idx + total_size]

            # 4) Validate sample tag byte
            pos = config.HEADER_SIZE
            valid = True
            for i in range(num_samples):
                sample_tag_index = pos + (config.SAMPLE_UNIT_SIZE - 1)
                sample_tag = packet[sample_tag_index]
                if sample_tag != config.SAMPLE_TAG:
                    logger.warning(
                        f"Invalid sample-tag in sample {i}: "
                        f"found 0x{sample_tag:02x}, "
                        f"expected 0x{config.SAMPLE_TAG:02x}. Discarted packet."
                    )
                    valid = False
                    break
                pos += config.SAMPLE_UNIT_SIZE
            if not valid:
                # Next posible packet
                continue

            # 5) Enqueue complete packet
            try:
                data_queue.put(packet, timeout=config.QUEUE_PUT_TIMEOUT)
            except queue.Full:
                event_queue.put("data_queue_full")
            except Exception as e:
                logger.exception(f"Error in enqueue complete packet: {e}")

    logger.info("Parser thread finished succesfully")





        
        

                


