#!/usr/bin/env python
import os
import sys
import re
import uuid
import logging
import logging.config

from lib.constants import VT_FETCHMAIL_VERSION, VT_HOME
from configparser import ConfigParser

try:
    config = ConfigParser()
    config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
except ImportError:
    raise SystemExit('vt.ini was not found or was not accessible.')

incoming_emails = config.get('locations', 'incoming_emails')

if not os.path.exists(incoming_emails):
    os.mkdir(incoming_emails)

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

fout = open(incoming_emails + fname, 'w')
fout.write(fstr)
fout.close()
