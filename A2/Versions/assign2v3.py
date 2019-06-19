# REF: https://pymotw.com/2/struct/
#Creating a RUSH packet sender
import sys
import socket
from collections import namedtuple
from struct import pack, unpack

LOCALHOST = "127.0.0.1"
LOCAL_ADDR_INFO =(LOCALHOST,0)
PACKET_SIZE = 1472
PAYLOAD_SIZE = 1466
PAYLOAD_SIZE_BITS = PAYLOAD_SIZE * 8
SEND_SIZE = 1500 #Max size of RUSH packet
RECV_SIZE = 1500 #Max size of RUSH packet

SEND_MODE = "Sent packet to"
RECV_MODE = "Received packet from"

#Creating RUSH packets
rushFields = ("seq_num","ack_num","ack_flag","nak_flag","get_flag","dat_flag","fin_flag","reserved","data")
defaultFieldValues = [0,0,0,0,0,0,0,0]
Packet = namedtuple('RUSH', rushFields, defaults = defaultFieldValues)
#pkt.seq_num,pkt.ack_num, pkt.ack_flag, pkt.nak_flag, pkt.get_flag, pkt.dat_flag, pkt.fin_flag


def free_port():
    dummy = socket.socket()
    dummy.bind(LOCAL_ADDR_INFO)    # Bind to a free port provided by the host computer. (port 0)
    freePort = dummy.getsockname()[1]
    dummy.close()
    return freePort  # Return the port number assigned.

def str_to_int(string, pad=PAYLOAD_SIZE):
    b_str = string.encode("UTF-8")
    if pad is not None:
        for i in range(len(string), pad):
            b_str += b'\0'
    return int.from_bytes(b_str, byteorder='big')


def int_to_str(integer, size=PAYLOAD_SIZE):
    return integer.to_bytes(size, byteorder='big').rstrip(b'\x00').decode("UTF-8")

# #This class creates C like struct ex. P = RUSH(packet); p.seq_num = 0... See ctypes _fields_ or collection.namedtuple
# class RUSH(Packet):
#     name = "RUSH"
#     fields_desc = [
#         "seq_num","ack_num","ack_flag","nak_flag","get_flag","dat_flag","fin_flag","reserved","data"
#     ]

#     def __init__(self,packet):
#         self.packet

#     def packet_fields(self,packet=self.packet):
#         # Create a field description of the packet -> Could be a dict or list

#     def construct_packet(self,packet=self.packet):
#         #Construct packet using struct '!' -> Big endian/network 

class RUSH(Packet):
    #packet with default value
    def __init__(self,packet):
        self.packet = packet
    def construct_packet(self):
        #Construct packet using struct '!' -> Big endian/network
        #My concern so far:
        #                   Do I pack the packet at this point or init
        #                   How am I gonna recieve the packet using the same rush structure
        #                   


        pass  


    def _print(self):
        print(repr(self.packet))


#########################################################################################################

class Connection:
    def __init__(self, my_ip, my_port):
        self._my_info = (my_ip, my_port)
        self._socket = None
        self._seq_num = 1

    def _print(self, pkt, port, mode):
        output = "{} port {}:\n    (seq_num={}, ack_num={}, flags={}{}{}{}{})".format(mode, port, pkt.seq_num,
                        pkt.ack_num, pkt.ack_flag, pkt.nak_flag, pkt.get_flag, pkt.dat_flag, pkt.fin_flag)
        output += "\n    Data: {}".format(repr(int_to_str(pkt.data)))
        print(output + "\n")

    def _find_freeport(self):
        return free_port()

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
            #OLD:
            # return RUSH(raw_data), info
             ###########   
        except:
            assert False, "Could not decode packet: " + repr(raw_data)

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

#############################################################################################
def main(argv):
    if len(argv) >= 2:
        print("Usage: python3 assign2.py")
        return

    my_port = free_port()
    serv_port = free_port()
    print("my port:",my_port,"serv port:",serv_port)
    LOCAL_ADDR_INFO = (LOCALHOST,my_port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(LOCAL_ADDR_INFO)
    #========================================================================#

    # conn = Connection(LOCALHOST, my_port, LOCALHOST, serv_port, debug_level)
    # if not conn.connect():
    #     return

    # try:
    #     conn.send_request(FILE_NAME)
    #     conn.run()
    # except AssertionError as e:
    #     print(e.args[0])

    # conn.close()
    sock.close()

if __name__ == "__main__":
    main(sys.argv)