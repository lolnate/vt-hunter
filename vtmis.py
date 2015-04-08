#!/usr/bin/env python
from __future__ import print
import argparse
import hashlib
import sys
import os
import requests

class vtAPI():
    def __init__(self, settings):
        self.base = 'https://www.virustotal.com/vtapi/v2/'
        self.settings = settings

    def downloadFile(self, vthash):
        try:
            param = {'hash': md5, 'apikey': self.settings.VT_API_LOCAL}
            url = self.base + 'file/download'
            data = urllib.urlencode(param)
            req = urllib2.Request(url, data)
            result = urllib2.urlopen(req)
            downloadedfile = result.read()
            if len(downloadedfile) > 0:
                fout = open(settings.VT_API_LOCAL + name, 'w')
                fout.write(downloadedfile)
                fout.close()
                return 0
            else:
                return 1
        except Exception:
            return 1

def parse_arguments():
    '''
    Parse command line arguments
    '''
    opt = argparse.ArgumentParser(description='Search and Download from VirusTotal')
    opt.add_argument('vthash', metavar='Hash', help='An MD5/SHA1/SHA256 Hash')
    opt.add_argument('-d', '--download', action='store_true', help='Download File from VT')
    return opt.parse_args()

def main():
    try:
        import local_settings as settings
    except ImportError:
        raise SystemExit('local_settings.py was not found or was not accessible.')

    os.environ["http_proxy"] = settings.HTTP_PROXY
    os.environ["https_proxy"] = settings.HTTPS_PROXY

    options = parse_arguments()
    vt = vtAPI()
    if options.download:
        retcode = vt.downloadFile(md5, md5, settings.DOWNLOADS_DIR)
        if retcode > 0:
            return retcode
    return 0

if __name__ == '__main__':
    retcode = main()
    exit(retcode)
