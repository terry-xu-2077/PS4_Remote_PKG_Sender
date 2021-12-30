import os.path
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as msgbox
from tkinter import filedialog
import pygubu
from Core import *
import windnd
import webbrowser
import locale
from pkg_parser import getPkgInfo
from Server import FilesServer
from ui_res_base64 import ui_data,ui_icon
from language import __lang__

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

RES_PATH = get_resource_path('res')
PKG_SERVER = None
csv_data = './PKG.csv'
column_fileName = 5
column_status = 7
sort_key = {
    'GAME':1,
    'UPDATE':2,
    'DLC':3,
    'THEME':4
}
pkg_info_dict = {
    'gd':'GAME',
    'gp':'UPDATE',
    'ac':'DLC'
}

config = myJson('./Config.json')

if config.get('language') == None:
    if locale.getdefaultlocale()[0] == 'zh_CN':
        config['language'] = myDict(__lang__)
    else:
        lang_data = {}
        for k in __lang__.keys():
            lang_data.setdefault(k, k)
        config['language'] = myDict(lang_data)

class task_progress():
    def __init__(self, task_id, callback):
        self.task_id = task_id
        self.callback = callback
        self.flag = True

    def start(self):
        while self.flag:
            info = PS4_API.get_task_progress(self.task_id)
            self.callback(info, self.task_id)

    def stop(self):
        self.flag = False

class GuiApp():
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        #builder.add_resource_path(RES_PATH)
        builder.add_from_xmlnode(ET.fromstring(ui_data))
        #builder.add_from_file(RES_PATH + "/appUI.ui")
        self.mainwindow = builder.get_object('toplevel1', master)
        self.mainwindow.iconphoto(True,tk.PhotoImage(data=ui_icon,format='png'))

        self.mainwindow.protocol("WM_DELETE_WINDOW", self.on_close_window)
        self.mainmenu = builder.get_object('tree_menu', master)
        self.boxServerIP = builder.get_object('boxServerIP', master)
        self.entry_Port = builder.get_object('entry_Port', master)
        self.entry_ps4ip = builder.get_object('entry_ps4ip', master)
        self.tree = builder.get_object('tree_pkg_info', master)
        self.tree.bind("<Button-3>", self.open_menu)
        self.tree.bind('<ButtonRelease-1>', self.treeSlected)
        self.scroll_y = builder.get_object('scrollbar1', master)
        self.scroll_y['command'] = self.tree.yview
        self.tree['yscrollcommand'] = self.scroll_y.set
        self.progressbar1 = builder.get_object('progressbar1', master)
        self.button_check = builder.get_object('button_check_ps4_ip', master)

        self.cv_server = builder.get_object('canvas_server', master)
        self.cv_ps4 = builder.get_object('canvas_ps4', master)

        self.var_show_task_id = tk.StringVar()
        self.var_show_task_id.set('')
        self.label_task_id = builder.get_object('label_task_id', master)
        self.label_task_id['textvariable'] = self.var_show_task_id
        self.label_task_id.bind('<ButtonRelease-1>', self.label_progress_continue)
        self.label_url = builder.get_object('label1_url', master)
        #self.label_url.bind('<ButtonRelease-1>', self.btn_url)
        self.label_url['text'] = ''

        host_ip_list = get_host_ip()
        self.var_server_ip = tk.StringVar()
        self.boxServerIP['textvariable'] = self.var_server_ip
        self.boxServerIP['value'] = host_ip_list

        self.task_td = None
        self.task_item = None
        self.task_id = ''
        self.task_cancel = False
        self.task_progress_wait = False

        for col in self.tree['columns']:
            text = self.tree.heading(col)['text']
            column = col
            self.tree.heading(
                column,
                command=lambda column=column,text=text: self.tree_sort_column(column,text,True)
            )

        callbacks = {
            'btn1_clicked': self.btn_import_pkg,
            'btn3_clicked': self.btn_send_pkg,
            'btn4_clicked': self.btn_cancel,
            'treeMenuCommand': self.treeMenuCommand,
            'combox_changed': self.combox_changed,
            'check_ps4_ip':self.check_ps4_ip
        }
        builder.connect_callbacks(callbacks)

        self.translate_widgets = {
            'ServerIP': builder.get_object('label2', master),
            'Port': builder.get_object(('label4'), master),
            'PS4IP': builder.get_object('label3', master),
            'Task': builder.get_object('labelframe2', master),
            'ImportPKG': builder.get_object('button_import', master),
            'Stop': builder.get_object('button_stop', master),
            'Send': builder.get_object('button_send', master),
            'Menu': builder.get_object('tree_menu', master),
            'Check':self.button_check,
            #'Url':self.label_url
        }

        self.lock_list = [
            self.tree,
            self.boxServerIP,
            self.entry_Port,
            self.entry_ps4ip,
            self.builder.get_object('button_import', master),
            self.builder.get_object('button_send', master),
        ]

        self.myStyle = ttk.Style()
        # self.myStyle.theme_use('clam')
        self.myStyle.configure('blue.Horizontal.TProgressbar', background='blue')
        self.progressbar1.config(style='blue.Horizontal.TProgressbar')

        self.canvans_draw()
        self.translate()
        self.load_config()
        self.mainwindow.geometry('1000x540')

    def run(self):
        self.mainwindow.mainloop()

    def canvans_draw(self, mode='init'):
        pos = (2, 2, 16, 16)
        option = {
            'fill': '#c0c0c0',
            'width': 0,
        }
        if mode == 'init':
            self.cv_server.delete('all')
            self.cv_ps4.delete('all')
            self.cv_server.create_oval(pos, **option)
            self.cv_ps4.create_oval(pos, **option)
        elif mode == 'ps4:yes':
            option['fill'] = '#1de298'
            self.cv_ps4.create_oval(pos, **option)
        elif mode == 'ps4:No find':
            option['fill'] = '#bd395a'
            self.cv_ps4.create_oval(pos, **option)
        elif mode == 'ps4:No remote':
            option['fill'] = '#eba93a'
            self.cv_ps4.create_oval(pos, **option)
        elif mode == 'server:start':
            option['fill'] = '#1de298'
            self.cv_server.create_oval(pos, **option)
        elif mode == 'server:stop':
            option['fill'] = '#c0c0c0'
            self.cv_server.create_oval(pos, **option)
        elif mode == 'server:err':
            option['fill'] = '#bd395a'
            self.cv_server.create_oval(pos, **option)

    def load_config(self):
        global PKG_SERVER
        server_ip = config['server_ip']
        if server_ip: self.var_server_ip.set(server_ip)

        port = config['port']
        if port == None:
            port = 8888
        self.entry_Port.delete(0, tk.END)
        self.entry_Port.insert(0, port)
        PKG_SERVER = FilesServer(port)
        PKG_SERVER.start()
        if server_ip:
            if PKG_SERVER.running:
                self.canvans_draw('server:start')
                self.server_url = 'http://{}:{}'.format(self.boxServerIP.get(), self.entry_Port.get())
            else:
                self.canvans_draw('server:err')

        ps4_ip = config['ps4_ip']
        if ps4_ip:
            self.entry_ps4ip.delete(0, tk.END)
            self.entry_ps4ip.insert(0, ps4_ip)
            if ps4_ip and ps4_check_ip(ps4_ip):
                self.canvans_draw('ps4:yes')
            else:
                self.canvans_draw('ps4:No find')

        self.tree_read_data()

    def on_close_window(self): # todo: 当窗口关闭时
        global config
        config['server_ip'] = self.boxServerIP.get()
        config['port'] = self.entry_Port.get()
        config['ps4_ip'] = self.entry_ps4ip.get()
        config.save()
        PKG_SERVER.stop()
        self.task_progress_wait = False
        self.tree_save_data()
        myPrint('退出程序')
        self.mainwindow.destroy()

    def lock_widgets(self, mode='lock'):
        if mode == 'unlock':
            for item in self.lock_list:
                if isinstance(item, pygubu.widgets.editabletreeview.EditableTreeview):
                    item.config(selectmode=tk.EXTENDED)
                else:
                    item.config(state=tk.NORMAL)
        else:
            for item in self.lock_list:
                if isinstance(item, pygubu.widgets.editabletreeview.EditableTreeview):
                    item.config(selectmode=tk.NONE)
                else:
                    item.config(state=tk.DISABLED)

    def translate(self):
        for k in self.translate_widgets.keys():
            item = self.translate_widgets[k]
            if isinstance(item, tk.Menu):
                for i in range(10):
                    try:
                        item.entryconfig(i, label=config['language'][item.entrycget(i, 'label')])
                    except:
                        pass
            else:
                try:
                    self.translate_widgets[k]['text'] = config['language'][k]
                except:
                    pass
        for c in range(9):
            text = self.tree.heading(c)['text']
            if text != None:
                self.tree.heading(c, text=config['language'][text])

    def set_ps4_ip_text(self, info):
        self.entry_ps4ip.delete(0, tk.END)
        if config['language'].get(info):
            self.canvans_draw('ps4:' + info)
            self.entry_ps4ip.insert(0, config['language'][info])
        else:
            self.canvans_draw('ps4:yes')
            self.entry_ps4ip.insert(0, info)

    def open_menu(self, event):
        item = self.tree.identify_row(event.y)
        try:
            self.tree.selection_add(item)
        except:
            pass
        try:
            self.mainmenu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.mainmenu.grab_release()

    def tree_save_data(self):
        save_csv_data(self.tree_get_data(), csv_data)

    def tree_get_data(self):
        items = self.tree.get_children()
        data_list = []
        for item in items:
            data_list.append(list(self.tree.item(item, 'values')))
        return data_list

    def tree_read_data(self):
        for data in read_csv_data(csv_data):
            self.tree.insert('', tk.END, values=data)

    def tree_sort_column(self,column,text,rev):
        li = [(self.tree.set(id,column),id,sort_key.get(self.tree.set(id,column))) for id in self.tree.get_children('')]
        if text == 'Type':
            li.sort(reverse=rev,key= lambda item:item[2])
        else:
            li.sort(reverse=rev)

        for i,(value,item_id,key) in enumerate(li):
            self.tree.move(item_id,'',i)

        self.tree.heading(
            column,
            command=lambda : self.tree_sort_column(column,text,not rev)
        )

    def td_tree_insert(self, pkg_list): # todo: 批量填表
        for i, f in enumerate(pkg_list):
            info = getPkgInfo(f)
            pkg_type = pkg_info_dict[info['CATEGORY']]
            if 'THEME' in info['CONTENT_ID']:
                pkg_type = 'THEME'
            data = (
                str(i + 1),
                pkg_type,
                info['VER'],
                info['TITLE_ID'],
                info['TITLE'],
                os.path.split(f)[1],
                info['SIZE'],
                config['language']['----'],
                f
            )
            self.tree.insert('', tk.END, values=data)
        self.update_tree_id()

    def check_ps4_ip(self):
        if ps4_check_ip(self.entry_ps4ip.get()):
            self.server_url = 'http://{}:{}'.format(self.boxServerIP.get(), self.entry_Port.get())
            PS4_API.set_ps4_url(self.entry_ps4ip.get())
            self.canvans_draw('ps4:yes')
            if not PS4_API.is_readly():
                self.canvans_draw('ps4:No remote')
        else:
            self.canvans_draw('ps4:No find')

    def combox_changed(self, event):
        self.server_url = 'http://{}:{}'.format(self.boxServerIP.get(), self.entry_Port.get())

    def stop_all(self):
        self.tree.set(self.task_item, column=column_status, value=config['language']['Canceled'])
        self.progressbar1.config(style='red.Horizontal.TProgressbar')
        self.progressbar1["value"] = 0
        self.task_td.stop()
        self.task_cancel = True
        PKG_SERVER.stop()
        self.lock_widgets('unlock')

    def btn_cancel(self): # todo:取消
        if self.task_id:
            info = PS4_API.unregister_task(self.task_id)
            if info.get('status') == 'success':
                self.stop_all()
            else:
                msgbox.showinfo(config['language']['No response'], config['language']['Remote Package Installer'])
                myPrint('cancel:', info)

    def label_progress_continue(self,event):
        self.task_progress_wait = False

    def progress_animation(self,v,sleep):
        if v <= self.progressbar1['value']:
            return
        t = 0.02
        s = (v - self.progressbar1['value']) / ( sleep / t )
        while self.progressbar1['value'] < v and not self.task_cancel:
            self.progressbar1['value'] += s
            time.sleep(t)
        if self.progressbar1["value"] > 999:
            self.progressbar1["value"] = 0

    def update_progress(self, info, task_id): # todo: 更新任务进度
        if info.get('transferred') != None:
            if info['transferred'] + info['length_total'] != 0:

                if info.get('rest_sec') > 0:
                    task_info = format_task_info(info, config['language'][
                        '{} / {} (Remaining {} minute {} seconds, Speed: {}MB/S)'])
                    self.var_show_task_id.set(task_info)

                percent = round(info['transferred'] / info['length_total'] * 1000, 2)
                animation = threading.Thread(target=self.progress_animation, args=(percent, 2.2))
                animation.start()
                animation.join()

                if int(info['length_total'] - info['transferred']) == 0: # 如果进度条走满
                    status_text = config['language'][info.get('status')]
                    self.task_td.stop()
                    self.tree.set(self.task_item, column=column_status, value=status_text)

        elif info.get('PS4-Request-Error'): # todo:循环等待确认
            wait_time = 0
            self.task_progress_wait = True
            while self.task_progress_wait:
                wait_time += 1
                self.var_show_task_id.set(
                    config['language'][
                        'The PS4 application is suspended or not responding. Please click here to try again ({})'].format(wait_time)
                )
                time.sleep(1)
        else:
            myPrint('progress err:',info)
            self.task_td.stop()
            self.progressbar1["value"] = 0

    def td_send_pkg(self):  # todo: -------------------------------- 发送 -----------------------------------
        self.lock_widgets()
        self.tree.selection_set()
        items = self.tree.get_children()
        PS4_API.server_url = self.server_url

        self.task_td = None
        self.task_item = None
        self.task_id = ''
        self.task_cancel = False
        self.task_progress_wait = False

        total = len(items)
        for i, item in enumerate(items):
            if self.task_cancel == True:
                break
            data = list(self.tree.item(item, 'values'))

            if data[column_status] == config['language']['----'] or data[column_status] == config['language']['Ready...']:
                self.tree.selection_set(item)
                self.tree.see(item)
                self.task_item = item
                info = PS4_API.install_pkg([data[column_fileName]])
                self.task_id = info.get('task_id')
                if self.task_id:
                    self.progressbar1.config(style='green.Horizontal.TProgressbar')
                    self.tree.set(item, column=column_status, value=config['language']['Sending'])
                    self.task_td = task_progress(self.task_id,self.update_progress)
                    self.task_td.start()
                    if i + 1  < total:
                        self.tree.set(items[i + 1], column=column_status, value=config['language']['Ready...'])
                        time.sleep(2)
                else:
                    error = info.get('error_code')
                    if str(error) != '0':
                        if isinstance(error,int):
                            err_text = config['language'][PS4_API.error_code.get(error)]
                            if not err_text:
                                err_text = error
                            self.tree.set(item, column=column_status, value=config['language']['Error:{}'].format(err_text))
                        else:
                            msgbox.showinfo('Remote Package Installer', info)
                    elif info.get('PS4-Request-Error'):
                        msgbox.showinfo(config['language']['No response'], config['language']['Remote Package Installer'])
                    else:
                        msgbox.showinfo('Error', 'NONE')

        self.var_show_task_id.set('')
        myPrint('列队完成')
        self.lock_widgets('unlock')
        self.task_id = ''

    def btn_send_pkg(self):
        self.server_url = 'http://{}:{}'.format(self.boxServerIP.get(), self.entry_Port.get())
        if PKG_SERVER.port != self.entry_Port.get():
            PKG_SERVER.reset_port(self.entry_Port.get())
        self.progressbar1["value"] = 0
        PS4_API.set_ps4_url(self.entry_ps4ip.get())
        if PS4_API.is_readly():
            if PKG_SERVER.update(self.tree_get_data()):
                td_send = threading.Thread(target=self.td_send_pkg)
                td_send.start()
            else:
                msgbox.showinfo(config['language']['PKG-SERVER'], config['language']['The server is abnormal'])
        else:
            myPrint(PS4_API.ps4_url)
            msgbox.showinfo(config['language']['No response'], config['language']['Remote Package Installer'])

    def btn_import_pkg(self,dropFiles=None):
        global config
        myPrint('import pkg')
        pkg_list = []

        if dropFiles !=None and isinstance(dropFiles,list):
            for i in dropFiles:
                try:
                    f = i.decode('utf-8')
                except:
                    f = i.decode('gbk')
                pkg_list.append(f)
        else:
            pkg_list = filedialog.askopenfilenames(initialdir=config['pkg_folder'])

        if pkg_list:
            config['pkg_folder'] = os.path.split(pkg_list[-1])[0]
        td = threading.Thread(target=self.td_tree_insert, args=(pkg_list,))
        td.start()

    def btn_url(self,event):
        return
        self.server_url = 'http://{}:{}'.format(self.boxServerIP.get(), self.entry_Port.get())
        if PKG_SERVER.port != self.entry_Port.get():
            PKG_SERVER.reset_port(self.entry_Port.get())
        if PKG_SERVER.is_ready():
            print(0)
            if PKG_SERVER.update(self.tree_get_data()):
                print(1)
                webbrowser.open(self.server_url)

    def treeSlected(self, event):
        pass
        # for item in self.tree.selection():
        #     text = self.tree.item(item, 'values')
        #     myPrint('select:', text[0])

    def update_tree_id(self):
        items = self.tree.get_children()
        for i, item in enumerate(items):
            self.tree.set(item, column=0, value=str(i + 1))

    def treeMenuCommand(self, event):
        myPrint('menu:', event)

        if event == 'command_open':
            for item in self.tree.selection():
                text = self.tree.item(item, 'values')
                os.startfile(os.path.split(text[-1])[0])

        elif event == 'command_del':
            for item in self.tree.selection():
                self.tree.delete(item)
            self.update_tree_id()

        elif event == 'command_clear':
            items = self.tree.get_children()
            for item in items:
                self.tree.delete(item)

        elif event == 'command_skip':
            for item in self.tree.selection():
                self.tree.set(item, column=column_status, value=config['language'][' Skip '])

        elif event == 'command_unskip':
            for item in self.tree.selection():
                self.tree.set(item, column=column_status, value=config['language']['----'])

        elif event == 'command_up':
            items = self.tree.selection()
            if items:
                up = self.tree.index(items[0]) - 1
                for item in self.tree.selection():
                    self.tree.move(item, '', up)
                self.update_tree_id()

        elif event == 'command_down':
            items = self.tree.selection()
            if items:
                down = self.tree.index(items[-1]) + 1
                for item in self.tree.selection():
                    self.tree.move(item, '', down)
                self.update_tree_id()


if __name__ == '__main__':
    app = GuiApp()
    windnd.hook_dropfiles(app.mainwindow,func=app.btn_import_pkg)
    app.run()
