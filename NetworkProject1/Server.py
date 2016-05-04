from socket import *
import time
import threading
import sys
import signal

name=[]
password=[]
n=0
BLOCK_TIME=60  #input username and password 3 times wrong, block this connection 
TIME_OUT=1800 #no command for more than TIME_OUT time, drop the connection
port1=4119 
threadCount={} #record username->connection
threadTime={}#record username->connect time

#read username and password in user_pass.txt
file1 = open('user_pass.txt')
try:
    for line in file1:
        temp=line.split(' ')
        name.append(temp[0])
        password.append(temp[1].strip())
finally:
    file1.close()
print name
print password

#thread for each client connection
class timer(threading.Thread):
    def __init__(self, name, connection):  
        threading.Thread.__init__(self)  
        self.name = name  
        self.connection = connection
        self.time=None #record connect time 
        self.thread_stop = False  
   
    def run(self): #Overwrite run() method, put the function here  
        count=1
        #login
        while True:
            logstate=False
            info=connection.recv(1024)
            print info
            info1=info.split(' ')
            name1=info1[0]
            password1=info1[1]
            n1=len(name)
            for i in range(n1):
                if name1==name[i] and password1==password[i]:
                    logstate=True
                    break
            if logstate==True:
                connection.send('welcome to server!\n')
                break
            else:
                connection.send('Wrong username and password!')
                count+=1
                if count==3:
                    count=0
                    connection.send('3 times wrong!BLOCK '+ str(BLOCK_TIME)+' second!\n')
                    time.sleep(BLOCK_TIME)
         
        #put username, connection and connect time into dicts            
        self.name=name1
        threadCount[name1]=connection
        self.time=time.time()
        threadTime[name1]=self.time
               
        
        while not self.thread_stop:  
            try:
                self.connection.settimeout(TIME_OUT) #set TIME_OUT time
                command1=self.connection.recv(1024)
                command1=command1.strip()
                infoC=command1.split(' ')
                infoLen=len(infoC)
                if infoLen==1:
                    if 'logout' in command1: #logout
                        del threadCount[self.name]
                        self.connection.send('Logout! Good bye!')
                        break
                    elif 'whoelse' in command1:  #whoelse
                        print self.name+':whoelse'
                        self.connection.send(self.name+':whoelse\n')
                        msg=''
                        for key in threadCount:
                            msg=msg + key+'\n'
                        print msg
                        self.connection.send(msg)
                        continue
                    elif 'help'==command1:
                        self.connection.send('Commands:\nwhoelse\nwholast <number>\nbroadcast message'\
                                              +' <message>\nbroadcast user <user> <user> message' \
                                              +' <message>\nmessage <user> <message>\nlogout\nhelp\n')
                        continue
                    elif 'get' == command1: #do nothing, just get message
                        continue
                    else:
                        print 'wrong command'
                        print command1
                        self.connection.send('wrong command')
                        continue
                elif infoLen==2 and 'wholast' ==infoC[0]:  #wholast
                    self.connection.send(self.name+':'+command1+'\n')
                    msg=''
                    timeNow=time.time()
                    for key in threadTime:
                        if timeNow-threadTime[key]<=int(infoC[1])*60:
                            print key #show the user in LAST_TIME
                            msg=msg+key+'\n'
                    if msg!='':
                        self.connection.send(msg)
                    else:
                        self.connection.send('Nobody!') #no one in dict threadTime
                    continue
                elif infoLen==2 and 'change password' == command1: #change password
                    self.connection.send('New Password(no space):')
                    change_password=connection.recv(1024).strip()
                    file1 = open('user_pass.txt','a')
                    try:
                        file1.write(self.name+' '+change_password+'\n')
                    finally:
                        file1.close()
                    name.append(self.name)
                    password.append(change_password)
                    #print name
                    #print password
                    #test whether the information has been written to txt and lists
                    self.connection.send('Successful! Now you can use new password to login!\n')
                    continue
                elif infoLen==2 and 'add user' == command1:
                    self.connection.send('Please input username and password!\nusername:')
                    usernameNEW=connection.recv(1024).strip()
                    self.connection.send('password:')
                    passwordNew=connection.recv(1024).strip()
                    file1 = open('user_pass.txt','a')
                    try:
                        file1.write(usernameNEW+' '+passwordNew+'\n')
                    finally:
                        file1.close()
                    name.append(usernameNEW)
                    password.append(passwordNew)
                    #print name
                    #print password
                    #test whether the information has been written to txt and lists
                    self.connection.send('Successfully! Now you can use new user information to login!\n')
                    continue
                elif 'broadcast message' in command1:
                    #broadcast to all online user
                    self.connection.send(self.name+':'+command1+'\n')
                    for key in threadCount:
                        threadCount[key].send(self.name+': '+command1[18:])
                    continue
                elif 'message' == infoC[0] and infoLen>=3:  #message to a person
                    self.connection.send(self.name+':'+command1+'\n')
                    msgX=''
                    for i in range(2,infoLen):
                        msgX=msgX+infoC[i]+' '
                    if infoC[1] in threadCount:
                        threadCount[infoC[1]].send(self.name+': '+msgX)
                    else:
                        print 'no such user\n'
                        self.connection.send('no such user\n')
                    continue
                elif infoLen>=5 and 'broadcast' in infoC[0] and 'user' in infoC[1]:
                    #broadcast to many online people
                    self.connection.send(self.name+':'+command1+'\n')
                    indexM=infoC.index('message')
                    msgX=''
                    for i in range(indexM+1,infoLen):
                        msgX=msgX+infoC[i]+' '
                    for i in range(2,indexM):
                        if infoC[i] in threadCount:
                            threadCount[infoC[i]].send(self.name+': '+msgX)
                        else:
                            print 'no such user\n'
                            self.connection.send('\nno such user:'+infoC[i]+'\n')
                    continue
                else: #wrong command
                    print 'wrong command'
                    print command1
                    self.connection.send('wrong command')
                    continue
             
            except timeout: #when more than TIME_OUT and no command
                print 'time out!'
                self.thread_stop=True
                self.connection.send('Time out! Good bye!')
                
            except KeyboardInterrupt:
                print "break out"

            print self.name+' leave the Server!'       
                        
    def stop(self):  
        self.thread_stop = True  


#receive the control+c signal
def handler(signum, frame):
    print "\nReceive Ctrl+C signal!"
    print 'Exit!'
    sys.exit()
    
#receive argument port and print the port number 
port1=int(sys.argv[1])
print 'port:'
print port1

#serverSocket
serverSocket=socket(AF_INET,SOCK_STREAM)
serverSocket.bind(('', port1))
serverSocket.listen(10)

#wait to receive control+c signal
signal.signal(signal.SIGINT, handler)
signal.signal(signal.SIGTERM, handler)

#accept client connection and open a new thread for it
while True:
    connection,address=serverSocket.accept()
    t1=timer(None, connection)
    t1.setDaemon(True)
    t1.start()

    
    
    
