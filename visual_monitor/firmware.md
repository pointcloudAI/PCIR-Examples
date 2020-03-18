** 烧录固件步骤
1. 安装python3
2. 安装esptool.py

```
pip install esptool
```

3. 获得最版本固件为firmware.bin
4. 插上6条线的转接板，连接板的usb连接到PC
5. 确认PC找到串口设备，假设为 com2
6. 修改一下烧录命令的对应 固件路径 和串口端口号，并在命令行下运行
```
    esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 2000000 --before default_reset --after hard_reset write_flash -z --flash_mode dio --flash_freq 40m --flash_size detect 0x10000 firmware.bin
```

