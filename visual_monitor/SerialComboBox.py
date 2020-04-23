# coding=UTF-8 
'''
@function:calibration with blackbody
@Author: lukehan
@Date: 2020-03-17 16:45:38
@LastEditTime: 2020-03-18 01:22:04
'''
from serial import Serial
from serial import SerialException
import serial.tools.list_ports
from PyQt5.QtWidgets import  QComboBox
from PyQt5.QtCore import pyqtSignal


class SerialComboBox(QComboBox):
    popupAboutToBeShown = pyqtSignal()

    def __init__(self, parent = None):
        super(SerialComboBox,self).__init__(parent)

    # 重写showPopup函数
    def showPopup(self):
        # 先清空原有的选项
        self.clear()
        self.insertItem(0, "Please select serial device")
        index = 1
        # 获取接入的所有串口信息，插入combobox的选项中
        portlist = self.get_port_list(self)
        if portlist is not None:
            for port in portlist:
                self.insertItem(index, port)
                index += 1
        QComboBox.showPopup(self)   # 弹出选项框

    @staticmethod
    # 获取接入的所有串口号
    def get_port_list(self):
        try:
            port_list = list(serial.tools.list_ports.comports())
            for port in port_list:
                # if(port.pid == 29987): # Show ch34x only 
                yield str(port.device)
        except Exception as e:
            logging.error("获取接入的所有串口设备出错！\n错误信息："+str(e))
