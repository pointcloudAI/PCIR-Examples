<!--
 * @功能: 
 * @Author: swortain
 * @Date: 2020-03-16 17:20:10
 * @LastEditTime: 2020-03-16 17:24:27
 -->
# PCIR-Examples

## 项目介绍
本项目是深圳市点云智能测温产品PCIR-xxCx series 的使用例程。该系列例程主要由PC上运行的python及anroid运行的java例程组成。  
1.    PC端Python：[Python例程](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/visual_monitor)

        command line：python ./ir_demo.py -p 串口端口 

2.    Android java例程：[Android例程](https://gitee.com/pointcloudai/PCIR-Examples/tree/master/android_visual_monitor)
## Demo效果
1.    产品预览

![MLX90640BAA 芯片](https://images.gitee.com/uploads/images/2020/0310/192830_675f8a8e_5484807.png "mlx90640.png")
![PCIR-400CA 模组](https://images.gitee.com/uploads/images/2020/0310/192931_518ae6c5_5484807.png "PCIR-40CA.png")

2.    运行效果

![PCIR40CB效果图](https://images.gitee.com/uploads/images/2020/0310/134856_e3d5d594_5484807.png "PCIR40CB.png")

## 系统接口
1.    Interface: UART
2.    Baud Rate: 460800

### Evaluate Mode

评估模式直接输出ASCII的温度数据，以供客户以最快的方式评估温度的精度是否满足需要。

1.    硬件上电连接成功后， UART口直接输出以ASCII字符的温度信息，每帧以\r\n结束。3帧/秒的刷新速率。
2.    PCIR-40CA/PCIR-40CB 输出32X24分辨率的温度数据， 
3.    每个温度数据是小数点2位的字符串，每个数据以","号隔开。行优先排列。
4.    举例：一帧数据 = 32X24 一共768个数据:
    \r\n36.01,35.02,34.03....................37.01,36.21,36.01,35.02,34.03\r\n

### Operate Mode
开发模式集成到产品的使用方式,请跟点云智能的工作人员(support@pointcloud.ai)联系烧录开发者版本的固件。