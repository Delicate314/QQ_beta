import socket
import tkinter as tk
import sys
import time
import os
import threading
import pyaudio
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import filedialog
from tkinter import simpledialog
from PIL import ImageTk,Image

class Client:
    def __init__(self, host, port):
        try:
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error:
            print('Failed to create socket.')
            sys.exit()
        self.socket.connect((host, port))  # 连接服务器
        self.username = "anonymous"
        print('已连接')

    def send_data(self, data):
        try:
            if type(data) == bytes:
                length = len(data) + 10000
                len_message = str(length)
                len_message = bytes(len_message, encoding='utf-8')
                send_data = len_message + data
                self.socket.sendall(send_data)
            else:
                length = len(data.encode('utf-8')) + 10000
                send_data = str(length) + data
                self.socket.sendall(send_data.encode('utf-8'))
        except socket.error:
            print('Send failed')
            sys.exit()

    def receive_data(self):
        try:
            length = self.socket.recv(5)
        except socket.error:
            messagebox.showerror("错误", "与服务器的连接已断开")
            sys.exit()
        length = length.decode('utf-8')
        length = int(length) - 10000
        data = b""
        while length > len(data):
                data += self.socket.recv(length - len(data))
    
        try:
            data1=data[0:13].decode('utf-8')
            if data[0:12].decode('utf-8') == 'FILE_CONTENT':
                return f"{data[0:12].decode('utf-8')}", data[13:]
            elif data[0:13].decode('utf-8') == 'VOICE_CONTENT':
                return f"{data[0:13].decode('utf-8')}", data[14:]
            else:
                data = data.decode('utf-8')
                return data, b""
        except UnicodeDecodeError:
            data = data.decode('utf-8')
            return data, b""


class LoginWindow:
    def __init__(self, _client):
        self.client = _client
        self.window = tk.Tk()
        photo = Image.open("images/qq.jpg")
        photo = ImageTk.PhotoImage(photo)
        label = tk.Label(image=photo)
        # 窗口置于最前
        self.window.attributes("-topmost", True)
        # 设置窗口颜色
        self.window.configure(bg='lightblue')
        self.window.geometry("450x450")
        label.place(x=0, y=0)
        self.window.title("QQ beta 登录")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        #self.window.after(1000, self.check_connect)
        # 用户名标签
        self.label_username = tk.Label(self.window, text="用户名", font=18, bg='yellow')
        self.label_username.place(x=60, y=100)
        # 用户名输入框
        self.entry_username = tk.Entry(self.window, font=("Helvetica", 14))
        self.entry_username.place(x=150, y=100)
        # 密码标签
        self.label_password = tk.Label(self.window, text="密码", font=18, bg='yellow')
        self.label_password.place(x=60, y=200)
        # 密码输入框
        self.entry_password = tk.Entry(self.window, font=("Helvetica", 14), show='*')
        self.entry_password.place(x=150, y=200)
        # 登录按钮
        self.button_login = tk.Button(self.window, text="登录", font=18, command=self.login, bg='green')
        self.button_login.place(x=150, y=300)
        # 注册按钮
        self.button_register = tk.Button(self.window, text="注册", font=18, command=self.register_window, bg='green')
        self.button_register.place(x=250, y=300)

        self.window_sign_up = self.window
        self.window_sign_up_entry_username = self.entry_username
        self.window_sign_up_entry_password = self.entry_password

        # 关闭窗口时退出程序
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.mainloop()

    def login(self):
        username = self.entry_username.get()
        if username.isalnum():
            password = self.entry_password.get()
            if len(password) >= 6 and password.isalnum():
                data = "LOGIN|"+username+"|"+password
                self.client.send_data(data)
                status, b_data = self.client.receive_data()
                if status == "Login succeeded":
                    self.client.username = username
                    self.window.destroy()
                elif status == "Login failed: wrong password":
                    messagebox.showerror(title="登录失败",message="密码错误")
                elif status == "Login failed: user not found":
                    messagebox.showerror(title="登录失败",message="用户不存在")
            else:
                messagebox.showerror(title="登录失败",message="密码必须为英文字母或数字且长度不小于6位！")
        else:
            messagebox.showerror(title="登录失败",message="用户名只能为英文字母或数字！")

    def register_window(self):
        self.window_sign_up = tk.Toplevel(master=self.window)
        self.window_sign_up.geometry('400x300')
        self.window_sign_up.title("账号注册")
        # 窗口置于最前
        self.window_sign_up.attributes("-topmost", True)
        # 用户名标签
        self.window_sign_up.label_username = tk.Label(self.window_sign_up, text="用户名", font=20)
        self.window_sign_up.label_username.place(x=60, y=50)
        # 用户名输入框
        self.window_sign_up_entry_username = tk.Entry(self.window_sign_up, font=("Helvetica", 14))
        self.window_sign_up_entry_username.place(x=150, y=50)
        # 密码标签
        self.window_sign_up.label_password = tk.Label(self.window_sign_up, text="密码", font=20)
        self.window_sign_up.label_password.place(x=60, y=100)
        # 密码输入框
        self.window_sign_up_entry_password = tk.Entry(self.window_sign_up, font=("Helvetica", 14))
        self.window_sign_up_entry_password.place(x=150, y=100)
        # 注册按钮
        self.window_sign_up.button_register = tk.Button(self.window_sign_up, text="注册", font=25, command=self.register)
        self.window_sign_up.button_register.place(x=150, y=250)
        # 返回
        self.window_sign_up.back = tk.Button(self.window_sign_up, text="返回", font=25, command=self.window_sign_up.destroy)
        self.window_sign_up.back.place(x=300, y=250)

    def register(self):
        username = self.window_sign_up_entry_username.get()
        if len(username)>=10:
            messagebox.showerror(title="注册失败", message="用户名长度不得超过9位")
        elif username.isalnum():
            password = self.window_sign_up_entry_password.get()
            if len(password) >= 6 and password.isalnum():
                data = "REGISTER|" + username + "|" + password
                #向服务器发送注册信息
                self.client.send_data(data)
                # 等待服务器发送注册成功与否的信息
                status, b_data = self.client.receive_data()
                if status == "Register succeeded":
                    messagebox.showinfo(message="注册成功！请使用注册的用户名登录")
                    self.window_sign_up.destroy()
                elif status == "Register failed,user already exists":
                    messagebox.showerror(title="注册失败", message="用户名已存在")
            else:
                messagebox.showerror(title="注册失败", message="密码必须为英文字母或数字且长度不小于6位！")
        else:
            messagebox.showerror(title="注册失败", message="用户名只能为英文字母或数字！")

    # 检测连接是否断开
    def check_connect(self):
        pass
        '''
        if self.client.close_window:
            self.window.destroy()
            raise SystemExit
        else:
            # 每隔1秒检测连接是否断开
            self.window.after(1000, self.check_connect)
        '''

    #用户关闭登录窗口，退出程序
    def on_closing(self):
        self.client.socket.close()
        self.window.destroy()
        raise SystemExit
    
class ChatRoom:
    def __init__(self, _client):
        self.client = _client
        self.file_state = 0
        self.cur_file_name = ""
        self.file_cancel_record = {}       # 记录中断发送的文件信息
        
        self.nat_peer = ""
        self.nat_sock = None
        self.p2p_chat_state = 0
        self.window = tk.Tk()
        self.window.geometry("560x480")
        username = self.client.username
        self.window.title("QQ beta ("+ username + ")")
        # 窗口置于最前
        self.window.attributes("-topmost", True)
        # 消息显示框
        self.textbox = scrolledtext.ScrolledText(self.window, font=("Helvetica", 14), width=32, height=15, bg='lightblue')
        self.textbox.place(x=5, y=5)
        self.textbox.bind("<Key>", self.disable_keyboard)
        # 输入框
        self.input = tk.Text(self.window, font=("Helvetica", 14), width=32, height=4, bg='lightblue')
        self.input.place(x=5, y=365)
        # 在线用户列表
        self.user_list = tk.Listbox(self.window, font=("Helvetica", 14), selectmode="single", width=15, height=12, bg='lightblue')
        self.user_list.place(x=380, y=35)
        # 在线用户列表标签
        self.label1 = tk.Label(self.window, text="当前在线用户", font=10)
        self.label1.place(x=380, y=5)
        # 发送消息按钮
        self.button1 = tk.Button(self.window, text="发送", font=10, command=self.public_chat)
        self.button1.place(x=460, y=320)
        # 私聊按钮
        self.button1 = tk.Button(self.window, text="私聊", font=10, command=self.private_chat)
        self.button1.place(x=400, y=320)
        # 发送文件按钮
        self.button2 = tk.Button(self.window, text="文件", font=10, command=self.send_file)
        self.button2.place(x=400, y=360)
        # 语音通话按钮
        self.button3 = tk.Button(self.window, text="语音", font=10, command=self.send_voice_request)
        self.button3.place(x=460, y=360)
        # NAT穿透按钮
        self.button4 = tk.Button(self.window, text="NAT穿透", font=10, command=self.nat_request)
        self.button4.place(x=380, y=400)
        # NAT后私聊按钮
        self.button5 = tk.Button(self.window, text="P2P私聊", font=10, command=self.p2p_chat)
        self.button5.place(x=460, y=400)

        chunk_size = 1024  # 512
        audio_format = pyaudio.paInt16
        channels = 1
        rate = 20000

        # 初始化音频流
        self.voice_state = 0
        self.p = pyaudio.PyAudio()
        self.playing_stream = self.p.open(format=audio_format, channels=channels, rate=rate, output=True,
                                          frames_per_buffer=chunk_size)
        self.recording_stream = self.p.open(format=audio_format, channels=channels, rate=rate, input=True,
                                            frames_per_buffer=chunk_size)
        self.voice_sender = "anonymous"
        self.voice_recipient = "anonymous"
        #接收新消息
        self.receive_thread = threading.Thread(target=self.receive_message, daemon=True)
        self.receive_thread.start()

        self.window.mainloop()

    # 消息显示界面禁止键盘输入
    @staticmethod
    def disable_keyboard(event):
        return "break"
    
    # 公屏聊天
    def public_chat(self):
        message = self.input.get("1.0",tk.END)
        # 清空输入框
        self.input.delete("1.0", tk.END)
        if message=="\n":
                message = ""
        if message:
            message = f"PUBLIC|{self.client.username}|{message}"
            self.client.send_data(message)
        else:
            messagebox.showerror("错误", "发送的消息不能为空")


    #  私聊
    def private_chat(self):
        # 获取选中的私聊用户
        recipient = self.user_list.get("anchor")
        if recipient:
            message = self.input.get("1.0", tk.END)
            # 清空输入框
            self.input.delete("1.0", tk.END)
            if message=="\n":
                message = ""
            if message:
                # 向服务器发送消息
                message = f"PRIVATE|{self.client.username}|{recipient}|{message}"
                self.client.send_data(message)
            else:
                messagebox.showerror("错误", "发送的消息不能为空")
        else:
            messagebox.showerror("错误", "未选择私聊对象")

    def receive_message(self):
        while True:
            message, data = self.client.receive_data()
            if message.startswith("PUBLIC"):
                message = message.split("|", 2)
                t = time.localtime()
                show_message = str(t.tm_year) + "年" + str(t.tm_mon) + "月" + str(t.tm_mday) + "日" + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec) + "\n" + message[1] + ":" + message[2]
                self.textbox.insert(tk.END, show_message)
            elif message.startswith("PRIVATE"):
                message = message.split("|", 3)
                t = time.localtime()
                show_message = str(t.tm_year) + "年" + str(t.tm_mon) + "月" + str(t.tm_mday) + "日" + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec) +"(私聊)"+ "\n" +message[1] + "对" + message[2] + "说：" + message[3]
                self.textbox.insert(tk.END, show_message)
            elif message.startswith("FILE"):
                self.receive_file(message, data)
            elif message.startswith("VOICE"):
                self.receive_voice(message, data)
            elif message.startswith("ONLINE") or message.startswith("OFFLINE"):
                self.update_online_users(message)
            elif message.startswith("NAT"):
                self.nat_handle(message)    
            else:
                t = time.localtime()
                show_message = str(t.tm_year) + "年" + str(t.tm_mon) + "月" + str(t.tm_mday) + "日" + " " + str(t.tm_hour) + ":" + str(t.tm_min) + ":" + str(t.tm_sec) + "\n" + message
                self.textbox.insert(tk.END, show_message)

    def send_file(self):
        # 选择文件
        file_path = filedialog.askopenfilename()
        if file_path:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            sender = self.client.username
            # 选择接收方
            recipient = simpledialog.askstring("文件传输", "请输入接收方名称")
            if recipient:
                request = "FILE_REQUEST|"+sender+ "|"+ recipient+"|" + file_name
                self.client.send_data(request)
                threading.Thread(target=self.send_file_thread, args=(file_path, file_size, recipient)).start()
            else:
                messagebox.showerror("错误", "未选择发送对象")

    #开始发送
    def send_file_thread(self, file_path, file_size, recipient):
        # 等待对方接收
        while self.file_state == 0:
            continue
        # 对方拒绝接收或用户不存在
        if self.file_state == 2:
            self.file_state = 0
        # 对方接收
        elif self.file_state == 1:
            file_name = os.path.basename(file_path)
            # UI界面
            file_window = tk.Toplevel(self.window)
            file_window.title("文件传输")
            file_window.protocol("WM_DELETE_WINDOW", self.file_cancel)
            file_window.geometry("300x100")
            #窗口置顶
            file_window.attributes("-topmost", True)
            tk.Label(file_window, text=f"{file_name}文件上传中...", font=20).pack()
            len_recipient = len(recipient)
            len_recipient = str(len_recipient)
            # 控制信息
            control_message = f"FILE_CONTENT|{len_recipient}|{recipient}|" 
            with open(file_path, "rb") as f:
                # 定位到先前已发送的位置
                file_sent = self.file_cancel_record.get(file_name)
                if file_sent is None:
                    f.seek(0)
                    total_sent = 0
                else:
                    print('断点续传')
                    f.seek(file_sent)
                    self.file_cancel_record.pop(file_name)
                    total_sent = file_sent
                # 发送文件数据
                while self.file_state != 0 and total_sent < file_size:
                    data = f.read(2048)
                    total_sent += len(data)
                    self.client.send_data(bytes(control_message, encoding='utf-8')+data)
            file_window.destroy()
            if self.file_state != 0:
                # 发送完成
                self.client.send_data(f"FILE_END|{recipient}|{file_name}")
                messagebox.showinfo("文件传输", f"{file_name}文件发送完成")
                self.file_state = 0
                return SystemExit
            else:
                # 发送取消
                self.client.send_data(f"FILE_CANCEL|{recipient}|{file_name}")
                messagebox.showinfo("文件传输", "已取消发送")
                self.file_cancel_record[file_name] = total_sent

    def receive_file(self, message, data):
        if message.startswith("FILE_ACCEPT"):
            self.file_state = 1
        elif message.startswith("FILE_REJECT"):
            self.file_state = 2
            messagebox.showinfo("文件传输失败", "对方拒绝接收")
        elif message.startswith("FILE_USER_NO_EXIST"):
            messagebox.showinfo("文件传输", "用户不存在")
            self.file_state = 2
        elif message.startswith("FILE_REQUEST"):
            message = message.split("|", 3)
            sender = message[1]
            recipient = message[2]
            file_name = message[3]
            if messagebox.askyesno("文件传输", f"{sender} 向你发送文件{file_name}\n是否接收?"):
                self.client.send_data(f"FILE_ACCEPT|{sender}")
                self.cur_file_name = file_name
                f = open('./' + file_name + '.tmp', 'w')
                f.close()
            else:
                self.client.send_data(f"FILE_REJECT|{sender}")
        elif message.startswith("FILE_CONTENT"):
            # 若为文件内容
            file_name = self.cur_file_name
            file_content = data
            with open('./'+file_name+'.tmp', 'ab') as recv_file:
                recv_file.write(file_content)
        elif message.startswith("FILE_END"):
            # 若文件已发完
            get_data = message.split("|", 1)
            file_name = get_data[1]
            try:
                os.rename('./'+file_name+'.tmp', file_name)
            except FileExistsError:
                os.remove('./'+file_name)
                os.rename('./'+file_name+'.tmp', file_name)
            messagebox.showinfo("文件传输", f"{file_name}文件接收完成")
        elif message.startswith("FILE_CANCEL"):
            # 若文件发送中断
            get_data = message.split("|", 1)
            file_name = get_data[1]
            messagebox.showinfo("文件传输", f"{file_name}文件发送中断")

    def file_cancel(self):
        self.file_state = 0

    def update_online_users(self, message):
        message = message.split("|", 1)
        user = message[1]
        # 用户上线
        if message[0]=="ONLINE":
            self.user_list.insert(tk.END, user)
        # 用户离线
        elif message[0]=="OFFLINE":
            for i in range(self.user_list.size()):
                if self.user_list.get(i) == user:
                    self.user_list.delete(i)
                    break

    def send_voice_request(self):
        # 获取选中的语音用户
        recipient = self.user_list.get("anchor")
        # 更新通话双方的信息（自己是sender，别人是recipient）
        self.voice_recipient = recipient
        self.voice_sender = self.client.username
        request = f"VOICE_REQUEST|{self.client.username}|{self.voice_recipient}"
        self.client.send_data(request)

    def send_voice_thread(self):
        # UI界面
        recipient = self.voice_recipient
        voice_window = tk.Toplevel(self.window)
        voice_window.title("语音通话")
        # 调整窗口大小
        voice_window.geometry("200x100")
        tk.Label(voice_window, text=f"正在通话中...", font=20).pack()
        voice_window.protocol("WM_DELETE_WINDOW", self.close_voice)
        # 控制信息
        len_recipient = len(recipient)
        len_recipient = str(len_recipient)
        control_message = f"VOICE_CONTENT|{len_recipient}|{recipient}|"
        # 发送语音数据
        while self.voice_state == 1:
            data = self.recording_stream.read(1024)
            self.client.send_data(bytes(control_message, encoding='utf-8') + data)
        # 语音通话结束
        voice_window.destroy()
        sendend = f"VOICE_END|{recipient}"
        self.client.send_data(sendend)
        self.voice_state = 0

    def close_voice(self):
        self.voice_state = 0

    def receive_voice(self, message, data):
        if message.startswith("VOICE_ACCEPT"):
            #自己是sender，别人是recipient
            recipient = self.voice_recipient
            self.voice_state = 1
            threading.Thread(target=self.send_voice_thread).start()
        elif message.startswith("VOICE_REJECT"):
            messagebox.showinfo("语音通话", "对方已拒绝")
        elif message.startswith("VOICE_REQUEST"):
            message = message.split("|", 1)
            sender_name = message[1]
            if messagebox.askyesno("语音通话", f"{sender_name}邀请你进行语音通话\n是否接受?"):
                self.client.send_data(f"VOICE_ACCEPT|{sender_name}")
                self.voice_state = 1
                #对方是语音接收方
                self.voice_recipient = sender_name
                self.voice_sender = self.client.username
                # 开启语音发送线程
                recipient = self.voice_recipient
                threading.Thread(target=self.send_voice_thread).start()
            else:
                self.client.send_data(f"VOICE_REJECT|{sender_name}")
        elif message.startswith("VOICE_CONTENT"):
            voice_data = data
            self.playing_stream.write(voice_data)
        elif message.startswith("VOICE_END"):
            messagebox.showinfo("语音通话", "语音通话已结束")
            self.voice_state = 0

    def nat_request(self): 
        recipient = self.user_list.get("anchor")
        if recipient:
            self.client.send_data(f"NAT_REQUEST|{self.client.username}|{recipient}")
        else:
            messagebox.showerror("错误", "未选择连接方")
    
    def nat_handle(self, message):
        if  message.startswith("NAT_REQUEST"):
            message = message.split("|", 1)
            sender = message[1]
            if messagebox.askyesno("NAT穿透", f"{sender}请求与你建立连接\n是否同意?"):
                #同意建立连接
                self.client.send_data(f"NAT_ACCEPT|{sender}|{self.client.username}")
                #创建一个UDP套接字，该套接字使用IPv4地址族（socket.AF_INET）和数据报协议（socket.SOCK_DGRAM)
                self.nat_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # 向服务器发送消息以通知对方自己的公网ip地址与端口
                peer = sender
                self.nat_sock.sendto(f"NAT_ADDR|{self.client.username}|{peer}".encode("utf-8"), ("120.46.87.181",520))
                #self.nat_sock.sendto(f"NAT_ADDR|{self.client.username}|{sender}".encode("utf-8"), ("127.0.0.1",520))
                

            else:
                self.client.send_data(f"NAT_REJECT|{sender}")
        #对方同意建立连接
        elif message.startswith("NAT_ACCEPT"):  
            #创建一个UDP套接字，该套接字使用IPv4地址族（socket.AF_INET）和数据报协议（socket.SOCK_DGRAM)
            message = message.split("|", 1)
            peer = message[1]
            self.nat_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 向服务器发送消息以通知对方自己的公网ip地址与端口
            self.nat_sock.sendto(f"NAT_ADDR|{self.client.username}|{peer}".encode("utf-8"), ("120.46.87.181",520))
            #self.nat_sock.sendto(f"NAT_ADDR|{self.client.username}|{peer}".encode("utf-8"), ("127.0.0.1",520))
            
        #对方拒绝建立连接
        elif message.startswith("NAT_REJECT"):  
            messagebox.showinfo("NAT穿透", "对方拒绝建立连接")
        elif message.startswith("NAT_ADDR"):
            message = message.split("|", 1)
            self.nat_peer = eval(message[1])
            print("NAT穿透成功")
            print("对方的公网ip地址与端口:", self.nat_peer)
            threading.Thread(target=self.p2p_receive_message).start()


    def p2p_chat(self):   
        message = self.input.get("1.0", tk.END)
        # 清空输入框
        self.input.delete("1.0", tk.END)
        self.p2p_chat_state = 0
        if message:
            # 显示在聊天界面
            t = time.localtime()
            show_message = f"{t.tm_year}年{t.tm_mon}月{t.tm_mday}日 {t.tm_hour}:{t.tm_min}:{t.tm_sec}(p2p_chat)\n{self.client.username}: {message}"
            self.textbox.insert(tk.END, show_message)
            self.textbox.see(tk.END)
            try:
                # 发送消息
                self.nat_sock.sendto(f"{self.client.username}|{message}".encode("utf-8"), self.nat_peer)
            except socket.error as e:
                # 连接出错
                self.nat_sock.close()
                raise SystemExit
        else:
            messagebox.showerror("错误", "发送的消息不能为空")
                    
    def p2p_receive_message(self):
        while True:
            try:
                message, address = self.nat_sock.recvfrom(1024)
                message = message.decode("utf-8")
                message = message.split("|", 1)
                sender = message[0]
                message = message[1]
            except socket.error:
                messagebox.showerror("错误", "P2P连接已断开")
                return SystemExit
            t = time.localtime()
            show_message = f"{t.tm_year}年{t.tm_mon}月{t.tm_mday}日 {t.tm_hour}:{t.tm_min}:{t.tm_sec}(p2p_chat)\n{sender}: {message}"
            self.textbox.insert(tk.END, show_message)
            self.textbox.see(tk.END)

if __name__ == '__main__':
    #服务器外网ip
    #host = '127.0.0.1'
    host ='120.46.87.181'
    port = 996
    client = Client(host,port)
    LoginWindow(client)
    ChatRoom(client)
