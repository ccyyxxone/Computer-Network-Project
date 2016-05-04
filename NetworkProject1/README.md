# Computer-Network-Project
Project 1
(a)A brief description of code
In the program, I achieve the required functions as follows:
1.login
2.Block user 60 seconds if he inputs wrong information for 3 times.
3.Multiple client support
4.whoelse
5.broadcast to all online user
6.wholast <min>
7.private message to online user
8.Automatic logout of clients after 30 min of inactivity
9.Exit when press control+C. (client and server)
10.logout

And 3 additional commands(description in part(e)):
1.change password
2.add new user information
3.help-show all available commands

In this program, after server starts, when server accepts a new connection, it will arrange a new thread for this client to achieve the multiple client support. And in each client, there are also two threads, one is for listening the message from server and the other is for sending message to server.

(b)Details on development environment
Language: Python
IDE: eclipse

(c)Instructions of running code
Run this Program in terminal like this:
python Server.py <port>
python Client.py <IP address> <port>
Run the Server first.

(d)Sample commands to invoke code
python Server.py 4119
python Client.py 0.0.0.0 4119

(e)Additional functions and commands
1.change passwords
User can change his login password. First user inputs command ‘change password’, then receive a message ‘New Password(no space):’. User can input new password, after that, user can use this new password to login to Server.(old password can still be used)

2.add new user
The online user can sign up another user information. First user inputs command ‘add user’, then inputs the new username and password, Server writes the information into txt and record, so user can use the new username and password to login next time.

3.help
When user inputs the command “help”, server will present the available commands list to help user know what commands he can use. 
