import socket
import time
import threading
import sys
import datetime
import copy
import json

IP='127.0.0.1'

IP = socket.gethostbyname(socket.gethostname())  #local IP

port=41191
global TIMEOUT
global record
global recordFlag
global timeRecord
global neighbors
global INF
TIMEOUT = 60
record = {}
recordFlag = 0  #control sending messages, if record changes, value becomes 1, send message
neighbors = []  #record neighbors
timeRecord = {}  #record receive time of neighbors
INF = float('inf')  #define inf

#read arguments
if len(sys.argv) >= 6 and (len(sys.argv)-3)%3==0:
    port = int(sys.argv[1])
    TIMEOUT = int(sys.argv[2])
    count = (len(sys.argv)-3)/3
    for i in range(count):
        record[sys.argv[i*3+3]+':'+sys.argv[i*3+4]] = [float(sys.argv[i*3+5]), (sys.argv[i*3+3], int(sys.argv[i*3+4]))]
        neighbors.append((sys.argv[i*3+3], int(sys.argv[i*3+4])))
        timeRecord[(sys.argv[i*3+3], int(sys.argv[i*3+4]))] = time.time()
else:
    print 'Wrong Input!'
    exit(0)
    
print 'IP address is: ' + IP
print 'port is: ' + str(port)
    
# print neighbors
# print record
    
originalRecord = copy.deepcopy(record)  #record the original data


#socket
address = (IP, port)   
UDPSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   
UDPSock.bind(address) 


# listen thread, just receive data
class listenThread(threading.Thread):
    def __init__(self, UDPSock1):  
        threading.Thread.__init__(self)  
        self.UDPSock = UDPSock1  
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        global record
        global recordFlag
        global timeRecord
        global neighbors
        global INF
        while not self.thread_stop: 
            #receive and analyze data
            data1, addr = self.UDPSock.recvfrom(1024)
            
            #CREATE
            if 'CREATE' in data1:
                neighbors.append(addr)
                record[addr[0]+':'+str(addr[1])] = [float(data1[6:]), addr]
                recordFlag = 1
                continue
            
            #LINKDOWN
            if 'LINKDOWN' in data1:
                neighbors.remove(addr)
                record[addr[0]+':'+str(addr[1])] = [INF, addr]
                #tmp1 = addr[0] + ':' + str(addr[1])
                tmp2 = addr
                for x in record:
                    if record[x][1] == tmp2:
                        record[x][0] = INF
                for x in record:
                    if record[x][0] == INF:
                        index1 = x.index(':')
                        temp = (x[:index1], int(x[index1+1:]))
                        if temp in neighbors and x in originalRecord:
                            record[x] = copy.deepcopy(originalRecord[x])
                             
                recordFlag = 1
                continue
            
            #LINKUP
            if 'LINKUP' in data1:
                neighbors.append(addr)
                record[addr[0]+':'+str(addr[1])] = copy.deepcopy(originalRecord[addr[0]+':'+str(addr[1])])
                             
                recordFlag = 1
                continue
            
            #else - just data record
            data = json.loads(data1)
            
            #print data
            #print ''
            #print record
            #print '-------------------------------------------------------' 
            
            changeFlag = 0  #initialize changeFlag
            if addr not in neighbors:
                continue

            for x in data:
                if x in record:  #the record contains distance to that node
                    
                    #rule out inf + x = inf situation
                    if record[addr[0]+':'+str(addr[1])][0] != INF:  #update distance
                        if record[addr[0]+':'+str(addr[1])][0] + data[x][0] < record[x][0] and list(data[x][1]) != list(address):
                            record[x][0] = record[addr[0]+':'+str(addr[1])][0] + data[x][0]
                            record[x][1] = addr
                            changeFlag = 1
                    else:
                        if data[x][0] < record[x][0] and list(data[x][1]) != list(address): #update distance
                            record[x][0] = data[x][0]
                            record[x][1] = addr
                            changeFlag = 1
                    
                    #inf case, find other path    
                    if data[x][0] == INF:
                        for x2 in record:
                            if list(record[x2][1]) == list(addr) and x2==x:
                                record[x2][0] = INF
                                changeFlag = 1
                        for x2 in record:
                            if record[x2][0] == INF:
                                index1 = x2.index(':')
                                temp = (x2[:index1], int(x2[index1+1:]))
                                if temp in neighbors and x2 in originalRecord:
                                    record[x2] = copy.deepcopy(originalRecord[x2])
                
                #if record doesn't contain the data                  
                else:
                    #path to this node
                    if x == address[0]+':'+str(address[1]):
                        continue
                    
                    #add data to record
                    else:
                        record[str(x)] = [record[addr[0]+':'+str(addr[1])][0]+data[x][0], addr]
                        changeFlag = 1
            
            #record has been changed, should broadcast new record (recordFlag==1)    
            if changeFlag == 1:
                recordFlag = 1
                
            #record time
            timeRecord[addr] = time.time()
            time.sleep(0.01)
                                                   
    def stop(self):  
        self.thread_stop = True  

#send message thread
class sendThread(threading.Thread):
    def __init__(self, UDPSock1):  
        threading.Thread.__init__(self)  
        self.UDPSock = UDPSock1 
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        global record
        global recordFlag
        global neighbors
        global TIMEOUT
        
        #initialize sendTime
        sendTime = time.time()
        while not self.thread_stop:
            #recordFlag==1, should send record to neighbors
            if recordFlag == 1:
                for x in record:
                    if type(x) != type('a'):
                        print x
                        print type(x)
                record1 = json.dumps(record)
                for x in neighbors:
                    self.UDPSock.sendto(record1, x)
                recordFlag = 0
                sendTime = time.time()
#             print time.time()
#             print sendTime
#             print TIMEOUT
            
            #TIMEOUT, should send record to neighbors
            if time.time() - sendTime >= TIMEOUT:
                record1 = json.dumps(record)
                for x in neighbors:
                    self.UDPSock.sendto(record1, x)
                recordFlag = 0
                sendTime = time.time()
            time.sleep(0.01)
                                                               
    def stop(self):  
        self.thread_stop = True 
        
class waitThread(threading.Thread):
    def __init__(self, UDPSock1):  
        threading.Thread.__init__(self)  
        self.UDPSock = UDPSock1 
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        global record
        global recordFlag
        global TIMEOUT
        global timeRecord
        global INF
        
        #wait all client join the network
        time.sleep(3*TIMEOUT)
        
        while not self.thread_stop:
            #haven't received record for 3*TIMEOUT, say goodbye
            for x in timeRecord:
                if time.time() - timeRecord[x] >= 3*TIMEOUT:
                    if record[x[0]+':'+str(x[1])][0] != INF:
                        record[x[0]+':'+str(x[1])] = [INF, x]
                        recordFlag = 1
                    #print '3 * TIMEOUT!!!'
            time.sleep(0.2)
                                                               
    def stop(self):  
        self.thread_stop = True  
           
#open the 3 threads
t1=listenThread(UDPSock)
t2=sendThread(UDPSock)
t3=waitThread(UDPSock)
t1.setDaemon(True)
t2.setDaemon(True)
t3.setDaemon(True)
t1.start()
t2.start()
t3.start()

print 'Start!'
print 'You can use \nSHOWRT \nSHOWNEIGHBORS \nLINKDOWN <ip_address> <port> \nLINKUP <ip_address> <port> \nCREATE <ip_address> <port> <value> \nCLOSE \ncommands! (Please input capital letters)'

#receive commands
command = raw_input('> ').strip()
while command != 'CLOSE':
    
    #SHOWRT
    if command == 'SHOWRT':
        currentTime = str(datetime.datetime.now())[:-7]
        print '<' + currentTime + '>' + 'Distance vector is:'
        for x in record:
            print 'Destination=' + x +', Cost=' + str(record[x][0])+', Link=(' + str(record[x][1][0]) + ':' + str(record[x][1][1]) + ')'
    
    #show neighbors
    elif command == 'SHOWNEIGHBORS':
        currentTime = str(datetime.datetime.now())[:-7]
        print '<' + currentTime + '>' + 'Neighbors:'
        for x in neighbors:
            print x
    
    #wrong input
    elif ' ' not in command:
        print 'Wrong command!'
    else:
        command1 = command.split(' ')
        
        #LINKDOWN
        if command1[0] == 'LINKDOWN':
            tmp1 = command1[1] + ':' + str(command1[2])
            tmp2 = (command1[1], int(command1[2]))
            
            #can only linkdown the node which is among neighbors
            if (tmp1 in record) and (tmp2 in neighbors):
                record[tmp1][0] = INF
                record[tmp1][1] = tmp2
                neighbors.remove(tmp2)
                for x in record:
                    if record[x][1] == tmp2:
                        record[x][0] = INF
                
                #find new path (if exists)
                for x in record:
                    if record[x][0] == INF:
                        index1 = x.index(':')
                        temp = (x[:index1], int(x[index1+1:]))
                        if temp in neighbors and x in originalRecord:
                            record[x] = copy.deepcopy(originalRecord[x])
                
                UDPSock.sendto('LINKDOWN', tmp2)
                recordFlag = 1
                print 'LINKDOWN successful!'
            
            #wrong input
            else:
                print 'Wrong input! IP and port not in record or not a neighbor of this node!'
        
        #LINKUP
        elif command1[0] == 'LINKUP':
            tmp1 = command1[1] + ':' + str(command1[2])
            tmp2 = (command1[1], int(command1[2]))
            
            #can only linkup node which is among neighbors at first but not now
            if (tmp1 in originalRecord) and (tmp2 not in neighbors):
                record[tmp1] = copy.deepcopy(originalRecord[tmp1])
                neighbors.append(tmp2)
                
                UDPSock.sendto('LINKUP', tmp2)
                     
                recordFlag = 1
                print 'LINKUP successful!'
            else:
                print 'Wrong input!'
                
        #EXTRA, create a direct path to a node
        elif command1[0] == 'CREATE':
            tmp1 = command1[1] + ':' + command1[2]
            tmp2 = (command1[1], int(command1[2]))
            
            #can only create path to node which isn't among neighbors
            if tmp2 in neighbors:
                print 'Wrong input! Input node is neighbor of this node!'
                continue
            
            #add to neighbors
            neighbors.append(tmp2)
            value = float(command1[3])
            UDPSock.sendto('CREATE'+str(value), tmp2)
            
            #add data to record
            record[tmp1] = [value, tmp2]
            recordFlag = 1
            print 'Create new link successfully!'
            
    command = raw_input('> ').strip()
    
#if command is CLOSE, break from the circulation
#CLOSE - send LINKDOWN to all neighbors
for x in record:
    record[x][0] = INF
for x in neighbors:
    UDPSock.sendto('LINKDOWN', x)
recordFlag = 1
time.sleep(0.5)

#exit
t1.stop()
t2.stop()
t3.stop()
time.sleep(0.2)
print 'Goodbye!'
exit(0)

        
        
        
        
        
        
        

