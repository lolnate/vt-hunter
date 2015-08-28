#!/usr/bin/env python3
import argparse
import json
import os
import requests
import time
import logging
import logging.config
import lib.hunting as hunting

from lib.constants import VT_VERSION, VT_HOME
from configparser import ConfigParser
from datetime import datetime

log_path = os.path.join(VT_HOME, "etc", "logging.ini")
try:
    logging.config.fileConfig(log_path)
    log = logging.getLogger("processDownloads")
except Exception as e:
    raise SystemExit("unable to load logging configuration file {0}: {1}".format(log_path, str(e)))

def collector_init():
    global config
    global downloads_dir 

    log.debug("Running VT Hunter version {0}".format(VT_VERSION))
    try:
        config = ConfigParser()
        config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
    except ImportError:
        raise SystemExit('vt.ini was not found or was not accessible.')

    # TODO: Not used yet, but at some point we will watch for certain source ids or 
    # other indicators and will download files automatically
    downloads_dir = config.get('locations', 'downloads')

    if not os.path.exists(downloads_dir):
        os.mkdir(downloads_dir)

    os.environ["http_proxy"] = config.get("proxy", "http")
    os.environ["https_proxy"] = config.get("proxy", "https")


def download_feed(last_timestamp):
    # If we don't have a timestamp, we just retrieve the last 500 files
    params = { 'apikey' : config.get('vt', 'api_master'), 'reports' : 'false', 'after' : last_timestamp, 'limit' : config.get('vt', 'limit') }

    logging.debug('Making distribution API call')
    r = requests.get( 'https://www.virustotal.com/vtapi/v2/file/distribution', params=params )
    first_ts = 0
    last_ts = 0
    last_md5 = ''
    if r.status_code == 200:
        logging.debug('Status code 200 received. Parsing results...')
        count = 0
        r_json = r.json()
        for entry in r_json:
            count += 1
            if count == 1:
                first_ts = entry['timestamp']
            # Check to see if we already have this entry
            fs = None
            fs = None
            if entry['first_seen'] is not None:
                fs = datetime.strptime(entry['first_seen'], '%Y-%m-%d %H:%M:%S')
            if entry['first_seen'] is not None:
                ls = datetime.strptime(entry['last_seen'], '%Y-%m-%d %H:%M:%S')
            tags = ''
            if len(entry['tags']) > 0:
                tags = ','.join(entry['tags'])

            statement = {'md5': entry['md5'], 'sha1' : entry['sha1'], 'sha256' : entry['sha256'], 'size' : entry['size'], 'type' : entry['type'], 'vhash' : entry['vhash'], 'ssdeep' : entry['ssdeep'], 'link' : entry['link'], 'source_country' : entry['source_country'], 'first_seen' : fs, 'last_seen' : ls, 'source_id' : entry['source_id'], 'orig_filename' : entry['name'], 'timestamp' : entry['timestamp'], 'tags' : tags }
            hunting.insert_vt_sample(statement)
            last_ts = entry['timestamp']
            last_md5 = entry['md5']

        hunting.sess.commit()

        logging.info('Processed {0} results from distribution feed.'.format(count))
    else:
        logging.warning('Received non-200 status code from distribution feed: {0}'.format(r.status_code))

    logging.debug('Last MD5 is {0}'.format(last_md5))
    return (first_ts, last_ts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version="You are running VT collector {0}".format(VT_VERSION))
    args = parser.parse_args()

    running = True
    collector_init()
    last_ts = time.time() * 1000
    last_ts = int(last_ts)
    time.sleep(5)

    while running:
        try:
            returnobj = download_feed(last_ts)
            first_ts = returnobj[0]
            last_ts = returnobj[1]
            first_dt = datetime.fromtimestamp(first_ts / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
            last_dt = datetime.fromtimestamp(last_ts / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
            logging.debug('First timestamp is {0} and last timestamp is {1}'.format(first_ts, last_ts))
            logging.debug('First datetime is {0} and last datetime is {1}'.format(first_dt, last_dt))
            logging.debug('Sleeping for 10 seconds')
            time.sleep(10)
        except KeyboardInterrupt:
            log.info('Caught kill signal, shutting down.')
            running = False
            # TODO: Find a way to clean up running processes
