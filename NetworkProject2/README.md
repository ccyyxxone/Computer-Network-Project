# Computer-Network-Project
Yixing Chen, yc3094

In this project, there are 2 files, Sender.py and Receiver.py. Please run proxy first, then run receiver, and run sender at last.

Sender and receiver have default arguments. For sender, the default IP is localhost, the port is 41191, filename is test.txt, logfile_name is Senderlog.txt, and window_size is 1.
For receiver, the default IP is localhost, the port is 41194, filename is receivefile.txt,  logfile_name is Receiverlog.txt, sender_IP and port is as same as in sender.py. So you can run the file like this:
python Sender.py, python Receiver.py

And you can also run the files as the way in assignment:
python Sender.py <filename> <remote_IP> <remote_port> <ack_port_num> <log_filename> <window_size>  (if ignore the <window_size> parameter, the default size is 1)
sample:
python Sender.py test.txt 127.0.0.1 41192 41191 Senderlog.txt 1

python Receiver.py <filename> <listening_port> <sender_IP> <sender_port> <log_filename>
sample:
python Receiver.py receivefile.txt 41194 127.0.0.1 41191 Receiverlog.txt

brief description
(a)the TCP segment structure
20 bytes TCP head:
2 bytes SourcePort
2 bytes DestinationPort
4 bytes Sequence
4 bytes AcknowledgeNumber
2 bytes HeadLength_and_flags (including headlength, unused part, URG bit, ACK bit, PSH bit, RST bit, SYN bit, FIN bit)
2 bytes AcceptWindow (0)
2 bytes checksum
2 bytes EmergencyPointer (0)
I use struct.pack() function to pack these ints into one TCPHead. And in receiver I use struct.unpack() function to restore them.

And 500 bytes binary data (MSS=500)

(b)the states typically visited by a sender and receiver
sender:
ListeningThread:
1. Keep receiving ACK
2. if receive the correct ACK value, change the global variable ACK in sender 
sendThread:
1. Read the file, put the content into a list. (MSS=500)
2. For every segment, change the 500 bytes data into binary data, calculate its checksum, change TCPHead into binary data, add TCPHead and data, send this TCP segment to proxy.
3. Wait a very short time, move the window until the first unsent segment becomes the first segment in the window. Calculate retransmit times. Keep sending.
4. When all file contents have been sent, send the segment(FIN=1) to proxy.  

Receiver:
1. Receive TCP segments, check sequence and checksum
2. If receive the correct segment, write the content into file, write log, send ACK back to sender.
3. If receive the wrong segment, drop it. 

(c)loss recovery mechanism
In sender, I arrange a global variable ACK. If the listeningThread receive ACKnumber from receiver and its value equals to ACK + MSS, I think the TCP segment is sent correctly, and change the value of ACK to ACKnumber, otherwise, if the ACK value doesn’t change, I think the segment is lost, after a very short time, the sendThread sends this segment again.

In receiver, I also arrange a variable FileACK. When receiver gets TCP segment from proxy, it will check the sequence number of segment, if the sequence number equals the value of FileACK, I think it’s the correct segment, receiver writes data into file, sends ACK (=FileACK+MSS) back to sender, and let FileACK=ACK. If the sequence number doesn’t equal to the value of FileACK, I think it’s wrong segment (package loss or out of order), so the receiver will drop this segment, and will not send anything back to sender.
Besides, when receiver gets TCP segment from proxy, it will check data correctness using checksum, if the sum of data and checksum is not 65535, I think bit error happens, the receiver drops this segment and send -999 back to sender (I can also let it do not send anything back, but I think send -999 can help to debug).

Additional feature:
For window_size (pipeline), I don’t set buffer in sender or receiver.
If receiver gets wrong segment, drops.
And in sender, for example, if window_size=5, the 3rd segment is lost, sender will think first 2 segments are sent successfully, and regard the 3rd segment as the first segment in the new window, resend 3rd, 4th, 5th and send 6th, 7th segments. In this scenario, retransmit times = 3.

