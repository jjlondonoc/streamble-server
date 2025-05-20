import logging
import asyncio
import queue
from bleak import BleakScanner, BleakClient

from .state import data_queue_raw, event_queue

logger = logging.getLogger(__name__)

async def connect_ble_device(name: str, time_out: float) -> str | None:
    """Scan BLE devices searching for peripheral with selected name"""
    logger.info(f"Scanning BLE peripheral with name: '{name}' during {time_out}s…")
    try:
        devices = await BleakScanner.discover(timeout=time_out)
    except asyncio.TimeoutError:
        logger.warning("Timeout in BLE scanning.")
        return None

    for device in devices:
        if device.name == name:
            return device.address
    return None

def on_ble_disconnected(client: BleakClient):
    event_queue.put("ble_disconnected")

async def send_command(client: BleakClient, command: str, command_char_uuid: str) -> bool:
    """Send GATT command with confirmation message."""
    if not client.is_connected:
        logger.warning("BLE not connected, command omited")
        return False
    try:
        await client.write_gatt_char(command_char_uuid, command.encode(), response=True)
        logger.info(f"Command {command} sended succesfully to characteristic {command_char_uuid}")
        return True
    except Exception as e:
        logger.error(f"Error sending command'{command} to characteristic {command_char_uuid}': {e}")
        return False


def notification_handler(sender, data: bytearray):
    """Notify callback. Enqueue raw data without block"""
    try:
        data_queue_raw.put_nowait(data)
    except queue.Full:
        logger.warning("data_queue_raw full, discarded packet")
    except Exception as e:
        logger.exception(f"Error in notification_handler: {e}")
