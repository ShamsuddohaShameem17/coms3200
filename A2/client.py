import socket
import sys
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, BitField
from scapy.all import raw
import time


LOCALHOST = "127.0.0.1"
FILE_NAME = "file.txt"

PACKET_SIZE = 1472
PAYLOAD_SIZE = 1466
PAYLOAD_SIZE_BITS = PAYLOAD_SIZE * 8

RECV_SIZE = 1500

SEND_MODE = "Sent packet to"
RECV_MODE = "Received packet from"


def str_to_int(string, pad=PAYLOAD_SIZE):
    b_str = string.encode("UTF-8")
    if pad is not None:
        for i in range(len(string), pad):
            b_str += b'\0'
    return int.from_bytes(b_str, byteorder='big')


def int_to_str(integer, size=PAYLOAD_SIZE):
    return integer.to_bytes(size, byteorder='big').rstrip(b'\x00').decode("UTF-8")


class RUSH(Packet):
    name = "RUSH"
    fields_desc = [
        ShortField("seq_num", 0),
        ShortField("ack_num", 0),
        BitField("ack_flag", 0, 1),
        BitField("nak_flag", 0, 1),
        BitField("get_flag", 0, 1),
        BitField("dat_flag", 0, 1),
        BitField("fin_flag", 0, 1),
        BitField("reserved", 0, 11),
        BitField("data", 0, PAYLOAD_SIZE_BITS)
    ]


"""
DEBUG Level 0 - Do not print anything
DEBUG Level 1 - Print packet headers
DEBUG Level 2 - Print packet headers + timestamp
DEBUG Level 3 - Print packet headers + timestamp + data
DEBUG Level 9 - Special test level
"""


class Connection:
    def __init__(self, my_ip, my_port, serv_ip, serv_port, output=sys.stdout, debug_level=1):
        self._my_info = (my_ip, my_port)
        self._serv_info = (serv_ip, serv_port)
        self._socket = None
        self._seq_num = 1
        self._output = output
        self._debug_level = debug_level
        self._start_time = time.time()

    def _print(self, pkt, port, mode, note=""):
        output = ""
        timer = round(time.time() - self._start_time, 4)
        if self._debug_level > 0:
            output += "{} port{}{}:\n    (seq_num={}, ack_num={}, flags={}{}{}{}{}) {}".format(mode, 
                        " " + str(port) if self._debug_level != 9 else "", 
                        " @ {}s".format(timer) if self._debug_level in (2, 3) else "",
                        pkt.seq_num, pkt.ack_num, pkt.ack_flag, pkt.nak_flag, pkt.get_flag, pkt.dat_flag, pkt.fin_flag, 
                        note if self._debug_level != 9 else "")
        if self._debug_level in (3, 9):
            output += "\n    Data: {}".format(repr(int_to_str(pkt.data)))
        self._output.write(output + "\n\n")

    def connect(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.bind(self._my_info)
            return True
        except socket.error as err:
            print("Error encountered when opening socket:\n", err)
            return False

    def close(self):
        self._socket.close()

    def send_request(self, resource):
        pkt = RUSH(seq_num=self._seq_num, get_flag=1, data=str_to_int(resource))
        self._socket.sendto(raw(pkt), self._serv_info)
        self._seq_num += 1
        self._print(pkt, self._serv_info[1], SEND_MODE)

    def recv_pkt(self):
        raw_data, info = self._socket.recvfrom(RECV_SIZE)
        assert len(raw_data) <= PACKET_SIZE, "Received overlong packet: " + repr(raw_data)
        try:
            return RUSH(raw_data), info
        except:
            assert False, "Could not decode packet: " + repr(raw_data)

    def nak(self):
        pkt, info = self.recv_pkt()
        self._print(pkt, info[1], RECV_MODE)
        nak = RUSH(seq_num=self._seq_num, ack_num=1, dat_flag=1, nak_flag=1)
        self._socket.sendto(raw(nak), self._serv_info)
        self._print(nak, self._serv_info[1], SEND_MODE)
        self._seq_num += 1

    def timeout(self):
        pkt, info = self.recv_pkt()
        self._print(pkt, info[1], RECV_MODE)
        # let the server timeout by doing nothing

    def invalid_flags(self):
        """Invalid because the server should be expecting an ACK or a NAK, not a get"""
        pkt, info = self.recv_pkt()
        self._print(pkt, info[1], RECV_MODE)
        invalid = RUSH(seq_num=self._seq_num, ack_num=1, get_flag=1)
        self._socket.sendto(raw(invalid), self._serv_info)
        self._print(invalid, self._serv_info[1], SEND_MODE, note="[INVALID]")

    def invalid_seq(self):
        """Invalid because the server is expecting a packet with sequence number 2"""
        pkt, info = self.recv_pkt()
        self._print(pkt, info[1], RECV_MODE)
        invalid = RUSH(seq_num=self._seq_num+1, ack_num=1, dat_flag=1, ack_flag=1)
        self._socket.sendto(raw(invalid), self._serv_info)
        self._print(invalid, self._serv_info[1], SEND_MODE, note="[INVALID]")

    def invalid_ack(self):
        """Invalid because the server is expecting a packet acknowledging packet 1"""
        pkt, info = self.recv_pkt()
        self._print(pkt, info[1], RECV_MODE)
        invalid = RUSH(seq_num=self._seq_num, ack_num=2, dat_flag=1, ack_flag=1)
        self._socket.sendto(raw(invalid), self._serv_info)
        self._print(invalid, self._serv_info[1], SEND_MODE, note="[INVALID]")

    def run(self):
        while True:
            pkt, info = self.recv_pkt()
            self._print(pkt, info[1], RECV_MODE)
            if pkt.fin_flag == 1 and all(i == 0 for i in (pkt.ack_flag, pkt.nak_flag, pkt.dat_flag, pkt.get_flag)):
                cli_fin_ack = RUSH(seq_num=self._seq_num, ack_num=pkt.seq_num, fin_flag=1, ack_flag=1)
                self._socket.sendto(raw(cli_fin_ack), self._serv_info)
                self._seq_num += 1
                self._print(cli_fin_ack, self._serv_info[1], SEND_MODE)

                while True:
                    serv_fin_ack, info = self.recv_pkt()
                    self._print(serv_fin_ack, info[1], RECV_MODE)
                    if serv_fin_ack.fin_flag == 1 and serv_fin_ack.ack_flag == 1 and \
                            all(i == 0 for i in (serv_fin_ack.nak_flag, serv_fin_ack.dat_flag, serv_fin_ack.get_flag)):
                        return  # end of connection
            elif pkt.dat_flag == 1:
                ack = RUSH(seq_num=self._seq_num, ack_num=pkt.seq_num, dat_flag=1, ack_flag=1)
                self._socket.sendto(raw(ack), self._serv_info)
                self._seq_num += 1
                self._print(ack, self._serv_info[1], SEND_MODE)

SIMPLE_MODE = [Connection.run]
NAK_MODE = [Connection.nak, Connection.run]
MULTI_NAK_MODE = [Connection.nak, Connection.nak, Connection.nak, Connection.run]
TIMEOUT_MODE = [Connection.timeout, Connection.run]
MULTI_TIMEOUT_MODE = [Connection.timeout, Connection.nak, Connection.timeout, Connection.run]
INVALID_SEQ_MODE = [Connection.invalid_seq, Connection.run]
INVALID_ACK_MODE = [Connection.invalid_ack, Connection.run]
INVALID_FLAGS_MODE = [Connection.invalid_flags, Connection.run]

def main(argv):
    if len(argv) <= 2 or not argv[1].isdigit() or not argv[2].isdigit():
        print("Usage: python3 client.py client_port server_port [-m mode] [-v verbosity] [-o output]")
        return

    my_port = int(argv[1])
    serv_port = int(argv[2])

    debug_level = 2
    mode = SIMPLE_MODE
    output = sys.stdout
    for i, arg in enumerate(argv[3:]):
        if arg == "-v" and argv[i+4] in ("0", "1", "2", "3", "9"):
            debug_level = int(argv[i+4])
        elif arg == "-m":
            mode = {"SIMPLE": SIMPLE_MODE, "NAK": NAK_MODE, "MULTI_NAK": MULTI_NAK_MODE, "TIMEOUT": TIMEOUT_MODE,
                    "MULTI_TIMEOUT": MULTI_TIMEOUT_MODE, "INVALID_SEQ": INVALID_SEQ_MODE,
                    "INVALID_ACK": INVALID_ACK_MODE, "INVALID_FLAGS": INVALID_FLAGS_MODE}.get(argv[i+4].upper(), SIMPLE_MODE)
        elif arg == "-o":
            output = open(argv[i+4], "w")

    conn = Connection(LOCALHOST, my_port, LOCALHOST, serv_port, output, debug_level)
    if not conn.connect():
        return

    try:
        conn.send_request(FILE_NAME)
        for method in mode:
            method(conn)
    except AssertionError as e:
        print(e.args[0])

    conn.close()
    if output != sys.stdout:
        output.close()

if __name__ == "__main__":
    main(sys.argv)