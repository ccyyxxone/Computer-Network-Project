# Computer-Network-Project
Yixing Chen, yc3094

In this project, there are 1 files, Client.py.

You can run the file as the way in assignment:
python Client.py <local port> <timeout> <ip_address 1> <port 1> <weight 1> <ip_address 2> <port 2> <weight 2> …  

sample:
python Client.py 4115 10 127.0.0.1 4116 5.0 127.0.0.1 4118 30.0

Usage scenarios
After running several clients, user can use some commands to control the node:
- SHOWRT: show the time and the router table which contains the shortest path to other nodes (min cost and next node)
- (extra)SHOWNEIGHBORS: show the neighbors list
- LINKDOWN <ip_address> <port>: destroy an exist path, value becomes infinity if there is no other path
- LINKUP <ip_address> <port>: restore the destroyed path
- CLOSE: close this node, linkdown all its links  
- (extra) CREATE <ip_address> <port> <weight>: create a new direct path to a node

Program feature
The main variables:
1. record: a dict that records the data about path to other nodes, key is IP_address and port of other nodes, value is a list which contains the value of shortest path and next node. When client wants to send record data message to other nodes, it sends this dict (first should use json.dump() to change it into json array.)
2. recordFlag: int (0 or 1), initial value is 0, when the value becomes 1, socket will send record message to all its neighbors.
3. neighbors: a list which records (IP_address, port) of neighbors
4. timeRecord: a dict which records receiving time from nodes
5. originalRecord: a dict which records the initial data about path to neighbors, can be used to find other path when LINKDOWN or restore links when LINKUP 
6. address: record IP_address and port

Program structure:
The program contains 3 threads - listenThread, sendThread, waitThread, and the main thread
1. listenThread: receive data from other nodes. If data contains LINKDOWN, LINKUP or CREATE, do the corresponding action to record table. If data is the normal record table, then scan the table and judge whether it should update its own record table, if record is updated, change the value of recordFlag to 1 (so sendThread will know it should send its record table).
2. sendThread: if recordFlag==1 or timeout, send record table to all neighbor nodes. Because record is a dict, so I should use json.dumps(record) to change dict to son array, then use UDP socket to send data, and listenThread should use json.loads(data) to restore the dict data.
3. waitThread: just wait, if this node hasn't received record for 3*TIMEOUT from another node, set its value to inf
4. main thread: receive user’s command and do corresponding action to the command.

Additional feature (extra):
1. Add 2 new commands - CREATE and SHOWNEIGHBORS. CREATE command can create a direct path from this node to another node which isn’t among neighbors, make the network more Complicated. SHOWNEIGHBORS can show the neighbors list.
2. Can control the count-to-infinity situation, when the weight between two nodes changes to inf, the node will find other path from its record immediately.


