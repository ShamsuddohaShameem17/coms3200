"""
@file    assign1.py
@author  Shamsuddoha Shameem s4xxxxxx
@date    24/03/2019
@brief   Retrieve a ﬁle on a webserver via HTTP protocol
@Reference a1.pdf (COMS3200)
    usage: python3 assign1.py url
"""

# imports
import datetime
import socket
import warnings
from urllib.parse import urlsplit

import sys

# Global variable
clientIP, clientPort = (0,0) 

# Converts GMT time to AEST time
def GMT_to_AEST_timezone(time):
    date = datetime.datetime.strptime(time, '%a, %d %b %Y %H:%M:%S %Z')
    # Change the date into local timezone setting AEST
    aestDate = date.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)
    time_format = "%d/%m/%Y %H:%M:%S AEST"
    return aestDate.strftime(time_format)
pass

# Return current Client Address Info
def client_address():
    # Get current host ip and port details using UDP socket
    dummySock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    dummySock.connect(("8.8.8.8", 80))
    clientAddrInfo = dummySock.getsockname()
    clientIP = clientAddrInfo[0]
    clientPort = clientAddrInfo[1]
    dummySock.close()
    return clientIP, clientPort
pass   

# Recieve response and data (encoded) from the server
def server_response(sock):
    CLRF = b"\r\n\r\n"
    data = recv_data(sock)
    response = data.split(CLRF)[0].decode()
    data = data.split(CLRF)[1]
    return (response, data)
pass

# Set the client IP and PORT from it's address
clientIP, clientPort = client_address()

# Recieve complete data from the socket recieve
def recv_data(sock):
    totalData = []
    while True:
        # Data are in bytes
        data = sock.recv(4096)
        if not data: break
        totalData.append(data)
    return b''.join(totalData)
pass


# Write data to a file from its type
def write_data_to_file(data, type):
    outputFile = open(("output" + type), "wb")
    # write data into the output file
    outputFile.write(data)
pass


# Find the right file extension (accept: MIMETYPE)
def find_file_extension(type):
    if (type == "text/plain"):
        return ".txt"
    elif (type == "text/html"):
        return ".html"
    elif (type == "text/css"):
        return ".css"
    elif (type == "application/javascript" or type == "text/javascript"):
        return ".js"
    elif (type == "application/json"):
        return ".json"
    else:
        return ""
    pass
pass
    

# Set the TCP client connection to URL
def TCP_client_connection(sock, URL):
    # Re-format URL for the TCP connection
    clientSock = sock
    parsedURL = urlsplit(URL)
    serverHostName = parsedURL.netloc if 'http' in URL else parsedURL.path.split('/')[0]
    parsedPath = parsedURL.path if 'http' in URL else '/' + parsedURL.path.split('/')[
        1] if '/' in parsedURL.path else parsedURL.netloc
    path = '/' if parsedPath == '' else parsedPath

    # Get address info
    af, socktype, proto, canonname, sa = socket.getaddrinfo(serverHostName, 80)[0]
    serverIP, serverPort = sa

    # Start connection
    clientSock.connect(sa)

    # Get HTTP response
    CRN = "\r\n"
    CLRF = "\r\n\r\n"
    acceptType = "Accept: {0},{1},{2},{3},{4},{5}". \
        format("text/plain", "text/html", "text/css", "application/javascript", "application/json",
               "application/octet-stream")
    acceptLang = "Accept-Language: en-us,en;q=0.5"
    acceptEnc = "Accept-Encoding: UTF-8"
    acceptChar = "Accept-Charset: ISO-8859-1,UTF-8;q=0.7"
    message = " {2} HTTP/1.1{0}" \
                  "Host: {1}{0}" \
                  "User-Agent: Chrome/72.0.3626.121{0}" \
                  "{3}{0}{4}{0}{5}{0}{6}{0}" \
                  "Keep-Alive: 115{0}Connection: close{7}". \
        format(CRN, serverHostName, path, acceptType, acceptLang, acceptEnc, acceptChar, CLRF)

    # Get HTTP response data
    request = "GET" + message
    clientSock.sendall(request.encode())
    response , data = server_response(clientSock)
    clientSock.close()

    # Fix up the response
    responseList = str(response).strip().split('\r\n')
    statusRaw = responseList[0][9:12]
    statusReason = responseList[0][12:]
    return {'serverIP': serverIP, 'serverPort': serverPort,
            'data': data, 'responseRaw': response, 'responseList': responseList,
            'status': int(statusRaw), 'statusReason': statusReason}
pass

# Base functionality of the assignment 1
def base_function(URL):
    if 'https://' not in URL:
        # setup a TCP client socket
        clientSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #clientIP, clientPort = client_address()

        # Get TCP response
        TCPResponse = TCP_client_connection(clientSock, URL)
        status = TCPResponse['status']
        statusReason = TCPResponse['statusReason']
        serverIP = TCPResponse['serverIP']
        serverPort = TCPResponse['serverPort']
        responseList = TCPResponse['responseList']
        headers = dict(item.strip().split(":", 1) for item in responseList[1:] if len(item.split(":", 1)) == 2)
        for key in headers:
            headers[key] = headers[key].strip()
        printMessage = list()
        printMessage.append("Client: {0} {1}".format(clientIP, clientPort))
        printMessage.append("Server: {0} {1}".format(serverIP, serverPort))

        if (status >= 400):
            printMessage.append("Retrieval Failed ({0})".format(status))
        elif (status >= 300):
            newLocation = headers['Location']
            # Empty the print message so we print directly
            printMessage = list()
            print("Client:", clientIP, clientPort)
            print("Server:", serverIP, serverPort)
            reason = statusReason.lstrip().lower().split(" ")[1]
            print("Resource", reason, "moved to", newLocation)
            base_function(newLocation)
        elif (status == 200):
            # Assuming OK status is recieved
            date_accessed = GMT_to_AEST_timezone(headers['Date'])
            printMessage.append("Retrieval successful")

            if 'Content-Type' in headers:
                data = TCPResponse['data']
                fileType = headers['Content-Type'].split("; ")[0]
                write_data_to_file(data, find_file_extension(fileType))
            printMessage.append("Date Accessed: {0}".format(date_accessed))

            try:
                last_modified = GMT_to_AEST_timezone(headers['Last-Modified'])
                printMessage.append("Last Modified: {0}".format(last_modified))
            except KeyError:
                printMessage.append("Last Modified not available")
        for i in printMessage:
            print(i)
    else:
        print("HTTPS Not Supported")
    pass
pass


# Main function call
def main(URL):
    print("URL Requested:", URL)
    base_function(URL)
pass


# Python __main__ call to redirect to main()
if __name__ == "__main__":
    if len(sys.argv) == 2:
        URL = sys.argv[1]
        main(URL)
    else:
        warnings.warn("Please provide an url.\nusage:\t python3 assign1.py url")
