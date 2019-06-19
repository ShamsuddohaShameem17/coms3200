##Updates from v1: It includes CLI commands as V1 and it can check CIDR of an IP
#Imports python module
import sys
import socket
import threading

ll_address = 0 # port
ip_address = ""
gw_ip = 'None'
ARP_table = {} #Just an empty dictionary
msg_to_send = {}
mtu =1500
default = {'gw':gw_ip,'gw_port':ll_address, 'CIDR':0, 'ip_address':ip_address,'mtu':mtu}

def check_valid_ip(ip):
    ret = int(ip.split('.')[3])<255 and ip!='0.0.0.0' and ip !='255.255.255.255'
    return ret
pass    


def check_IP_in_subnet(ip,cidr =default['CIDR']):
    if(not check_valid_ip(ip)):
        print("Not a valid IP.")
        return
    temp= list()
    for i in range(int(cidr/8)):
        temp.append('255')
    if((cidr%8)!=0):
        #oct = bin(cidr%8)[2:]+(8-cidr%8)*'0'
        oct = (cidr%8)*'1'+(8-cidr%8)*'0'
        temp.append(str(int(oct,2)))
    while(len(temp)<4):
        temp.append('0')  
    pass
    
    subnet_mask = '.'.join(temp)     
    network_id = list()
    network_ip = [int(x) for x in default['ip_address'].split('.')]
    
    for i in range(4):
        network_id.append(int(subnet_mask.split('.')[i])&network_ip[i])
    #print("network_id: ",network_id)
    network_id = map(str,network_id)
    default["network_id"]='.'.join(network_id)
    default["subnet_mask"] = subnet_mask

    test1= ip.split('.')[:int(cidr/8)] == default["network_id"].split('.')[:int(cidr/8)]
    if((cidr%8)!=0):
        # require additional test
        oct = str(int(((cidr%8)*'1'+(8-cidr%8)*'0'),2))
        max_val = (255-int(oct)) + int(default["network_id"].split('.')[int(cidr/8)])
        test2 = max_val > (int(ip.split('.')[int(cidr/8)]))
        # Calculate the broadcast id
        broadcast_id = default["network_id"].split('.')
        broadcast_id[int(cidr/8)] = str(max_val)
        index = int(cidr/8)+1
        while(index<4):
            broadcast_id[index]='255' #if index!=3 else '254'
            index+=1
        default['broadcast_id']='.'.join(broadcast_id) 
        broadcast_id = default['broadcast_id']

        # print("oct",oct,"max_val:",max_val,(255-int(ip.split('.')[int(cidr/8)])))
        return test1 and test2
    return test1
pass    

def default_command():
    return str(input("> "))

def help():
    print("list of commands:\r\n------------------")
    print(" gw set [ip-addr] : set the gateway IP address"+ 
    "\r\n gw get : print the currently stored gateway IP address "+
    "\r\n arp set [ip-addr] [ll-addr] : insert into the host’s ARP table \r\n arp get [ip-addr] : print the currently stored port mapped to [ip-addr]"+ 
    "\r\n exit : terminate the program")
    print(" msg [ip-addr] [payload] : send a virtual IPv4 packet to [ip-addr] with the given payload ")
    print(" mtu set [value] : set the MTU \r\n mtu get : print the currently stored MTU")
    print(" dbg : prints the debug information")    
pass

def debug():
    for i in range(len(list(default))):
        print(list(default)[i],":",list(default.values())[i])
    pass    
pass    

def gw_get():
    return default.get('gw')

def gw_set(s):
    default['gw']= s if(len(s.split('.'))==4) else default.get('gw')
    return
def arp_get(ip):
    return ARP_table.get(ip)
def arp_set(s):
    if(len(s.split())!=2):
        return
    ip,port = s.split()
    if(len(ip.split('.'))!=4):
        return
    ARP_table[ip] = int(port)
    return

def mtu_get():
    return default.get('mtu')

def mtu_set(s):
    res = int(s)
    mtu = res if res>100 else default.get('mtu') 
    default['mtu']=mtu
    return 



def msg_command(s):
    if(len(s.split())!=2):
        return
    ip,msg = s.split()
    if(ip==gw_get() or ARP_table.__contains__(ip)):
        msg_to_send[ip]=msg
    else:
        if(not ARP_table.__contains__(ip)):
            print("No ARP entry found")
    return    

def cli_command():
    while(1):
        out = default_command()
        if(out == 'exit'):
            return
        elif(out == "gw get"):
            print(gw_get())
        elif("gw set" in out):
            gw_set(out[len("gw set "):])
        elif("arp get" in out):
            print(arp_get(out[len("arp get "):]))
        elif("mtu get" in out):
            print(mtu_get()) 
        elif("arp set" in out):
            arp_set(out[len("arp set "):])
        elif("mtu set" in out):
            mtu_set(out[len("mtu set "):])    
        elif("msg" in out):
            msg_command(out[len("msg "):])
        elif(out == 'help'):
            help()  
        elif(out == 'dbg'):
            debug()            
    return


def main(argv):
    if len(argv) != 3:
        print("Usage: python3 assign3.py ip-addr ll-addr")
        return
    prog,ip_address_cidr,ll_address = argv
    ip_address,CIDR_mask = ip_address_cidr.split('/')
    CIDR_mask=int(CIDR_mask)
    default['CIDR']=CIDR_mask
    default['ip_address']= ip_address
    if(len(ip_address.split('.'))!=4 or not((0<int(CIDR_mask)<32))):
        return
    #Handle cli
    print(check_IP_in_subnet('172.10.60.17',CIDR_mask))
    cli_command()

pass    

if __name__ == "__main__":
    main(sys.argv)