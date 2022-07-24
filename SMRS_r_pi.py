#!/usr/bin/env python
# coding=utf8

import os, sys, time, datetime, warnings, signal
from PyQt5.QtCore import QSize, QRect, QObject, pyqtSignal, QThread, pyqtSignal, pyqtSlot, Qt, QEvent, QTimer, QProcess
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, \
    QListView
from PyQt5.QtWidgets import QPushButton, QGridLayout, QLCDNumber
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtTest, QtGui, QtCore

import numpy as np
import shelve
from datetime import datetime
# import pandas as pd

import time
import pymongo
import pprint

import subprocess

import mqtt.sub_class as sc
import json
import psutil

server_ip = '203.251.78.135'

userid = 'smrs_1'
passwd = 'smrs2580_1!'

mongo_port = 27017
mqtt_port = 1883

pub_root_topic = "R_PI/"
sub_root_topic = "APP/"

DEBUG_PRINT = False
# DEBUG_PRINT = True
# ------------------------------------------------------------------------------
# config -----------------------------------------------------------------------
# ------------------------------------------------------------------------------
# x_size = 360# graph's x size
x_size = 720# graph's x size
# NUM_X_AXIS = 300
NUM_X_AXIS = 720
NUM_UPDATE_X_AXIS = 5

ROW_COUNT = 7
COL_COUNT = 3

SEND_SENSOR_DATA_INTERVAL = 1000 # ms -> timer setting
HEATING_TIME = 5000 # ms -> timeer setting

KEYPAD_TIME = 5000

pre_heat_road_temp = 0
heat_road_temp  = 0
set_road_humidity = 0
set_air_temp = 0
pre_heat_on_time = 0
heat_on_time = 0

form_class = uic.loadUiType('SMRS_r_pi.ui')[0]

# --------------------------------------------------------------
# [THREAD] 
# --------------------------------------------------------------
class THREAD_RECEIVE_Data(QThread):
    intReady = pyqtSignal(float)
    to_excel = pyqtSignal(str, float)

    @pyqtSlot()
    def __init__(self):
        super(THREAD_RECEIVE_Data, self).__init__()
        self.time_format = '%Y%m%d_%H%M%S'

        self.__suspend = False
        self.__exit = False
        self.log_flag = False

    def run(self):
        while True:
            ### Suspend ###
            while self.__suspend:
                time.sleep(0.5)

            _time = datetime.now()
            _time = _time.strftime(self.time_format)

            ### Exit ###
            if self.__exit:
                break

    def mySuspend(self):
        self.__suspend = True

    def myResume(self):
        self.__suspend = False

    def myExit(self):
        self.__exit = True

    def close(self):
        self.mySuspend()


class KEY_PAD_UI(QWidget):
    cb_signal = pyqtSignal(str)
    
    def __init__(self, _timer):
        super().__init__()
        self.Init_UI()
        self.text = ''
        self.num = '0'
        # self.obj = QLCDNumber()
        self.endFlag = 1
        self.obj = None
        self.timer = _timer

    def Init_UI(self):
        # self.setGeometry(750, 300, 400, 300)
        # self.setGeometry(300, 100, 400, 300)
        self.setGeometry(300, 100, 350, 350)
        self.setWindowTitle('Keypad')

        grid = QGridLayout()
        self.setLayout(grid)        

        self.lcd = QLCDNumber()
        self.lcd.setSegmentStyle(QLCDNumber.Flat)
        grid.addWidget(self.lcd, 0, 0, 3, 0)
        grid.setSpacing(10)

        """
        names = ['Cls', '', '',  'Close',
                 '7',   '8',  '9', '',
                 '4',   '5',  '6', '',
                 '1',   '2',  '3', '',
                 '-',   '0',  '.', 'Enter']
        """
        names = ['Cls',    '',   'Close',
                 '7',     '8',  '9',
                 '4',     '5',  '6',
                 '1',     '2',  '3',
                 '-',     '0',  '.',
                 'OK',     '', 'Cancel']

        # positions = [(i,j) for i in range(4, 9) for j in range(4, 8)]
        positions = [(i,j) for i in range(4, 10) for j in range(4, 7)]

        for position, name in zip(positions, names):
            # print("position=`{}`, name=`{}`".format(position, name))
            if name == '':
                continue

            button = QPushButton(name)
            grid.addWidget(button, *position)
            button.clicked.connect(self.Cli)

        # self.show()

    def Cli(self):
        self.timer.stop()
        self.timer.start(KEYPAD_TIME)
        sender = self.sender().text()

        if sender == 'OK':
            print("in pad: ", self.text)
            # self.obj.display(self.text)
            if self.text != '':
                self.num = self.text

            self.text = ''
            self.lcd.display(self.text)
            self.endFlag = 0
            self.close()
            self.cb_signal.emit(self.num)
            return
        elif sender == 'Cls':
            self.text = ''
        elif sender == 'Close':
            self.endFlag = 0
            self.text = ''
            self.close()
        else:
            self.text += sender

        self.lcd.display(self.text)
    
    def close_func(self, timer):
        timer.stop()
        self.text = ''
        self.lcd.display(self.text)
        self.endFlag = 0
        self.close()


class qt(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # self.setWindowFlags(Qt.FramelessWindowHint)

        self.pushButton.clicked.connect(lambda: self.send_STATUS(self.pushButton))
        self.pushButton_2.clicked.connect(lambda: self.send_STATUS(self.pushButton_2))

        # qeury(read) from start date (time) to end date (time)
        # TODO: need to modify "query_time" as a user input

        # Keypad timer setting ##############################
        self.keypad_timer = QtCore.QTimer()
        self.keypad_timer.timeout.connect(lambda: self.ex.close_func(self.keypad_timer))
        
        ##################################################
        self.ex = KEY_PAD_UI(self.keypad_timer)
        self.ex.cb_signal.connect(self.LineEdit_RET)

        # self.query_time = datetime.now()
        self.query_time = datetime(2022, 6, 15, 18, 22, 37)
        results = collection.find({"timestamp": {"$gt": self.query_time}}, limit=NUM_X_AXIS)

        # table Widget ------------------------------------------------------------------
        self.tableWidget.setRowCount(ROW_COUNT)
        self.tableWidget.setColumnCount(COL_COUNT)  # MEAN, parallel resistance

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.x_size = 720
        self.sine_x_data = np.linspace(-np.pi, np.pi, self.x_size)
        self.idx = 0
        self.temp_data = {}

        # loop for sending sensor data ###################
        self.timer = QtCore.QTimer()
        self.timer.setInterval(SEND_SENSOR_DATA_INTERVAL) # 100ms 
        self.timer.timeout.connect(self.send_msg_loop_timer)

        self.timer.start()
        ##################################################

        # HEAT TIME setting ##############################
        self.label_timer1 = QtCore.QTimer()
        self.label_timer2 = QtCore.QTimer()
        self.label_timer1.timeout.connect(lambda: self.label_color_change(self.label_7))
        self.label_timer2.timeout.connect(lambda: self.label_color_change(self.label_8))
        # self.label_timer.setInterval(HEATING_TIME) # 100ms 
        ##################################################


        self.thread_rcv_data = THREAD_RECEIVE_Data()
        self.thread_rcv_data.to_excel.connect(self.to_excel_func)
        # self.thread_rcv_data.start()

        self.resist_data = []
        self.log_flag = False

        ################################################
        # self.sub_mqtt = sc.SUB_MQTT(_topic = sub_root_topic + 'DATA')
        self.sub_mqtt = sc.SUB_MQTT(_broker_address = server_ip, _topic = sub_root_topic+'+', _client='client_r_pi', _mqtt_debug = DEBUG_PRINT)
        ################################################

        self.label_7.setStyleSheet("background-color: gray")
        self.label_8.setStyleSheet("background-color: gray")

        self.temp_lcdNumber = None

        self.clickable(self.pre_heat_road_temp).connect(lambda: self.input_value(self.pre_heat_road_temp))      # pre_heat_road_temp
        self.clickable(self.heat_road_temp).connect(lambda: self.input_value(self.heat_road_temp))              # heat_road_temp
        self.clickable(self.set_road_humidity).connect(lambda: self.input_value(self.set_road_humidity))        # set_road_humidity
        self.clickable(self.set_air_temp).connect(lambda: self.input_value(self.set_air_temp))                  # set_air_temp 
        self.clickable(self.pre_heat_on_time).connect(lambda: self.input_value(self.pre_heat_on_time))          # pre_heat_on_time
        self.clickable(self.heat_on_time).connect(lambda: self.input_value(self.heat_on_time))                  # heat_on_time
        # TODO: connect all lcdNums

        self.config_dict = {
            self.pre_heat_road_temp:['pre_heat_road_temp', pre_heat_road_temp], 
            self.heat_road_temp:    ['heat_road_temp',     heat_road_temp],
            self.set_road_humidity: ['set_road_humidity',  set_road_humidity],
            self.set_air_temp:      ['set_air_temp',       set_air_temp],
            self.pre_heat_on_time:  ['pre_heat_on_time',   pre_heat_on_time],
            self.heat_on_time:      ['heat_on_time',       heat_on_time]       
        }

        self.config_dict_new = {
            'pre_heat_road_temp': pre_heat_road_temp, 
            'heat_road_temp':     heat_road_temp,
            'set_road_humidity':  set_road_humidity,
            'set_air_temp':       set_air_temp,
            'pre_heat_on_time':   pre_heat_on_time,
            'heat_on_time':       heat_on_time       
        }

        self.lineEdit.setVisible(False)

        '''
        # virtual keyboard & input lineEdit setting
        self.lineEdit.returnPressed.connect(self.LineEdit_RET)

        self.process = QProcess(self)
        self.pid = None
        # self.pid = subprocess.Popen(['florence'])
        os.system('florence hide')
        '''


    def LineEdit_RET(self, input_num):
        # 1. Display in lcdNumber
        self.temp_lcdNumber.display(input_num)

        # 2. update Global Config Variable
        # variable_name = self.config_dict[self.temp_lcdNumber][0]
        # self.config_dict[self.temp_lcdNumber][1] = input_num
        variable_name = self.temp_lcdNumber.objectName()
        self.config_dict_new[variable_name] = input_num

        # 3. send mqtt msg
        self.sub_mqtt.send_msg(pub_root_topic+"CONFIG", json.dumps({variable_name: input_num}))

        # 4. update DB

        # 5. save config 

        # print(self.config_dict[self.temp_lcdNumber][0])

        # TODO: send config datas to PC & DB
        # or if recevied config data from PC, update local & DB config data


        # self.temp_lcdNumber.display(self.lineEdit.text())
        # self.lineEdit.setVisible(False)
        # self.lineEdit.setText("")


        # os.system('florence hide')

        # self.process.terminate()
        # self.process.start("kill -9 " + str(self.pid))

        # self.pid.kill()
        # os.killpg(self.pid.pid, signal.SIGKILL)


    def input_value(self, lcdNum):
        # print(lcdNum.objectName())
        # print('test::: ', self.findChild(QLCDNumber, lcdNum.objectName()).objectName())
        self.temp_lcdNumber = lcdNum
        self.keypad_timer.start(KEYPAD_TIME)
        self.ex.show()

        return

        # self.lineEdit.setVisible(True)
        # self.lineEdit.setFocus()
        pl = list()
        for process in psutil.process_iter():
            pl.append(process.name())

        if 'florence' in pl:
            os.system('florence show')

        """
        # proc = os.system('ps -a')
        proc = subprocess.check_output(['ps', '-a'])
        print(proc)
        b = proc.splitlines()
        print(b)
        flag = 0
        for item in b:
            print(item)
            if 'florence' in str(item):
                print('-----------------------------', str(item))
                os.system('florence show')
                flag = 1
                break
        
        if flag == 0:
            os.system('florence')
            
        """
                
        # ret, pid = QProcess.startDetached('florence')
        # ret = QProcess.startDetached('florence')
        # ret = self.process.startDetached("florence")
        # self.process = QProcess()

        # ret = self.process.start('florence')
        # self.pid = self.process.pid()

        # self.pid = subprocess.Popen(['florence'])

        # print('333333333333333333333', pid)
        # self.flag = 0
        # pid.kill()


    @QtCore.pyqtSlot(str, str)
    def on_message_callback(self, msg, topic):
        jsonData = json.loads(msg) 
        if topic == sub_root_topic + 'CMD':
            print("CMD: ", "CH1: ", str(jsonData['CH1']))
            print("CMD: ", "CH2: ", str(jsonData['CH2']))
            if jsonData['CH1'] == True and jsonData['CH2'] == False:
                print("CH1: ON, CH2: OFF")
                # self.label_7.setStyleSheet("background-color: green")
                # self.label_timer1.start(HEATING_TIME)
                self.send_STATUS(self.pushButton)
                # TODO: update DB for heating status
            elif jsonData['CH1'] == True and jsonData['CH2'] == True:
                print("CH1: ON, Ch2: ON")
                # self.label_8.setStyleSheet("background-color: green")
                # self.label_timer2.start(HEATING_TIME)
                self.send_STATUS(self.pushButton_2)
                # TODO: update DB for heating status

        elif topic == sub_root_topic+'CONFIG':
            for key, value in jsonData.items():
                # lcd = [k for k, v in self.config_dict.items() if v[0] == key]
                # self.temp_lcdNumber = lcd[0]
                lcdNum = self.findChild(QLCDNumber, key)
                self.temp_lcdNumber = lcdNum
                self.LineEdit_RET(value)

            # for key, value in jsonData.items():
            #     print('*****************************************************')
            #     print(key, value)
            #     lcd = [k for k, v in self.config_dict.items() if v[0] == key]
            #     lcd[0].display(value)


    def label_color_change(self, inLabel):
        if inLabel == self.label_7:
            self.label_timer1.stop()
            self.pushButton.setStyleSheet("background-color: gray; border: 1px solid black")
        else:
            self.label_timer2.stop()
            self.pushButton_2.setStyleSheet("background-color: gray; border: 1px solid black")

        inLabel.setStyleSheet("background-color: gray")
        # TODO: update DB for heating status -> OFF
        self.sub_mqtt.send_msg(pub_root_topic+"STATUS", json.dumps({'CH1': False, 'CH2': False}))

    def send_msg_loop_timer(self):
        sine_value = np.sin(self.sine_x_data[self.idx%self.x_size])
        # temp_data['_id'] = idx
        self.temp_data['road_temp'] = sine_value
        self.temp_data['road_humidity'] = sine_value * 5 
        self.temp_data['air_temp'] = sine_value * 10 
        self.temp_data['timestamp'] = datetime.now()
        self.temp_data['metadata'] = {"sensorId": self.idx, "type": "sensor data"}

        result = collection.insert_one(self.temp_data)

        if DEBUG_PRINT:
            print("inserted data", self.temp_data['timestamp'])

        del self.temp_data['_id']
        # del temp_data['timestamp']
        self.temp_data['timestamp'] = str(self.temp_data['timestamp'])
        # pub_mqtt.send_msg(root_topic+"DATA", json.dumps(temp_data))
        self.sub_mqtt.send_msg(pub_root_topic+"DATA", json.dumps(self.temp_data))

        self.idx += 1

    # sned STATUS by mqtt
    def send_STATUS(self, button):
        button.setStyleSheet("background-color: green; border: 1px solid black")
        if button == self.pushButton:
            print('send CH1 on')
            self.sub_mqtt.send_msg(pub_root_topic+"STATUS", json.dumps({'CH1': True, 'CH2': False}))
            self.label_7.setStyleSheet("background-color: green")
            self.label_timer1.start(HEATING_TIME)
        elif button == self.pushButton_2:
            print('send CH1 & CH2 on')
            self.sub_mqtt.send_msg(pub_root_topic+"STATUS", json.dumps({'CH1': True, 'CH2': True}))
            self.label_8.setStyleSheet("background-color: green")
            self.label_timer2.start(HEATING_TIME)

    def loop_start_func(self):
        self.sub_mqtt.messageSignal.connect(self.on_message_callback)
        self.sub_mqtt.loop_start_func()

    @QtCore.pyqtSlot(str, str)
    def on_message_1(self, msg, topic):
        if topic == sub_root_topic + 'DATA':
            jsonData = json.loads(msg) 
            roadTemp = jsonData['road_temp']
            roadHumidity = jsonData['road_humidity']
            airTemp = jsonData['air_temp']

        # if message.topic == root_topic + 'CMD':
        #     print("CMD: ", str(jsonData['CH1']))

    def clickable(self, widget):
        class Filter(QObject):
            clicked = pyqtSignal()  # pyside2 사용자는 pyqtSignal() -> Signal()로 변경

            def eventFilter(self, obj, event):

                if obj == widget:
                    if event.type() == QEvent.MouseButtonRelease:
                        if obj.rect().contains(event.pos()):
                            self.clicked.emit()
                            # The developer can opt for .emit(obj) to get the object within the slot.
                            return True
                return False
        filter = Filter(widget)
        widget.installEventFilter(filter)
        return filter.clicked

    def save_var(self, key, value):
        with shelve.open('config.db') as f:
            f[key] = value

    def stParam(self, lcdNum):
        with shelve.open('config.db') as f:
            if lcdNum == self.lcdNum_line_num:
                f['LINE_NUM'] = self.lcdNum_line_num.value()

    def to_excel_func(self, _time, data):
        tt = [_time, data]
        self.resist_data.append(tt)
        print(tt)


    def graph_plot(self):
        update_data_road_temp = []
        update_data_road_humidity = []
        update_data_air_temp = []

        update_results = collection.find({"timestamp": {"$gt":self.query_time}}, limit=NUM_UPDATE_X_AXIS)
        for result in update_results:
            update_data_road_temp.append(result.get("road_temp"))
            update_data_road_humidity.append(result.get("road_humidity"))
            update_data_air_temp.append(result.get("air_temp"))
            self.query_time = result.get("timestamp")


def run():
    app = QApplication(sys.argv)
    widget = qt()
    widget.show()

    widget.loop_start_func()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # conn = pymongo.MongoClient('203.251.78.135', 27017)

    conn = pymongo.MongoClient('mongodb://' + server_ip,
                        username = userid,
                        password =  passwd,
                        authSource = 'road_1')

    db = conn.get_database('road_1')
    collection = db.get_collection('device_1')

    #results = collection.find()  # find()에 인자가 없으면 해당 컬렉션의 전체 데이터 조회. return type = cursor
    #for result in results:
    #    print(result)

    run()
