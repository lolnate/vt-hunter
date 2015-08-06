#!/usr/bin/env python3
from __future__ import print_function
import argparse
import hashlib
import sys
import os
import requests

from configparser import ConfigParser
from lib.constants import VT_DOWNLOADER_VERSION, VT_HOME

class vtAPI():
    def __init__(self, config):
        self.base = 'https://www.virustotal.com/vtapi/v2/'
        self.config = config

    def downloadFile(self, vthash, dl_location):
        try:
            params = {'hash': vthash, 'apikey': self.config.get('vt', 'api_local')}
            r = requests.get(self.base + 'file/download', params=params)
            if r.status_code == 200:
                downloaded_file = r.content
                if len(downloaded_file) > 0:
                    fout = open(dl_location + vthash, 'wb')
                    fout.write(downloaded_file)
                    fout.close()
                    return 0
            else:
                print('Received status code {0} and message {1}'.format(r.status_code, r.content))
                return 1
        except Exception as e:
            print("Exception: {0}".format(e))
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
        config = ConfigParser()
        config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
    except ImportError:
        raise SystemExit('vt.ini was not found or was not accessible.')

    os.environ["http_proxy"] = config.get('proxy', 'http')
    os.environ["https_proxy"] = config.get('proxy', 'https')

    options = parse_arguments()
    vt = vtAPI(config)
    if options.download:
        retcode = vt.downloadFile(options.vthash, config.get('locations', 'downloads'))
        if retcode > 0:
            return retcode
        return 0

if __name__ == '__main__':
    retcode = main()
    exit(retcode)
