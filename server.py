import network
import socket
import time
import gc
import sys
from machine import Timer


class ServerEventListener:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))
        self.socket.setblocking(False)

        self.client_registry = {}
        self.next_id = 1
        self.max_clients = 10
        self.timer = Timer(0)

        # Event callbacks definitions
        self.on_message_callback = None
        self.on_connect_callback = None

    def on_connect(self, callback):
        self.on_connect_callback = callback

    def on_message(self, callback):
        self.on_message_callback = callback

    def start(self):
        self.timer.init(period=40, mode=Timer.PERIODIC, callback=self._check_network)

    def broadcast(self, message, skip_addr=None):
        payload = message.encode('utf-8')
        for addr in self.client_registry:
            if addr != skip_addr:
                try:
                    self.socket.sendto(payload, addr)
                except OSError:
                    pass

    def _check_network(self, t):
        try:
            while True:
                try:
                    data, addr = self.socket.recvfrom(1024)
                    if not data:
                        break

                    text = data.decode('utf-8').strip()

                    # Handle new dynamic connections automatically
                    if addr not in self.client_registry:
                        if len(self.client_registry) < self.max_clients:
                            self.client_registry[addr] = self.next_id
                            if self.on_connect_callback:
                                self.on_connect_callback(self.next_id, addr)
                            self.next_id += 1
                        else:
                            self.socket.sendto(b"[SYSTEM] Server Full.", addr)
                            continue

                    if text == "[Hello System]":
                        continue

                    sender_id = self.client_registry[addr]
                    if self.on_message_callback:
                        self.on_message_callback(sender_id, text, addr)

                except OSError:
                    break
        except Exception:
            pass


# --- MAIN APP ARCHITECTURE (NO LOOPS) ---

ap = network.WLAN(network.AP_IF)
ap.active(False);
time.sleep(0.5);
ap.active(True);
time.sleep(0.5)
ap.config(ssid='MyESP32S3_AP', password='password123', channel=6, authmode=network.AUTH_WPA2_PSK)
time.sleep(0.5)

IP_ADDRESS = ap.ifconfig()[0]
PORT = 5005

print("--- REGISTERING SERVER EVENT LISTENERS ---")
server = ServerEventListener(IP_ADDRESS, PORT)


# Defining Event Listeners directly
@server.on_connect
def handle_new_user(client_id, address):
    sys.stdout.write(f"\r\x1b[K[EVENT] Client {client_id} linked up from {address}\nServer > ")


@server.on_message
def handle_incoming_text(client_id, text, address):
    sys.stdout.write(f"\r\x1b[KClient {client_id}: {text}\nServer > ")
    # Echo out to everyone else automatically
    server.broadcast(f"Client {client_id}: {text}", skip_addr=address)


# Fire up the engine
server.start()

try:
    while True:
        gc.collect()
        sys.stdout.write("\r\x1b[KServer > ")
        line = sys.stdin.readline()
        if line:
            msg = line.strip()
            if msg:
                sys.stdout.write(f"\r\x1b[KYou (Server): {msg}\n")
                server.broadcast(f"[SERVER]: {msg}")
except KeyboardInterrupt:
    server.timer.deinit()
    server.socket.close()
    ap.active(False)
