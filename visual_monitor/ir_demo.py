'''
@功能: 
@Author: swortain
@Date: 2020-03-02 16:45:38
@LastEditTime: 2020-03-05 19:56:35
'''
#!/usr/local/opt/python/bin/python3.7

# -*- coding: utf-8 -*-
import re
import sys

from pointcloud_ircamera import run

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(run())
