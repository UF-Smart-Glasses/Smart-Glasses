import queue
import socket
import threading

from core import config
from core.shared_mem import SharedMem

# ints that would never be returned as number of packets lost:
SEQUENCE_LATE = 0
SEQUENCE_FIRST = -1
SEQUENCE_IN_ORDER = -2


udp_shutdown_event = threading.Event()


# helper class to check in what sequence packets are arriving
class SequenceTracker:
    def __init__(self):
        self.expected = None

    def update(self, sequence):
        sequence &= 0xFFFFFFFF

        if self.expected is None:
            self.expected = (sequence + 1) & 0xFFFFFFFF # for unsigned 32 bit behavior
            return SEQUENCE_FIRST

        diff = (sequence - self.expected) & 0xFFFFFFFF

        if diff == 0:
            self.expected = (self.expected + 1) & 0xFFFFFFFF
            return SEQUENCE_IN_ORDER

        # Interpret diff as signed 32-bit and check if negative (meaning its late)
        if diff & 0x80000000:
            return SEQUENCE_LATE

        # Packet is ahead of what we expected
        missed = diff

        self.expected = (sequence + 1) & 0xFFFFFFFF

        return missed 



def udp_receiver_thread(shared_mem: SharedMem) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)

    sock.settimeout(1.0)  # time-out to check udp_shutdown
    sock.bind((config.HOST, config.PORT))

    print(f"[System] UDP Server listening on {config.HOST}:{config.PORT}")

    # instantiate before loop, so that a new one is not created for each loop iteration
    sequence_tracker = SequenceTracker()

    while not udp_shutdown_event.is_set():
        try:
            data, addr = sock.recvfrom(65507)
            if not data:
                continue

            if len(data) < 5:
                print("[System] Received malformed UDP packet.")
                continue

            header = data[0:1]
            if header not in (config.HEADER_VISION, config.HEADER_AUDIO):
                print("[System] Received unknown type of packet/corrupt packet.")
                continue

            sequence = int.from_bytes(
                data[1:5],
                byteorder="big"
            )

            payload = data[5:]
            
            result = sequence_tracker.update(sequence)

            # Only alert how many are missing and latest sequence if packets are missing
            if result > 0:
                print(f"[System] UDP sequence: {sequence} -> missing {result} packet(s)")

            if header == config.HEADER_VISION:
                if shared_mem.vision_queue.full():
                    try:
                        shared_mem.vision_queue.get_nowait()
                    except queue.Empty:
                        pass
                shared_mem.vision_queue.put_nowait(payload)

            elif header == config.HEADER_AUDIO:
                if shared_mem.audio_queue.full():
                    try:
                        shared_mem.audio_queue.get_nowait()
                    except queue.Empty:
                        pass
                shared_mem.audio_queue.put_nowait(payload)

        except socket.timeout:
            continue
        except Exception as e:
            if not udp_shutdown_event.is_set():
                print(f"[System] UDP Error: {e}")

    sock.close()
    print("[System] UDP socket closed.")