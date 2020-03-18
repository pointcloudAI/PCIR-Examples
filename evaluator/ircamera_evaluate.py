import sys
import threading
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
        QGraphicsBlurEffect
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
maxHet = 0
minHet = 0
lock = threading.Lock()
minHue = 90
maxHue = 360
chip_type = 'mlx90640'


class SerialDataReader(QThread):
    drawRequire = pyqtSignal()
    def __init__(self, port):
        super(SerialDataReader, self).__init__()
        self.port = port
        #self.com = Serial(self.port, 460800, timeout=5)
        #self.com = Serial(self.port, 115200, timeout=5)
        self.com = Serial(self.port, baud_rate, timeout=5)
        print("SerialDataReader:",self.port,baud_rate)
        self.frameCount = 0

    def paser_data(self,vecData,data_len = 768,data_width = 32):
        global maxHet
        global minHet
        print("paser_data.............data:",len(vecData)," data_len:",data_len," data_width:",data_width)
        if  len(vecData) < data_len :
            return

        maxHet = 0
        minHet = 500
        tempData = []
        for i in range(0, data_len):
            curCol = i % data_width
            newValueForNanPoint = 0

            if i < len(vecData) and isDigital(vecData[i]):
                tempData.append(float(vecData[i]))
                maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                minHet = tempData[i] if tempData[i] < minHet else minHet
            else:
                interpolationPointCount = 0
                sumValue = 0
                # print("curCol",curCol,"i",i)

                abovePointIndex = i-data_width
                if (abovePointIndex>0):
                    if vecData[abovePointIndex] is not "nan" :
                        interpolationPointCount += 1
                        sumValue += float(vecData[abovePointIndex])

                belowPointIndex = i+data_width
                if (belowPointIndex<data_len):
                    print(" ")
                    if vecData[belowPointIndex] is not "nan" :
                        interpolationPointCount += 1
                        sumValue += float(vecData[belowPointIndex])
                        
                leftPointIndex = i -1
                if (curCol != data_width - 1):
                    if vecData[leftPointIndex]  is not "nan" :
                        interpolationPointCount += 1
                        sumValue += float(vecData[leftPointIndex])

                rightPointIndex = i + 1
                if (belowPointIndex<data_len):
                    if (curCol != 0):
                        if vecData[rightPointIndex] is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(vecData[rightPointIndex])

                newValueForNanPoint =  sumValue /interpolationPointCount
               
                # For debug :
                # print(abovePointIndex,belowPointIndex,leftPointIndex,rightPointIndex)
                # print("newValueForNanPoint",newValueForNanPoint," interpolationPointCount" , interpolationPointCount ,"sumValue",sumValue)
                
                tempData.append(newValueForNanPoint)
                nanCount +=1
    
        if maxHet == 0:
            return
        # For debug :
        
        # map value to 180-360

        #print("display_mlx90640.......................minHet:",minHet," maxHet:",maxHet," len:",len(tempData))    
        for i in range(len(tempData)):
            tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)
        lock.acquire()
        hetaData.append(tempData)
        lock.release()
        self.drawRequire.emit()
        self.frameCount = self.frameCount + 1

    def display_mlx90641(self,vecData):
        if  len(vecData) < 192 :
            return

        for i in range(0, 192):
            curCol = i % 16
            newValueForNanPoint = 0

            if i < len(vecData) and isDigital(vecData[i]):
                tempData.append(float(vecData[i]))
                maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                minHet = tempData[i] if tempData[i] < minHet else minHet
            else:
                interpolationPointCount = 0
                sumValue = 0
                # print("curCol",curCol,"i",i)

                abovePointIndex = i-16
                if (abovePointIndex>0):
                    if vecData[abovePointIndex] is not "nan" :
                        interpolationPointCount += 1
                        sumValue += float(vecData[abovePointIndex])

                belowPointIndex = i+16
                if (belowPointIndex<192):
                    print(" ")
                    if vecData[belowPointIndex] is not "nan" :
                        interpolationPointCount += 1
                        sumValue += float(vecData[belowPointIndex])
                        
                leftPointIndex = i -1
                if (curCol != 15):
                    if vecData[leftPointIndex]  is not "nan" :
                        interpolationPointCount += 1
                        sumValue += float(vecData[leftPointIndex])

                rightPointIndex = i + 1
                if (belowPointIndex<192):
                    if (curCol != 0):
                        if vecData[rightPointIndex] is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(vecData[rightPointIndex])

                newValueForNanPoint =  sumValue /interpolationPointCount
               
                # For debug :
                # print(abovePointIndex,belowPointIndex,leftPointIndex,rightPointIndex)
                # print("newValueForNanPoint",newValueForNanPoint," interpolationPointCount" , interpolationPointCount ,"sumValue",sumValue)
                
                tempData.append(newValueForNanPoint)
                nanCount +=1
        if maxHet == 0:
            return
        # For debug :
        
        # map value to 180-360
        for i in range(len(tempData)):
            tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)
        lock.acquire()
        vecData.append(tempData)
        lock.release()
        self.drawRequire.emit()
        self.frameCount = self.frameCount + 1

    def run(self):
        #global maxHet
        #global minHet
        # throw first frame
        self.com.read_until(terminator=b'\r\n')
        while True:
            hetData = self.com.read_until(terminator=b'\r\n')
            hetData = str(hetData, encoding="utf8").split(",")     
            #hetData = str(hetData, encoding="ascii").split(",")             
            hetData = hetData[:-1]
            #maxHet = 0
            #minHet = 500
            #tempData = []
            nanCount = 0
            print("data length:",len(hetData))
            data_len = 768
            data_width = 32
            if chip_type == 'mlx90641':
                data_len = 192
                data_width = 16

            self.paser_data(hetData,data_len,data_width)
            '''
            if  len(hetData) < 768 :
                continue

            for i in range(0, 768):
                curCol = i % 32
                newValueForNanPoint = 0

                if i < len(hetData) and isDigital(hetData[i]):
                    tempData.append(float(hetData[i]))
                    maxHet = tempData[i] if tempData[i] > maxHet else maxHet
                    minHet = tempData[i] if tempData[i] < minHet else minHet
                else:
                    interpolationPointCount = 0
                    sumValue = 0
                    # print("curCol",curCol,"i",i)

                    abovePointIndex = i-32
                    if (abovePointIndex>0):
                        if hetData[abovePointIndex] is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(hetData[abovePointIndex])

                    belowPointIndex = i+32
                    if (belowPointIndex<768):
                        print(" ")
                        if hetData[belowPointIndex] is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(hetData[belowPointIndex])
                            
                    leftPointIndex = i -1
                    if (curCol != 31):
                        if hetData[leftPointIndex]  is not "nan" :
                            interpolationPointCount += 1
                            sumValue += float(hetData[leftPointIndex])

                    rightPointIndex = i + 1
                    if (belowPointIndex<768):
                        if (curCol != 0):
                            if hetData[rightPointIndex] is not "nan" :
                                interpolationPointCount += 1
                                sumValue += float(hetData[rightPointIndex])

                    newValueForNanPoint =  sumValue /interpolationPointCount
                   
                    # For debug :
                    # print(abovePointIndex,belowPointIndex,leftPointIndex,rightPointIndex)
                    # print("newValueForNanPoint",newValueForNanPoint," interpolationPointCount" , interpolationPointCount ,"sumValue",sumValue)
                    
                    tempData.append(newValueForNanPoint)
                    nanCount +=1
            if maxHet == 0:
                continue
            # For debug :
            
            # map value to 180-360
            for i in range(len(tempData)):
                tempData[i] = constrain(mapValue(tempData[i], minHet, maxHet, minHue, maxHue), minHue, maxHue)
            lock.acquire()
            hetaData.append(tempData)
            lock.release()
            self.drawRequire.emit()
            self.frameCount = self.frameCount + 1
            #print("data->" + str(self.frameCount))
            '''
        self.com.close()

class painter(QGraphicsView):
    narrowRatio = 1 #int(sys.argv[6]) if len(sys.argv) >= 6 else 1
    useBlur = True #sys.argv[5] != "False" if len(sys.argv) >= 7 else True
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
    textLineHeight = fontSize + 10
    blurRaduis = 50  # Smoother improvement
    def __init__(self):
        super(painter, self).__init__()

        if chip_type == 'mlx90641':
            self.width = int (240 / self.narrowRatio)
            self.height = int(180 / self.narrowRatio)
            self.col = self.width / self.pixelSize
            self.line = self.height / self.pixelSize
            self.centerIndex = int(round(((self.line / 2 - 1) * self.col) + self.col / 2))
            self.fontSize = int(15 / self.narrowRatio)
            self.anchorLineSize = int(50 / self.narrowRatio)
            self.ellipseRadius = int(4 / self.narrowRatio)
            self.textInterval = int(45 / self.narrowRatio)
            self.textLineHeight = self.fontSize + 5
            self.blurRaduis = 25

        print("painter width:",self.width," height:",self.height," pixelSize:",self.pixelSize," col:",self.col," line:",self.line)
    
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
        if self.useBlur:
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

        print("picture->"+str(self.frameCount)+" minHet:",minHet," maxHet:",maxHet," hetDiff:",hetDiff," bastNum:",bastNum," interval:",interval)    
        for i in range(5):
            hue = constrain(mapValue((bastNum + (i * interval)), minHet, maxHet, minHue, maxHue), minHue, maxHue)
            color.setHsvF(hue / 360, 1.0, 1.0)
            p.setPen(color)
            p.setFont(font)
            p.drawText(i * self.textInterval, self.fontSize + 3, str(bastNum + (i * interval)) + "°")
        self.hetTextItem.setPixmap(self.hetTextBuffer)
        # draw center het text
        center = round(mapValue(frame[self.centerIndex], minHue, maxHue, minHet, maxHet), 1)
        centerText = "<font color=white>%s</font>"
        self.centerTextItem.setFont(font)
        self.centerTextItem.setHtml(centerText % (str(center) + "°"))
        self.frameCount = self.frameCount + 1



if __name__ == '__main__':
    #global minHue
    #global maxHue
    #global baud_rate 
    #global chip_type
    baud_rate = 230400
    if len(sys.argv) < 2:
        print("pointcloud_ircamera Usage: %s PortName  [chip_type=mlx90640|mlx90641] [baud_rate] [minHue] [maxHue] [NarrowRatio] [UseBlur]" % sys.argv[0])
        exit(0)

    if len(sys.argv) == 3:
        chip_type = sys.argv[2]

    if len(sys.argv) == 4:
        baud_rate = int(sys.argv[3])

    if len(sys.argv) >= 5:
        chip_type = int(sys.argv[2])
        baud_rate = sys.argv[3]
        minHue = int(sys.argv[4])
        maxHue = int(sys.argv[5])

    print("ircamera ",sys.argv[1],"  baud_rate:",baud_rate," chip_type:",chip_type," minHue:",minHue," maxHue:",maxHue)
    app = QApplication(sys.argv)
    window = painter()
    dataThread = SerialDataReader(sys.argv[1])
    dataThread.drawRequire.connect(window.draw)
    dataThread.start()
    window.show()
    app.exec_()

