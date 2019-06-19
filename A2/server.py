import socket
import sys
from scapy.packet import Packet
from scapy.fields import ByteField, ShortField, BitField
from scapy.all import raw


LOCALHOST = "127.0.0.1"
FILE_NAME = "file.txt"

PACKET_SIZE = 1472
PAYLOAD_SIZE = 1466
PAYLOAD_SIZE_BITS = PAYLOAD_SIZE * 8

RECV_SIZE = 1500

SEND_MODE = "Sent packet to"
RECV_MODE = "Received packet from"

def free_port():
    dummy = socket.socket()
    dummy.bind((LOCALHOST,0))    # Bind to a free port provided by the host computer. (port 0)
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
DEBUG Level 2 - Print packet headers + data
"""


class Connection:
    def __init__(self, my_ip, my_port, debug_level=1):
        self._my_info = (my_ip, my_port)
        self._socket = None
        self._seq_num = 1
        self._debug_level = debug_level

    def _print(self, pkt, port, mode):
        output = ""
        if self._debug_level > 0:
            output += "{} port {}:\n    (seq_num={}, ack_num={}, flags={}{}{}{}{})".format(mode, port, pkt.seq_num,
                        pkt.ack_num, pkt.ack_flag, pkt.nak_flag, pkt.get_flag, pkt.dat_flag, pkt.fin_flag)
        if self._debug_level == 2:
            output += "\n    Data: {}".format(repr(int_to_str(pkt.data)))
        print(output + "\n")

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
        self._socket.sendto(raw(pkt), self._client_info)
        self._seq_num += 1
        self._print(pkt, self._client_info[1], SEND_MODE)

    def recv_pkt(self):
        raw_data, info = self._socket.recvfrom(RECV_SIZE)
        self._client_info = info
        assert len(raw_data) <= PACKET_SIZE, "Received overlong packet: " + repr(raw_data)
        try:
            return RUSH(raw_data), info
        except:
            assert False, "Could not decode packet: " + repr(raw_data)

    def run(self):
        # serv_ack = RUSH(seq_num=self._seq_num, ack_num=1, fin_flag=0, ack_flag=1)
        while True:
            pkt, info = self.recv_pkt()
            #self._client_info = info
            self._print(pkt, info[1], RECV_MODE)
            ##ADDED
            # self._socket.sendto(raw(serv_ack), self._client_info)
            # self._seq_num += 1
            # self._print(serv_ack, self._client_info[1], SEND_MODE)
            ###END
            if pkt.fin_flag == 1 and all(i == 0 for i in (pkt.ack_flag, pkt.nak_flag, pkt.dat_flag, pkt.get_flag)):
                cli_fin_ack = RUSH(seq_num=self._seq_num, ack_num=pkt.seq_num, fin_flag=1, ack_flag=1)
                self._socket.sendto(raw(cli_fin_ack), self._client_info)
                self._seq_num += 1
                self._print(cli_fin_ack, self._client_info[1], SEND_MODE)

                while True:
                    serv_fin_ack, info = self.recv_pkt()
                    self._print(serv_fin_ack, info[1], RECV_MODE)
                    if serv_fin_ack.fin_flag == 1 and serv_fin_ack.ack_flag == 1 and \
                            all(i == 0 for i in (serv_fin_ack.nak_flag, serv_fin_ack.dat_flag, serv_fin_ack.get_flag)):
                        return  # end of connection
            elif pkt.dat_flag == 1:
                ack = RUSH(seq_num=self._seq_num, ack_num=pkt.seq_num, dat_flag=1, ack_flag=1)
                self._socket.sendto(raw(ack), self._client_info)
                self._seq_num += 1
                self._print(ack, self._client_info[1], SEND_MODE)


def main(argv):
    if len(argv) >1:
        print("Usage: python3 server.py [verbosity]")
        return

    my_port = free_port()
    print("[port] <client> <server> :",free_port(),my_port)

    debug_level = 1
    if len(argv) > 2:
        if argv[1] in ("0", "1", "2"):
            debug_level = int(argv[1])

    # conn = Connection(LOCALHOST, my_port, debug_level)
    # if not conn.connect():
    #     return

    try:
        # clientResp, clientInfo= conn.recv_pkt()

        # Fix up the response
        # print("Raw:",raw(clientResp))
        # responseList = str(clientResp).strip().split(' ')
        # print("AS LIST\r\n::",responseList)
        # print("ENCODE\r\n::",*responseList)
        # print("REPR\r\n::",repr(*responseList))
        ack = RUSH(seq_num=2, ack_num=1, dat_flag=1, ack_flag=1)
        print(raw(ack))
        print(repr(ack))



        # conn.run()
    except AssertionError as e:
        print(e.args[0])

    # conn.close()

if __name__ == "__main__":
    main(sys.argv)



#(<RUSH  seq_num=1 ack_num=0 ack_flag=0 nak_flag=0 get_flag=1 dat_flag=0 fin_flag=0 reserved=0 data=120753360189176235089216481375646866551087056283378995295053589602654854479513807332288796834951652007005902952132704420883146269668132750972282066739744348076091253368658182177878230159514170158703139850579047114875292567320847361515827245918744168958899765489471831639360558933687315146319123407884005129597418194116729832359692468979945717071084658020864834080311941442893427153823473609694906076777258901712554197621439471415018591469053911308573525105927656417237546968048985802707802224743742751307189361465800358384624770684873244110701836161662740220755140345219537662273725623009663268368565614478973804438917420732272438707334873546521852533628676921487444221607153121939826847461981164190253816243292888608390134896482478194515129318557030878948685876984275668813189804117511292787517953261919147355364389160231205038672144416747773152943676599423258385482796219169727338220273452348972161152535191372648717001155699896949973016067052894766680313729356450016903687021246974097194037654229844740679458529971366725128477053196536029569067165250514760745868153508205362978236122203672992931912966443434729496969109394376807024390994156023579187681724283894632120402850612355004901239020850720988373856216466083199497280905295763019268492619373610730752432276986185073909527084536400661584094450573875690668152711179501722326111635805469213903462353155603673991613406549406659776749144653949413098336391348911283839209941201223031737389807998633461124160047056456307056410142227598997724247275183796594288082230796504097414716527866777523797831473469547120362971850959159714008329375887793063201260941096793952783088558856646725608517265599725084384724563175899484728186995560290568807291826555071559466892036519612760220504602699914138367068172472017213682774967498701887581576623161758571812333859780259447306697217030079578897235635328736690869036673780574492864633992100216409926170704123909251778840227826004818156537128033200631508772626830227107036373126584283677145476537983934858713880890243734239692788929504571485237756978946897771534216268580118435819518265287019848284025634777877074995766690365323398182981407785286242127618931820406732964653930660155758461208175370783585128691434623046359931898162186733757111302033596729049254009030509216321711163892102827871675454454391781347802586564248032221168741170776241572147775258040040329627458131907667392605393963294455058024940357403275791857029672922704683845333640092279148461815166308612371919572404842591354551966759265854906305023113373464153225704383499664936527466246223661476797869951210031469586761543084810274429135013965707334631732702337824841740330567658750228268691074058230045179042525582463280738205215738570654990878750743473632964015238272734962837192587340749388049536691858127130119105897250796730422035633135852911912554197394401571728824866266035486632334893434781082989891682391872173497252507844118543080852524070954189044447189720419596997871318131061371754953084300140537999671269133877760556091565082970148447134663456996356247831557843817944052398872204541240300181655678829009153525040619726608338891378901153809526162389142748033770813670802228951206999025991977794242984873993367091968935438558744197934101316517229803133561417224142350165889451321851528767924907247493359835935276489293354822841055106711722938546805389980577020010960906614259775846332553974329644809666989569988315925588056744474717370644710641738559779564955115885584929625371493114354608121617916447497642500228004782706320382255759265948054495519710027710464 |>, ('127.0.0.1', 8331))