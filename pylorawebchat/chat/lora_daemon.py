import datetime
import sys
import threading
import time
import serial.threaded
from redis import Redis

from config.settings.base import env
import random

from .models import Node
from .models import Message as MessageModel


class Message(object):
    """
    Messages Object
    """

    def __init__(self, address: str = None, msg: str = None):
        self.address: str = address
        self.msg: str = msg

    def from_string(self, message_string: str):
        self.address = message_string[:4]
        self.msg = message_string[4:]
        print("{}: {}".format(self.address, self.msg))

    def to_string(self):
        return "{:>4}{}".format(self.address, self.msg)


class Daemon(serial.threaded.Protocol):
    """
    LoRa Daemon
    - send every 30 - 60 seconds an RTI messages to broadcast
    - handling messages sending & receiving
    """

    TERMINATOR = b"\r\n"  # serial response terminator

    def __init__(self):
        self.next_rti_broadcast: float = time.time()  # time for next RTI broadcast

        self.message_queue: [Message] = []  # outgoing message queue

        self.active = True  # threat should stay active

        # init serial interface
        self.ser = serial.serial_for_url("/dev/ttyACM0", do_not_open=True)
        self.ser.baudrate = 115200
        self.ser.bytesize = 8
        self.ser.parity = "N"
        self.ser.stopbits = 1
        self.ser.rtscts = False
        self.ser.xonxoff = False

        sys.stderr.write(
            "--- {p.name}  {p.baudrate},{p.bytesize},{p.parity},{p.stopbits} ---\n".format(
                p=self.ser
            )
        )

        try:
            self.ser.open()
        except serial.SerialException as e:
            sys.stderr.write(
                "Could not open serial port {}: {}\n".format(self.ser.name, e)
            )
            sys.exit(1)

        # start serial data receive listener as background process
        self.serial_worker = serial.threaded.ReaderThread(self.ser, self)
        self.serial_worker.start()

        # serial buffer
        self.buffer = bytearray()
        self.transport = None

        # setup serial device
        time.sleep(0.2)
        print("setup device")
        self.ser.write(
            "AT+CFG={},{},{},{},{},{},{},{},{},{},{},{},{}\r\n".format(
                env("CARRIER_FREQUENCY"),
                env("POWER"),
                env("BANDWIDTH"),
                env("SPREADING"),
                env("ERROR_CORRECTION_CODE"),
                env("CRC"),
                env("IMPLICIT_HEADER"),
                env("ONE_TIME_RECEPTION"),
                env("FREQUENCY_MODULATION"),
                env("FREQUENCY_MODULATION_PERIOD"),
                env("RECEIVE_TIMEOUT_TIME"),
                env("USER_DATA_LENGTH"),
                env("PREAMBLE"),
            ).encode()
        )

        # set device address
        time.sleep(0.2)
        print("set device address")
        self.ser.write("AT+ADDR={}\r\n".format(env("DEVICE_ADDRESS")).encode())

        # main background process
        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True  # Daemonize thread
        self.thread.start()  # Start the execution

        # redis queue consumer process
        self.redis_work_consumer: RedisWorkConsumer = RedisWorkConsumer(self)
        self.redis_work_consumer.start()

    def __call__(self):
        return self

    def stop(self):
        """
        stop all processes
        """
        self.active = False
        self.redis_work_consumer.stop()
        self.serial_worker.stop()

    def data_received(self, data: bytes):
        """Buffer received data, find TERMINATOR, call handle_packet"""
        self.buffer.extend(data)
        while self.TERMINATOR in self.buffer:
            packet, self.buffer = self.buffer.split(self.TERMINATOR, 1)
            self.handle_packet(packet)

    def handle_packet(self, packet: bytes):
        """Process packets"""
        incoming_packet: str = packet.decode("utf-8")

        print(incoming_packet)

        # check if packet is a message
        if incoming_packet[:2] == "LR":
            msg: Message = Message(
                msg=incoming_packet[11:], address=incoming_packet[3:7]
            )

            # get or create Node object
            try:
                node: Node = Node.objects.get(address=msg.address)
            except Node.DoesNotExist:
                node: Node = Node(address=msg.address)

            node.save()
            if msg.msg != "RTI":
                node.save()
                message_model: MessageModel = MessageModel(
                    node=node, message=msg.msg, message_type="i", instant_send=True
                )
                message_model.save()

    def send_message(self, msg: str, dest_address: str = "FFFF") -> None:
        """
        send messages via lora
        :param msg:             messages
        :param dest_address:    address
        """
        time.sleep(0.1)
        self.ser.write("AT+DEST={}\r\n".format(dest_address).encode())
        time.sleep(0.1)
        self.ser.write("AT+SEND={}\r\n".format(len(msg)).encode())
        time.sleep(0.1)
        self.ser.write("{}\r\n".format(msg).encode())
        time.sleep(2)

    def add_messages_to_queue(self, address: str, msg: str):
        self.message_queue.append(Message(address=address, msg=msg))

    def send_rti(self):
        print("send RTI: {}".format(datetime.datetime.now()))
        time.sleep(0.1)
        self.ser.write("AT+DEST=FFFF\r\n".encode())
        time.sleep(0.1)
        self.ser.write("AT+SEND=3\r\n".encode())
        time.sleep(0.1)
        self.ser.write("RTI\r\n".encode())  # RTI = routing table information

        # set time for next RTI broadcast
        self.next_rti_broadcast: float = time.time() + random.randint(30, 61)

    def run(self):
        """ main threat to send RTI & messages """
        while self.active:

            if time.time() > self.next_rti_broadcast:
                self.send_rti()

            while len(self.message_queue) > 0:
                msg: Message = self.message_queue.pop(0)
                self.send_message(msg=msg.msg, dest_address=msg.address)

            time.sleep(0.1)


class RedisWorkConsumer(threading.Thread):
    def __init__(self, lora_daemon: Daemon):
        super().__init__()
        self.lora_daemon: Daemon = lora_daemon
        self.redis_con: Redis = Redis(host="redis")
        self.active = True

    def stop(self):
        self.active = False

    def run(self):
        while self.active:
            try:
                message_queue: [bytes, bytes] = self.redis_con.blpop(
                    "message_queue", timeout=1
                )
                message: Message = Message()
                message.from_string(message_queue[1].decode("utf-8"))
                self.lora_daemon.message_queue.append(message)
                print(message.to_string())
            except TypeError:
                continue
