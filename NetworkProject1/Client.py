from socket import *
import threading
import time
import signal
import sys

flag=0
port1=4119
BLOCK_TIME=60

#receive control+c signal
def handler(signum, frame):
    print "\nReceive Ctrl+C signal!"
    print 'Exit!'
    sys.exit()



# listen thread, just receive the information from Server
class listenThread(threading.Thread):
    def __init__(self, clientSocket1):  
        threading.Thread.__init__(self)  
        self.clientSocket = clientSocket1  
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        while not self.thread_stop:  
            a=self.clientSocket.recv(1024)
            time.sleep(0.1)
            print a
            print '\n'
            if flag==1:
                self.thread_stop=True
                                            
    def stop(self):  
        self.thread_stop = True  

#send message thread, send message to Server
class sendThread(threading.Thread):
    def __init__(self, clientSocket1):  
        threading.Thread.__init__(self)  
        self.clientSocket = clientSocket1  
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put function here 
        try:
            while not self.thread_stop:  
                command1=raw_input('>>')
                self.clientSocket.send(command1)
                time.sleep(0.8)

                if command1=='logout': #logout
                    print 'Leave the Server! Please press Control+C!'
                    self.thread_stop=True
                    flag=1
                    self.clientSocket.close() #Exit
                    sys.exit()
        except KeyboardInterrupt:
            print 'Ctrl+c! Leave the Server!'
            sys.exit()
                                            
    def stop(self):  
        self.thread_stop = True  


#receive port and IP as input arguments
port1=int(sys.argv[2])
IP=sys.argv[1]

#print IP and port
print 'IP:'
print IP
print 'port:'
print port1

#client socket
clientSocket= socket(AF_INET, SOCK_STREAM)
clientSocket.connect((IP, port1))

#wait for Control+C signal
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

#login
result=''
while 'welcome' not in result:
    #Block this connection
    if 'BLOCK' in result:
        print 'BLOCK ' +str(BLOCK_TIME)+' SECOND!'
        time.sleep(BLOCK_TIME)
    #input username and password
    print 'LOG IN'
    name1=raw_input('username:')
    password1=raw_input('password:')
    clientSocket.send(name1+' '+password1)
    result=clientSocket.recv(1024)
    print result

#after successful login, open listenThread and sendThread for this client    
t1=listenThread(clientSocket)
t1.setDaemon(True)
t1.start()
t2=sendThread(clientSocket)
t2.setDaemon(True)
t2.start()

while 1:
        alive = False
        alive = alive or t1.isAlive()
        alive = alive or t2.isAlive()
        if not alive:
            break

