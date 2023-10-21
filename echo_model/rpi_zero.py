import sys, os, serial, time, datetime
import serial.tools.list_ports
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox #, QProgressBar,  QComboBox, QWidget, QVBoxLayout
from PyQt5.uic import loadUi
from PyQt5 import uic, QtTest

import zmq
context = zmq.Context()

socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

DEBUG_RECEIVE_TEST_DATA = True
PASS_CHECKSUM = True

PORTS = []

if not DEBUG_RECEIVE_TEST_DATA:
    PORTS = [
        p.device
        for p in serial.tools.list_ports.comports()
        # if 'USB' in p.description
    ]
    print(PORTS)

# PORTS = ["/dev/serial0", "/dev/serial1", "/dev/ttyUSB0"]

data_arr = [
    # [0x12, 0x00, 0x21, 0xcd],
    [0x12, 0x00, 0x20, 0xcd],
    [0x12, 0x08, 0x61, 0xcd],
    [0x12, 0x91, 0xA1, 0xcc],
    [0x12, 0x62, 0x21, 0xcc],
    [0x12, 0x03, 0x20, 0xcc],
    [0x12, 0x84, 0x61, 0xcc],
    [0x12, 0x44, 0xA1, 0xcc]
]

data_arr2 = [
    [b'\x12\x00\x20\xcd'],
    [b'\x12\x08\x61\xcd'],
    [b'\x12\x91\xA1\xcd'],
    [b'\x12\x62\x21\xcd'],
    [b'\x12\x03\x20\xcd'],
    [b'\x12\x84\x61\xcd'],
    [b'\x12\x44\xA1\xcd']
]

DATA_2 = {
    'radar_1':      7,
    'radar_0':      6,
    'elec_lock':    5,
    'working_sw':   4
}

RADAR_1         = 7
RADAR_0         = 6
FOOT_SW         = 5
ELEC_LOCK       = 4
WORKING_SW      = 3
SHOT_MODE_2     = 2
SHOT_MODE_1     = 1
SHOT_MODE_0     = 0

SHOT_SW         = 7
ABNORMAL_SW     = 6
ELEC            = 5


vulcan_data = {
    'source':                       0xd1,       # 0xd1, 0xd2, 0xd3, 0xd4
    'destination':                  0x11,       # 0x11, 0x21, 0x31, 0x41
    'phase':                        0xa1,       # 0xa0, 0xa1, 0xa2
    'gun_barrel_elevation_angle':   0,          # 0 ~ 90
    'gun_azimuth_angle':            -90,          # -180 ~ 180
    'scope_elevation_angle':        0,          # 0 ~ 90
    'scope_azimuth_angle':          -90,          # -180 ~ 180
    'trigger':                      0,          # 0 or 1
    'shot_motor':                   0,          # ?
    'gun_barrel_speed_up_down':     0,          # ?
    'gun_barrel_speed_left_right':  0           # ?
}

def twoComplement(number):
    return (-number) & (2**8 - 1)

#--------------------------------------------------------------
# [THREAD] RECEIVE from FPGA, SEND to Smart Glass
#--------------------------------------------------------------
class THREAD_FPGA_SMART_GLASS(QThread):
    vulcan_qt_signal = pyqtSignal(dict)
    def __init__(self):
        super(THREAD_FPGA_SMART_GLASS, self).__init__()
        self.__suspend = False
        self.__exit = False
        self.idx = 0

    def _test_data(self):
        # self.idx += 1

        for key in vulcan_data:
            if key in ['source', 'destination', 'phase']: continue
            if self.idx > 40:
                vulcan_data[key] = 0

            vulcan_data[key] += (self.idx * 2)
            self.idx += 1

            print(key, vulcan_data[key])
            print('idx: ', self.idx)

        if self.idx > 50: self.idx = 0

    def _test_data2(self):
        if self.idx == 100: self.idx = 0
        self.idx += 1
        print('[idx] : ', self.idx)

        for key in vulcan_data:
            if key in ['source', 'destination', 'phase']: continue
            if self.idx == 100:
                vulcan_data[key] = 0

            if 'elevation_angle' in key:
                vulcan_data[key] += 90/100
            elif 'azimuth_angle' in key:
                vulcan_data[key] += 180/100
            elif  'trigger' in key:
                if self.idx > 50: vulcan_data[key] = 1
                else: vulcan_data[key] = 0
            else:
                vulcan_data[key] = self.idx

            print(key, vulcan_data[key])

    def _uartHandler(self, rcvData):
        print(['0x{:02x}'.format(i) for i in rcvData])

    # --- RECEIVE UART DATA and SEND by ZMQ
    def run(self):
        while True:
            ### Suspend ###
            while self.__suspend:
                time.sleep(0.5)


            self._test_data2()
            self.vulcan_qt_signal.emit(vulcan_data)

            socket.send_json(vulcan_data)

            QtTest.QTest.qWait(1000)
            
            ### Exit ###
            if self.__exit:
                break

    def mySuspend(self):
        self.__suspend = True
         
    def myResume(self):
        self.__suspend = False

    def myExit(self):
        self.__exit = True

#--------------------------------------------------------------
# [THREAD] RECEIVE from MCU
#--------------------------------------------------------------
class THREAD_RECEIVE_MCU(QThread):
    def __init__(self):
        super( THREAD_RECEIVE_MCU, self).__init__()
        self.__suspend = False
        self.__exit = False


    # --- RECEIVE MCU UART DATA
    def run(self):
        while True:
            ### Suspend ###
            while self.__suspend:
                time.sleep(0.5)

            
            ### Exit ###
            if self.__exit:
                break

    def mySuspend(self):
        self.__suspend = True
         
    def myResume(self):
        self.__suspend = False

    def myExit(self):
        self.__exit = True

class main_window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        loadUi('./rpi_zero.ui', self)        
        
        # setting  the fixed width of window       
        # width = 1000
        # height = 700
        # self.setFixedWidth(width)
        # self.setFixedHeight(height)

        self.pushButton_8.setStyleSheet("border-style: outset; border-width: 0px")
        self.pushButton_9.setStyleSheet("border-style: outset; border-width: 0px")


def run():
    app = QApplication(sys.argv)
    widget = main_window()

    widget.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    run()
