import asyncio
import serial
import json
import threading
import time
import re
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
import sys

class SerialConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'serial_group'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        self.serial_connections = {}  # COM port connections
        self.serial_threads = {}  # Threads per COM port
        self.previous_data = {}  # Previous data per COM port
        self.printed_lines = {}  # Printed line tracking per COM port

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get('command')

        if command in ['start_serial', 'start_communication']:
            await self.start_serial_communication(data)

    async def start_serial_communication(self, data):
        com_port = data.get('com_port')
        baud_rate = data.get('baud_rate')
        parity = data.get('parity')
        stopbits = data.get('stopbit')
        bytesize = data.get('databit')
        self.card = data.get("card")

        if com_port in self.serial_connections:
            print(f"{com_port} is already running.")
            return

        if await self.configure_serial_port(com_port, baud_rate, parity, stopbits, bytesize):
            command_message = "MMMMMMMMMM"  # Example command
            self.serial_connections[com_port].write(command_message.encode('ASCII'))

            serial_thread = threading.Thread(
                target=self.serial_read_thread,
                args=(com_port,),
                daemon=True
            )
            self.serial_threads[com_port] = serial_thread
            serial_thread.start()

    async def configure_serial_port(self, com_port, baud_rate, parity, stopbits, bytesize):
        try:
            if not all([com_port, baud_rate, parity, stopbits, bytesize]):
                print("Missing parameters.")
                return False

            ser = serial.Serial(
                port=com_port,
                baudrate=int(baud_rate),
                bytesize=int(bytesize),
                timeout=None,
                stopbits=float(stopbits),
                parity=parity[0].upper()
            )
            self.serial_connections[com_port] = ser
            print(f"✅ Connected to {com_port}")
            return True
        except (ValueError, serial.SerialException) as e:
            print(f"❌ Error opening {com_port}: {e}")
            return False

    def is_valid_message(self, message):
        """
        Validates message format:
        A+ddddddB+ddddddC+ddddddD+/-dddddd
        """
        return re.match(r"^A[+-]\d{6}B[+-]\d{6}C[+-]\d{6}D[+-]\d{6}$", message) is not None

    def serial_read_thread(self, com_port):
        try:
            ser = self.serial_connections[com_port]
            accumulated_data = ""

            while True:
                if ser.is_open and ser.in_waiting > 0:
                    received_data = ser.read(ser.in_waiting).decode('ASCII', errors='ignore')
                    accumulated_data += received_data

                    if '\r' in accumulated_data:
                        messages = accumulated_data.split('\r')
                        accumulated_data = messages.pop()

                        for message in messages:
                            message = message.strip()
                            if message and self.is_valid_message(message):
                                length = len(message)

                                if self.previous_data.get(com_port) != message:
                                    self.previous_data[com_port] = message
                                    self.print_com_port_data(com_port, message, length)

                                    async_to_sync(self.channel_layer.group_send)(self.group_name, {
                                        'type': 'serial_message',
                                        'message': message,
                                        'com_port': com_port,
                                        'length': length
                                    })

                time.sleep(0.1)
        except Exception as e:
            print(f"❌ Error in serial read thread for {com_port}: {str(e)}")
        finally:
            if ser and ser.is_open:
                ser.close()
            self.serial_connections.pop(com_port, None)
            self.serial_threads.pop(com_port, None)

    def print_com_port_data(self, com_port, message, length):
        """
        Print data cleanly per COM port
        """
        if com_port not in self.printed_lines:
            print(f"{com_port}: {message} (Length: {length})")
            self.printed_lines[com_port] = True
        else:
            print(f"\n{com_port}: {message} (Length: {length})", end="")

        sys.stdout.flush()

    async def serial_message(self, event):
        await self.send(text_data=json.dumps({
            'com_port': event['com_port'],
            'message': event['message'],
            'length': event['length']
        }))



import json
import threading
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer

from gpiozero import DigitalOutputDevice, DigitalInputDevice
from time import sleep


class KeypadController:
    def __init__(self):
        self.mode = "NUM"
        self.callback = None  # This gets overwritten on every new connect

        # Keypad 1
        self.rows_1 = [DigitalOutputDevice(pin, active_high=False, initial_value=False) for pin in [5, 6, 13, 19]]
        self.cols_1 = [DigitalInputDevice(pin, pull_up=True) for pin in [12, 16, 20, 21]]
        self.KEYPAD_1 = [
            ["1", "2", "3", "UP"],
            ["4", "5", "6", "RGT"],
            ["7", "8", "9", "LFT"],
            ["0", "START/STOP", "ENT", "DWN"]
        ]

        # Keypad 2
        self.rows_2 = [DigitalOutputDevice(pin, active_high=False, initial_value=False) for pin in [27, 26, 25, 24]]
        self.cols_2 = [DigitalInputDevice(pin, pull_up=True) for pin in [17, 18, 22, 23]]
        self.KEYPAD_2 = [
            ["C1", "C2", "C3", "V-Key"],
            ["C4", "C5", "C6", "TAB"],
            ["F1", "F2", "F3", "F6"],
            ["F9", "F10", "ALP/NUM", "F12"]
        ]

    def set_callback(self, callback):
        self.callback = callback
        print("[KeypadController] Callback set!")

    def handle_key(self, key):
        if key == "ALP/NUM":
            self.mode = "ALPHA" if self.mode == "NUM" else "NUM"
            print(f"[MODE SWITCH] Changed to {self.mode}")
        else:
            print(f"[{self.mode}] Key Pressed: {key}")

    def scan_keypad(self, rows, cols, KEYPAD, label):
        for r in rows:
            r.off()

        for row_idx, row_pin in enumerate(rows):
            row_pin.on()
            sleep(0.01)
            for col_idx, col_pin in enumerate(cols):
                if col_pin.is_active:
                    key = KEYPAD[row_idx][col_idx]
                    print(f"[{label}] Raw Key: {key}")
                    self.handle_key(key)

                    if self.callback:
                        self.callback({"key": key, "mode": self.mode})

                    while col_pin.is_active:
                        sleep(0.05)
                    sleep(0.1)
            row_pin.off()

    def run(self):
        print("Press keys on the keypad. Use ALP/NUM to toggle modes.")
        try:
            while True:
                self.scan_keypad(self.rows_1, self.cols_1, self.KEYPAD_1, "Keypad 1")
                self.scan_keypad(self.rows_2, self.cols_2, self.KEYPAD_2, "Keypad 2")
                sleep(0.05)
        except KeyboardInterrupt:
            print("\n[EXITING KeypadController]")


# Global instance shared across WebSocket connections
keypad_controller = None
keypad_thread = None


class KeypadConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        global keypad_controller, keypad_thread

        await self.accept()

        # New callback for this connection
        def send_key(data):
            try:
                async_to_sync(self.send)(text_data=json.dumps(data))
            except Exception as e:
                print(f"[WebSocket Send Error] {e}")

        if keypad_controller is None:
            keypad_controller = KeypadController()
            keypad_controller.set_callback(send_key)

            keypad_thread = threading.Thread(target=keypad_controller.run)
            keypad_thread.daemon = True
            keypad_thread.start()
            print("[KeypadConsumer] Started keypad thread.")
        else:
            # Re-register callback for new connection
            keypad_controller.set_callback(send_key)
            print("[KeypadConsumer] Updated callback for new client.")

    async def disconnect(self, close_code):
        print(f"[WebSocket] Disconnected client (code {close_code})")
        # Optionally: you could clear the callback if no more clients are connected
        pass
