#!/usr/bin/env python
# coding=utf8

import os, sys, time, datetime, warnings, signal
from PyQt5.QtCore import QSize, QRect, QObject, pyqtSignal, QThread, pyqtSignal, pyqtSlot, Qt, QEvent, QTimer
from PyQt5.QtWidgets import QApplication, QComboBox, QDialog, QMainWindow, QWidget, QLabel, QTextEdit, QListWidget, \
    QListView
from PyQt5.QtWidgets import QPushButton, QGridLayout, QLCDNumber
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtTest, QtGui, QtCore

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

        self.pushButton.clicked.connect(lambda: self.send_CMD(self.pushButton))
        self.pushButton_2.clicked.connect(lambda: self.send_CMD(self.pushButton_2))

        self.data_temp = []
        self.data_hum = []
        self.data_pres = []

        # qeury(read) from start date (time) to end date (time)
        # TODO: need to modify "query_time" as a user input
        self.query_time = datetime(2022, 6, 15, 18, 22, 37)
        results = collection.find({"timestamp": {"$gt": self.query_time}}, limit=NUM_X_AXIS)
        for result in results:
            self.data_temp.append(result.get("road_temp"))
            self.data_hum.append(result.get("road_humidity"))
            self.data_pres.append(result.get("air_temp"))
            self.query_time = result.get("timestamp")
            # print(result)
            # print(result.get("road_temp"))
            # print(self.query_time)

        # print("self.data_temp")
        # print(self.data_temp)
        # print("self.data_hum")
        # print(self.data_hum)
        # print("self.data_pres")
        # print(self.data_pres)


        self.data = np.linspace(-np.pi, np.pi, x_size)
        self.y2_1 = np.sin(self.data)
        # self.y2_1 = np.zeros(x_size)

        self.road_temp = np.zeros(x_size)
        self.road_humidity = np.zeros(x_size)
        self.air_temp = np.zeros(x_size)


        # table Widget ------------------------------------------------------------------
        self.tableWidget.setRowCount(ROW_COUNT)
        self.tableWidget.setColumnCount(COL_COUNT)  # MEAN, parallel resistance

        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

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

        self.timer = QtCore.QTimer()
        self.timer.setInterval(1000) # 100ms 
        self.timer.timeout.connect(self.graph_plot)

        # start loop for drawing graph #################
        self.timer.start()
        ################################################

        self.thread_rcv_data = THREAD_RECEIVE_Data()
        self.thread_rcv_data.to_excel.connect(self.to_excel_func)
        # self.thread_rcv_data.start()

        self.resist_data = []
        self.log_flag = False

        ################################################
        self.sub_mqtt = sc.SUB_MQTT(_topic = 'device_1/DATA')
        ################################################

    def loop_start_func(self):
        self.sub_mqtt.messageSignal.connect(self.on_message_1)
        self.sub_mqtt.loop_start_func()

    @QtCore.pyqtSlot(str, str)
    def on_message_1(self, msg, topic):
        if topic == 'device_1/DATA':
            jsonData = json.loads(msg) 
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

        # print("data_temp")
        # print(self.data_temp)
        # print("data_hum")
        # print(self.data_hum)
        # print("data_pres")
        # print(self.data_pres)
        # print("update_data_road_temp")
        # print(update_data_road_temp)
        # print("update_data_road_humidity")
        # print(update_data_road_humidity)
        # print("update_data_air_temp")
        # print(update_data_air_temp)

        self.data_temp = self.data_temp[NUM_UPDATE_X_AXIS : NUM_X_AXIS+NUM_UPDATE_X_AXIS-1] + update_data_road_temp
        self.data_hum = self.data_hum[NUM_UPDATE_X_AXIS : NUM_X_AXIS+NUM_UPDATE_X_AXIS-1] + update_data_road_humidity
        self.data_pres = self.data_pres[NUM_UPDATE_X_AXIS : NUM_X_AXIS+NUM_UPDATE_X_AXIS-1] + update_data_air_temp

        update_data_road_temp.clear()
        update_data_road_humidity.clear()
        update_data_air_temp.clear()

        self.curve_road_temp.setData(self.data_temp)
        self.curve_road_humidity.setData(self.data_hum)
        self.curve_air_temp.setData(self.data_pres)

    # sned CMD by mqtt
    def send_CMD(self, button):
        if button == self.pushButton:
            print('send CH1 on')
            self.sub_mqtt.send_msg('device_1/CMD', 'CH1 ON')
        elif button == self.pushButton_2:
            print('send CH1 & CH2 on')
            self.sub_mqtt.send_msg('device_1/CMD', 'CH1 & CH2 ON')


def run():
    app = QApplication(sys.argv)
    widget = qt()
    widget.show()

    # widget.loop_start_func()
    sys.exit(app.exec_())


ip = '203.251.78.135'
mongo_port = 27017
mqtt_port = 1883

userid = 'smrs_1'
passwd = 'smrs2580_1!'

if __name__ == "__main__":
    # conn = pymongo.MongoClient('203.251.78.135', 27017)

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
