 #  PCIR-Examples
 
 ## Description
 
 The project is powered by PointCloud.Ai. It's demo of PCIR-xxCx series consist of python's examples on computer and java's examples on android phone.These product compatible with melexis IR sensors MLX90640,MLX90641 and MLX90621.
 
 1. python on computer: [Python Example](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/visual_monitor)  command line：python ir_demo.py serialPort [serial Baud rate]
 
    example: `python3 ir_demo.py /dev/cu.usbserial-1410`(/dev/cu.usbserial-1410 should replaced by your serial port which named like COMx on windows or /dev/cu.xxxxx on OSX)
 
 2. java on android: [Android Example](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/android_visual_monitor)
 
 ## Performance
 
  **1. product** 

![MLX90640_1](https://images.gitee.com/uploads/images/2020/0324/182357_9950db7a_5484807.png "90640_board.png")
![MLX90640_2](https://images.gitee.com/uploads/images/2020/0324/181221_ca126112_5484807.png "90640_board.png")

  **2. development kit**
1.   Install CH340 driver on system ([serial to usb driver](http://www.wch.cn/downloads/category/30.html)).
2.   Plug type-c connector to device and host pc. 
3.   Install python3 environment and pySerial(use pip tool).
3.   Run Visual monitor on host PC.
This Development Kit help customer evaluate the performance on Window,Mac or Ubuntu system.

![DevKit](https://images.gitee.com/uploads/images/2020/0324/182443_5826c56b_5484807.png "90640_devkit.png")

  **2. running Visual Monitor Demo** 

this demo demonstrator how to send command to device and handle result from device, also illustrator how to process data frame on host.
 ## Python source code [visual monitor](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/visual_monitor)

 ![Visual Monitor for MLX90640](https://images.gitee.com/uploads/images/2020/0317/230625_d4215c52_5484807.png "visual_monitor.png")

## Document

1.    [Serial command list](https://gitee.com/pointcloudai/PCIR-Examples/blob/master/Doc/200313PCIR-xxCx%20series%E6%8C%87%E4%BB%A4%E6%89%8B%E5%86%8C%20v1.4.pdf)
2.    [PCIR series datasheet](https://gitee.com/pointcloudai/PCIR-Examples/blob/master/Doc/%E4%BA%A7%E5%93%81%E8%A7%84%E6%A0%BC%E4%B9%A6.pdf)
3.    [Hardware design](https://gitee.com/pointcloudai/PCIR-Examples/blob/master/Doc/PCIR-40C%E7%A1%AC%E4%BB%B6%E4%BD%BF%E7%94%A8%E6%8C%87%E5%8D%97.pdf)
4.    [Board size describe](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/Doc)

## Interface
 
 1. interface: UART
 2. Baud Rate:  **230400**  [firmware ver1.0 baud rate:460800]
 
## Data Frame
 
### Evaluate Mode
 this mode is for customer evaluate temperature precision result if suitable for their product as soon as possible.
 
 1. After power on, module will output the ASCII temperature data, each frame ends with `\r\n` on 3FPS.
 
 2. Output resolution of PCIR-40CA/PCIR-40CB is 32x24.
 
 3. temperature data of each point is float with 2 decimal places. Row precedence.
 
 4. example: a frame = 32x24(768 points' data) 
 
    ​	\r\n36.01,35.02,34.03....................37.01,36.21,36.01,35.02,34.03\r\n
 
### Operate Mode
 
 this mode is for integrate to product, Data format is following:
      data frame format:  'DAT' + Data Bytes Length[2 bytes] + Envirment Temp[4 Bytes float type] + data[pixelx4bytes float] + '/r/n'

     example mlx90640 32x24 pixel:
     3Bytes + 2Byte + 4Bytes + 32X24X4 + 2Bytes = 3083Bytes
	 example mlx90641 16x12 pixel:
     3Bytes + 2Byte + 4Bytes + 16X12X4 + 2Bytes = 779Bytes
 
## Command List:
**a typical use is following line:** 

    Send setting command 'CMDE\0\0' 
    Send setting command 'CMDF\2\0'
    Send open command 'CMDC\1\0'
    Parser receive data 'DAT',validate data Length equal to sensor pixel and frame end '\r\n'.
  
 1.    CAMMAND LIST  6BYTE = 'CMD'+Type[1Byte]+Value[1Byte]+CRC[1Byte].Except Evavluate command 9 BYTES
 
     Open     command:  Type = C  Value = [1-open | 0-close | 2- 1 Frame if Mode command ==0]
     Mode     command:  Type = M  Value = [0-receive frame manual | 1-receiver frame continuous]
     Object   command:  Type = O  value = [1-body measure| 0-object measure]
     Freq     command:  Type = F  Value = [0-1/2fps | 1-1fps | 2-2fps | 3-3fps | 4-4fps]
     Version  command:  Type = V  Value = [0]
     Evaluate command:  Type = E  Value = [ 0-Operate mode | 1- Evaluate mode | 2- get Evaluate mode status]
     (When you set evaluate command, this status will save to rom to keep the status after reboot)
    Offset get  command:  Type = T  Value = [0-get common offset]
    Offset set  command: this command have 9BYTE= 'CMDE'+Value[4Byte float format]+CRC[1Byte].
    (When you set offset command, this status will save to rom to keep the status after reboot)

2.    Command Result List:  'RETCMD + Type[1Byte] + Value[multiple Byte] + '\r\n'

     Open     result:   'RET' + Open Command[6 bytes] + '\r\n'
     Mode     result:   'RET' + Mode Command[6 bytes] + '\r\n'
     Object   result:   'RET' + Object Command[6 bytes] + '\r\n'
     Freq     result:   'RET' + Freq Command[6 bytes] + '\r\n'
     Version  result:   'RETCMDV' + firmware version[4 bytes] + ',' + calibrate version[4 bytes] + '\r\n'
     Evaluate command:  'RETCMDE' + type[1 bytes] + '\r\n'
     Offset   command:  'RETCMDT' + common offset[6 bytes] + '\r\n' 

3.    Error command Result: 'RETERR' + command[6 bytes] + '\r\n'

 ## Calibration

the difference distance need calibration for accurate body temperature measurement. we offer calibration file to adjust actual temperature value suitable for real environment.  **for use calibration tools you maybe install**  [esp32-idf framework](https://docs.espressif.com/projects/esp-idf/en/stable/get-started/)

1.    src [src code](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/calibration)
2.    calibration file: data/cali.dat there have two line. following is file structure of cali.dat ( **file name Can not be change** )

    1    calibration version
    2.0  common offset of temperature

3.    compile to .bin file that firmware can recognition 

    cd [caliration directory]
    ./spiffsgen.py 20480 ./data/ ./cali_001.bin

4.    upload to device **/dev/cu.usbserial-1420 is changed to your real usb serial port** 
    
    ./esptool.py -p /dev/cu.usbserial-1420 -b 230400 --before default_reset  --after hard_reset --chip esp32 write_flash --flash_mode dio --flash_size detect --flash_freq 40m 0x110000 ./cali_001.bin        
    
 

