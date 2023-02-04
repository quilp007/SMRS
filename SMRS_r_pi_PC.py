#!/usr/bin/env python
# coding=utf8

# auto excution in booting time
# sudo vi .config/lxsession/LXDE-pi/autostart 

import os, sys, time, datetime, warnings, signal
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSignal, pyqtSlot, Qt, QEvent
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget
from PyQt5.QtWidgets import QPushButton, QGridLayout, QLCDNumber
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtTest, QtGui, QtCore
from PyQt5.QtGui import QPixmap

import cv2

import numpy as np
import shelve
from datetime import datetime
# import pandas as pd

import time
import pymongo

import mqtt.sub_class as sc
import json
import serial
import base64
import argparse
import platform

ARG_TEST = True 
TEST = False
CERTI = True

if ARG_TEST:
    parser = argparse.ArgumentParser(description='SMRS raspberry pi for PC')
    parser.add_argument('-id', '--arg1', help='arg for mqtt id/publisher topic')
    args = parser.parse_args()
    if args.arg1 != None:
        print('arg1=', args.arg1)
        DEVICE_ID = args.arg1
    else:
        print('arg is None!! please input arg!!')
        exit(1)

USB_SERIAL = False
MQTT_ENABLE = True

# serial_port = "/dev/ttyACM0"
serial_port = "/dev/ttyUSB0"

if USB_SERIAL == True:
    mcuSerial = serial.Serial(serial_port, 115200)

server_ip = '203.251.78.135'

userid = 'smrs_1'
passwd = 'smrs2580_1!'

mongo_port = 27017
mqtt_port = 1883

if ARG_TEST:
    MQTT_CLIENT_ID = 'client_' + DEVICE_ID
    pub_root_topic = "PUB_" + DEVICE_ID + "/"
    sub_root_topic = "SUB_" + DEVICE_ID + "/"

    print(pub_root_topic)
    print(sub_root_topic)
else:
    if TEST == False:
        MQTT_CLIENT_ID = 'client_r_pi1'
        pub_root_topic = "R_PI111/"
        sub_root_topic = "APP111/"
    else:
        MQTT_CLIENT_ID = 'client_r_pi_test'
        pub_root_topic = "R_PI_test/"
        sub_root_topic = "APP_test/"

# TTA version is TEST = True, MQTT ID no is 1

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

SEND_SENSOR_DATA_INTERVAL   = 1000 # ms -> timer setting

PRE_HEATING_TIME            = 3000 # ms -> timer setting
HEATING_TIME                = 5000 # ms -> timer setting

LABEL_WARNING_TIME          = 3000 # ms -> timer setting

CHECK_TEMP_INTERVAL_TIME    = 1000 # ms -> timer setting

KEYPAD_TIME = 5000

sensor_data_dict = {
    'road_temp':        0, 
    'road_humidity':    0,
    'air_temp':         0
}


def resource_path(*relative_Path_AND_File):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(
            sys,
            '_MEIPASS',
            os.path.dirname(os.path.abspath(__file__))
        )
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, *relative_Path_AND_File)


if CERTI == True and platform.system() == 'Windows':
    form_class = uic.loadUiType(resource_path("C:\work\SMRS\SMRS_r_pi.ui"))[0]
else:
    form_class = uic.loadUiType('SMRS_r_pi.ui')[0]


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.__suspend = True 

    def run(self):
        print('thread running')
        # capture from web cam
        self.cap = cv2.VideoCapture(0)
        while self._run_flag:
            while self.__suspend:
                time.sleep(0.5)

            ret, cv_img = self.cap.read()
            if ret:
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        self.cap.release()

    def stop(self):
        print('thread stoped')
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()

    def mySuspend(self):
        self.__suspend = True

    def myResume(self):
        self.__suspend = False
        self._run_flag = True

# --------------------------------------------------------------
# [THREAD] 
# --------------------------------------------------------------
class THREAD_RECEIVE_Data(QThread):
    intReady = pyqtSignal()
    # to_excel = pyqtSignal(str, float)

    @pyqtSlot()
    def __init__(self, qt_object, mqtt_object):
        super(THREAD_RECEIVE_Data, self).__init__()
        self.time_format = '%Y%m%d_%H%M%S'

        self.__suspend = False
        self.__exit = False
        self.log_flag = False
        self.qt_object = qt_object 
        self.mqtt_object = mqtt_object 


    def run(self):
        while True:
            ### Suspend ###
            while self.__suspend:
                time.sleep(0.5)

            _time = datetime.now()
            _time = _time.strftime(self.time_format)

            # TEST CODE - send data
            # self.intReady.emit() # call send_msg_loop_timer()
            # time.sleep(1)

            try: 
                line = mcuSerial.readline()
                print(line)
            except:
                print('MCU uart readline error!!!')
                pass
            else:
                try:
                    data = json.loads(line)
                except:
                    print('json error!!')
                    pass
                else:
                    # sensor_data_dict = data
                    # for key, value in data.items():

                    # self.intReady.emit()

                    for key, value in data.items():
                        lcdNum = self.qt_object.findChild(QLCDNumber, key)    # find LCDNumber with key 
                        if lcdNum is not None:
                            print('lcd is not empty!!')
                            lcdNum.display(value)                        # display to LCDNumber

                        print('received key: {} value: {}'.format(key, value))
                        print('value type: ', type(value))
            
                        # send to PC or S/P
                        self.mqtt_object.send_msg(pub_root_topic+"CONFIG", json.dumps({key: value}))

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


class Util_Function:
    def Qsleep(self, ms):
        QtTest.QTest.qWait(ms)

    def save_var(self, key, value):
        with shelve.open('C:\work\SMRS\config') as f:
            f[key] = int(value)

    def read_var(self, key):
        with shelve.open('C:\work\SMRS\config') as f:
            try:
                temp = int(f[key])
                # print(f[key])
                return temp
            except:
                pass


    def to_excel_func(self, _time, data):
        tt = [_time, data]
        self.resist_data.append(tt)
        print(tt)


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

        names = ['Cls',    '',   'Close',
                 '7',     '8',  '9',
                 '4',     '5',  '6',
                 '1',     '2',  '3',
                 '-',     '0',  '.',
                 '',      '',   'OK']

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

            self.endFlag = 0
            self.close()

            if self.text == '':
                return

            self.num = self.text
            self.text = ''
            self.lcd.display(self.text)
            self.cb_signal.emit(self.num)
            self.num = ''
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

        self.btn_HEAT_ON.clicked.connect(self.func_btn_HEAT_ON)
        self.btn_HEAT_ON_AND_STOP.clicked.connect(self.func_btn_HEAT_ON_AND_STOP)
        
        self.btn_PRE_HEAT_ON.clicked.connect(self.func_btn_PRE_HEAT_ON)
        self.btn_PRE_HEAT_ON_AND_STOP.clicked.connect(self.func_btn_PRE_HEAT_ON_AND_STOP)
        
        self.btn_AUTO_MODE.clicked.connect(self.func_btn_AUTO_MODE)
        self.btn_HEAT_STOP.clicked.connect(self.func_btn_HEAT_STOP)

        self.btn_INIT_MODE.clicked.connect(self.func_btn_INIT_MODE)

        # qeury(read) from start date (time) to end date (time)
        # TODO: need to modify "query_time" as a user input

        # Keypad timer setting ##############################
        self.keypad_timer = QtCore.QTimer()
        self.keypad_timer.timeout.connect(lambda: self.ex.close_func(self.keypad_timer))
        
        ##################################################
        self.ex = KEY_PAD_UI(self.keypad_timer)
        self.ex.cb_signal.connect(self.LineEdit_RET)

        self.util_func = Util_Function()

        # self.query_time = datetime.now()
        self.query_time = datetime(2022, 6, 15, 18, 22, 37)
        results = collection.find({"timestamp": {"$gt": self.query_time}}, limit=NUM_X_AXIS)

        # table Widget ------------------------------------------------------------------
        # self.tableWidget.setRowCount(ROW_COUNT)
        # self.tableWidget.setColumnCount(COL_COUNT)  # MEAN, parallel resistance

        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.x_size = 720
        self.sine_x_data = np.linspace(-np.pi, np.pi, self.x_size)
        self.idx = 0
        self.temp_data = {}

        # loop for sending sensor data ###################
        # self.timer = QtCore.QTimer()
        # self.timer.setInterval(SEND_SENSOR_DATA_INTERVAL) # 100ms 
        # self.timer.timeout.connect(self.send_msg_loop_timer)

        # self.timer.start()

        # HEAT TIMER setting ##############################
        self.heat_timer = QtCore.QTimer()
        self.pre_heat_timer = QtCore.QTimer()
        self.pre_heat_timer.timeout.connect(lambda: self.heat_timeout_func(self.label_pre_heat_on))
        self.heat_timer.timeout.connect(lambda: self.heat_timeout_func(self.label_heat_on))

        self.heating_timer = QtCore.QTimer()
        self.heating_timer.timeout.connect(lambda: self.heat_timeout_func(None))

        # Warning label TIMER setting ##############################
        self.label_warning_timer = QtCore.QTimer()
        self.label_warning_timer.timeout.connect(self.label_warning_timeout_func)

        # Check Temp and ON/OFF HEAT TIMER setting ##############################
        self.check_temp_timer = QtCore.QTimer()
        self.check_temp_timer.timeout.connect(self.check_temp)

        # MQTT init ###############################################
        self.sub_mqtt = sc.SUB_MQTT(_broker_address = server_ip, _topic = sub_root_topic+'+',\
                                     _client=MQTT_CLIENT_ID, _mqtt_debug = DEBUG_PRINT)
        
        # self.sub_mqtt.client1.username_pw_set(username="steve",password="password")

        # serial receive THREAD ##############################
        self.thread_rcv_data = THREAD_RECEIVE_Data(self, self.sub_mqtt)
        # self.thread_rcv_data.to_excel.connect(self.to_excel_func)
        self.thread_rcv_data.intReady.connect(self.send_msg_loop_timer)

        if USB_SERIAL == True:
            self.thread_rcv_data.start()

        self.resist_data = []
        self.log_flag = False

        self.label_pre_heat_on.setStyleSheet("background-color: gray")
        self.label_heat_on.setStyleSheet("background-color: gray")
        self.label_emc_heat_on.setStyleSheet("background-color: gray")

        self.temp_lcdNumber = None

        self.clickable(self.pre_heat_road_temp).connect(lambda: self.input_value(self.pre_heat_road_temp))      # pre_heat_road_temp
        self.clickable(self.heat_road_temp).connect(lambda: self.input_value(self.heat_road_temp))              # heat_road_temp
        self.clickable(self.set_road_humidity).connect(lambda: self.input_value(self.set_road_humidity))        # set_road_humidity
        self.clickable(self.set_air_temp).connect(lambda: self.input_value(self.set_air_temp))                  # set_air_temp 
        self.clickable(self.pre_heat_on_time).connect(lambda: self.input_value(self.pre_heat_on_time))          # pre_heat_on_time
        self.clickable(self.heat_on_time).connect(lambda: self.input_value(self.heat_on_time))                  # heat_on_time
        
        self.clickable(self.road_temp).connect(lambda: self.input_value(self.road_temp))
        self.clickable(self.road_humidity).connect(lambda: self.input_value(self.road_humidity))
        self.clickable(self.air_temp).connect(lambda: self.input_value(self.air_temp))


        # TODO: connect all lcdNums

        self.config_dict = {
            'pre_heat_road_temp':   3,
            'heat_road_temp':       1,
            'set_road_humidity':    3,
            'set_air_temp':         -15,
            'pre_heat_on_time':     60,
            'heat_on_time':         90,
            'road_temp':            0,
            'road_humidity':        0,
            'air_temp':             0
        }

        self.btn_list = [
            self.btn_HEAT_ON,
            self.btn_HEAT_ON_AND_STOP,
            self.btn_PRE_HEAT_ON,
            self.btn_PRE_HEAT_ON_AND_STOP
        ]

        self.label_list = [
            self.label_pre_heat_on,
            self.label_heat_on,
            self.label_emc_heat_on
        ]

        self.HEATING_TIME = 0
        self.PRE_HEATING_TIME = 0

        if not os.path.isfile('config.dat'):
            for key, value in self.config_dict.items():
                self.util_func.save_var(key, value)

        # laod saved config data and display to QLCDNumber
        for key, value in self.config_dict.items():     # saved (LCDNumber name, value) in config.db
            temp = self.util_func.read_var(key)         # read config data from local db file
            lcdNum = self.findChild(QLCDNumber, key)    # find LCDNumber with key 
            lcdNum.display(temp)                        # display to LCDNumber
            self.config_dict[key] = temp                # set the data to config_dict

            lcdNum = self.findChild(QLCDNumber, key+'_2')    # find LCDNumber with key 
            if (lcdNum is not None):
                lcdNum.display(temp)                        # display to LCDNumber

            print('key: {0}, value: {1}'.format(key, temp))

            if key == 'heat_on_time' and temp != None:
                self.HEATING_TIME = int(temp)*60*1000
            elif key == 'pre_heat_on_time' and temp!= None:
                self.PRE_HEATING_TIME = int(temp)*60*1000

        print('=========================================================================')
        print('self.HEATING_TIME: ', self.HEATING_TIME, 'type: ', type(self.HEATING_TIME))

        # limit line to 150 (log textEdit)
        self.textEdit_log.document().setMaximumBlockCount(150)

        self.label_warning.setVisible(False)
        # self.lineEdit.setVisible(False)

        # GLOBAL VARIABLE --------------------------------------------------
        # BLOCK change config during HEAT ON time
        self.flag_HEAT_ON = False
        self.flag_AUTO_MODE = False

        self.PRE_HEAT_STATUS = False
        self.HEAT_STATUS = False

        self.flag_EMC_HEAT_ON = False

        # CAM preview/caputre THREAD ##############################
        self.disply_width = 360
        self.display_height = 240

        # create the video capture thread
        self.V_thread = VideoThread()
        # connect its signal to the update_image slot
        self.V_thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.V_thread.start()
        self.V_thread.stop()

        self.btn_capture.clicked.connect(self.func_btn_capture)
        self.rb_preview.clicked.connect(self._preview)

        self.check_temp_timer.start(CHECK_TEMP_INTERVAL_TIME)

        self.current_STATUS()


    def check_temp(self):
        # flag_HEAT_ON <= True: 1. pre heat on 2. heat on 3. emergency heat on
        # flag_AUTO_MODE <= True: 1. set auto mode 2. auto mode after pre/heat on
        # flag_AUTO_MODE <= False: 1. Stop 2. stop after pre/heat on

        # if self.flag_HEAT_ON == True or self.flag_AUTO_MODE == False:
        if self.flag_AUTO_MODE == False:
            return

        if self.config_dict['air_temp'] <= self.config_dict['set_air_temp']:
            self.flag_EMC_HEAT_ON = True
            self.func_btn_HEAT_ON('EMC')

        elif (self.config_dict['road_temp'] <= self.config_dict['heat_road_temp']) and \
            (self.config_dict['road_humidity'] >= self.config_dict['set_road_humidity']):
            self.func_btn_HEAT_ON('AUTO')

        elif self.config_dict['road_temp'] <= self.config_dict['pre_heat_road_temp']:
            self.func_btn_PRE_HEAT_ON('AUTO')


    def _preview(self):
        if self.rb_preview.isChecked():
            self.V_thread.myResume()
            self.V_thread.start()

            self.label_cam.show()

            # changing text of label
            self.textEdit.setText("preview on")
  
        # if it is not checked
        else:
            self.V_thread.mySuspend()
            self.V_thread.stop()

            # img = np.zeros((270, 360, 3), np.uint8)
            # self.update_image(img, 360, 270)

            self.label_cam.hide()

            # self.label_cam.setStyleSheet("background-color: gray; border: 1px solid black")
            # self.label_cam.setStyleSheet("background-color: gray")
              
            # changing text of label
            self.textEdit.setText("preview off")

    def func_btn_INIT_MODE(self):
        self.config_dict['pre_heat_road_temp']  = 5
        self.config_dict['pre_heat_on_time']    = 1 
        self.config_dict['heat_road_temp']      = 1
        self.config_dict['set_road_humidity']   = 3
        self.config_dict['heat_on_time']        = 2
        self.config_dict['set_air_temp']        = -20

        self.HEATING_TIME = 0
        self.PRE_HEATING_TIME = 0

        # laod saved config data and display to QLCDNumber
        for key, value in self.config_dict.items():     # saved (LCDNumber name, value) in config.db
            print('key: {0}, value: {1}'.format(key, value))
            lcdNum = self.findChild(QLCDNumber, key)    # find LCDNumber with key
            if (lcdNum is not None):
                lcdNum.display(value)                        # display to LCDNumber

            lcdNum = self.findChild(QLCDNumber, key+'_2')    # find LCDNumber with key
            if (lcdNum is not None):
                lcdNum.display(value)                        # display to LCDNumber

            if key == 'heat_on_time' and value:
                self.HEATING_TIME = int(value)*20*60*1000   # 1 time -> 20min
            elif key == 'pre_heat_on_time' and value:
                self.PRE_HEATING_TIME = int(value)*20*60*1000

        print('=========================================================================')
        print('self.HEATING_TIME: ', self.HEATING_TIME, 'type: ', type(self.HEATING_TIME))


    def func_btn_capture(self):
        new_cap = False
        ret, img = self.V_thread.cap.read()

        if ret == False:
            new_cap = True
            cap = cv2.VideoCapture(0)
            ret, img = cap.read()

        filename = './video/' + time.strftime('%y%m%d_%H%M%S', time.localtime(time.time())) + '.jpg'
        try:
            cv2.imwrite(filename, img)
        except:
            print('save image error!!')
            print('(image is not saved!!)')
            return

        self.textEdit.append('captured ' + filename)
        
        qt_img = self.convert_cv_qt(img, 480, 360)
        self.label_cam_2.setPixmap(qt_img)

        if new_cap == True:
            cap.release()

        # to encode for JSON
        str_img = base64.b64encode(cv2.imencode('.jpg', img)[1]).decode()
        self.sub_mqtt.send_msg(pub_root_topic+"IMAGE", json.dumps({'filename': filename, 'IMG': str_img}))


    def closeEvent(self, event):
        self.V_thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img, _width = 360, _height = 270):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img, _width, _height)
        self.label_cam.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img, _width = 360, _height = 270):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        p = convert_to_Qt_format.scaled(_width, _height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    # Keypad 'OK' pressed event -> emit signal in keypad
    def LineEdit_RET(self, input_num):
        # 1. Display in lcdNumber
        try:
            input_num = int(input_num)

        except:
            print('input is not number!!')
            return

        input_num = int(input_num)
        print(type(input_num))

        if self.temp_lcdNumber == self.pre_heat_road_temp or self.temp_lcdNumber == self.heat_road_temp or self.temp_lcdNumber == self.set_air_temp:
            if input_num > 60 or input_num < -30:
                return
        elif self.temp_lcdNumber == self.set_road_humidity:
            if input_num > 9 or input_num < 0:
                return
        elif self.temp_lcdNumber == self.pre_heat_on_time or self.temp_lcdNumber == self.heat_on_time:
            if input_num > 120 or input_num < 1:
                return

        self.temp_lcdNumber.display(input_num)

        lcdNum = self.findChild(QLCDNumber, self.temp_lcdNumber.objectName()+'_2')    # find LCDNumber with key 
        if (lcdNum is not None):
            lcdNum.display(input_num)

        # 2. update Global Config Variable
        variable_name = self.temp_lcdNumber.objectName()
        self.config_dict[variable_name] = input_num

        # 3. send mqtt msg
        self.sub_mqtt.send_msg(pub_root_topic+"CONFIG", json.dumps({variable_name: input_num}))

        # 4. update DB

        # 5. save config to local file 
        self.util_func.save_var(variable_name, input_num)
        print(self.util_func.read_var(variable_name))

        # TODO: send config datas to PC & DB
        # or if recevied config data from PC, update local & DB config data

        if self.temp_lcdNumber.objectName() == 'heat_on_time':
            self.HEATING_TIME = int(input_num) * 60*1000
        elif self.temp_lcdNumber.objectName() == 'pre_heat_on_time':
            self.PRE_HEATING_TIME = int(input_num) * 60*1000


    # QLCDNumber input
    def input_value(self, lcdNum):
        # if self.flag_HEAT_ON == True:
        print(lcdNum.objectName())
        print(sensor_data_dict.keys())

        print((lcdNum.objectName() in sensor_data_dict.keys()))
        # print(sensor_data_dict[lcdNum.objectName()])
        # print(sensor_data_dict.values())

        if (not(lcdNum.objectName() in sensor_data_dict.keys())) and self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        # print(lcdNum.objectName())
        # print('test::: ', self.findChild(QLCDNumber, lcdNum.objectName()).objectName())
        self.temp_lcdNumber = lcdNum
        self.keypad_timer.start(KEYPAD_TIME)
        self.ex.show()


    # MQTT received msg callback function
    # @QtCore.pyqtSlot(str, str)
    def on_message_callback(self, msg, topic):
        jsonData = json.loads(msg) 

        if topic == sub_root_topic + 'INIT':
            if jsonData['REQUEST'] == 'INIT':
                print('received: ', 'INIT')
                self.current_STATUS()
                return

        elif topic == sub_root_topic + 'CMD':

            print("CMD: ", "CH1: ", str(jsonData['CH1']))
            print("CMD: ", "CH2: ", str(jsonData['CH2']))
            if jsonData['CH1'] == True and jsonData['CH2'] == False:
                print("pressed pre-heat-on")
                self.func_btn_PRE_HEAT_ON()
                # TODO: update DB for heating status
            elif jsonData['CH1'] == False and jsonData['CH2'] == True:
                print("pressed heat-on")
                self.func_btn_HEAT_ON()
                # TODO: update DB for heating status

        elif topic == sub_root_topic + 'BUTTON':
            func_btn_xxx = getattr(self, 'func_' + jsonData['btn'])
            func_btn_xxx()

        elif topic == sub_root_topic+'CONFIG':
            for key, value in jsonData.items():
                lcdNum = self.findChild(QLCDNumber, key)
                self.temp_lcdNumber = lcdNum
                self.LineEdit_RET(value)

        elif topic == sub_root_topic+'CAPTURE':
            self.func_btn_capture()

        elif topic == sub_root_topic+'INIT_SETTING':
            self.func_btn_INIT_MODE()

    def heat_timeout_func(self, inLabel):
        if inLabel == self.btn_HEAT_STOP:
            self.flag_AUTO_MODE = False
            self.btn_AUTO_MODE.setStyleSheet("background-color: gray; border: 1px solid black")

            # send mqtt msg to chagne color
            self.send_mqtt_msg('BUTTON', self.btn_AUTO_MODE.objectName(), 'gray')

        self.heating_timer.stop()

        self.flag_HEAT_ON = False
        self.flag_EMC_HEAT_ON = False

        self.PRE_HEAT_STATUS = False
        self.HEAT_STATUS = False

        # change color of all buttons to gray
        for obj in self.btn_list:
            obj.setStyleSheet("background-color: {}; border: 1px solid black".format('gray'))

        # change color of all label to gray
        for obj in self.label_list:
            obj.setStyleSheet("background-color: {}; border: 1px solid black".format('gray'))

        self.label_warning_timer.stop()
        self.label_warning.setVisible(False)

        if USB_SERIAL == True:
            mcuSerial.write(b'2')

        # send mqtt msg to chagne color
        for obj in self.btn_list:
            self.send_mqtt_msg('BUTTON', obj.objectName(), 'gray')

        for obj in self.label_list:
            self.send_mqtt_msg('LABEL', obj.objectName(), 'gray')


    def label_warning_timeout_func(self):
        self.label_warning.setVisible(False)

    # TEST FUNCTION for mongoDB to send msg periodically
    # TODO: move to UART RECEIVE THREAD
    def send_msg_loop_timer(self):

        # for key, value in sensor_data_dict.items():
        #     print('received key: {} value: {}'.format(key, value))
        #     print('value type: ', type(value))

            # lcdNum = self.findChild(QLCDNumber, key)    # find LCDNumber with key 
            # if lcdNum is not None:
            #     lcdNum.display(value)                        # display to LCDNumber

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


    def insert_log(self, txt):
        time_text = time.strftime('%y.%m.%d_%H:%M:%S', time.localtime(time.time()))
        log_text = time_text + '   ' + txt
        self.textEdit_log.append(log_text)

    # change color of remote button/label
    def send_mqtt_msg(self, obj_type, obj_name, color):
        if not MQTT_ENABLE:
            print('MQTT is disabled!!!')
            return

        if obj_type == 'BUTTON':
            self.sub_mqtt.send_msg(pub_root_topic+"BUTTON", json.dumps({'btn': [obj_name, color]}))
        elif obj_type == 'LABEL':
            self.sub_mqtt.send_msg(pub_root_topic+"LABEL", json.dumps({'label': [obj_name, color]}))


    def func_btn_AUTO_MODE(self):
        self.flag_AUTO_MODE = True
        self.btn_AUTO_MODE.setStyleSheet(f"background-color: blue; border: 1px solid black")

        self.send_mqtt_msg('BUTTON', self.btn_AUTO_MODE.objectName(), 'blue')
        self.insert_log('AUTO_MODE')

    def func_btn_HEAT_STOP(self):
        self.heat_timeout_func(self.btn_HEAT_STOP)
        self.insert_log('HEAT_STOP')

    def func_btn_PRE_HEAT_ON(self, mode = None):
        if self.flag_HEAT_ON:
            return

        self.label_pre_heat_on.setStyleSheet("background-color: yellow")
        self.label_emc_heat_on.setStyleSheet("background-color: gray")

        if mode != 'AUTO':
            self.btn_PRE_HEAT_ON.setStyleSheet("background-color: yellow; border: 1px solid black")

        self.flag_AUTO_MODE = True
        self.btn_AUTO_MODE.setStyleSheet("background-color: blue; border: 1px solid black")

        self.heating_timer.start(PRE_HEATING_TIME)

        self.flag_HEAT_ON = True
        self.PRE_HEAT_STATUS = True
        self.HEAT_STATUS = False

        if USB_SERIAL == True:
            mcuSerial.write(b'1')

        # send mqtt msg to chagne color
        self.send_mqtt_msg('BUTTON', self.btn_AUTO_MODE.objectName(),       'blue')
        if mode != 'AUTO':
            self.send_mqtt_msg('BUTTON', self.btn_PRE_HEAT_ON.objectName(),     'yellow')
        self.send_mqtt_msg('LABEL',  self.label_pre_heat_on.objectName(),   'yellow')
        self.send_mqtt_msg('LABEL',  self.label_emc_heat_on.objectName(),   'gray')

        self.insert_log('PRE_HEAT_ON')

    def func_btn_PRE_HEAT_ON_AND_STOP(self):
        if self.flag_HEAT_ON:
            return

        self.label_pre_heat_on.setStyleSheet("background-color: yellow")
        self.label_emc_heat_on.setStyleSheet("background-color: gray")

        self.flag_AUTO_MODE = False
        self.btn_AUTO_MODE.setStyleSheet("background-color: gray; border: 1px solid black")
        self.btn_PRE_HEAT_ON_AND_STOP.setStyleSheet("background-color: yellow; border: 1px solid black")

        self.heating_timer.start(PRE_HEATING_TIME)

        self.flag_HEAT_ON = True
        self.PRE_HEAT_STATUS = True
        self.HEAT_STATUS = False

        if USB_SERIAL == True:
            mcuSerial.write(b'1')

        # send mqtt msg to chagne color
        self.send_mqtt_msg('BUTTON', self.btn_AUTO_MODE.objectName(),               'gray')
        self.send_mqtt_msg('BUTTON', self.btn_PRE_HEAT_ON_AND_STOP.objectName(),    'yellow')
        self.send_mqtt_msg('LABEL',  self.label_pre_heat_on.objectName(),           'yellow')
        self.send_mqtt_msg('LABEL',  self.label_emc_heat_on.objectName(),           'gray')

        self.insert_log('PRE_HEAT_ON_AND_STOP')

    def func_btn_HEAT_ON(self, mode = False):
        if self.flag_HEAT_ON:
            return

        self.label_heat_on.setStyleSheet("background-color: pink")

        if mode == False:
            self.btn_HEAT_ON.setStyleSheet("background-color: pink; border: 1px solid black")

        self.flag_AUTO_MODE = True
        self.btn_AUTO_MODE.setStyleSheet("background-color: blue; border: 1px solid black")

        # if self.flag_EMC_HEAT_ON == True:
        if mode == 'EMC':
            self.label_emc_heat_on.setStyleSheet("background-color: red")

            # send mqtt msg to chagne color
            self.send_mqtt_msg('LABEL', self.label_emc_heat_on.objectName(), 'red')

        self.heating_timer.start(HEATING_TIME)

        self.flag_HEAT_ON = True
        self.PRE_HEAT_STATUS = False
        self.HEAT_STATUS = True

        if USB_SERIAL == True:
            mcuSerial.write(b'3')

        # send mqtt msg to chagne color
        self.send_mqtt_msg('BUTTON', self.btn_AUTO_MODE.objectName(),   'blue')
        if mode == False:
            self.send_mqtt_msg('BUTTON', self.btn_HEAT_ON.objectName(), 'pink')
        self.send_mqtt_msg('LABEL',  self.label_heat_on.objectName(),   'pink')

        self.insert_log('HEAT_ON')

    def func_btn_HEAT_ON_AND_STOP(self):
        if self.flag_HEAT_ON:
            return

        self.label_heat_on.setStyleSheet("background-color: pink")

        self.flag_AUTO_MODE = False
        self.btn_AUTO_MODE.setStyleSheet("background-color: gray; border: 1px solid black")
        self.btn_HEAT_ON_AND_STOP.setStyleSheet("background-color: pink; border: 1px solid black")

        # if self.flag_EMC_HEAT_ON == True:
        #     self.label_emc_heat_on.setStyleSheet("background-color: red")
        #     if MQTT_ENABLE:
        #         self.sub_mqtt.send_msg(pub_root_topic+"LABEL", json.dumps({'label': [self.label_emc_heat_on.objectName(), 'red']}))

        self.heating_timer.start(HEATING_TIME)

        self.flag_HEAT_ON = True
        self.PRE_HEAT_STATUS = False
        self.HEAT_STATUS = True

        if USB_SERIAL == True:
            mcuSerial.write(b'3')

        # send mqtt msg to chagne color
        self.send_mqtt_msg('BUTTON', self.btn_AUTO_MODE.objectName(),       'gray')
        self.send_mqtt_msg('BUTTON', self.btn_HEAT_ON_AND_STOP.objectName(),'pink')
        self.send_mqtt_msg('LABEL',  self.label_heat_on.objectName(),       'pink')

        self.insert_log('HEAT_ON_AND_STOP')

    def current_STATUS(self):
        print("request current STATUS")
        self.sub_mqtt.send_msg(pub_root_topic+"CONFIG", json.dumps(self.config_dict))

        obj = self.btn_AUTO_MODE
        self.send_mqtt_msg('BUTTON', obj.objectName(), obj.palette().window().color().name())

        # send mqtt msg to chagne color
        for obj in self.btn_list:
            self.send_mqtt_msg('BUTTON', obj.objectName(), obj.palette().window().color().name())

        for obj in self.label_list:
            self.send_mqtt_msg('LABEL', obj.objectName(), obj.palette().window().color().name())

    def loop_start_func(self):
        self.sub_mqtt.messageSignal.connect(self.on_message_callback)
        self.sub_mqtt.loop_start_func()

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
