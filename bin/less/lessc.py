#!/usr/bin/env python

import sys
import os

if __name__ == '__main__':
    #xx=sys.argv
    cmd =r'node "'
    for arg in sys.argv:
        cmd +=r"%s " % arg
    cmd +='"'
    os.popen(cmd)
    print cmd