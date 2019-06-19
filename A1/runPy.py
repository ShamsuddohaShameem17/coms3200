import warnings
import sys
import socket
import urllib3

#Usage:
"""
python3 assign1.py url
"""
try:
    url = str(sys.argv[1])
    #set up the client socket
    client_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_port = 80
    server_ip = socket.gethostbyname(url)
    #get current host ip and port details
    #Bind the new socket to some address and port
    client_sock.bind(('0.0.0.0', 0))
    client_addr_info = client_sock.getsockname() # this is a tuple
    client_ip = client_addr_info[0]
    client_port = client_addr_info[1]
    #set the url request handler using urllib3
    # try:
    #     http = urllib3.PoolManager()
    #     r = http.request('GET', 'http://httpbin.org/robots.txt')
    # except    
    http = urllib3.PoolManager()
    response = http.request('GET', url)
    print(response.status)
    print(client_ip,server_ip,server_port)
    print("\n\n")
    client_sock.connect((server_ip,server_port))
    #client_sock.send("HELLO:)")
    data = client_sock.recv(1024)
    print(data)
    client_sock.close()

except IndexError as ie:
    print("Please provide an url.\nusage:\t python3 assign1.py url")


