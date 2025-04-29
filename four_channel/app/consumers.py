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
