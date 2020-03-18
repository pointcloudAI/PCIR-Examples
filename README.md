 #  PCIR-Examples
 
 ## Description
 
 The project is powerd by PointCloud.Ai. It's demo of PCIR-xxCx series consist of python's examples  on computer and java's examples on android phone.
 
 1. python on computer: [Python Example](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/visual_monitor)  command line：python ir_demo.py serialPort [serial Baud rate]
 
    example: `python3 ir_demo.py /dev/cu.usbserial-1410`(/dev/cu.usbserial-1410 should replaced by your serial port which named like COMx on windows or /dev/cu.xxxxx on OSX)
 
 2. java on android: [Android Example](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/android_visual_monitor)
 
 ## Performance
 
  **1. product** 
 
 ![MLX90640BAA chip](https://images.gitee.com/uploads/images/2020/0310/192830_675f8a8e_5484807.png "mlx90640.png")
 ![PCIR-400CA module](https://images.gitee.com/uploads/images/2020/0310/192931_518ae6c5_5484807.png "PCIR-40CA.png")
 
  **2. running Visual Monitor Demo** 

this demo demonstrator how to send command to device and handle result from device, also illustrator how to process data frame on host.
 ## Python source code [visual monitor](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/visual_monitor)
 ![Visual Monitor for MLX90640](https://images.gitee.com/uploads/images/2020/0317/230625_d4215c52_5484807.png "visual_monitor.png")
 ## Interface
 
 1. interface: UART
 2. Baud Rate:  **230400**  [firmware ver1.0 baud rate:460800]
 
 ### Evaluate Mode
 this mode is for customer evaluate temperature precision result if suitable for their product as soon as possible.
 
 1. After power on, module will output the ASCII temperature data, each frame ends with `\r\n` on 3FPS.
 
 2. Output resolution of PCIR-40CA/PCIR-40CB is 32x24.
 
 3. temperature data of each point is float with 2 decimal places. Row precedence.
 
 4. example: a frame = 32x24(768 points' data) 
 
    ​	\r\n36.01,35.02,34.03....................37.01,36.21,36.01,35.02,34.03\r\n
 
 
 
 ### Operate Mode
 
 this mode is for integrate to product, please contact us(support@pointcloud.ai) for product version firmware.
 
**a typical use is following line:** 

    Send setting command 'CMDE\0\0' 
    Send setting command 'CMDF\2\0'
    Send open command 'CMDC\1\0'
    Parser receive data 'DAT',validate data Length equal to sensor pixel and frame end '\r\n'.
  
 1.    CAMMAND LIST  6BYE = 'CMD'+Type[1Byte]+Value[1Byte]+CRC[1Byte]
 
     Open     command:  Type = C  Value = [1-open | 0-close | 2- 1 Frame if Mode command ==0]
     Mode     command:  Type = M  Value = [0-receive frame manual | 1-receiver frame continuous]
     Object   command:  Type = O  value = [0-body measure| 1-object measure]
     Freq     command:  Type = F  Value = [0-1/2fps | 1-1fps | 2-2fps | 3-3fps | 4-4fps]
     Version  command:  Type = V  Value = [0]
     Evaluate command:  Type = E  Value = [ 0-Operate mode | 1- Evaluate mode | 3- get Evaluate mode status]
     Offset   command:  Type = T  Value = [0]

2.    Command Result List:  'RETCMD + Type[1Byte] + Value[multiple Byte] + '\r\n'

	 Open     result:   'RET' + Open Command[6 bytes] + '\r\n'
     Mode     result:   'RET' + Open Command[6 bytes] + '\r\n'
     Object   result:   'RET' + Open Command[6 bytes] + '\r\n'
     Freq     result:   'RET' + Open Command[6 bytes] + '\r\n'
     Version  result:   'RETCMDV' + firmware version[4 bytes] + ',' + calibrate version[4 bytes] + '\r\n'
     Evaluate command:  'RETCMDE' + type[1 bytes] + '\r\n'
     Offset   command:  'RETCMDT' + common offset[6 bytes] + '\r\n' 

3.    Error command Result: 'RETERR' + command[6 bytes] + '\r\n'
4.    data frame format:  'DAT' + Data Bytes Length[2 bytes] + Envirment Temp[4 Bytes float type] + data[pixelx4bytes float] + '/r/n'

     example mlx90640 32x24 pixel:
     3Bytes + 2Byte + 4Bytes + 32X24X4 + 2Bytes = 3083Bytes
	 example mlx90641 16x12 pixel:
     3Bytes + 2Byte + 4Bytes + 16X12X4 + 2Bytes = 779Bytes



