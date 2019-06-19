"""
Example CLI output
python3 assign2.py 192.168.1.1/24 1024 
> gw get 
None 
> gw set 192.168.1.30 
> gw get 
192.168.1.30 
> msg 192.168.1.2 "hello" 
No ARP entry found 
> arp get 192.168.1.2 
None 
> arp set 192.168.1.2 2222 
> arp get 192.168.1.2 
2222 
> msg 192.168.1.2 "hello" 
> mtu get 
1500 
> mtu set 1600 
> mtu get 
1600 
Message received from 192.168.1.2: "hello there, thankyou for your message" 
Message received from 192.168.1.3 with protocol 0x06 
> exit
"""

#Imports python module
import warnings
import sys
import socket
import threading

net_port = 0
ip_address = ""
CIDR_mask = 0
gw_ip = 'None'
ARP_table = {} #Just an empty dictionary
msg_to_send = {}
mtu =1500
default = {'gw':gw_ip,'gw_port':net_port, 'ip_address':ip_address,'mtu':mtu}

def default_command():
    return str(input("> "))

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
    return


def main(argv):
    if len(argv) != 3:
        print("Usage: python3 assign3.py ip-addr ll-addr")
        return
    prog,ip_address_cidr,net_port = argv
    ip_address,CIDR_mask = ip_address_cidr.split('/')
    CIDR_mask=int(CIDR_mask)
    if(len(ip_address.split('.'))!=4 or ((0<int(CIDR_mask)<32))):
        return
    #Handle cli
    cli_command()
pass    

if __name__ == "__main__":
    main(sys.argv)