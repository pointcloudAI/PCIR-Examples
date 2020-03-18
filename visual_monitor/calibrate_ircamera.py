'''
@功能: 
@Author: swortain
@Date: 2020-03-02 16:45:38
@LastEditTime: 2020-03-16 17:32:05
'''

import sys
import getopt
import threading
import math
import struct
from serial import Serial
import serial.tools.list_ports
import serial.tools.miniterm as miniterm

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
        QMessageBox,
        QLineEdit

    )

from PyQt5.QtGui import QPainter, QBrush, QColor, QFont, QPixmap
from PyQt5.QtCore import QThread, QObject, pyqtSignal, QPointF, Qt



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


hetaData = []
btn_index = 3
strButton = ["1/2fps","1fps","2fps","3fps"]
strFpsCmd = ['CMDF\0','CMDF\1','CMDF\2','CMDF\3']
calibrateStr = ["开始校准","结束校准"]
maxHet = 0
minHet = 0
lock = threading.Lock()
minHue = 90
maxHue = 360
dataThread = None
#mode = 'operate' # 
mode = 'evaluate'
useBlur = False
narrowRatio = 1
calibration_start = False 
calibration_max_list = [] 
calibration_list_limit = 8
blackbody_temperature = 37
calibration_offset = 0
calibration_frame_count = 0 



class SerialDataHandler(QThread):
    drawRequire = pyqtSignal()
    calibrateFinish = pyqtSignal()
    def __init__(self, port):
        super(SerialDataHandler, self).__init__()
        self.port = port
        self.com = Serial(self.port, 230400, timeout=5)
        # self.com = Serial(self.port, 115200, timeout=5)
        print("SerialDataHandler:",self.port,460800)
        # print("SerialDataHandler:",self.port,115200)
        self.frameCount = 0

    def send_data(self,s): # send cmd to mcu with serial
        crc = 0
        for i in range(0,len(s)):
            crc = crc + ord(s[i])
        crc = crc & 0xFF
        s += chr(crc)
        self.com.write(s.encode('utf-8'))

    def perfomr_calibration(self,currentMaxValue):
        global blackbody_temperature 
        global calibration_list_limit
        global calibration_max_list
        global calibration_start
        global calibration_offset
        global calibration_frame_count

        if calibration_start:
            calibration_frame_count +=1 
            calibration_max_list.append(currentMaxValue)
            if (len(calibration_max_list) >= 8 ):
                list_max = max(calibration_max_list)
                list_min = min(calibration_max_list)
                # print("list_max",list_max,"list_max",list_min,"diff ",list_max - list_min)
                if (list_max - list_min <=0.1):
                    calibration_start = False
                    calibration_offset = blackbody_temperature - list_max
                    print("calibration_offset",calibration_offset)
                    self.calibrateFinish.emit() 
                del calibration_max_list[0]
            if (calibration_frame_count > 90):
                calibration_start = False
                self.calibrateFinish.emit() 
           

    def run(self):
        
        global maxHet
        global minHet
        global calibration_start

        if mode == 'evaluate': # evluate mode
            # throw first frame
            self.com.read_until(terminator=b'\r\n')
            while True:
                print('1 frame')
                hetData = self.com.read_until(terminator=b'\r\n')
                hetData = str(hetData, encoding="utf8").split(",")            
                hetData = hetData[:-1]

                print(len(hetData))
                if  len(hetData) < 768 :
                    continue
                
                tempData = []
                nanCount = 0
                maxHet = 0
                minHet = 500
                currentMaxValue = 0
                zone1_y_begin = 4
                zone1_y_end = 19
                zone1_x_begin = 8
                zone1_x_end = 23
                
                for i in range(0, 768):
                    curCol = i % 32
                    newValueForNanPoint = 0
                

                    # if i < len(hetData) and isDigital(hetData[i]):
                    if i < len(hetData) and isDigital(hetData[i]):
                        tempData.append(float(hetData[i]))
                        maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                        minHet = tempData[i] if tempData[i] < minHet else minHet
                   
                        
                    else:
                        interpolationPointCount = 0
                        sumValue = 0

                        abovePointIndex = i-32
                        if (abovePointIndex>0):
                            
                            if  hetData[abovePointIndex] != 'nan':
                                interpolationPointCount += 1
                                sumValue += float(hetData[abovePointIndex])

                        belowPointIndex = i+32
                        if (belowPointIndex<768):
                            if  hetData[belowPointIndex] != 'nan':
                                interpolationPointCount += 1
                                sumValue += float(hetData[belowPointIndex])
                                
                        leftPointIndex = i -1
                        if (curCol != 31):
                            if  hetData[leftPointIndex] != 'nan':
                                interpolationPointCount += 1
                                sumValue += float(hetData[leftPointIndex])

                        rightPointIndex = i + 1
                        if (belowPointIndex<768):
                            if (curCol != 0):
                                if  hetData[rightPointIndex] != 'nan':
                                    interpolationPointCount += 1
                                    sumValue += float(hetData[rightPointIndex])

                        newValueForNanPoint =  sumValue /interpolationPointCount
                    
                        # For debug :
                        # print(abovePointIndex,belowPointIndex,leftPointIndex,rightPointIndex)
                        # print("newValueForNanPoint",newValueForNanPoint," interpolationPointCount" , interpolationPointCount ,"sumValue",sumValue)
                        
                        tempData.append(newValueForNanPoint)
                        nanCount +=1
                    curValue = tempData[i]

                    curRow = int(i/32)
                    if (curCol>= zone1_x_begin and curCol<=zone1_x_end and curRow >= zone1_y_begin and curRow<= zone1_y_end):
                        currentMaxValue = max(currentMaxValue,tempData[i]) # get max value on this frame zone1 for calibration
                        # print("curRow ",curRow,"curCol",curCol)

                # map value to 180-360
                if maxHet == 0:
                    print('maxHet == 0')
                    continue
                
                for i in range(len(tempData)):
                   tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)
                self.perfomr_calibration(currentMaxValue)
                lock.acquire()
                hetaData.append(tempData)
                lock.release()
                self.drawRequire.emit()
                self.frameCount = self.frameCount + 1
                print("data->" + str(self.frameCount))
                
        else: # operator mode
            while True:
                hetData = self.com.read_until(terminator=b'\r\n')
                if hetData[:3] != b'DAT':
                    print(hetData)
                else:
                    hetData = hetData[3:]
                    dataLen = int.from_bytes(hetData[:2],byteorder='big',signed=False)
                    hetData = hetData[2:]
                    if hetData[-2:] != b'\r\n':
                        continue
                    hetData = hetData[:-2]


                    Ta = struct.unpack('1f',hetData[:4])
                    print('TA = %f\n'%Ta)
                    hetData = hetData[4:]

                    
                    if 4*dataLen == len(hetData):
                        tempData = struct.unpack(str(dataLen)+'f',hetData)
                        tempData = list(tempData)
                            
                        # map value to 180-360
                        maxHet = 0
                        minHet = 500
                        currentMaxValue = 0
                        # print(tempData)
                        for i in range(len(tempData)):
                            maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                            minHet = tempData[i] if tempData[i] < minHet else minHet

                            if math.isnan(tempData[i]):
                                print('got a nan')

                                curCol = i % 32
                                newValueForNanPoint = 0
                                
                                interpolationPointCount = 0
                                sumValue = 0

                                abovePointIndex = i-32
                                if (abovePointIndex>0):
                                    if not math.isnan(hetData[abovePointIndex]):
                                        interpolationPointCount += 1
                                        sumValue += float(hetData[abovePointIndex])

                                belowPointIndex = i+32
                                if (belowPointIndex<768):
                                    print(" ")
                                    if not math.isnan(hetData[belowPointIndex]) :
                                        interpolationPointCount += 1
                                        sumValue += float(hetData[belowPointIndex])
                                        
                                leftPointIndex = i -1
                                if (curCol != 31):
                                    if not math.isnan(hetData[leftPointIndex] ):
                                        interpolationPointCount += 1
                                        sumValue += float(hetData[leftPointIndex])

                                rightPointIndex = i + 1
                                if (belowPointIndex<768):
                                    if (curCol != 0):
                                        if not math.isnan(hetData[rightPointIndex]):
                                            interpolationPointCount += 1
                                            sumValue += float(hetData[rightPointIndex])

                                newValueForNanPoint =  sumValue /interpolationPointCount
                                tempData[i] = newValueForNanPoint
                                
                        for i in range(len(tempData)):
                            tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)
                        lock.acquire()
                        hetaData.append(tempData)
                        lock.release()
                        self.drawRequire.emit()
                        self.frameCount = self.frameCount + 1
                        print("data->" + str(self.frameCount))
            
class painter(QGraphicsView):
    pixelSize = int(15 / narrowRatio)
    width = int (480 / narrowRatio)
    height = int(360 / narrowRatio)
    fontSize = int(30 / narrowRatio)
    anchorLineSize = int(100 / narrowRatio)
    ellipseRadius = int(8 / narrowRatio)
    textInterval = int(90 / narrowRatio)
    col = width / pixelSize
    line = height / pixelSize
    centerIndex = int(round(((line / 2 - 1) * col) + col / 2))
    frameCount = 0
    baseZValue = 0
    mode = 1
    body = 1
    open_status = 0
    textLineHeight = fontSize + 10
    blurRaduis = 50  # Smoother improvement
    def __init__(self,dataThread):
        super(painter, self).__init__()
        self.dataThread = dataThread
        self.setFixedSize(self.width, self.height + self.textLineHeight)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        # center het text item
        self.centerTextItem = QGraphicsTextItem()
        self.centerTextItem.setPos(self.width / 2 - self.fontSize, 0)
        self.centerTextItem.setZValue(self.baseZValue + 1)
        self.scene.addItem(self.centerTextItem)
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
        self.cameraItem.setPos(0, 0)
        self.cameraItem.setZValue(self.baseZValue)
        self.scene.addItem(self.cameraItem)
        # het text item
        self.hetTextBuffer = QPixmap(self.width, self.textLineHeight)
        self.hetTextItem = QGraphicsPixmapItem()
        self.hetTextItem.setPos(0, self.height)
        self.hetTextItem.setZValue(self.baseZValue)
        self.scene.addItem(self.hetTextItem)
        # button item
        self.ctrlOpenButton = QPushButton('Open',self)
        self.ctrlOpenButton.clicked.connect(self.ctrl_open)
        self.ctrlOpenButton.setGeometry(10,30,100,40)
        '''
        self.ctrlCloseButton = QPushButton('stop send',self)
        self.ctrlCloseButton.clicked.connect(self.ctrl_close)
        self.ctrlCloseButton.setGeometry(10,80,100,40)
        '''
        self.getOnePicButton = QPushButton('send a frame',self)
        self.getOnePicButton.clicked.connect(self.ctrl_sendone)
        self.getOnePicButton.setGeometry(10,130,100,40)
        self.getOnePicButton.setEnabled(False)  
        
        self.modeManualButton = QPushButton('Auto',self)
        self.modeManualButton.clicked.connect(self.mode_manual)
        self.modeManualButton.setGeometry(10,180,100,40)

        self.modeObjButton = QPushButton('Body',self)
        self.modeObjButton.clicked.connect(self.obj_body)
        self.modeObjButton.setGeometry(10,230,100,40)
        '''
        self.modeAutoButton = QPushButton('mode: auto',self)
        self.modeAutoButton.clicked.connect(self.mode_auto)
        self.modeAutoButton.setGeometry(10,230,100,40)
        '''
        self.modeFpsButton = QPushButton('3fps',self)
        self.modeFpsButton.clicked.connect(self.rate_0)
        self.modeFpsButton.setGeometry(10,280,100,40)

        self.blackbodyEdit  = QLineEdit()
        self.blackbodyEdit.setGeometry(270,200,100,40)
        self.blackbodyEdit.setText('37')


        self.calibrateButton = QPushButton(calibrateStr[0],self)
        self.calibrateButton.clicked.connect(self.calibrate_handle)
        self.calibrateButton.setGeometry(370,280,100,40)


        


        '''
        self.modeAutoButton = QPushButton('1fps',self)
        self.modeAutoButton.clicked.connect(self.rate_1)
        self.modeAutoButton.setGeometry(35,280,50,40)

        self.modeAutoButton = QPushButton('2fps',self)
        self.modeAutoButton.clicked.connect(self.rate_2)
        self.modeAutoButton.setGeometry(60,280,50,40)

        self.modeAutoButton = QPushButton('3fps',self)
        self.modeAutoButton.clicked.connect(self.rate_3)
        self.modeAutoButton.setGeometry(85,280,50,40)
        '''

        
        '''
        self.modeAutoButton = QPushButton('obj: common',self)
        self.modeAutoButton.clicked.connect(self.obj_common)
        self.modeAutoButton.setGeometry(370,80,100,40)
        '''
        # self.modeAutoButton = QPushButton('version',self)
        # self.modeAutoButton.clicked.connect(self.sys_ver)
        # self.modeAutoButton.setGeometry(370,230,100,40)
    
    def ctrl_open(self):
        if self.open_status == 1:
            print('start send C command 0')
            self.open_status = 0

            self.ctrlOpenButton.setText("Open")
            self.dataThread.send_data('CMDC\0')
        else:
            print('start send C command 1')
            self.open_status = 1

            self.ctrlOpenButton.setText("Close")
            self.dataThread.send_data('CMDC\1')
    '''
    def ctrl_close(self):
        print('stop send')
        self.dataThread.send_data('CMDC\0')
    '''
    def ctrl_sendone(self):
        print('send a frame')
        self.dataThread.send_data('CMDC\2')

    def mode_manual(self): 
        if self.mode == 1:     
            self.getOnePicButton.setEnabled(True) 
            self.modeManualButton.setText("Manual")
            self.dataThread.send_data('CMDM\0')
            self.mode = 0
            print('mode: manual') 
        else:

            self.getOnePicButton.setEnabled(False) 
            self.modeManualButton.setText("Auto")
            self.dataThread.send_data('CMDM\1')
            print('mode: auto') 
            self.mode = 1
    
    def mode_auto(self):
        print('mode: auto')  
        self.dataThread.send_data('CMDM\1')

    def stop_calibration(self):
        global calibration_offset
        calibration_start = False;
        self.calibrateButton.setText(calibrateStr[0])
        if(calibration_frame_count):
            reply = QMessageBox.information(self, '信息', '校准很久都不行，模组是否没有预热20分钟呢？', QMessageBox.Yes)
        else:
            reply = QMessageBox.information(self, '信息', '校准已完成', QMessageBox.Yes)

    def calibrate_handle(self):
        global calibration_start
        global calibration_max_list
        global blackbody_temperature
        if calibration_start:
            calibration_start = False;
            self.calibrateButton.setText(calibrateStr[0])
        else: 
            calibration_max_list.clear()
            blackbody_temperature =  float(self.blackbodyEdit.text())
            calibration_start = True;
            print(" blackbody_temperature ",blackbody_temperature)
            self.calibrateButton.setText(calibrateStr[1])
    
    def rate_0(self):
        global btn_index
        btn_index = (btn_index+1)%4
        print('FPS:',strButton[btn_index]) 
        self.modeFpsButton.setText(strButton[btn_index])
        self.dataThread.send_data(strFpsCmd[btn_index]) #'CMDF\0')
    '''
    def rate_1(self):
        print('FPS：1') 
        self.dataThread.send_data('CMDF\1')
    def rate_2(self):
        print('FPS：2') 
        self.dataThread.send_data('CMDF\2')
    def rate_3(self):
        print('FPS：3') 
        self.dataThread.send_data('CMDF\3')
    '''
    def obj_body(self):
        if self.body == 1:
            self.body = 0
            print('obj: Object') 
            self.modeObjButton.setText("Object")
            self.dataThread.send_data('CMDO\0')
        else:
            self.body = 1
            print('obj: Human Body') 
            self.modeObjButton.setText("Body")
            self.dataThread.send_data('CMDO\1')
    '''
    def obj_common(self):
        print('obj: common') 
        self.dataThread.send_data('CMDO\1')
    def sys_slp(self):
        print('sleep')
        self.dataThread.send_data('CMDS\1')
    '''
    

    def draw(self):
        if len(hetaData) == 0:
            return
        font = QFont()
        color = QColor()
        font.setPointSize(self.fontSize)
        font.setFamily("Microsoft YaHei")
        font.setLetterSpacing(QFont.AbsoluteSpacing, 0)
        index = 0
        lock.acquire()
        frame = hetaData.pop(0)
        lock.release()
        p = QPainter(self.cameraBuffer)
        p.fillRect(
                0, 0, self.width, 
                self.height + self.textLineHeight, 
                QBrush(QColor(Qt.black))
            )
        # draw camera
        color = QColor()
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
        self.cameraItem.setPixmap(self.cameraBuffer)
        # draw text
        p = QPainter(self.hetTextBuffer)
        p.fillRect(
                0, 0, self.width, 
                self.height + self.textLineHeight, 
                QBrush(QColor(Qt.black))
            )
        hetDiff = maxHet - minHet
        bastNum = round(minHet)
        interval = round(hetDiff / 5)
        for i in range(5):
            hue = constrain(mapValue((bastNum + (i * interval)), minHet, maxHet, minHue, maxHue), minHue, maxHue)
            color.setHsvF(hue / 360, 1.0, 1.0)
            p.setPen(color)
            p.setFont(font)
            p.drawText(i * self.textInterval, self.fontSize + 3, str(bastNum + (i * interval)) + "°")
        self.hetTextItem.setPixmap(self.hetTextBuffer)
        # draw center het text
        cneter = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
        centerText = "<font color=white>%s</font>"
        self.centerTextItem.setFont(font)
        self.centerTextItem.setHtml(centerText % (str(cneter) + "°"))
        self.frameCount = self.frameCount + 1
        print("picture->"+str(self.frameCount))


def run():
    global minHue
    global maxHue
    global mode
    global useBlur
    global narrowRatio
    global btn_index

    serialPort = ''
    narrowRatio =  1
    useBlur = True


    # if len(sys.argv) < 2:
    #     print("pointcloud_ircamera Usage: %s PortName [minHue] [maxHue] [NarrowRatio] [UseBlur]" % sys.argv[0])
    #     exit(0)

    # if len(sys.argv) >= 4:
    #     minHue = int(sys.argv[2])
    #     maxHue = int(sys.argv[3])

    
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
        
    
    if serialPort == '':
        print('\n\nNo serial Port found,please declare the serial port\n\n \
              pointcloud_ircamera Usage: \n \
              \t%s -p,--port= <PortName>  [options]\n\n \
              option:\n \
              \t e,--evaluate\n \
              \t -i,--minhue= <minhue>\n \
              \t -a,--maxhue= <maxhue>\n \
              \t -n,--narrowratio= <narrowratio>\n \
              \t d,--disableblur')
        exit(0)

    print("...............pointcloud_ircamera..................")
    
    app = QApplication(sys.argv)
    
    dataThread = SerialDataHandler(serialPort)
    window = painter(dataThread)
    dataThread.drawRequire.connect(window.draw)
    dataThread.calibrateFinish.connect(window.stop_calibration)
    dataThread.start()
    window.show()
    app.exec_()

if __name__ == '__main__':
    run()

