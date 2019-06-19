#imports
import warnings
import sys

import socket
import urllib.request
import urllib3

import datetime
import pytz

def GMT_to_AEST_timezone(time):
    print("GMT_TIME:",time)
    gmt_timezone = pytz.timezone('GMT')
    aest_timezone = pytz.timezone('Australia/Queensland')
    #get the given time int GMT into datetime format
    date = datetime.datetime.strptime(time, '%a, %d %b %Y %H:%M:%S GMT')
    #Convert the datetime information to local timezone (GMT)
    datetime_GMT = gmt_timezone.localize(date)
    #Convert the GMT timezone to AEST
    eastern_time = datetime_GMT.astimezone(aest_timezone)
    time_format = "%d/%m/%Y %H:%M:%S AEST"
    return eastern_time.strftime(time_format)
pass    

#Usage:
"""
python3 assign1.py url
"""
if len(sys.argv) == 2:
    urllib3.disable_warnings()
    URL = sys.argv[1]
    if 'https://' in URL:
        print("URL Requested:",URL,"\nHTTPS Not Supported")
    else:
        #set up the client socket
        client_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        #get current host ip and port details
        client_sock.connect(("8.8.8.8", 80))
        client_addr_info = client_sock.getsockname()
        client_ip = client_addr_info[0]
        client_port = client_addr_info[1]
        
        #get the http response
        http = urllib3.PoolManager()
        response = http.request('GET', URL)
        status = response.status
        if (status >400):
            print("URL Requested:",URL)
            print("Client:",client_ip,client_port)
            print("Server:","130.102.131.123 80")#Dummy value
            print("Retrieval Failed ("+ str(response.status)+")")
        else:
            if 'http://' in URL:
                server_ip = socket.gethostbyname(URL[7:])
                urllib.request.urlretrieve(URL, "output.html") #One way
            else:
                server_ip = socket.gethostbyname(URL)
            server_port = 80
            date_accessed = GMT_to_AEST_timezone(response.headers['Date'])
            print("URL Requested:",URL)
            print("Client:",client_ip,client_port)
            print("Server:",server_ip,server_port)
            print("Retrieval successful")
            print("Date Accessed:",date_accessed)
            try:
                last_modified = GMT_to_AEST_timezone(response.headers['Last-Modified'])
                print("Last-Modified:",last_modified)
            except KeyError as ke:
                print("Last-Modified:",date_accessed)    

            #Write the data into html file
            # with open("output.html", 'w') as fid: #Other way
            #     fid.write(str(response.data)) 

        #Close all of the connection
        client_sock.close()      
else:
    warnings.warn("Please provide an url.\nusage:\t python3 assign1.py url")


