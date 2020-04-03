** Python 工具使用方法

1. 安装python3
   参看 [Python3在各个系统平台的安装](https://www.runoob.com/python3/python3-install.html)
2. 安装依赖库 串口和QT

```
pip3 install pyserial
pip3 install PyQt5
```
3. 查看后得知串口对应端口，然后执行
```
python ./ir_demo.py -p 串口端口
```