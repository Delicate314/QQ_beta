import socket
import sys
import threading
import datetime
import os

class Server:
    def __init__(self, server_ip, server_port):
        self.clients={} # 存储客户端信息
        self.file_state = {} # 文件传输状态
        self.offline_recip_and_filename = {} # 离线文件名和接收方
        self.offline_sender_and_filename = {} # 离线文件名和发送方
        self.file_cancel_record = {} # 文件传输取消记录
        self.voice_state = 0 # 语音通话状态
        self.nat_state = 0 # NAT穿透状态
        self.send_file_muxtex = 0 #同一时间只允许服务器进行一个文件的发送
        try:
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error:
            print('Failed to create socket.')
            sys.exit()
        #套接字绑定到指定ip和端口
        self.socket.bind((server_ip, server_port))
        #监听
        self.socket.listen(10)
        print(f"Server listening on {server_ip}: {server_port} ...")
        self.username = ""


    def start(self):
        while True:
            # 接受客户端连接请求
            client_socket, client_address = self.socket.accept()
            # 为每个客户端创建一个线程来处理该客户端的请求
            threading.Thread(target=self.handle_client, args=(client_socket, )).start()

    # 处理客户端请求
    def handle_client(self,client_socket):
        while True:
            try:
                message, data = self.receive_data(client_socket)
            except TypeError:
                break
            if message.startswith("LOGIN"):
                self.check_login(client_socket, message)
            elif message.startswith("REGISTER"):
                self.check_register(client_socket, message)
            elif message.startswith("PUBLIC"):
                self.send_message(message)
            elif message.startswith("PRIVATE"):
                self.private_message(message)
            elif message.startswith("FILE"):
                self.receive_and_send_file(client_socket, message, data)
            elif message.startswith("VOICE"):
                self.transfer_voice(message, data)
            elif message.startswith("NAT"):
                self.nat(message)

    # 检查登录信息
    def check_login(self, client_socket ,data):
        data = data.split("|",2)
        username = data[1]
        password = data[2]
        with open('users.txt', 'r') as user_file:
            user_file.seek(0)
            lines = user_file.readlines()
            found = False
            for line in lines:
                user_info = line.split()
                # 登录成功
                if username == user_info[0] and password == user_info[1]:
                    found = True
                    self.send_data(client_socket,f"Login succeeded")
                    # 登录成功后，记录用户信息
                    self.clients[username] = client_socket
                    # 服务器端打印登录信息
                    print(f"{username} login at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    # 向所有在线用户发送更新用户列表信息
                    # 自己是新上线用户
                    self.update_online_users(username, client_socket, "NEW")
                    # 遍历除了自己之外的在线用户,发送自己的上线信息
                    for online_name, sock in self.clients.items():
                        if username != online_name:
                            self.update_online_users(username, sock, "ONLINE")
                    # 检查该用户是否有离线文件
                    for file_name, recipient in self.offline_recip_and_filename.items():
                        if recipient == username:
                            print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} : offline_file {file_name} begin to be sent to {username}.')
                            threading.Thread(target=self.send_offline_file_thread, args=(client_socket, file_name)).start()
                # 密码错误
                elif username == user_info[0] and password != user_info[1]:
                    found = True
                    self.send_data(client_socket,f"Login failed: wrong password")
            # 用户不存在
            if not found:
                self.send_data(client_socket,f"Login failed: user not found")
            user_file.close()
    
    #  向客户端发送更新用户列表信息
    def update_online_users(self ,username ,client_sock, status):
        # 向已在线用户广播更新消息
        if status == "ONLINE":
                self.send_data(client_sock, f"ONLINE|{username}")
        # 向新上线用户发送在线用户列表
        elif status == "NEW":
            for online_name, sock in self.clients.items():
                    self.send_data(client_sock, f"ONLINE|{online_name}")
        # 离线消息，发给其他在线用户
        elif status == "OFFLINE":
            for online_name, sock in self.clients.items():
                self.send_data(self.clients[online_name], f"OFFLINE|{username}")

    # 服务器根据发送消息给客户端是否成功判断客户端是否在线
    def offline_users(self, client_socket):
        for username, sock in self.clients.items():
            if sock == client_socket:
                print(f"{username} offline at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                self.clients.pop(username)
                self.update_online_users(username, client_socket, "OFFLINE")
                break
    # 注册
    def check_register(self,client_socket, data):
        data = data.split("|", 2)
        username = data[1]
        password = data[2]
        with open('./users.txt', 'a+') as user_file:
            user_file.seek(0)
            lines = user_file.readlines()
            found = False
            for line in lines:
                user_info = line.split()
                if username == user_info[0]:
                    found = True
                    self.send_data(client_socket,f"Register failed,user already exists")
                    break
            if not found:
                user_info = username+" "+password+"\n"
                user_file.write(user_info)
                self.send_data(client_socket,f"Register succeeded")
            user_file.close()

    # 服务器转发文件信息给客户端
    def receive_and_send_file(self, client_socket, message, data):
        if message.startswith("FILE_ACCEPT"):
            flag=0 #标记是否为离线文件接收方接受文件信息
            message = message.split("|", 1)
            sender = message[1]
            #离线文件的接收方接受文件信息给发送文件方
            for file_name, off_sender in self.offline_sender_and_filename.items():
                if off_sender == sender:
                    #更新对应文件状态
                    self.file_state[file_name] = 1
                    flag=1
                    break
            #转发接收方接受文件信息给发送文件方
            if flag==0:
                if sender in self.clients:
                    self.send_data(self.clients[sender], f"FILE_ACCEPT")
        elif message.startswith("FILE_REJECT"):
            message = message.split("|", 1)
            sender = message[1]
            #转发接收方拒绝文件信息给发送文件方
            if sender in self.clients:
                self.send_data(self.clients[sender], f"FILE_REJECT")

        elif message.startswith("FILE_REQUEST"):
            message = message.split("|", 3)
            sender = message[1]
            recipient = message[2]
            file_name = message[3]
            #在用户文件中查找接收方
            with open('users.txt', 'r') as f:
                f.seek(0)
                lines = f.readlines()
                found = False
                for line in lines:
                    parts = line.strip().split()
                    if parts[0] == recipient:
                        found = True
                        if recipient in self.clients:
                            # 接收方在线,将发送请求转发给接收方
                            self.send_data(self.clients[recipient], f"FILE_REQUEST|{sender}|{recipient}|{file_name}")
                            break
                        else:
                            # 接收方离线,记录发送方，接收方和文件名信息
                            self.offline_recip_and_filename[file_name] = recipient
                            self.offline_sender_and_filename[file_name] = sender
                            #通知发送文件方开始发送
                            self.send_data(self.clients[sender], f"FILE_ACCEPT")
                            print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: begin to receive offline_file {file_name} from {sender}.')
                            
                            break       
                # 接收方不存在
                if not found:
                    self.send_data(client_socket, "FILE_USER_NO_EXIST")
        elif message.startswith("FILE_CONTENT"):
            message = message.split("|", 2)
            recipient = message[2]
            file_content = data
            message = f"FILE_CONTENT|"
            send_data = message.encode('utf-8') + file_content
            # 发送文件内容给接收方
            if recipient in self.clients:
                self.send_data(self.clients[recipient], send_data)
            # 接收方离线,存文件到服务器
            else:
                for file_name ,rec in self.offline_recip_and_filename.items():
                    if rec == recipient:
                        with open('./offline_files/'+file_name+'.tmp', 'ab') as recv_file:
                            recv_file.write(file_content)

        elif message.startswith("FILE_END"):
            message = message.split("|", 2)
            recipient = message[1]
            file_name = message[2]
            # 发送文件结束信息给接收方
            if recipient in self.clients:
                self.send_data(self.clients[recipient], f"FILE_END|{file_name}")
            # 接收方离线,文件在服务器,重命名文件
            else:
                try:
                    os.rename('./offline_files/'+file_name+'.tmp', './offline_files/'+file_name)
                except FileExistsError:
                    # 文件已存在，先删除原文件再重命名
                    os.remove('./offline_files/'+file_name)
                    os.rename('./offline_files/'+file_name+'.tmp', './offline_files/'+file_name)
                print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}: {file_name} received done.')
            

        elif message.startswith("FILE_CANCEL"):
            message = message.split("|", 2)
            recipient = message[1]
            file_name = message[2]
            # 转发取消文件信息给接收方
            if recipient in self.clients:
                self.send_data(self.clients[recipient], f"FILE_CANCEL|{file_name}")

    def send_offline_file_thread(self, client_socket, file_name):
        sender = self.offline_sender_and_filename[file_name]
        recipient = self.offline_recip_and_filename[file_name]
        file_path = './offline_files/'+file_name
        total_sent = 0
        self.file_state[file_name] = 0
        #查看是否有其他文件正在发送
        while(self.send_file_muxtex == 1):
            continue
        if(self.send_file_muxtex == 0):
            self.send_file_muxtex = 1
        # 发送文件请求
        request_message = f"FILE_REQUEST|{sender}|{recipient}|{file_name}"
        self.send_data(client_socket, request_message)
        # 等待对方接收
        while self.file_state[file_name] == 0:
            continue
        # 对方拒绝接收
        if self.file_state[file_name] == 2:
            self.file_state.pop(file_name)
            self.offline_recip_and_filename.pop(file_name)
            self.offline_sender_and_filename.pop(file_name)
            self.send_file_muxtex = 0
            return SystemExit
        # 对方接收
        elif self.file_state[file_name] == 1:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            len_recipient = len(recipient)
            len_recipient = str(len_recipient)

            with open('./offline_files/'+file_name, "rb") as f:
                # 如果文件之前发送过，从上次发送的位置开始发送
                file_sent = self.file_cancel_record.get(file_name)
                if file_sent is None:
                    f.seek(0)
                    total_sent = 0
                else:
                    f.seek(file_sent)
                    total_sent = file_sent
                # 发送文件数据
                while self.file_state != 0 and total_sent < file_size:
                    file_content = f.read(4096)
                    total_sent += len(file_content)
                    message = f"FILE_CONTENT|"
                    send_data = message.encode('utf-8') + file_content
                    # 发送文件内容给接收方
                    try:
                        self.send_data(client_socket, send_data)
                    except socket.error:
                        print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, {file_name} Send failed: client offline.')
                        return SystemExit

            if self.file_state != 0:
                # 发送完成
                self.send_data(client_socket, f"FILE_END|{file_name}")
                print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}:  {file_name} sent to {recipient} done.")
                self.file_state.pop(file_name)
                self.offline_recip_and_filename.pop(file_name)
                self.offline_sender_and_filename.pop(file_name)
                self.send_file_muxtex = 0
                return SystemExit
            else:
                # 发送取消
                self.send_data(client_socket, f"FILE_CANCEL|{recipient}|{file_name}")
                self.file_cancel_record[file_name] = total_sent
                self.send_file_muxtex = 0

    def send_data(self, client_socket, data):
        # 发送数据
        try:
            # 二进制数据
            if type(data) == bytes:
                length = len(data) + 10000
                len_message = str(length)
                len_message = bytes(len_message, encoding='utf-8')
                client_socket.sendall(len_message + data)
            # 字符串数据
            else:
                length = len(data.encode('utf-8')) + 10000
                data = str(length) + data
                client_socket.sendall(data.encode('utf-8'))
        except ConnectionResetError:
            print('Send failed: client offline.')
            self.offline_users(client_socket)
        except socket.error:
            print('Send failed: client offline.')
            self.offline_users(client_socket)


    # 接收数据
    def receive_data(self , client_socket):
        try:
            length = client_socket.recv(5) # 接收数据长度信息
        # 客户端下线
        except socket.error:
            self.offline_users(client_socket)
            return SystemExit
        try:
            #print(f'length:{length}')
            length = length.decode('utf-8') # 解码
            flag=1
        except UnicodeDecodeError:
            print('Unicode Error')
            print(f'length:{length}')
        try:
            length = int(length) - 10000 # 数据长度(发送的时候+了10000)
        except ValueError:
            print('ValueError')
            print(f'length:{length}')
        data=b""
        while length>len(data):
            data += client_socket.recv(length-len(data)) # 接收数据包含数据类别头部
        # 根据数据头部判断数据类型 文件/语音/普通消息
        #0-13:FILE_CONTENT| 14:recipient_length 15:| 16-16+recipient_length-1:recipient 16+recipient_length:| 16+recipient_length+1-end:file_content
        try:
            data1=data[0:13].decode('utf-8')
            if data[0:12].decode('utf-8') == 'FILE_CONTENT':
                len_recipient = data[0:14].decode('utf-8')
                len_recipient = len_recipient.split("|", 1)
                len_recipient = len_recipient[1]
                len_message = 16 + int(len_recipient)
                return f"{data[0:(len_message-1)].decode('utf-8')}", data[len_message:]
            #0-14 VOICE_CONTENT| 15:recipient_length 16:| 17-17+recipient_length-1:recipient 17+recipient_length:| 17+recipient_length+1-end:voice_content
            elif data[0:13].decode('utf-8') == 'VOICE_CONTENT':
                len_recipient = data[0:15].decode('utf-8')
                len_recipient = len_recipient.split("|", 1)
                len_recipient = len_recipient[1]
                len_message = 17 + int(len_recipient)
                return f"{data[0:(len_message-1)].decode('utf-8')}", data[len_message:]
            else:
                data = data.decode('utf-8')
                return data, b""
        except UnicodeDecodeError:
            message = data.decode('utf-8')
            return message, b""

    def send_message(self, message):
        message = message.split("|", 2)
        sender = message[1]
        data = message[2]
        for username, client_sock in self.clients.items():
            self.send_data(client_sock, f"PUBLIC|{sender}|{data}")
    
    def private_message(self, message):
        message = message.split("|", 3)
        sender = message[1]
        receiver = message[2]
        data = message[3]
        if receiver in self.clients.keys():
            self.send_data(self.clients[receiver], f"PRIVATE|{sender}|{receiver}|{data}")
        if sender in self.clients.keys():
            self.send_data(self.clients[sender], f"PRIVATE|{sender}|{receiver}|{data}")

    def transfer_voice(self, message, data):
        if message.startswith("VOICE_REQUEST"):
            message = message.split("|", 2)
            sender = message[1]
            recipient = message[2]
            #转发语音请求给接收方
            if recipient in self.clients.keys():
                self.send_data(self.clients[recipient], f"VOICE_REQUEST|{sender}")
        elif message.startswith("VOICE_ACCEPT"):
            message = message.split("|", 1)
            # 向发起通话方转发接受通话信息
            sender = message[1]
            if sender in self.clients.keys():
                self.send_data(self.clients[sender], f"VOICE_ACCEPT")
        elif message.startswith("VOICE_REJECT"):
            message = message.split("|", 1)
            # 向发起通话方转发拒绝通话信息
            sender = message[1]
            if sender in self.clients.keys():
                self.send_data(self.clients[sender], f"VOICE_REJECT")
        elif message.startswith("VOICE_END"):
            message = message.split("|", 1)
            # 向发起通话方转发结束通话信息
            sender = message[1]
            if sender in self.clients.keys():
                self.send_data(self.clients[sender], f"VOICE_END")
        elif message.startswith("VOICE_CONTENT"):
            message = message.split("|", 2)
            recipient = message[2]
            voice_content = data
            message = f"VOICE_CONTENT|"
            send_data = message.encode('utf-8') + voice_content
            # 发送语音内容给接收方
            if recipient in self.clients.keys():
                self.send_data(self.clients[recipient], send_data)



    def nat(self, message):
        if message.startswith('NAT_REQUEST'):
            message = message.split("|", 2)
            sender = message[1]
            recipient = message[2]
            #转发NAT请求给接收方
            if recipient in self.clients.keys():
                self.send_data(self.clients[recipient], f"NAT_REQUEST|{sender}")
                threading.Thread(target=self.nat_thread).start()
            
        elif message.startswith('NAT_ACCEPT'):
            message = message.split("|", 2)
            # 向发起NAT方转发接受NAT信息
            sender = message[1]
            recipient = message[2]
            if sender in self.clients.keys():
                self.send_data(self.clients[sender], f"NAT_ACCEPT|{recipient}")
            self.nat_state = 1
            
        elif message.startswith('NAT_REJECT'):
            message = message.split("|", 1)
            # 向发起NAT方转发拒绝NAT信息
            sender = message[1]
            if sender in self.clients.keys():
                self.send_data(self.clients[sender], f"NAT_REJECT")

    def nat_thread(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #设置端口复用
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #服务器自己的内网IP
        #sock.bind(("127.0.0.1", 520))
        sock.bind(("192.168.0.60", 520))
        while(self.nat_state == 0):
            continue
        if self.nat_state == 1:
            self.nat_state = 0
            for i in range(2):
            # 两个客户端公网ip地址与端口号各自转发给双方
                message, address = sock.recvfrom(1024)
                message = message.decode("utf-8")
                message = message.split("|", maxsplit=2)
                recipient = message[2]
                self.send_data(self.clients[recipient], f"NAT_ADDR|{address}")
            sock.close()
            return SystemExit
        elif self.nat_state == 2:
            self.nat_state = 0
            sock.close()
            return SystemExit
        
    
if __name__ == '__main__':
    #服务器自己的内网ip
    #host = '127.0.0.1'
    host = '192.168.0.60'
    port = 996
    server = Server(host,port)
    server.start()

