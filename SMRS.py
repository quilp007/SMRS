#!/usr/bin/env python
# coding=utf8

import os, sys, time, datetime, warnings, signal
from PyQt5.QtCore import QSize, QRect, QObject, pyqtSignal, QThread, pyqtSignal, pyqtSlot, Qt, QEvent, QTimer
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, \
    QListView
from PyQt5.QtWidgets import QPushButton, QGridLayout, QLCDNumber
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtTest, QtGui, QtCore
from PyQt5.QtGui import QPixmap

import numpy as np
import shelve
from datetime import datetime
import pandas as pd
import pyqtgraph as pg

import time
import pymongo
import pprint

import mqtt.sub_class as sc
import json
import base64

import cv2

# ------------------------------------------------------------------------------
# config -----------------------------------------------------------------------
# ------------------------------------------------------------------------------

ENABLE_MONGODB = False
PASSWORD_2 = "1234"

# x_size = 360# graph's x size
x_size = 720# graph's x size
# NUM_X_AXIS = 300
NUM_X_AXIS = 720
NUM_UPDATE_X_AXIS = 5

ROW_COUNT = 7
COL_COUNT = 3

LABEL_WARNING_TIME          = 3000 # ms -> timer setting

server_ip = '203.251.78.135'

userid = 'smrs_1'
passwd = 'smrs2580_1!'

mongo_port = 27017
mqtt_port = 1883

pub_root_topic = "APP/"
sub_root_topic = "R_PI/"

pre_heat_road_temp = 0
heat_road_temp  = 0
set_road_humidity = 0
set_air_temp = 0
pre_heat_on_time = 0
heat_on_time = 0

DEBUG_PRINT = True

form_class = uic.loadUiType('SMRS.ui')[0]

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


class qt(QMainWindow, form_class):
    def __init__(self):
        # QMainWindow.__init__(self)
        # uic.loadUiType('qt_test2.ui', self)[0]

        super().__init__()

        self.setupUi(self)
        # self.setWindowFlags(Qt.FramelessWindowHint)


        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, False)
        self.tabWidget.setTabEnabled(4, False)
        self.Login_2.setFocus()

        self.btn_PRE_HEAT_ON.clicked.connect(lambda: self.send_CMD(self.btn_PRE_HEAT_ON))
        self.btn_HEAT_ON.clicked.connect(lambda: self.send_CMD(self.btn_HEAT_ON))
        self.btn_capture.clicked.connect(lambda: self.send_CMD(self.btn_capture))

        self.road_temp = []
        self.road_humidity = []
        self.air_temp = []

        # qeury(read) from start date (time) to end date (time)
        # TODO: need to modify "query_time" as a user input

        if ENABLE_MONGODB:
            self.query_time = datetime(2022, 6, 20, 00, 36, 43)
            results = collection.find({"timestamp": {"$gt": self.query_time}}, limit=NUM_X_AXIS)

            # self.query_time = datetime.now()
            # results = collection.find({}, {"_id": -1, limit = NUM_X_AXIS})

            for result in results:
                self.road_temp.append(result.get("road_temp"))
                self.road_humidity.append(result.get("road_humidity"))
                self.air_temp.append(result.get("air_temp"))
                self.query_time = result.get("timestamp")
                # print(result)
                # print(result.get("road_temp"))
                # print(self.query_time)

            # print("self.road_temp")
            # print(self.road_temp)
            # print("self.road_humidity")
            # print(self.road_humidity)
            # print("self.air_temp")
            # print(self.air_temp)


        self.data = np.linspace(-np.pi, np.pi, x_size)
        self.y2_1 = np.sin(self.data)
        # self.y2_1 = np.zeros(x_size)

        # self.road_temp = np.zeros(x_size)
        # self.road_humidity = np.zeros(x_size)
        # self.air_temp = np.zeros(x_size)

        self.lineEdit.returnPressed.connect(lambda: self.LineEdit_RET(self.lineEdit.text()))
        self.Login_2.returnPressed.connect(lambda: self.LineEdit_Login_2_RET(self.Login_2.text()))

        self.textEdit_log.setReadOnly(True)

        # table Widget ------------------------------------------------------------------
        """
        self.tableWidget.setRowCount(ROW_COUNT)
        self.tableWidget.setColumnCount(COL_COUNT)  # MEAN, parallel resistance

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        """

        """
        # Updating Plot
        self.plot = self.graphWidget.addPlot(title="Current Status")

        self.curve_road_temp = self.plot.plot(pen='g')
        self.curve_road_humidity = self.plot.plot(pen='r')
        self.curve_air_temp = self.plot.plot(pen='y')

        # self.plot.setGeometry(0, 0, x_size, 5)
        self.plot.setGeometry(0, 0, NUM_X_AXIS, 5)

        # self.plot.setYRange(self.plot_upper, self.plot_lower, padding=0)

        # self.drawLine(self.plot, self.error_lower, 'y')
        # self.drawLine(self.plot, self.error_upper, 'y')
        # self.drawLine(self.plot, self.error_limit_lower, 'r')
        # self.drawLine(self.plot, self.error_limit_upper, 'r')

        # self.graphWidget.nextRow()
        """

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000) # 100ms 
        self.timer.timeout.connect(self.graph_plot)

        # start loop for drawing graph #################
        # self.timer.start()
        ################################################
        
        # Warning label TIMER setting ##############################
        self.label_warning_timer = QtCore.QTimer()
        self.label_warning_timer.timeout.connect(self.label_warning_timeout_func)
        ##################################################

        self.thread_rcv_data = THREAD_RECEIVE_Data()
        self.thread_rcv_data.to_excel.connect(self.to_excel_func)
        # self.thread_rcv_data.start()

        self.resist_data = []
        self.log_flag = False

        ################################################
        # self.sub_mqtt = sc.SUB_MQTT(_topic = sub_root_topic + 'DATA')
        # self.sub_mqtt = sc.SUB_MQTT(_topic = sub_root_topic + '+', _mqtt_debug = False)
        # self.sub_mqtt = sc.SUB_MQTT(_broker_address = server_ip, _topic = sub_root_topic+'+', _client='client_pc', _mqtt_debug = DEBUG_PRINT)
        self.sub_mqtt = sc.SUB_MQTT(_broker_address = server_ip, _topic = sub_root_topic+'+', _client='client_pc_1', _mqtt_debug = DEBUG_PRINT)
        # time.sleep(3)
        # self.sub_mqtt.client1.username_pw_set(username="steve",password="password")
        ################################################

        self.clickable(self.pre_heat_road_temp).connect(lambda: self.input_value(self.pre_heat_road_temp))      # pre_heat_road_temp
        self.clickable(self.heat_road_temp).connect(lambda: self.input_value(self.heat_road_temp))              # heat_road_temp
        self.clickable(self.set_road_humidity).connect(lambda: self.input_value(self.set_road_humidity))        # set_road_humidity
        self.clickable(self.set_air_temp).connect(lambda: self.input_value(self.set_air_temp))                  # set_air_temp 
        self.clickable(self.pre_heat_on_time).connect(lambda: self.input_value(self.pre_heat_on_time))          # pre_heat_on_time
        self.clickable(self.heat_on_time).connect(lambda: self.input_value(self.heat_on_time))                  # heat_on_time

        self.label_warning.setVisible(False)
        # self.lineEdit.setValidator(QtGui.QIntValidator(-30, 60, self))
        self.lineEdit.setVisible(False)

        self.flag_HEAT_ON = False

    def label_warning_timeout_func(self):
        self.label_warning.setVisible(False)

    def LineEdit_RET(self, input_num):
        # 1. Display in lcdNumber => after receive mqtt msg
        # self.temp_lcdNumber.display(input_num)

        lcdNum = self.findChild(QLCDNumber, self.temp_lcdNumber.objectName()+'_2')    # find LCDNumber with key 
        if (lcdNum is not None):
            lcdNum.display(input_num)

        # 2. update Global Config Variable
        variable_name = self.temp_lcdNumber.objectName()

        # 3. send mqtt msg
        self.sub_mqtt.send_msg(pub_root_topic+"CONFIG", json.dumps({variable_name: input_num}))

        # 4. update DB

        # 5. save config 

        # TODO: send config datas to PC & DB
        # or if recevied config data from PC, update local & DB config data

        # log
        log_text = time.strftime('%y%m%d_%H%M%S', time.localtime(time.time())) + ' ' + variable_name + ' ' + input_num
        self.textEdit_log.append(log_text)


        self.lineEdit.setVisible(False)
        self.lineEdit.setText("")

    def LineEdit_Login_2_RET(self, input_num):
        self.sub_mqtt.client1.username_pw_set(username="smrs",password=input_num)

        for x in range(5):
            print(x)
            if self.sub_mqtt.login_ok == True:
                self.tabWidget.setTabVisible(0, False)
                self.tabWidget.setTabEnabled(1, True)
                self.tabWidget.setTabEnabled(2, True)
                self.tabWidget.setTabEnabled(3, True)
                self.tabWidget.setTabEnabled(4, True)
                # self.tabWidget.setCurrentIndex(1)
                # TODO: DB Connection???????
                return

            time.sleep(1) 

        self.Login_2.clear()
        QMessageBox.warning(self, 'Wrong Password', 'Try Again')

    """
    def LineEdit_Login_2_RET(self, input_num):
        if input_num == PASSWORD_2:
            # self.sub_mqtt.client1.username_pw_set(username="steve",password="password")
            self.sub_mqtt.client1.username_pw_set(username="smrs",password="1234")
            self.tabWidget.setTabVisible(0, False)
            self.tabWidget.setTabEnabled(1, True)
            self.tabWidget.setTabEnabled(2, True)
            self.tabWidget.setTabEnabled(3, True)
            self.tabWidget.setTabEnabled(4, True)
            # self.tabWidget.setCurrentIndex(1)
            # TODO: DB Connection???????
        else:
            self.Login_2.clear()
            QMessageBox.warning(self, 'Wrong Password', 'Try Again')
    """

    def input_value(self, lcdNum):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        if('temp' in lcdNum.objectName()):
            self.lineEdit.setValidator(QtGui.QIntValidator(-30, 60, self))
        if('humidity' in lcdNum.objectName()):
            self.lineEdit.setValidator(QtGui.QIntValidator(0, 5, self))
        if('time' in lcdNum.objectName()):
            self.lineEdit.setValidator(QtGui.QIntValidator(1, 3, self))

        self.temp_lcdNumber = lcdNum
        self.lineEdit.setVisible(True)
        self.lineEdit.setFocus()

    def loop_start_func(self):
        self.sub_mqtt.messageSignal.connect(self.on_message_1)
        self.sub_mqtt.loop_start_func()
        self.send_CMD('INIT')

    @QtCore.pyqtSlot(str, str)
    def on_message_1(self, msg, topic):
        jsonData = json.loads(msg) 
        # print('on_message_callback: ', msg)
        if topic == sub_root_topic + 'DATA':
            roadTemp = jsonData['road_temp']
            roadHumidity = jsonData['road_humidity']
            airTemp = jsonData['air_temp']

            self.road_temp = np.roll(self.road_temp, -1)
            self.road_humidity = np.roll(self.road_humidity, -1)
            self.air_temp = np.roll(self.air_temp, -1)
            # print("on_message_1 data: ", msg)
            self.road_temp[-1] = roadTemp
            self.road_humidity[-1] = roadHumidity
            self.air_temp[-1] = airTemp

            self.curve_road_temp.setData(self.road_temp)
            self.curve_road_humidity.setData(self.road_humidity)
            self.curve_air_temp.setData(self.air_temp)

        elif topic == sub_root_topic + 'STATUS':
            print("CMD: ", "CH1: ", str(jsonData['CH1']))
            print("CMD: ", "CH2: ", str(jsonData['CH2']))

            self.flag_HEAT_ON = True
            self.label_warning_timer.stop()
            self.label_warning.setVisible(False)

            time_text = time.strftime('%y%m%d_%H%M%S', time.localtime(time.time()))

            if jsonData['CH1'] == True:             # PRE HEAT ON
                print("PRE HEAT: ON")
                self.label_7.setStyleSheet("background-color: green")
                self.btn_PRE_HEAT_ON.setStyleSheet("background-color: green")
                # log
                log_text = time_text + ' 예비 가동 시작'
            elif jsonData['CH1'] == False:          # PRE HEAT OFF
                print("PRE HEAT: OFF")
                self.label_7.setStyleSheet("background-color: gray")
                self.btn_PRE_HEAT_ON.setStyleSheet("background-color: gray")

            if jsonData['CH2'] == True:             # HEAT ON
                print("HEAT: ON")
                self.label_8.setStyleSheet("background-color: green")
                self.btn_HEAT_ON.setStyleSheet("background-color: green")
                log_text = time_text + ' 가동 시작'
            elif jsonData['CH2'] == False:            # HEAT OFF
                print("HEAT: OFF")
                self.label_8.setStyleSheet("background-color: gray")
                self.btn_HEAT_ON.setStyleSheet("background-color: gray")

            if jsonData['CH1'] == False and jsonData['CH2'] == False:   # heat time out -> ch1 or ch2 off -> both ch1 & ch2 off
                self.flag_HEAT_ON = False
                log_text = time_text + ' 가동 멈춤'

            self.textEdit_log.append(log_text)

        elif topic == sub_root_topic + 'CONFIG':
            print('received CONFIG')
            for key, value in jsonData.items():
                print(key, value)
                lcdNum = self.findChild(QLCDNumber, key)
                lcdNum.display(value)

                lcdNum = self.findChild(QLCDNumber, key+'_2')    # find LCDNumber with key 
                if (lcdNum is not None):
                    lcdNum.display(value)                        # display to LCDNumber
        
        elif topic == sub_root_topic + 'IMAGE':
            filename = jsonData['filename'].split('/')[2]
            img_str = jsonData['IMG']

            # to decode back to np.array
            jpg_original = base64.b64decode(img_str)
            jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
            decoded_img = cv2.imdecode(jpg_as_np, flags=1)

            self.update_image(decoded_img, 480, 360)
            self.btn_capture.setStyleSheet("background-color: gray; border: 1px solid black")

            self.textEdit.append('captured ' + filename)

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

    def drawLine(self, plot_name, val, color):
        line = pg.InfiniteLine(angle=0, movable=True, pen=color)
        line.setValue(val)
        plot_name.addItem(line, ignoreBounds=True)

    def stParam(self, lcdNum):
        with shelve.open('config.db') as f:
            if lcdNum == self.lcdNum_line_num:
                f['LINE_NUM'] = self.lcdNum_line_num.value()

    def to_excel_func(self, _time, data):
        tt = [_time, data]
        self.resist_data.append(tt)
        print(tt)


    def graph_plot(self):
        # self.g_plotWidget.plot(hour, temperature)
        # curve = self.graphWidget_2.plot(pen='y')

        update_data_road_temp = []
        update_data_road_humidity = []
        update_data_air_temp = []

        update_results = collection.find({"timestamp": {"$gt":self.query_time}}, limit=NUM_UPDATE_X_AXIS)
        for result in update_results:
            update_data_road_temp.append(result.get("road_temp"))
            update_data_road_humidity.append(result.get("road_humidity"))
            update_data_air_temp.append(result.get("air_temp"))
            self.query_time = result.get("timestamp")
            # print(result)
            # print(result.get("temperature"))
            # print(self.query_time)

        # print("road_temp")
        # print(self.road_temp)
        # print("road_humidity")
        # print(self.road_humidity)
        # print("air_temp")
        # print(self.air_temp)
        # print("update_data_road_temp")
        # print(update_data_road_temp)
        # print("update_data_road_humidity")
        # print(update_data_road_humidity)
        # print("update_data_air_temp")
        # print(update_data_air_temp)

        self.road_temp = self.road_temp[NUM_UPDATE_X_AXIS : NUM_X_AXIS+NUM_UPDATE_X_AXIS-1] + update_data_road_temp
        self.road_humidity = self.road_humidity[NUM_UPDATE_X_AXIS : NUM_X_AXIS+NUM_UPDATE_X_AXIS-1] + update_data_road_humidity
        self.air_temp = self.air_temp[NUM_UPDATE_X_AXIS : NUM_X_AXIS+NUM_UPDATE_X_AXIS-1] + update_data_air_temp

        update_data_road_temp.clear()
        update_data_road_humidity.clear()
        update_data_air_temp.clear()

        self.curve_road_temp.setData(self.road_temp)
        self.curve_road_humidity.setData(self.road_humidity)
        self.curve_air_temp.setData(self.air_temp)

    # sned CMD by mqtt
    def send_CMD(self, button):
        if button == 'INIT':
            print('INIT. request DATA, Config, Status!!')
            self.sub_mqtt.send_msg(pub_root_topic+"INIT", json.dumps({'REQUEST': 'INIT'}))
            return

        button.setStyleSheet("background-color: green; border: 1px solid black")
        if button == self.btn_PRE_HEAT_ON:
            print('pressed PRE HEAT BUtton')
            self.sub_mqtt.send_msg(pub_root_topic+"CMD", json.dumps({'CH1': True, 'CH2': False}))
        elif button == self.btn_HEAT_ON:
            print('pressed HEAT BUtton')
            self.sub_mqtt.send_msg(pub_root_topic+"CMD", json.dumps({'CH1': False, 'CH2': True}))
        elif button == self.btn_capture:
            print('pressed capture button')
            self.sub_mqtt.send_msg(pub_root_topic+"CAPTURE", json.dumps({'CAPTURE': True}))


    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img, _width = 360, _height = 270):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img, _width, _height)
        self.label_cam_2.setPixmap(qt_img)
    
    def convert_cv_qt(self, cv_img, _width = 360, _height = 270):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        p = convert_to_Qt_format.scaled(_width, _height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


def run():
    app = QApplication(sys.argv)
    widget = qt()
    widget.show()

    widget.loop_start_func()
    sys.exit(app.exec_())


ip = '203.251.78.135'
mongo_port = 27017
mqtt_port = 1883

userid = 'smrs_1'
passwd = 'smrs2580_1!'

if __name__ == "__main__":
    # conn = pymongo.MongoClient('203.251.78.135', 27017)

    if ENABLE_MONGODB:
        conn = pymongo.MongoClient('mongodb://' + ip,
                            username = userid,
                            password =  passwd,
                            authSource = 'road_1')

        db = conn.get_database('road_1')
        collection = db.get_collection('device_1')

    #results = collection.find()  # find()에 인자가 없으면 해당 컬렉션의 전체 데이터 조회. return type = cursor
    #for result in results:
    #    print(result)


    run()
