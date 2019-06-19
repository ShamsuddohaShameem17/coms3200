# REF: https://pymotw.com/2/struct/
#Creating a RUSH packet sender
import sys
import socket
import time
from collections import namedtuple
from struct import pack, unpack

LOCALHOST = "127.0.0.1"
LOCAL_ADDR_INFO =(LOCALHOST,0)
PACKET_SIZE = 1472
PAYLOAD_SIZE = 1466
PAYLOAD_SIZE_BITS = PAYLOAD_SIZE * 8
RECV_SIZE = 1500 #Max size of RUSH packet
TIMEOUT = 3
DEBUG = 1

# Creating RUSH packets
rushFields = ("seq_num","ack_num","ack_flag","nak_flag","get_flag","dat_flag","fin_flag","reserved","data")
defaultFieldValues = [0,0,0,0,0,0,0,'']
Packet = namedtuple('RUSH', rushFields, defaults = defaultFieldValues)

# Find free ports by PC
def free_port():
    dummy = socket.socket()
    dummy.bind(LOCAL_ADDR_INFO)    # Bind to a free port provided by the host computer. (port 0)
    freePort = dummy.getsockname()[1]
    dummy.close()
    return freePort  # Return the port number assigned.

# Convert string to integer (byte representation)
def str_to_int(string, pad=PAYLOAD_SIZE):
    b_str = string.encode("UTF-8")
    if pad is not None:
        for i in range(len(string), pad):
            b_str += b'\0'
    return int.from_bytes(b_str, byteorder='big')

# Convert byte (represented as integer) to string (data)
def int_to_str(integer, size=PAYLOAD_SIZE):
    return integer.to_bytes(size, byteorder='big').rstrip(b'\x00').decode("UTF-8")

# Convert the packet into bytes array
def raw(packet):
    # Packet Identifier
    seq_num = packet.seq_num
    ack_num = packet.ack_num
    packet_id_bytes = pack('!hh',seq_num,ack_num)
    # Flags
    ack_flag = packet.ack_flag
    nak_flag = packet.nak_flag
    get_flag = packet.get_flag
    dat_flag = packet.dat_flag
    fin_flag = packet.fin_flag
    flag_list = [ack_flag,nak_flag,get_flag,dat_flag,fin_flag]
    flag_str = "".join(map(str,flag_list))+"000"
    flag_byte = pack("!B",int(flag_str,base=2))
    # Reserved Byte
    reserved = b'\x00'
    #Data
    data_byte = str_to_int(packet.data).to_bytes(PAYLOAD_SIZE, byteorder='big')
    raw_byte =b"".join([packet_id_bytes,flag_byte,reserved, data_byte])
    return raw_byte

# Convert raw packet information into packet (repr)    
def raw_packet_decode(rawByte):
    # First 6 Bytes are RUSH HEADER without payload
    unpacked_data = unpack('!hhBx', rawByte[0:6]) 
    seq_num, ack_num, flag_byte= unpacked_data 
    flags = bin(flag_byte)[2:][:-3]
    flagStr = (5-len(str(flags)))*"0"+str(flags)#first 5 bits
    # Set the flag as list
    flags = [int(c) for c in flagStr] 
    data_info = rawByte[6:].rstrip(b'\x00').decode("UTF-8")
    packet_val_list = [seq_num,ack_num]
    packet_val_list.extend(flags)
    return Packet(*packet_val_list,data = data_info)

def print_packet(packet):
    print(repr(packet))

def validate_packet(packet):
    valid_flag_list = ["10000","01010","00100","00010","00001","10010","10001"]
    flags = list(packet[2:7])
    flags_Str = ''.join(map(str,flags))
    return int(flags_Str in valid_flag_list)
    
class Connection:
    def __init__(self, my_ip, my_port=free_port()):
        self._my_info = (my_ip, my_port)
        self._socket = None
        self._seq_num = 1
        self._file_name = ''
        print(f'{my_port}')
        sys.stdout.flush()

    def _find_freeport(self):
        return free_port()

    def _set_client_port(self, clientPort):
        self._client_port = clientPort
        self._client_info = (LOCALHOST,clientPort)    

    def send_data(self, client_packet, read_pos=0):
        if(self._file_name=='' and client_packet.data!=''):
            self._file_name = client_packet.data
        #Save the reading position    
        self._reading_pos = read_pos    
        file_name =self._file_name
        f = open(file_name, "r")
        f.seek(PAYLOAD_SIZE*read_pos)
        data_read = f.read(PAYLOAD_SIZE)
        serv_dat_flag = Packet(seq_num=self._seq_num, dat_flag = 1,data = data_read)
        # As long data is present, send them
        if(data_read):
            if(self.send(serv_dat_flag)):# successfully sent 
                #time.sleep(0.02) # give client time to process it
                return
        else:
            serv_fin_flag = Packet(seq_num=self._seq_num, fin_flag = 1)
            self.send(serv_fin_flag)
    pass    
            
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

    def send(self,pkt):
        self._socket.settimeout(TIMEOUT)
        self._socket.sendto(raw(pkt), self._client_info)

    def recv_pkt(self):
        try:
            raw_data, info = self._socket.recvfrom(RECV_SIZE)
            client_port = info[1]
            self._set_client_port(client_port)

            assert len(raw_data) <= PACKET_SIZE, "Received overlong packet: " + repr(raw_data)
            try:
                return raw_packet_decode(raw_data),info
            except:
                assert False, "Could not decode packet: " + repr(raw_data)        
        except socket.timeout:
            serv_resend_pack = Packet(seq_num=self._seq_num, dat_flag=1, data=self._file_name)
            self.send_data(serv_resend_pack,self._reading_pos)
        pass   

        
    def send_fin_ack_pkt(self, client_pkt):
        serv_fin_ack = Packet(seq_num=self._seq_num, ack_num=client_pkt.seq_num, fin_flag=1, ack_flag=1)
        self.send(serv_fin_ack)
        self._seq_num += 1

    def run(self):
        reading_pos = 0
        while True:
            pkt = self.recv_pkt()[0]
            if not validate_packet(pkt):
                pass
                #ignore
            else:
                #DEBUG FLAG
                if(DEBUG==1):
                    flags = ''.join(map(str,list(pkt[2:7])))
                    print(f'SEQ_NUM:{pkt.seq_num} ACK_NUM:{pkt.ack_num} flags:({flags}) data:{pkt.data}')
                # Handle fin
                if pkt.fin_flag == 1 and all(i == 0 for i in (pkt.ack_flag, pkt.nak_flag, pkt.dat_flag, pkt.get_flag)):
                    self.send_fin_ack_pkt(pkt)
                    while True:
                        serv_fin_ack = self.recv_pkt()[0]
                        if serv_fin_ack.fin_flag == 1 and serv_fin_ack.ack_flag == 1 and \
                                all(i == 0 for i in (serv_fin_ack.nak_flag, serv_fin_ack.dat_flag, serv_fin_ack.get_flag)):
                            return  # end of connection
                # Handle fin-ack            
                elif pkt.fin_flag == 1 and pkt.ack_flag == 1:
                    self._seq_num+=1
                    self.send_fin_ack_pkt(pkt)
                    return # end of connection
                # Handle dat-ack     
                elif pkt.dat_flag ==1 and pkt.ack_flag == 1:
                    reading_pos +=1
                    self._seq_num+=1
                    self.send_data(pkt,reading_pos)
                # Handle dat-nak     
                elif pkt.dat_flag ==1 and pkt.nak_flag == 1:
                    reading_pos =pkt.ack_num-1
                    self.send_data(pkt,reading_pos)
                # Handle get
                elif pkt.get_flag == 1:
                    self.send_data(pkt)
        pass
        return
    pass
pass               

def main(argv):
    if len(argv) >= 2:
        print("Usage: python3 assign2.py")
        return
    conn = Connection(LOCALHOST)
    if not conn.connect():
        return
    try:
        conn.run()
    except AssertionError as e:
        print(e.args[0])
    conn.close()
pass    

if __name__ == "__main__":
    main(sys.argv)