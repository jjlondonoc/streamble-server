import logging
import threading
import asyncio
import pywintypes
from bleak import BleakClient

from . import config
from . import pipe_writer
from . import ble_client
from . import packets_parser
from . import state

logging.basicConfig(
    level= logging.INFO,
    format= '[%(asctime)s] %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    # 1. Create pipe and wait until client connection:
    try:
        pipe = pipe_writer.create_pipe_connection(config.PIPE_NAME)
    except (BrokenPipeError, pywintypes.error) as e:
            logger.warning(f"Pipe error: {e}")

    # 2. When client connected, launch pipe_writer_thread
    pipe_writer_thread = threading.Thread(target=pipe_writer.pipe_writer, args=(pipe, state.shutdown_event,))
    pipe_writer_thread.daemon = True
    pipe_writer_thread.start()

    # 3. When pipe connected and thread launched, scann BLE devices
    device_address = await ble_client.connect_ble_device(config.DEVICE_NAME, config.SCAN_TIMEOUT)
    if not device_address:
        # If device is not found, finish server session
        logger.warning(f"Device {config.DEVICE_NAME} not found")
        logger.info("Stopping server session")
        logger.info("Stopping threads and disposing resources")
        state.shutdown_event.set() # Stop pipe_writer thread
        pipe_writer.close_pipe(pipe)
        pipe_writer_thread.join()

        return

    logger.info(f"Device found: {device_address}")

    parser_thread = None

    try:
        async with BleakClient(device_address) as client:
            # Disconection callback
            client.set_disconnected_callback(ble_client.on_ble_disconnected)

            parser_thread = threading.Thread(target=packets_parser.parser)
            parser_thread.daemon = True
            parser_thread.start()

            # Enable notify
            try:
                await client.start_notify(config.NOTIFY_CHAR_UUID, ble_client.notification_handler)
                logger.info(f"Notifications enabled in characteristic: {config.NOTIFY_CHAR_UUID}")
            except Exception as e:
                logger.error(f"Error enabling notifications in characteristic {config.NOTIFY_CHAR_UUID}")

            # Then send "start" command
            await ble_client.send_command(client, config.START_COMMAND, config.COMMAND_CHAR_UUID)

            loop = asyncio.get_running_loop()

            while True:
                event = await loop.run_in_executor(None, state.event_queue.get)

                if event == "pipe_disconnected":
                    logger.warning("Pipe disconnected, sending stop to device")
                    await ble_client.send_command(client, config.STOP_COMMAND, config.COMMAND_CHAR_UUID)
                    # Detener notificaciones
                    try:
                        await client.stop_notify(config.NOTIFY_CHAR_UUID)
                        logger.warning(f"Notification stopped")
                    except Exception as e:
                        logger.error(f"Error when stopping notifications in characteristic {config.NOTIFY_CHAR_UUID}")
                    break

                elif event == "data_queue_full":
                    logger.warning("data_queue full, sending stop to device until queue processing")
                    await ble_client.send_command(client, config.STOP_COMMAND, config.COMMAND_CHAR_UUID)
                    # Wait until queue size < 50
                    while state.data_queue.qsize() > 50:
                        logger.info(f"Waiting for data queue packets processing (actual: {state.data_queue.qsize()})...")
                        await asyncio.sleep(0.5)
                    logger.info("data_queue free, continue BLE transmission")
                    await ble_client.send_command(client, config.START_COMMAND, config.COMMAND_CHAR_UUID)

                elif event == "ble_disconnected":
                    logger.warning("BLE device unexpectedly disconnected. Stopping server session")
                    state.shutdown_event.set() # Detiene el hilo del pipe_writer
                    break

    except Exception as e:
        logger.exception("Error during BLE session")

    finally:
        logger.info("Stopping server sessionn")
        logger.info("Stopping threads and disposing resources")
        pipe_writer.close_pipe(pipe)
        pipe_writer_thread.join()
        # Ya se detuvo solo el hilo del pipe_writer
        # El hilo del parser está bloqueado esperando datas de data_queue_raw
        # Como ya detuve al periférico, se va a quedar ahí esperando datos en la cola
        # Así que envío la señal de shutdown en la cola data_queue_raw
        if parser_thread:
            state.data_queue_raw.put(config.SHUT_DOWN_COMMAND) # Con esto cierro el hilo del parser
            parser_thread.join()
        logger.info("Session finished succesfully")

# Ejecutar el programa principal
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")

         


                   
            
