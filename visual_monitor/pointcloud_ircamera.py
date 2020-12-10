'''
@function: 
@Author: swortain
@Date: 2020-03-02 16:45:38
@LastEditTime: 2020-03-18 00:17:22
'''
import sys
import getopt
import serial.tools.list_ports
import threading
import math
import struct
from SerialComboBox import SerialComboBox
from serial import Serial
import serial.tools.list_ports
import serial.tools.miniterm as miniterm
import time
import numpy as np

from PyQt5.QtWidgets import (
        QApplication,
        QGraphicsView,
        QGraphicsScene,
        QGraphicsPixmapItem,
        QGraphicsTextItem,
        QGraphicsEllipseItem,
        QGraphicsLineItem,
        QGraphicsBlurEffect,
        QPushButton,
        QLabel,
        QMessageBox
    )
from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QPixmap
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QPointF, Qt

mlx90640 = '90640'
mlx90641 = '90641'
mlx90621 = '90621'
chip = 'None'

def mapValue(value, curMin, curMax, desMin, desMax):
    curDistance = value - curMax
    if curDistance == 0:
        return desMax
    curRange = curMax - curMin
    direction = 1 if curDistance > 0 else -1
    ratio = curRange / curDistance
    desRange = desMax - desMin
    value = desMax + (desRange / ratio)
    return value

def constrain(value, down, up):
    value = up if value > up else value
    value = down if value < down else value
    return value        

def isDigital(value):
    try:
        if value == "nan":
            return False
        else:
            float(value)
        return True
    except ValueError:
        return False

def detectChipType(dataLen):
    global chip
    global pixel_width
    if dataLen == 768:
        chip = mlx90640
        pixel_width = 32
    elif dataLen ==192:
        chip = mlx90641
        pixel_width = 16
    elif dataLen ==64:
        chip = mlx90621
        pixel_width = 16
    else:
        print("Data parse Error Can't recongize chip type data length:",dataLen)

def nanFilter(idx,tempData,width):
    if math.isnan(tempData[idx]):
        #print('got a nan')
        curCol = idx % width
        newValueForNanPoint = 0
        interpolationPointCount = 0
        sumValue = 0
        abovePointIndex = idx - width
        if (abovePointIndex > 0):
            if not math.isnan(tempData[abovePointIndex]):
                interpolationPointCount += 1
                sumValue += float(tempData[abovePointIndex])

        belowPointIndex = idx + width
        if (belowPointIndex < len(tempData)):
            if not math.isnan(tempData[belowPointIndex]) :
                interpolationPointCount += 1
                sumValue += float(tempData[belowPointIndex])
                
        leftPointIndex = idx - 1
        if (curCol > 0):
            if not math.isnan(tempData[leftPointIndex] ):
                interpolationPointCount += 1
                sumValue += float(tempData[leftPointIndex])

        rightPointIndex = idx + 1
        if (curCol < width - 1):
            if not math.isnan(tempData[rightPointIndex]):
                interpolationPointCount += 1
                sumValue += float(tempData[rightPointIndex])

        if interpolationPointCount == 0:
            print("nanFilter idx:",idx," above:",tempData[abovePointIndex]," below:",
                tempData[belowPointIndex]," left:",tempData[leftPointIndex]," right:",tempData[rightPointIndex])
            return float('nan')

        newValueForNanPoint =  sumValue/interpolationPointCount
        return newValueForNanPoint
    else:
        return tempData[idx]


displayData = []
btn_index = 4
strButton = ["1/2fps","1fps","2fps","3fps","4fps"]
strFpsCmd = ['CMDF\0','CMDF\1','CMDF\2','CMDF\3','CMDF\4']
maxHet = 0
minHet = 0
device_commonOffset = 0.0
lock = threading.Lock()
minHue = 90
maxHue = 360
dataThread = None
evaluate_mode = "None"
detect_status = 'None'
useBlur = False
narrowRatio = 1
versoin = ''
pixel_width = 32


class SerialDataHandler(QThread):
    drawRequire = pyqtSignal()
    uiRequire = pyqtSignal()
    cmdRequire = pyqtSignal()
    def __init__(self,):
        super(SerialDataHandler, self).__init__()
        self.port = None
        # self.com = Serial(self.port, 230400, timeout=5)
        # print("SerialDataHandler:",self.port,230400)
        self.frameCount = 0
        self.failedCount = 0
        self.cali_id = 0
        self.version = 0

    def initSerialPort(self,port):
        try:
            print("try to init com")
            self.port = port
            self.com = Serial(port, 115200, timeout=5)
            return True
        except(OSError,serial.SerialException):
            print("init ",port,"fail")
            self.com = None
            return False

    def sendData(self,s): # send cmd to mcu with serial
        crc  = 0
        for i in range(0,len(s)):
            crc = crc + ord(s[i])
        crc = crc & 0xFF
        s += chr(crc)
        self.com.write(s.encode('utf-8'))

    def getID(self):
        return self.cali_id,self.version

    def parseRawData(self):
        rawData = self.com.read(2)
        DatLen = rawData[0]*256+rawData[1]
        
        rawData = self.com.read(4)
        Ta = struct.unpack('1f',rawData)
        rawData = self.com.read(4*DatLen)
        tempData = struct.unpack(str(DatLen)+'f',rawData)
        tempData = list(tempData)
        # print("DAT DatLen",DatLen," real pixel data size",len(tempData))
        rawData = self.com.read(2)
        if rawData != b'\r\n':
             print("Data parse Error: data end tag not correct data=",rawData)
        return tempData,Ta

    def parseTempData(self,hetData):
        global minHue
        global maxHue
        global maxHet
        global minHet
        global chip
        global pixel_width
        detectChipType(len(hetData[0]))
        if chip != 'None':
            #hetData = hetData[:-1]
            tempData = []
            nanCount = 0
            maxHet = 0
            minHet = 500
            tempData = hetData[0]
            for i in range(0, len(tempData)):
                tempData[i] = nanFilter(i,tempData,pixel_width)
                if math.isnan(tempData[i]):
                    print("pase Temperature data Nan!")
                    return

                maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                minHet = tempData[i] if tempData[i] < minHet else minHet

            for i in range(len(tempData)):
               tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)

            lock.acquire()
            displayData.append(tempData)
            lock.release()
            self.drawRequire.emit()
            self.frameCount = self.frameCount + 1
        else:
            print("pase Temperature data Error: can't detect chip type. data length:" , len(hetData))

    def processCommand(self,hetData):
        global device_commonOffset
        global evaluate_mode
        global flashSucceed
        global detect_status
        global chip
        #hetData = self.com.read(3)
        if hetData[0:3] == b'CMD':
            #hetData = self.com.read_until(terminator=b'\r\n')
            print('Receive a CMD: RETCMD',hetData, " T:",hetData[3] )
            if hetData[3] == 84:  #'T'
                str1 = hetData[4:].decode('utf-8','ignore') 
                i = 0
                while i < len(str1):
                    if str1[i] == '\0':
                        break
                    i+=1
                if i > 1: 
                    str1 = str1[:i]
                    device_commonOffset = float(str1)
                else:
                    device_commonOffset = 0.0
            elif  hetData[3] == 79: #'O'
                if hetData[4] == 1:
                    detect_status = 'Body'
                elif hetData[4] == 0:
                    detect_status = 'Object'
                else:
                    detect_status = 'None'
            elif  hetData[3] == 69: #'E'
                if hetData[4] == 0:
                    evaluate_mode = 'operate'
                else:
                    evaluate_mode = 'evaluate'
                print("evaluate:",evaluate_mode)
            elif  hetData[3] == 86: #'V'
                (self.version,) = struct.unpack('I',hetData[4:8])
                (self.cali_id,) = struct.unpack('I',hetData[9:13])
                print("CMDV v:",hetData[4:8]," c:",hetData[9:13]," ver:",self.version," cal:", self.cali_id )
            
            self.drawRequire.emit()
        elif hetData[0:3] == b'ERR':
            #hetData = self.com.read_until(terminator=b'\r\n')
            print('Receive a ERR: RETERR',len(hetData))

    def run(self):
        global maxHet
        global minHet
        global evaluate_mode
        global chip
        global pixel_width
        
        # while self.com.inWaiting() != 0:
        #     self.com.read()

        # self.cmdRequire.emit()
        while True:
            if self.port is None:
                # print(" arduinoCom  is not ready yet!!!" )
                time.sleep(1)
                continue
            dataType = self.com.read(3)
            if dataType == b'RET':
                cmdData = self.com.read_until(terminator=b'\r\n')
                self.processCommand(cmdData)
            elif dataType == b'DAT' and evaluate_mode != 'evaluate':
                resData = self.parseRawData()   
                self.parseTempData(resData)
            else:
                try:
                    strData = dataType + self.com.read_until(terminator=b'\r\n')
                    hetData = str(strData, encoding="utf8").split(",")
                    resData = [np.array(hetData[:-1]).astype(np.float),float(hetData[-1])]
                    self.parseTempData(resData)
                    print("evaluate mode resData size : ",len(resData[0]))
                except ValueError:
                    print("Paser Data Error in Evaluate Mode!",len(strData))
                    # print()
                    continue

class painter(QGraphicsView):
    pixelSize = int(15 / narrowRatio)
    width = int (480 / narrowRatio)
    height = int(360 / narrowRatio)
    fontSize = int(15 / narrowRatio)
    anchorLineSize = int(100 / narrowRatio)
    ellipseRadius = int(8 / narrowRatio)
    textInterval = int(90 / narrowRatio)
    col = width / pixelSize
    line = height / pixelSize
    centerIndex = int(round(((line / 2 - 1) * col) + col / 2))
    frameCount = 0
    failedCount = 0
    baseZValue = 0
    mode = 1
    body = 1
    open_status = 0
    textLineHeight = fontSize + 10
    blurRaduis = 50  # Smoother improvement

    def __init__(self,dataThread):
        super(painter, self).__init__()
        self.dataThread = dataThread
        self.setFixedSize(self.width + 200, self.height + self.textLineHeight)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        # center het text item
        self.centerTextItem = QGraphicsTextItem()
        self.centerTextItem.setPos((self.width + 200) / 2 - self.fontSize, 0)
        self.centerTextItem.setZValue(self.baseZValue + 1)
        self.scene.addItem(self.centerTextItem)
        # version text item
        self.versionTextItem = QGraphicsTextItem()
        self.versionTextItem.setPos(self.width *0.8 -self.fontSize,self.height*0.8-self.fontSize)
        self.versionTextItem.setZValue(self.baseZValue + 1)
        self.scene.addItem(self.versionTextItem)
        self.userCom = None

        # center anchor item
        centerX = self.width / 2
        centerY = self.height / 2
        self.ellipseItem = QGraphicsEllipseItem(
                0, 0, 
                self.ellipseRadius * 2, 
                self.ellipseRadius * 2
            )
        self.horLineItem = QGraphicsLineItem(0, 0, self.anchorLineSize, 0)
        self.verLineItem = QGraphicsLineItem(0, 0, 0, self.anchorLineSize)
        self.ellipseItem.setPos(
                centerX - self.ellipseRadius, 
                centerY - self.ellipseRadius
            )
        self.horLineItem.setPos(centerX - self.anchorLineSize / 2, centerY)
        self.verLineItem.setPos(centerX, centerY - self.anchorLineSize / 2)
        self.ellipseItem.setPen(QColor(Qt.white))
        self.horLineItem.setPen(QColor(Qt.white))
        self.verLineItem.setPen(QColor(Qt.white))
        self.ellipseItem.setZValue(self.baseZValue + 1)
        self.horLineItem.setZValue(self.baseZValue + 1)
        self.verLineItem.setZValue(self.baseZValue + 1)
        self.scene.addItem(self.ellipseItem)
        self.scene.addItem(self.horLineItem)
        self.scene.addItem(self.verLineItem)
        # camera item
        self.cameraBuffer = QPixmap(self.width, self.height + self.textLineHeight)
        self.cameraItem = QGraphicsPixmapItem()
        if useBlur:
            self.gusBlurEffect = QGraphicsBlurEffect()
            self.gusBlurEffect.setBlurRadius(self.blurRaduis)
            self.cameraItem.setGraphicsEffect(self.gusBlurEffect)
        self.cameraItem.setPos(100, 0)
        self.cameraItem.setZValue(self.baseZValue)
        self.scene.addItem(self.cameraItem)
        # het text item
        self.hetTextBuffer = QPixmap(self.width+200, self.textLineHeight)
        self.hetTextItem = QGraphicsPixmapItem()
        self.hetTextItem.setPos(0, self.height)
        self.hetTextItem.setZValue(self.baseZValue)
        self.scene.addItem(self.hetTextItem)    
        # button item
        self.ctrlOpenButton = QPushButton('Open',self)
        self.ctrlOpenButton.clicked.connect(self.ctrlOpen)
        self.ctrlOpenButton.setGeometry(10,30,100,40)
        
        self.EvaluateButton = QPushButton('None',self)
        self.EvaluateButton.clicked.connect(self.evaluate)
        self.EvaluateButton.setGeometry(10,80,100,40)
        
        self.getOnePicButton = QPushButton('Get a frame',self)
        self.getOnePicButton.clicked.connect(self.ctrlSendone)
        self.getOnePicButton.setGeometry(10,130,100,40)
        self.getOnePicButton.setEnabled(False)  
        
        self.modeManualButton = QPushButton('Auto',self)
        self.modeManualButton.clicked.connect(self.modeManual)
        self.modeManualButton.setGeometry(10,180,100,40)

        self.modeObjButton = QPushButton('Body',self)
        self.modeObjButton.clicked.connect(self.objBody)
        self.modeObjButton.setGeometry(10,230,100,40)

        self.modeFpsButton = QPushButton('4FPS',self)
        self.modeFpsButton.clicked.connect(self.rate)
        self.modeFpsButton.setGeometry(10,280,100,40)

        self.modeAutoButton = QPushButton('Get offset',self)
        self.modeAutoButton.clicked.connect(self.commonOffset)
        self.modeAutoButton.setGeometry(570,30,100,40)
        
        self.modeAutoButton = QPushButton('Get version',self)
        self.modeAutoButton.clicked.connect(self.sysVer)
        self.modeAutoButton.setGeometry(570,80,100,40)

        self.evaluate = 1
        self.evaluateButton = QPushButton('Evaluate',self)
        self.evaluateButton.clicked.connect(self.setEvaluate)
        self.evaluateButton.setGeometry(570,120,100,40)

        self.serial_l  = QLabel(self)

        self.serial_l.move(580,250)
        self.serial_l.resize(60,30)
        self.serial_l.setStyleSheet("QLabel{color:rgb(0,0,0,255);background-color: rgb(255,255,255);font-size:16px;font-weight:normal;font-family:Arial;}")
        self.serial_l.setText("Serial:") 

        self.serialList  = SerialComboBox(self)
        self.serialList.setCurrentIndex(0) 
        self.serialList.setStyleSheet("border-width: 1px;border-style: solid;border-color: rgb(255, 170, 0);")
        self.serialList.currentIndexChanged.connect(self.serialChange)
        # self.evaluateButton.setGeometry(570,140,100,40)
        self.serialList.move(580,280)
        self.serialList.resize(120,30)
        self.serialList.addItem("Please select serial device")
        
    def checkSerial(self):
        reply = QMessageBox.information(self, 'No serial', "Please select serial device" , QMessageBox.Yes)


        # portlist = SerialComboBox().get_port_list(self)
        # self.userCom = None
        # if portlist is not None:
        #     for port in portlist:
        #         print("port ",port)
        #         self.userCom = port
        #     if self.userCom is not None :
        #         self.dataThread.openSerial(self.userCom)
        #     else:
        #         reply = QMessageBox.information(self, '没有设置串口', "请选择串口" , QMessageBox.Yes)


    def serialChange(self,i):
        print("serialChange",i,self.serialList.currentText())
        if i>0:
            self.userCom = self.serialList.currentText()
            self.dataThread.initSerialPort(self.userCom)

    def ctrlOpen(self):
        print("self.userCom",self.userCom)
        if self.userCom is None:
            self.checkSerial()
            return

        if self.open_status == 1:
            print('start send C command 0')
            self.open_status = 0

            self.ctrlOpenButton.setText("Open")
            self.dataThread.sendData('CMDC\0')
        else:
            print('start send C command 1')
            self.open_status = 1

            self.ctrlOpenButton.setText("Close")
            self.dataThread.sendData('CMDC\1')

    def evaluate(self):
        if self.userCom is None:
            self.checkSerial()
            return
        global evaluate_mode
        if evaluate_mode == "operate":
            print('start send E command 0')
            evaluate_mode = "evaluate"
            self.EvaluateButton.setText("Evaluate")
            self.dataThread.sendData('CMDE\1')
        else:
            print('start send E command 1')
            evaluate_mode = "operate"
            self.EvaluateButton.setText("Operate")
            self.dataThread.sendData('CMDE\0')

    def ctrlSendone(self):
        if self.userCom is None:
            self.checkSerial()
            return
        print('send a frame')
        self.dataThread.sendData('CMDC\2')

    def modeManual(self): 
        if self.userCom is None:
            self.checkSerial()
            return
        if self.mode == 1:     
            self.getOnePicButton.setEnabled(True) 
            self.modeManualButton.setText("Manual")
            self.dataThread.sendData('CMDM\0')
            self.mode = 0
            print('mode: manual') 
        else:

            self.getOnePicButton.setEnabled(False) 
            self.modeManualButton.setText("Auto")
            self.dataThread.sendData('CMDM\1')
            print('mode: auto') 
            self.mode = 1
    
    def modeAuto(self):
        if self.userCom is None:
            self.checkSerial()
            return
        print('mode: auto')  
        self.dataThread.sendData('CMDM\1')
    
    def rate(self):
        if self.userCom is None:
            self.checkSerial()
            return
        global btn_index
        btn_index = (btn_index+1)%5
        print('FPS:',strButton[btn_index]) 
        self.modeFpsButton.setText(strButton[btn_index])
        self.dataThread.sendData(strFpsCmd[btn_index]) #'CMDF\0')

    def objBody(self):
        if self.userCom is None:
            self.checkSerial()
            return
        if self.body == 1:
            self.body = 0
            print('obj: Object') 
            self.modeObjButton.setText("Object")
            self.dataThread.sendData('CMDO\0')
        else:
            self.body = 1
            print('obj: Human Body') 
            self.modeObjButton.setText("Body")
            self.dataThread.sendData('CMDO\1')
            
    def uiUpdate(self):
        global evaluate_mode
        print("update UI ",evaluate_mode)
        if evaluate_mode == "operate":
            self.EvaluateButton.setText("Operate")
        elif evaluate_mode == "evaluate":
            self.EvaluateButton.setText("Evaluate")
        else:
            self.EvaluateButton.setText("None")

    def cmdUpdate(self):
        if self.userCom is None:
            self.checkSerial()
            return
        print("get evaluate status and version\n")
        time.sleep(0.1)
        self.dataThread.sendData('CMDE\2')
        time.sleep(0.1)
        self.dataThread.sendData('CMDV\0') 
        time.sleep(0.1)
        self.dataThread.sendData('CMDT\1')

    def commonOffset(self):
        if self.userCom is None:
            self.checkSerial()
            return 
        self.dataThread.sendData('CMDT\1')
        print("Get commonOffset")

    def sysVer(self):
        if self.userCom is None:
            self.checkSerial()
            return
        self.dataThread.sendData('CMDV\1')
        print("Get firmware version and calibration version.")

    def setEvaluate(self):
        if self.userCom is None:
            self.checkSerial()
            return
        if self.evaluate == 1:
            self.evaluate = 0
            self.evaluateButton.setText("Operate")
            self.dataThread.sendData('CMDE\0')
        else:
            self.evaluate = 1
            self.evaluateButton.setText("Evaluate")
            self.dataThread.sendData('CMDE\1')

    def draw(self):
        global minHue
        global maxHue
        global maxHet
        global minHet
        global device_commonOffset
        global evaluate_mode
        if len(displayData) == 0:
            return
        font = QFont()
        color = QColor()
        font.setPointSize(self.fontSize)
        #font.setFamily("Microsoft YaHei")
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0)
        index = 0
        lock.acquire()
        frame = displayData.pop(0)
        lock.release()
        p = QPainter(self.cameraBuffer)
        p.fillRect(
                0, 0, self.width, 
                self.height + self.textLineHeight, 
                QBrush(QColor(Qt.black))
            )
        # draw camera
        color = QColor()
        cneter = 0.0
        if chip == "90640":
            if self.centerIndex == 0:
                centerIndex = 12*32+16
            for yIndex in range(int(self.height / self.pixelSize)):
                for xIndex in range(int(self.width / self.pixelSize)):
                    color.setHsvF(frame[index] / 360, 1.0, 1.0)
                    p.fillRect(
                        xIndex * self.pixelSize,
                        yIndex * self.pixelSize,
                        self.pixelSize, self.pixelSize,
                        QBrush(color)
                    )
                    index = index + 1
            cneter = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
        elif chip == "90621":
            if self.centerIndex == 0 or self.centerIndex>=64:
                self.centerIndex = 2*16+8

            cneter = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
            for yIndex in range(int(self.height / self.pixelSize/6)):
                for xIndex in range(int(self.width / self.pixelSize/2)):
                    color.setHsvF(frame[index] / 360, 1.0, 1.0)
                    p.fillRect(
                        xIndex * self.pixelSize*2,
                        yIndex * self.pixelSize*2+160,
                        self.pixelSize*2, self.pixelSize*2,
                        QBrush(color)
                    )
                    index = index + 1
        elif chip == "90641":
            if self.centerIndex == 0 or self.centerIndex>=192:
                self.centerIndex = 6*16+8

            cneter = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
            for yIndex in range(int(self.height / self.pixelSize/2)):
                for xIndex in range(int(self.width / self.pixelSize/2)):
                    color.setHsvF(frame[index] / 360, 1.0, 1.0)
                    p.fillRect(
                        xIndex * self.pixelSize*2,
                        yIndex * self.pixelSize*2,
                        self.pixelSize*2, self.pixelSize*2,
                        QBrush(color)
                    )
                    index = index + 1
        else:
            print("Dsiplay Error: can't detect any chip type!")

        self.cameraItem.setPixmap(self.cameraBuffer)
        self.frameCount = self.frameCount + 1
        
        # draw text
        p = QPainter(self.hetTextBuffer)
        p.fillRect(
                0, 0, self.width + 200, 
                self.height + self.textLineHeight, 
                QBrush(QColor(Qt.black))
            )

        version = self.dataThread.getID()
        p.setPen(QColor(Qt.white))
        p.setFont(font)
        p.drawText( 0, self.fontSize , " max:"+ '{:.2f}'.format(maxHet))
        p.drawText( self.textInterval, self.fontSize , " min:"+ '{:.2f}'.format(minHet))
        p.drawText( self.textInterval*2, self.fontSize , "offset:"+ '{:.2f}'.format(device_commonOffset))
        p.drawText( self.textInterval*3, self.fontSize , "mode:" + detect_status)
        p.drawText( self.textInterval*4, self.fontSize , evaluate_mode)
        p.drawText( self.textInterval*5, self.fontSize , "ID:"+str(version[0]))
        p.drawText( self.textInterval*6, self.fontSize , "ver:"+str(version[1]&0xff))
        p.drawText( self.textInterval*7, self.fontSize ,chip)
        self.hetTextItem.setPixmap(self.hetTextBuffer)
        cneter = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
        centerText = "<font color=white>%s</font>"
        self.centerTextItem.setFont(font)
        self.centerTextItem.setHtml(centerText % (str(cneter) + "°"))
        # draw version text
        self.versionTextItem.setFont(font)
        
        
def run():
    global minHue
    global maxHue
    global useBlur
    global narrowRatio
    global btn_index
    serialPort = ''
    narrowRatio =  1
    useBlur = True

    opts,args = getopt.getopt(sys.argv[1:],'p:i:a:n:ue',['port=','minhue=','maxhue=','evaluate','narrowratio','useblur'])
    print(opts)
    print(args)
    for name,value in opts:
        if name in ('-i','--minhue'):
            minHue = value
        elif name in ('-a','--maxhue'):
            maxHue = value
        elif name in ('-p', '--port'):
            serialPort = value
        elif name in ('-n','--narrowratio'):
            narrowRatio = int(value)

    for ar in args:
        if ar in ('e','--evaluate'):
            mode = 'evaluate'
        if ar in ('d','--disableblur'):
            useBlur = False
        
    
    # if serialPort == '':
    #     print('\n\nNo serial Port found,please declare the serial port\n\n \
    #           pointcloud_ircamera Usage: \n \
    #           \t%s -p,--port= <PortName>  [options]\n\n \
    #           option:\n \
    #           \t -e,--evaluate\n \
    #           \t -i,--minhue= <minhue>\n \
    #           \t -a,--maxhue= <maxhue>\n \
    #           \t -n,--narrowratio= <narrowratio>\n \
    #           \t -d,--disableblur')
    #     port_list = list(serial.tools.list_ports.comports())
    #     com_size = len(port_list) 
    #     print("com_size",com_size)

        # for port in port_list:
        #     print("com",port)
        #     print("port.vid",port.vid,"port.pid ",port.pid,"port.device",port.device)
        #     if(port.pid == 29987):
        #         serialPort = port.device
        #         break
        # if serialPort == '':
        #     print("No valid devie found !!!! ")
        #     exit(0)

    app = QApplication(sys.argv)
    dataThread = SerialDataHandler()
    window = painter(dataThread)
    dataThread.drawRequire.connect(window.draw)
    dataThread.uiRequire.connect(window.uiUpdate)
    dataThread.cmdRequire.connect(window.cmdUpdate)
    dataThread.start()
    window.show()
    app.exec_()

