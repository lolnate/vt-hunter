#!/usr/bin/env python
import os
import sys
import re
import uuid

try:
    import local_settings as settings
except ImportError:
    raise SystemExit('local_settings.py was not found or was not accessible.')

if not os.path.exists(settings.INCOMING_DIR):
    os.mkdir(settings.INCOMING_DIR)

fname = str(uuid.uuid4())
fstr = ""
for line in sys.stdin:
    line = re.sub('=3D', '=', line)
    line = re.sub('=20', ' ', line)
    line = line.rstrip()
    if len(line) > 1:
        if line[-1] == "=":
            line = line[:-1]
            fstr = fstr + line
        else:
            fstr = fstr + line + '\n'
    else:
        fstr = fstr + line + '\n'

fout = open(settings.INCOMING_DIR + fname, 'w')
fout.write(fstr)
fout.close()
