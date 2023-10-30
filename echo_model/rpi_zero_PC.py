import sys, os, time, datetime
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QApplication 
from PyQt5.uic import loadUi
from PyQt5 import uic, QtTest, QtCore
import shelve

import zmq

context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:5555")

AUTO_BUTTON     = 0
MANUAL_BUTTON   = 1
LIVE            = 2
LOCATION        = 3
SOCKET_IDX      = 4

ON  = True
OFF = False

command_dict_list = []

for idx in range(8):
    command_dict = {
        'alive':        False,
        'auto_mode':    OFF,
        'manual_mode':  OFF
    }
    command_dict_list.append(command_dict)

class Util_Function:
    def Qsleep(self, ms):
        QtTest.QTest.qWait(ms)

    def save_var(self, key, value):
        # with shelve.open('C:\work\SMRS\config') as f:
        with shelve.open('location') as f:
            f[key] = value

    def read_var(self, key):
        # with shelve.open('C:\work\SMRS\config') as f:
        with shelve.open('location') as f:
            try:
                temp = f[key]
                # print(f[key])
                return temp
            except:
                pass

#--------------------------------------------------------------
# [THREAD] RECEIVE from RPI Zero
#--------------------------------------------------------------
class THREAD_RECEIVE_MSG(QThread):
    received_alive = pyqtSignal(int, dict)
    def __init__(self, idx, qt_obj):
        super( THREAD_RECEIVE_MSG, self).__init__()
        self.obj = qt_obj
        self.idx = idx

    def run(self):
        while True:
            event = self.obj.button_list[self.idx][SOCKET_IDX].poll(timeout = 2000) # wait 2 seconds
            self.check_event2(self.idx, event)

    def check_event2(self, idx, event):
        if event == 0:
            print(f'[{idx}]', 'timeout!!!!!!!!!!!!!!!!!!')
            command_dict_list[idx]['alive'] = False
            self.received_alive.emit(idx, command_dict_list[idx])
            return
        else:
            # print(f'[{idx}]', 'received alive!!')
            try:
                message = self.obj.button_list[idx][SOCKET_IDX].recv_json()
            except:
                print('rcv error!!')
                return

            if message['alive']:
                print(f'[THREAD] {[idx]} [alive]', message)
            else:
                print('[THREAD] not alive', message)

            self.received_alive.emit(idx, message)


class main_window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi('./rpi_zero_PC.ui', self)        

        # setting  the fixed width of window       
        # widtr = 1000
        # height = 700
        # self.setFixedWidth(width)
        # self.setFixedHeight(height)


        self.button_list = [
            #         0                     1                   2                 3                 4
            # AUTO MODE BUTTON   # MANUAL MODE BUTTON  # CONNECTION BUTTON   # LOCATION         # SOCKET
            [self.pb_autoMode_0, self.pb_manualMode_0, self.pb_connection_0, self.lineEdit_0],
            [self.pb_autoMode_1, self.pb_manualMode_1, self.pb_connection_1, self.lineEdit_1],
            [self.pb_autoMode_2, self.pb_manualMode_2, self.pb_connection_2, self.lineEdit_2],
            [self.pb_autoMode_3, self.pb_manualMode_3, self.pb_connection_3, self.lineEdit_3],
            [self.pb_autoMode_4, self.pb_manualMode_4, self.pb_connection_4, self.lineEdit_4],
            [self.pb_autoMode_5, self.pb_manualMode_5, self.pb_connection_5, self.lineEdit_5],
            [self.pb_autoMode_6, self.pb_manualMode_6, self.pb_connection_6, self.lineEdit_6],
            [self.pb_autoMode_7, self.pb_manualMode_7, self.pb_connection_7, self.lineEdit_7]
        ]

        self.util_func = Util_Function()
        self.location_dict = {
            '0': '0',
            '1': '1',
            '2': '2',
            '3': '3',
            '4': '4',
            '5': '5',
            '6': '6',
            '7': '7'
        } 

        if not os.path.isfile('location.db'):             # config.db -> macbook ok!!
            print('no file')
            for key, value in self.location_dict.items():
                self.util_func.save_var(key, value)

        # laod saved config data
        for key, value in self.location_dict.items():     
            temp = self.util_func.read_var(key)         # read config data from local db file
            self.location_dict[key] = temp                # set the data to config_dict
            self.button_list[int(key)][LOCATION].setText(temp)
            print('key: {0}, value: {1}'.format(key, temp))


        for buttons in self.button_list:
            for button in buttons:
                if 'lineEdit' in button.objectName():
                    continue
                button.setStyleSheet("border-style: outset; border-width: 0px")
                if 'connection' in button.objectName(): continue
                button.setDisabled(True)

            buttons[AUTO_BUTTON].clicked.connect(self.func_pb_autoMode)
            buttons[MANUAL_BUTTON].clicked.connect(self.func_pb_manualMode)
            buttons[LOCATION].returnPressed.connect(self.func_lineEdit_returnPressed)

        for idx in range(8):
            sock = context.socket(zmq.PAIR)
            sock.bind(f"tcp://*:550{idx}")
            self.button_list[idx].append(sock)  # zmq 소켓을 각 button_list 마지막에 넣는다.
            print('idx: ', idx, 'socket binded!!')

        for idx in range(8):
            thread = THREAD_RECEIVE_MSG(idx, self)
            thread.received_alive.connect(self.alive_func)
            thread.start()
            print('idx: ', idx, 'thread started!!')
            time.sleep(0.1)
        
        # self.lineEdit_0.returnPressed.connect(self.textEditEditingFinished)

    # def textEditEditingFinished(self):
    def func_lineEdit_returnPressed(self):
        # 사용자가 텍스트 입력을 마치면 이 함수가 호출됩니다.
        sender = self.sender()  # 이벤트를 발생시킨 버튼을 찾습니다.
        if sender:
            print(f'{sender.objectName()}')

        num = int(sender.objectName()[-1])

        edited_text = sender.text()
        self.util_func.save_var(str(num), edited_text)
        print(f"Editing finished. Text: {edited_text}")


    def alive_func(self, idx, message):
        if message['alive']:
            # print('+++ idx: ',idx, 'alive', message)
            self.button_list[idx][LIVE].setChecked(True)
            self.button_list[idx][AUTO_BUTTON].setEnabled(True)
            # self.pb_manualMode_1.setEnabled(True)
        else:
            print('--- not alive')
            self.button_list[idx][LIVE].setChecked(False)
            self.button_list[idx][AUTO_BUTTON].setChecked(False)
            self.button_list[idx][MANUAL_BUTTON].setChecked(False)
            self.button_list[idx][AUTO_BUTTON].setDisabled(True)
            self.button_list[idx][MANUAL_BUTTON].setDisabled(True)
            return
        
        if message['auto_mode']:
            self.button_list[idx][AUTO_BUTTON].setChecked(True)
            self.button_list[idx][MANUAL_BUTTON].setAutoExclusive(False)
        else:
            self.button_list[idx][AUTO_BUTTON].setChecked(False)
            self.button_list[idx][MANUAL_BUTTON].setAutoExclusive(True)

            if message['manual_mode']:
                self.button_list[idx][MANUAL_BUTTON].setChecked(True)
            else:
                self.button_list[idx][MANUAL_BUTTON].setChecked(False)
    

    def func_pb_autoMode(self):
        sender = self.sender()  # 이벤트를 발생시킨 버튼을 찾습니다.
        if sender:
            print(f'{sender.objectName()} 버튼이 클릭되었습니다.')

        num = int(sender.objectName()[-1])
        print('num: ', num)

        self.button_list[num][MANUAL_BUTTON].setChecked(False)

        if sender.isChecked():
            command_dict_list[num]['auto_mode'] = ON
            command_dict_list[num]['manual_mode'] = OFF
            print("auto mode pressed.")
            self.button_list[num][MANUAL_BUTTON].setDisabled(True)
        else:
            command_dict_list[num]['auto_mode'] = OFF
            print("auto mode not pressed.")
            self.button_list[num][MANUAL_BUTTON].setEnabled(True)

        self.button_list[num][SOCKET_IDX].send_json(command_dict_list[num])
        print('[{}][{}] {}'.format(sys._getframe().f_code.co_name, num, command_dict_list[num]))
        
    def func_pb_manualMode(self):
        sender = self.sender()  # 이벤트를 발생시킨 버튼을 찾습니다.
        if sender:
            print(f'{sender.objectName()} 버튼이 클릭되었습니다.')

        num = int(sender.objectName()[-1])
        print('num: ', num)

        if sender.isChecked():
            command_dict_list[num]['manual_mode'] = ON
            print("manual mode pressed.")
        else:
            command_dict_list[num]['manual_mode'] = OFF
            print("manual mode not pressed.")

        self.button_list[num][SOCKET_IDX].send_json(command_dict_list[num])


def run():
    app = QApplication(sys.argv)
    widget = main_window()

    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
