import socket
import time
import threading
import sys
import os
import datetime
import struct



#default value
IP='localhost'
port=41191

filename='test.txt'
remoteIP = 'localhost'
remotePort = 41192
logfile_name='Senderlog.txt'
global window_size
window_size=1

#arguments
if len(sys.argv) >= 6:
    port = int(sys.argv[4])
    filename = sys.argv[1]
    remoteIP = sys.argv[2]
    remotePort = int(sys.argv[3])
    logfile_name = sys.argv[5]
    if len(sys.argv) ==7:
        window_size=int(sys.argv[6])

global ACK
ACK = 0

#sender and receiver should have the same value of MSS
MSS=500

#read file
file1 = open(filename)
File=[]
filebuffer=''
try:
    filebuffer = file1.read(MSS)
    while filebuffer!='':
        File.append(filebuffer)
        filebuffer = file1.read(MSS)
finally:
    file1.close()

global filelength    
filelength=len(File)
filesize=os.path.getsize(filename)

#to calculate retransmit times
global retransmit
retransmit=0
global retransmitflag
retransmitflag=0 

#UDP Socket
address = (IP, port)   
SenderSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
SenderSock.bind(address) 

proxy = (remoteIP, remotePort)   

#set the first sample RTT, use sendTime and receiveTime to calculate sample RTT
global RTT 
RTT = 0.005
global sendTime
global receiveTime
global sampleRTT

# listen thread, just receive the ACK information
class listenThread(threading.Thread):
    def __init__(self, SenderSock1):  
        threading.Thread.__init__(self)  
        self.SenderSock = SenderSock1  
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        while not self.thread_stop:  
            global ACK
            global MSS
            global RTT
            global sendTime
            global receiveTime
            global sampleRTT
            
            a=self.SenderSock.recv(1024)
            A = int(a)
            if A-ACK==MSS:
                ACK = A
                receiveTime = time.time()
                sampleRTT = receiveTime - sendTime
                if A == MSS:
                    RTT = sampleRTT
                else:
                    RTT = 0.875*RTT + 0.125*sampleRTT #calculate estimated RTT
            elif A==-1:
                ACK = -1
                self.thread_stop = True  
                                            
    def stop(self):  
        self.thread_stop = True  

#send message thread, send TCP segments to Proxy
class sendThread(threading.Thread):
    def __init__(self, SenderSock1):  
        threading.Thread.__init__(self)  
        self.SenderSock = SenderSock1  
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        while not self.thread_stop:
            global sendTime
            global ACK
            global RTT
            global RTTrecord
            global retransmit
            global retransmitflag
            global window_size
            global filelength
            
            file1 = open(logfile_name,'w')
            try:
                file1.write('')
            finally:
                file1.close()
            
            print 'start!'

            if window_size > filelength:
                window_size = filelength
            #send TCP segments
            for i in range(filelength):
                if ACK>i*MSS:
                    retransmitflag+=1
                    continue
                if ACK!=0:
                    retransmit += (window_size - retransmitflag - 1)
                #print 'retransit:' + str(retransmit) + 'and retransitflag:' + str(retransmitflag)
                retransmitflag=0
                
                #use another circulation to achieve window_size (pipeline)
                for j in range(window_size):
                    if (i+j)>=filelength:
                        break
                    
                    #calculate checksum, and use pack to change string data into binary data
                    checksum = 0
                    Data = File[i+j]
                    Datal = len(Data)
                    Data1 = struct.pack(str(Datal)+'s', Data)
                    if Datal%2 != 1:
                        CHECK = struct.unpack(int(Datal/2)*'h',Data)
                    else:
                        CHECK = struct.unpack(int(Datal/2)*'h'+'b',Data)
                    for x in CHECK:
                        checksum = (checksum+x)%65536
                    checksum = 65535 - checksum
                    
                    #TCPHead data
                    SourcePort = port
                    DestinationPort = remotePort
                    Sequence = (i+j)*MSS
                    AcknowledgeNumber = ACK
                    HeadLength_and_flags = 20496 #HeadLength=5, flags =010000 
                    AcceptWindow = 0
                    Checksum = checksum
                    EmergencyPointer = 0
                    
                    #use pack to make TCPHead
                    TCPHead = struct.pack('HHIIHHHH',SourcePort,DestinationPort,Sequence,AcknowledgeNumber,HeadLength_and_flags,AcceptWindow,checksum,EmergencyPointer)
                    
                    #send TCP segments, write data into log, and print data on the screen
                    self.SenderSock.sendto(TCPHead + Data1, proxy)
                    print str(Sequence) + ':' + File[i+j]
                    file1 = open(logfile_name,'a')
                    try:
                        file1.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(port)+' Destination:'+str(remotePort)+' Sequence:'+str(Sequence)+' ACK:'+str(ACK)+' flag:010000'+' RTT:'+str(round(RTT,8)) +'\n')
                    finally:
                        file1.close()
                    
                    #record time
                    sendTime = time.time()
                    #time.sleep(0.001)
                time.sleep(0.02)
                
                #if the first segments wasn't sent, retransmit it
                while ACK==i*MSS:
                    
                    checksum = 0
                    Data = File[i]
                    Datal = len(Data)
                    Data1 = struct.pack(str(Datal)+'s', Data)
                    if Datal%2 != 1:
                        CHECK = struct.unpack(int(Datal/2)*'h',Data)
                    else:
                        CHECK = struct.unpack(int(Datal/2)*'h'+'b',Data)
                    for x in CHECK:
                        checksum = (checksum+x)%65536
                    checksum = 65535 - checksum
                    
                    SourcePort = port
                    DestinationPort = remotePort
                    Sequence = (i)*MSS
                    AcknowledgeNumber = ACK
                    HeadLength_and_flags = 20496 #HeadLength=5, flags=010000 
                    AcceptWindow = 0
                    Checksum = checksum
                    EmergencyPointer = 0
                    
                    TCPHead = struct.pack('HHIIHHHH',SourcePort,DestinationPort,Sequence,AcknowledgeNumber,HeadLength_and_flags,AcceptWindow,checksum,EmergencyPointer)
                    
                    self.SenderSock.sendto(TCPHead + Data1, proxy)
                    print str(Sequence) + ':' + File[i]
                    file1 = open(logfile_name,'a')
                    try:
                        file1.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(port)+' Destination:'+str(remotePort)+' Sequence:'+str(Sequence)+' ACK:'+str(ACK)+' flag:010000'+' RTT:'+str(round(RTT,8)) +'\n')
                    finally:
                        file1.close()
                    
                    sendTime = time.time() 
                    retransmit+=1
                    time.sleep(0.01)
            
            #send the last segment (no data, and FIN = 1)
            while ACK!=-1:
                
                    checksum = 65535
                    Data1 = struct.pack('',)
  
                    SourcePort = port
                    DestinationPort = remotePort
                    Sequence = (i+j)*MSS
                    AcknowledgeNumber = ACK
                    HeadLength_and_flags = 20497 #HeadLength=5, flags =010001
                    AcceptWindow = 0
                    Checksum = checksum
                    EmergencyPointer = 0
                    
                    TCPHead = struct.pack('HHIIHHHH',SourcePort,DestinationPort,Sequence,AcknowledgeNumber,HeadLength_and_flags,AcceptWindow,checksum,EmergencyPointer)
                    
                    
                    self.SenderSock.sendto(TCPHead + Data1, proxy)
                    file1 = open(logfile_name,'a')
                    try:
                        file1.write('Timestamp:'+str(datetime.datetime.now())[:-7]+' Source:'+str(port)+' Destination:'+str(remotePort)+' Sequence:'+str(Sequence)+' ACK:'+str(ACK)+' flag:010001'+' RTT:'+str(round(RTT,8)) +'\n')
                    finally:
                        file1.close()
                    
                    sendTime = time.time() 
                    #retransmit+=1
                    time.sleep(0.01)
                
            #print the result
            print 'Delivery completed successfully!'
            print 'Total bytes sent = ' + str(filesize)
            print 'Segments sent = ' + str(filelength) + ' + ' + str(retransmit)
            print 'Segments retransmitted = ' + str(retransmit)
            
            #compare the two file
#             print 'Comparing the two file....'
#             
#             file1 = open('test.txt')
#             File1=[]
#             try:
#                 for line in file1:
#                     File1.append(line)
#             finally:
#                 file1.close()
#             
#             file2 = open('receivefile.txt')
#             File2=[]
#             try:
#                 for line in file2:
#                     File2.append(line)
#             finally:
#                 file2.close()
#             l1=len(File1)
#             l2=len(File2)
#             
#             if l1!=l2:
#                 print 'Not Same!!!'
#             else:
#                 for x in range(l1):
#                     if File1[x]!=File2[x]:
#                         print 'Not Same!!!'
#                         break
#                 else:
#                     print 'Same! Successful!'
#             
               
            self.thread_stop = True  
                                            
    def stop(self):  
        self.thread_stop = True  
        
#open the 2 threads
t1=listenThread(SenderSock)
t2=sendThread(SenderSock)
t1.start()
t2.start()


    
  

