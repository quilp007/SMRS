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
import re
import platform
import uuid

if platform.system() == 'Windows':
    from winreg import *

# ------------------------------------------------------------------------------
# config -----------------------------------------------------------------------
# ------------------------------------------------------------------------------

WEB_APP_MODE = False
ENABLE_MQTT = True
ENABLE_MONGODB = True

# x_size = 360# graph's x size
x_size = 720  # graph's x size
# NUM_X_AXIS = 300
NUM_X_AXIS = 720
NUM_UPDATE_X_AXIS = 5

ROW_COUNT = 7
COL_COUNT = 3

LABEL_WARNING_TIME = 3000  # ms -> timer setting

server_ip = '203.251.78.135'

userid = 'smrs_1'
passwd = 'smrs2580_1!'

mongo_port = 27017
mqtt_port = 1883

TEST = False
CERTI = True

if TEST == False:
    MQTT_CLIENT_ID = 'client_pc1'
    pub_root_topic = "APP111/"
    sub_root_topic = "R_PI111/"
else:
    MQTT_CLIENT_ID = 'client_pc_test'
    pub_root_topic = "APP_test/"
    sub_root_topic = "R_PI_test/"

pre_heat_road_temp = 0
heat_road_temp = 0
set_road_humidity = 0
set_air_temp = 0
pre_heat_on_time = 0
heat_on_time = 0

DEBUG_PRINT = True


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


# def resource_path(relative_path):
#     """ Get absolute path to resource, works for dev and for PyInstaller """
#     base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
#     return os.path.join(base_path, relative_path)
#
# form = resource_path("SRMS.ui")
# form_class = uic.loadUiType(resource_path("SMRS.ui"))[0]


if CERTI == True and platform.system() == 'Windows':
    form_class = uic.loadUiType(resource_path("C:\work\SMRS\SMRS.ui"))[0]
else:
    form_class = uic.loadUiType('SMRS.ui')[0]

if ENABLE_MONGODB:
    conn = pymongo.MongoClient('mongodb://' + server_ip,
                               username=userid,
                               password=passwd,
                               authSource='road_1')

    db = conn.get_database('road_1')
    collection = db.get_collection('device_1')
    signup_col = db.get_collection('signup')


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

class Util_Function:
    def Qsleep(self, ms):
        QtTest.QTest.qWait(ms)

    def save_var(self, key, value):
        with shelve.open('config') as f:
            f[key] = value

    def read_var(self, key):
        with shelve.open('config') as f:
            try:
                temp = f[key]
                # print(f[key])
                return temp
            except:
                pass


class LineEdit(QLineEdit):
    def __int__(self):
        QLineEdit.__init__(self)

    def focusOutEvent(self, e):
        print("====================")


class qt(QMainWindow, form_class):
    def __init__(self):
        # QMainWindow.__init__(self)
        # uic.loadUiType('qt_test2.ui', self)[0]

        super().__init__()

        self.setupUi(self)
        # self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        # lineEdit = LineEdit(self)

        self.tabWidget.setTabEnabled(1, False)
        self.tabWidget.setTabEnabled(2, False)
        self.tabWidget.setTabEnabled(3, False)
        self.tabWidget.setTabEnabled(4, False)
        # self.Login_2.setFocus()
        self.le_id.setFocus()

        #jw0829변경분
        self.tabWidget.currentChanged.connect(self.onChangeTab) #탭변경시 필요한 초기화설정
        self.setFixedSize(QSize(1000, 530))                     #사이즈고정
        self.btn_PRE_HEAT_ON.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))#버튼 및 탭 마우스오버시 커서변경
        self.btn_HEAT_ON.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_capture.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.tabWidget.tabBar().installEventFilter(self)
        self.tabWidget.tabBar().setMouseTracking(True)

        self.btn_PRE_HEAT_ON.clicked.connect(lambda: self.send_CMD(self.btn_PRE_HEAT_ON))
        self.btn_HEAT_ON.clicked.connect(lambda: self.send_CMD(self.btn_HEAT_ON))
        self.btn_capture.clicked.connect(lambda: self.send_CMD(self.btn_capture))
        # self.btn_INIT_SETTING.clicked.connect(lambda: self.send_CMD(self.btn_INIT_SETTING))

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

        self.lineEdit_pre_heat_road_temp.returnPressed.connect(
            lambda: self.LineEdit_pre_heat_road_temp_RET(self.lineEdit_pre_heat_road_temp.text()))
        self.lineEdit_heat_road_temp.returnPressed.connect(
            lambda: self.LineEdit_heat_road_temp_RET(self.lineEdit_heat_road_temp.text()))
        self.lineEdit_set_road_humidity.returnPressed.connect(
            lambda: self.LineEdit_set_road_humidity_RET(self.lineEdit_set_road_humidity.text()))
        self.lineEdit_pre_heat_on_time.returnPressed.connect(
            lambda: self.LineEdit_pre_heat_on_time_RET(self.lineEdit_pre_heat_on_time.text()))
        self.lineEdit_heat_on_time.returnPressed.connect(
            lambda: self.LineEdit_heat_on_time_RET(self.lineEdit_heat_on_time.text()))
        self.lineEdit_set_air_temp.returnPressed.connect(
            lambda: self.LineEdit_set_air_temp_RET(self.lineEdit_set_air_temp.text()))

        self.le_id.returnPressed.connect(lambda: self.LineEdit_Login_id_RET(self.le_id.text()))
        self.le_id.editingFinished.connect(lambda: self.LineEdit_Login_id_RET(self.le_id.text()))

        self.Login_2.returnPressed.connect(lambda: self.LineEdit_Login_2_RET(self.Login_2.text()))
        self.Login_3.returnPressed.connect(lambda: self.LineEdit_Login_3_RET(self.Login_3.text()))
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
        self.timer.setInterval(1000)  # 100ms
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
        self.sub_mqtt = 0
        # if ENABLE_MQTT:
        #     self.sub_mqtt = sc.SUB_MQTT(_broker_address=server_ip, _topic=sub_root_topic + '+', _client=MQTT_CLIENT_ID,
        #                             _mqtt_debug=DEBUG_PRINT)
        # # time.sleep(3)
        # # self.sub_mqtt.client1.username_pw_set(username="steve",password="password")
        ################################################

        # check validation of input value
        re = QtCore.QRegExp("-[3][0]|-[1-2][0-9]|-[1-9]|[0-9]|[1-5][0-9]|[6][0]")
        self.lineEdit_pre_heat_road_temp.setValidator(QtGui.QRegExpValidator(re))
        self.lineEdit_heat_road_temp.setValidator(QtGui.QRegExpValidator(re))
        self.lineEdit_set_air_temp.setValidator(QtGui.QRegExpValidator(re))

        re = QtCore.QRegExp("[1-9]|[1-9][0-9]|[1][0-1][0-9]|[1][2][0]")
        self.lineEdit_pre_heat_on_time.setValidator(QtGui.QRegExpValidator(re))
        self.lineEdit_heat_on_time.setValidator(QtGui.QRegExpValidator(re))

        re = QtCore.QRegExp("[0-9]")
        self.lineEdit_set_road_humidity.setValidator(QtGui.QRegExpValidator(re))

        self.label_warning.setVisible(False)

        # limit line to 150 (log textEdit)
        self.textEdit_log.document().setMaximumBlockCount(150)

        self.flag_HEAT_ON = False

        # -------------------------------------------------------------
        self.NO_PASSWD_MODE = False

        self.check_passwd = 0
        self.login_id = 0

        self.util_func = Util_Function()

        if not ENABLE_MONGODB:
            passwd = self.util_func.read_var('enerpia_1')
            if passwd == None:
                print('no cfg file or no id\passwd')
                self.NO_PASSWD_MODE = True

            else:
                self.label_26.setVisible(False)
                self.Login_3.setVisible(False)
        else:
            self.label_26.setVisible(False)
            self.Login_3.setVisible(False)

        # -------------------------------------------------------------

    def onChangeTab(self):
        self.lineEdit_pre_heat_road_temp.setText("")
        self.lineEdit_heat_road_temp.setText("")
        self.lineEdit_set_road_humidity.setText("")
        self.lineEdit_pre_heat_on_time.setText("")
        self.lineEdit_heat_on_time.setText("")
        self.lineEdit_set_air_temp.setText("")

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.MouseMove and
                source is self.tabWidget.tabBar()):
            index = source.tabAt(event.pos())
            if index >= 0 and index != source.currentIndex():
                source.setCursor(QtCore.Qt.PointingHandCursor)
            else:
                source.setCursor(QtCore.Qt.ArrowCursor)
        return super(qt, self).eventFilter(source, event)

    def label_warning_timeout_func(self):
        self.label_warning.setVisible(False)

    """
    def LineEdit_RET(self, input_num):
        # 1. Display in lcdNumber => after receive mqtt msg
        # 2. update Global Config Variable
        # 3. send mqtt msg
        # 4. update DB
        # 5. save config
        # TODO: send config datas to PC & DB
        # or if recevied config data from PC, update local & DB config data
        # log
    """

    def LineEdit_pre_heat_road_temp_RET(self, input_num):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        REGEX = "-[3][0]|-[1-2][0-9]|-[1-9]|[0-9]|[1-5][0-9]|[6][0]"
        if not re.fullmatch(REGEX, str(input_num)):
            QMessageBox.warning(self, '입력오류', '숫자(범위:-30~60)만 입력해주세요.')
            self.lineEdit_pre_heat_road_temp.setText("")
        else:
            # self.findChild(QLCDNumber, "pre_heat_road_temp").display(input_num)
            # self.findChild(QLCDNumber, "pre_heat_road_temp_2").display(input_num)
            self.sub_mqtt.send_msg(pub_root_topic + "CONFIG", json.dumps({"pre_heat_road_temp": input_num}))

            if WEB_APP_MODE == False:
                log_text = time.strftime('%y%m%d_%H%M%S',time.localtime(time.time())) + ' ' + "pre_heat_road_temp" + ' ' + str(input_num)
                self.textEdit_log.append(log_text)
                self.lineEdit_pre_heat_road_temp.setText("")

    def LineEdit_heat_road_temp_RET(self, input_num):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        REGEX = "-[3][0]|-[1-2][0-9]|-[1-9]|[0-9]|[1-5][0-9]|[6][0]"
        if not re.fullmatch(REGEX, str(input_num)):
            QMessageBox.warning(self, '입력오류', '숫자(범위:-30~60)만 입력해주세요.')
            self.lineEdit_heat_road_temp.setText("")
        else:
            # self.findChild(QLCDNumber, "heat_road_temp").display(input_num)
            # self.findChild(QLCDNumber, "heat_road_temp_2").display(input_num)
            self.sub_mqtt.send_msg(pub_root_topic + "CONFIG", json.dumps({"heat_road_temp": input_num}))

            if WEB_APP_MODE == False:
                log_text = time.strftime('%y%m%d_%H%M%S',time.localtime(time.time())) + ' ' + "heat_road_temp" + ' ' + str(input_num)
                self.textEdit_log.append(log_text)
                self.lineEdit_heat_road_temp.setText("")

    def LineEdit_set_road_humidity_RET(self, input_num):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        REGEX = "[0-9]"
        if not re.fullmatch(REGEX, str(input_num)):
            QMessageBox.warning(self, '입력오류', '숫자(범위:-30~60)만 입력해주세요.')
            self.lineEdit_set_road_humidity.setText("")
        else:
            # self.findChild(QLCDNumber, "set_road_humidity").display(input_num)
            # self.findChild(QLCDNumber, "set_road_humidity_2").display(input_num)
            self.sub_mqtt.send_msg(pub_root_topic + "CONFIG", json.dumps({"set_road_humidity": input_num}))

            if WEB_APP_MODE == False:
                log_text = time.strftime('%y%m%d_%H%M%S',time.localtime(time.time())) + ' ' + "set_road_humidity" + ' ' + str(input_num)
                self.textEdit_log.append(log_text)
                self.lineEdit_set_road_humidity.setText("")

    def LineEdit_pre_heat_on_time_RET(self, input_num):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        REGEX = "[1-9]|[1-9][0-9]|[1][0-1][0-9]|[1][2][0]"
        if not re.fullmatch(REGEX, str(input_num)):
            QMessageBox.warning(self, '입력오류', '숫자(범위:-30~60)만 입력해주세요.')
            self.lineEdit_pre_heat_on_time.setText("")
        else:
            # self.findChild(QLCDNumber, "pre_heat_on_time").display(input_num)
            self.sub_mqtt.send_msg(pub_root_topic + "CONFIG", json.dumps({"pre_heat_on_time": input_num}))

            if WEB_APP_MODE == False:
                log_text = time.strftime('%y%m%d_%H%M%S', time.localtime(time.time())) + ' ' + "pre_heat_on_time" + ' ' + str(input_num)
                self.textEdit_log.append(log_text)
                self.lineEdit_pre_heat_on_time.setText("")

    def LineEdit_heat_on_time_RET(self, input_num):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        REGEX = "[1-9]|[1-9][0-9]|[1][0-1][0-9]|[1][2][0]"
        if not re.fullmatch(REGEX, str(input_num)):
            QMessageBox.warning(self, '입력오류', '숫자(범위:-30~60)만 입력해주세요.')
            self.lineEdit_heat_on_time.setText("")
        else:
            # self.findChild(QLCDNumber, "heat_on_time").display(input_num)
            self.sub_mqtt.send_msg(pub_root_topic + "CONFIG", json.dumps({"heat_on_time": input_num}))
            
            if WEB_APP_MODE == False:
                log_text = time.strftime('%y%m%d_%H%M%S',time.localtime(time.time())) + ' ' + "heat_on_time" + ' ' + str(input_num)
                self.textEdit_log.append(log_text)
                self.lineEdit_heat_on_time.setText("")

    def LineEdit_set_air_temp_RET(self, input_num):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        REGEX = "-[3][0]|-[1-2][0-9]|-[1-9]|[0-9]|[1-5][0-9]|[6][0]"
        if not re.fullmatch(REGEX, str(input_num)):
            QMessageBox.warning(self, '입력오류', '숫자(범위:-30~60)만 입력해주세요.')
            self.lineEdit_set_air_temp.setText("")
        else:
            # self.findChild(QLCDNumber, "set_air_temp").display(input_num)
            # self.findChild(QLCDNumber, "set_air_temp_2").display(input_num)
            self.sub_mqtt.send_msg(pub_root_topic + "CONFIG", json.dumps({"set_air_temp": input_num}))

            if WEB_APP_MODE == False:
                log_text = time.strftime('%y%m%d_%H%M%S',time.localtime(time.time())) + ' ' + "set_air_temp" + ' ' + str(input_num)
                self.textEdit_log.append(log_text)
                self.lineEdit_set_air_temp.setText("")

    def closeEvent(self, event):
        quit_msg = "종료하시겠습니까?"
        reply = QMessageBox.question(self, '종료알림', quit_msg, QMessageBox.Yes, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # Function to validate the password
    def password_check(self, passwd):

        SpecialSym =['!', '@', '#', '$', '%', '^', '&', '*']
        val = True

        if len(passwd) < 9:
            print('length should be at least 8')
            val = False

        if len(passwd) > 13:
            print('length should be not be greater than 12')
            val = False

        if not any(char.isdigit() for char in passwd):
            print('Password should have at least one numeral')
            val = False

        if not any(char.isupper() for char in passwd):
            print('Password should have at least one uppercase letter')
            val = False

        if not any(char.islower() for char in passwd):
            print('Password should have at least one lowercase letter')
            val = False

        if not any(char in SpecialSym for char in passwd):
            print('Password should have at least one of the symbols $@#')
            val = False
        if val:
            return val

    def set_Tab_visible(self):
        self.tabWidget.setTabVisible(0, False)
        self.tabWidget.setTabEnabled(1, True)
        self.tabWidget.setTabEnabled(2, True)
        self.tabWidget.setTabEnabled(3, True)
        self.tabWidget.setTabEnabled(4, True)

    def login_mqtt(self):
        self.sub_mqtt.client1.username_pw_set(username="smrs", password='1234')

        for x in range(15):
            print(x)
            if self.sub_mqtt.login_ok == True:
                self.set_Tab_visible()
                # self.tabWidget.setCurrentIndex(1)
                # TODO: DB Connection???????

                self.send_CMD('INIT')
                print('MQTT connection sucssess!!')
                return True

            time.sleep(0.5)

        # self.Login_2.clear()
        QMessageBox.warning(self, '네트워크 오류', '서버와의 연결이 원활하지 않습니다\n잠시후 다시 로그인해주세요')
        return False


    def LineEdit_Login_id_RET(self, input_num):
        if ENABLE_MONGODB:
            if signup_col.find_one({'id': input_num}) == None:
                QMessageBox.warning(self, '아이디 오류', '입력하신 아디이가 없습니다.')
            else:
                self.login_id = input_num


    def LineEdit_Login_3_RET(self, input_num):
        if not self.password_check(input_num):
            self.Login_3.clear()
            QMessageBox.warning(self, '패스워드 오류', '패스워드 형식이 맞지 않습니다.!')
            return
        else:
            print('Login_3 OK')
            if self.check_passwd == input_num:
                self.util_func.save_var(str(self.login_id), input_num)

                self.set_Tab_visible()

                if ENABLE_MQTT:
                    self.login_mqtt()

                print('passwd OK')
            else:
                QMessageBox.warning(self, '패스워드 오류', '패스워드가 맞지 않습니다.!!')
                self.Login_3.clear()
                return

    def LineEdit_Login_2_RET(self, input_num):
        if not self.password_check(input_num):
            self.Login_2.clear()
            QMessageBox.warning(self, '패스워드 오류', '패스워드 형식이 맞지 않습니다.!')
            return

        if self.NO_PASSWD_MODE == True:
            print('Login_2 OK')
            self.check_passwd = input_num
            self.Login_3.setFocus()
            return
        else: # normal mode
            # load passwd
            if ENABLE_MONGODB:
                saved_passwd = signup_col.find_one({'id': self.login_id})['pwd']
                print('mongoDB id/pwd: ', self.login_id, '/', saved_passwd)
            else:
                saved_passwd = self.util_func.read_var(self.login_id)

            # check passwd
            if saved_passwd != input_num:
                self.Login_2.clear()
                QMessageBox.warning(self, '패스워드 오류', '패스워드가 맞지 않습니다.')
                # wrong passwd, return
                return


        # self.sub_mqtt.client1.username_pw_set(username="smrs", password=input_num)
        # self.sub_mqtt.client1.username_pw_set(username="smrs", password='1234')
        # self.sub_mqtt.client1.username_pw_set(username="x2yenv1", password='aabc12#')

        if ENABLE_MQTT:
            self.initMqtt(self.login_id, self.on_message_1)

            if self.login_mqtt():
                self.set_Tab_visible()
            else:
                self.Login_2.clear()
                QMessageBox.warning(self, '네트워크 오류', '서버와의 연결이 원활하지 않습니다\n잠시후 다시 로그인해주세요')
        else:
            self.set_Tab_visible()

    
    def initMqtt(self, login_id, on_message, on_message_cb = None):
        global pub_root_topic, sub_root_topic
        mac_address = str(hex(uuid.getnode()))
        MQTT_CLIENT_ID = mac_address + '_' + login_id
        sub_root_topic = 'PUB_' + login_id + '/'
        pub_root_topic = 'SUB_' + login_id + '/'
        self.sub_mqtt = sc.SUB_MQTT(_broker_address=server_ip, _topic=sub_root_topic + '+', _client=MQTT_CLIENT_ID,
                                    _mqtt_debug=DEBUG_PRINT, _on_message = on_message_cb)

        self.loop_start_func(on_message)


    def input_value(self, lcdNum):
        if self.flag_HEAT_ON == True:
            self.label_warning.setVisible(True)
            self.label_warning_timer.start(LABEL_WARNING_TIME)
            print('Heat ON!!!')
            return

        # if('temp' in lcdNum.objectName()):
        # self.lineEdit.setValidator(QtGui.QIntValidator(-30, 60, self))
        # if('humidity' in lcdNum.objectName()):
        #     self.lineEdit.setValidator(QtGui.QIntValidator(0, 5, self))
        # if('time' in lcdNum.objectName()):
        #     self.lineEdit.setValidator(QtGui.QIntValidator(1, 120, self))

        # self.temp_lcdNumber = lcdNum
        # self.lineEdit.setVisible(True)
        # self.lineEdit.setFocus()
        if (lcdNum.objectName() == "pre_heat_road_temp"):
            self.lineEdit_pre_heat_road_temp.setFocus()
        if (lcdNum.objectName() == "heat_road_temp"):
            self.lineEdit_heat_road_temp.setFocus()
        if (lcdNum.objectName() == "set_road_humidity"):
            self.lineEdit_set_road_humidity.setFocus()
        if (lcdNum.objectName() == "pre_heat_on_time"):
            self.lineEdit_pre_heat_on_time.setFocus()
        if (lcdNum.objectName() == "heat_on_time"):
            self.lineEdit_heat_on_time.setFocus()
        if (lcdNum.objectName() == "set_air_temp"):
            self.lineEdit_set_air_temp.setFocus()

    def loop_start_func(self, on_message):
        self.sub_mqtt.messageSignal.connect(on_message)
        self.sub_mqtt.loop_start_func()
        # self.send_CMD('INIT')

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

            if jsonData['CH1'] == True and jsonData['CH2'] == True:  # heat time out -> ch1 or ch2 off -> both ch1 & ch2 off
                self.label_33.setStyleSheet("background-color: red")
                self.label_8.setStyleSheet("background-color: pink")
                self.btn_HEAT_ON.setStyleSheet("background-color: pink")
                log_text = time_text + '비상 가동 시작'
                self.textEdit_log.append(log_text)
                return

            if jsonData['CH1'] == True:  # PRE HEAT ON
                print("PRE HEAT: ON")
                self.label_7.setStyleSheet("background-color: yellow")
                self.btn_PRE_HEAT_ON.setStyleSheet("background-color: yellow")
                # log
                log_text = time_text + ' 예비 가동 시작'
            elif jsonData['CH1'] == False:  # PRE HEAT OFF
                print("PRE HEAT: OFF")
                self.label_7.setStyleSheet("background-color: gray")
                self.btn_PRE_HEAT_ON.setStyleSheet("background-color: gray")
                self.label_33.setStyleSheet("background-color: gray")

            if jsonData['CH2'] == True:  # HEAT ON
                print("HEAT: ON")
                self.label_8.setStyleSheet("background-color: pink")
                self.btn_HEAT_ON.setStyleSheet("background-color: pink")
                log_text = time_text + ' 가동 시작'
            elif jsonData['CH2'] == False:  # HEAT OFF
                print("HEAT: OFF")
                self.label_8.setStyleSheet("background-color: gray")
                self.btn_HEAT_ON.setStyleSheet("background-color: gray")
                self.label_33.setStyleSheet("background-color: gray")

            if jsonData['CH1'] == False and jsonData[
                'CH2'] == False:  # heat time out -> ch1 or ch2 off -> both ch1 & ch2 off
                self.flag_HEAT_ON = False
                # self.label_33.setStyleSheet("background-color: gray")
                log_text = time_text + ' 가동 멈춤'

            self.textEdit_log.append(log_text)

        elif topic == sub_root_topic + 'CONFIG':
            print('received CONFIG')
            for key, value in jsonData.items():
                print(key, value)
                lcdNum = self.findChild(QLCDNumber, key)
                lcdNum.display(value)

                lcdNum = self.findChild(QLCDNumber, key + '_2')  # find LCDNumber with key
                if (lcdNum is not None):
                    lcdNum.display(value)  # display to LCDNumber

        elif topic == sub_root_topic + 'IMAGE':
            filename = jsonData['filename'].split('/')[2]
            img_str = jsonData['IMG']

            # to decode back to np.array
            jpg_original = base64.b64decode(img_str)
            jpg_as_np = np.frombuffer(jpg_original, dtype=np.uint8)
            decoded_img = cv2.imdecode(jpg_as_np, flags=1)

            filename = jsonData['filename']
            cv2.imwrite(filename, decoded_img)
            print('image saved')

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

        update_results = collection.find({"timestamp": {"$gt": self.query_time}}, limit=NUM_UPDATE_X_AXIS)
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

        self.road_temp = self.road_temp[NUM_UPDATE_X_AXIS: NUM_X_AXIS + NUM_UPDATE_X_AXIS - 1] + update_data_road_temp
        self.road_humidity = self.road_humidity[
                             NUM_UPDATE_X_AXIS: NUM_X_AXIS + NUM_UPDATE_X_AXIS - 1] + update_data_road_humidity
        self.air_temp = self.air_temp[NUM_UPDATE_X_AXIS: NUM_X_AXIS + NUM_UPDATE_X_AXIS - 1] + update_data_air_temp

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
            self.sub_mqtt.send_msg(pub_root_topic + "INIT", json.dumps({'REQUEST': 'INIT'}))
            return

        # button.setStyleSheet("background-color: green; border: 1px solid black")
        if button == self.btn_PRE_HEAT_ON:
            print('pressed PRE HEAT BUtton')
            self.sub_mqtt.send_msg(pub_root_topic + "CMD", json.dumps({'CH1': True, 'CH2': False}))
        elif button == self.btn_HEAT_ON:
            print('pressed HEAT BUtton')
            self.sub_mqtt.send_msg(pub_root_topic + "CMD", json.dumps({'CH1': False, 'CH2': True}))
        elif button == self.btn_capture:
            print('pressed capture button')
            QMessageBox.warning(self, '사진촬영', '사진촬영 명령이 전송되었습니다.')
            self.sub_mqtt.send_msg(pub_root_topic + "CAPTURE", json.dumps({'CAPTURE': True}))
        elif button == self.btn_INIT_SETTING:
            print('pressed INIT SETTING')
            self.sub_mqtt.send_msg(pub_root_topic + "INIT_SETTING", json.dumps({'INIT_SETTING': True}))

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img, _width=360, _height=270):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img, _width, _height)
        self.label_cam_2.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img, _width=360, _height=270):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        # p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        p = convert_to_Qt_format.scaled(_width, _height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


def run(pc_app):
    app = QApplication(sys.argv)
    widget = qt()

    if pc_app:
        widget.show()

        # if ENABLE_MQTT:
        #     widget.loop_start_func()

        sys.exit(app.exec_())
    else:
        global WEB_APP_MODE
        WEB_APP_MODE = True

    return widget

if __name__ == "__main__":
    # initMongoDB()

    # conn = pymongo.MongoClient('203.251.78.135', 27017)
    # results = collection.find()  # find()에 인자가 없으면 해당 컬렉션의 전체 데이터 조회. return type = cursor
    # for result in results:
    #    print(result)

    run(pc_app = True)
