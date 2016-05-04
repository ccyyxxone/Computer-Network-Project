import socket
import sys
import datetime
import struct

#default value
IP='localhost'
port=41194
filename='receivefile.txt'
senderIP = 'localhost'
senderPort = 41191
logfile_name='Receiverlog.txt'

#arguments
if len(sys.argv)==6:
    port = int(sys.argv[2])
    filename = sys.argv[1]
    senderIP = sys.argv[3]
    senderPort = int(sys.argv[4])
    logfile_name = sys.argv[5]

sender = (senderIP, senderPort)
file1=open(filename,'w+')

#Socket
address = (IP, port)   
ReceiverSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
ReceiverSock.bind(address) 

#the value of MSS is as same as in sender
MSS=500
FileACK=0

#initialize logfile
file2 = open(logfile_name,'w')
try:
    file2.write('')
finally:
    file2.close()


print 'start!'

#receive TCP segment and send ACK
while True:
    #receive
    TCPSegment,addr = ReceiverSock.recvfrom(1024)
    Length = len(TCPSegment)
    DataLength = Length - 20 #minus 20 TCPHead
    
    #unpack the TCP segment
    senderPort1, port1, Sequence, AcknowledgeNumber, HeadLength_and_flags, AcceptWindow, checksum, EmergencyPointer, Data = struct.unpack('HHIIHHHH'+str(DataLength)+'s',TCPSegment)
    
    if HeadLength_and_flags == 20497:
        break
    
    file2 = open(logfile_name,'a')
    try:
        file2.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(senderPort1)+' Destination:'+str(port1)+' Sequence:'+str(Sequence)+' ACK:'+str(AcknowledgeNumber) + ' flag:010000' +'\n')
    finally:
        file2.close()
    
    struct.pack(str(DataLength)+'s', Data)
    
    #use checksum to check correctness of data
    Checksum=checksum
    if DataLength%2 != 1:
        CHECK = struct.unpack(int(DataLength/2)*'h',Data)
    else:
        CHECK = struct.unpack(int(DataLength/2)*'h'+'b',Data)
    for i in CHECK:
        Checksum = (Checksum + i)%65536
    if Checksum != 65535:
        ReceiverSock.sendto('-999',sender)
        continue

    #check segments loss
    if Sequence != FileACK:
        continue
    
    #calculate ACK value and send it to sender
    ACK = Sequence + MSS
    FileACK = ACK
    ReceiverSock.sendto(str(ACK),sender)
    
    file2 = open(logfile_name,'a')
    try:
        file2.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(port)+' Destination:'+str(senderPort)+' Sequence:/'+' ACK:'+str(ACK) + ' flag:/' +'\n')
    finally:
        file2.close()
    
    #print the data on screen, and write it into receivefile
    print str(Sequence) + ' :' + Data
    file1.writelines(Data)
    
    #write logfile
    
 
#after receiving TCP segment with FIN=1, send ACK=-1 to sender   
ReceiverSock.sendto('-1',sender)
file2 = open(logfile_name,'a')
try:
    file2.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(senderPort1)+' Destination:'+str(port1)+' Sequence:'+str(Sequence)+' ACK:'+str(AcknowledgeNumber)+'flag:010001' +'\n')
    file2.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(port)+' Destination:'+str(senderPort)+' Sequence:/'+' ACK:-1 ' + 'flag:/' +'\n')
finally:
    file2.close()
    
file1.close()

print 'Successfully done!'
exit(0)
