#!/usr/bin/env python
from __future__ import print_function

import sys, os
import hunting
from subprocess import call

try:
    import local_settings as settings
except ImportError:
    raise SystemExit('local_settings.py was not found or was not accessible.')

if not os.path.exists(settings.DOWNLOADS_DIR):
    os.mkdir(settings.DOWNLOADS_DIR)

# Gather md5s of malware to download
downloads = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '1').all()
if len(downloads) > 0:
    for download in downloads:
        # Download it
        rcode = call(["./vtmis.py", "-d", download.md5])
        if rcode > 0:
            print('Error: MD5 {0} not downloaded with downloader script.'.format(download.md5))
            download.process_state = '6'
            hunting.sess.commit()
        else:
            print("File downloaded successfully.")
            download.process_state = '2'
            hunting.sess.commit()

# Submit the sample for automated analysis
# TODO: Do file type determination with exiftool
# TODO: If file not determined, move to a review directory
to_analysis = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '2').all()
for download in to_analysis:
    print('Submitting {0} for analysis'.format(download.md5))
    rule_list = []
    hits = hunting.sess.query(hunting.Hit).filter(hunting.Hit.md5 == download.md5).all()
    if len(hits) > 0:
        for hit in hits:
            rule_list.extend(hit.rule)
    else:
        print('Error with MD5 {0} - No rules available in Hits database.'.format(download.md5))
        download.process_state = '6'
        hunting.sess.commit()
        continue

    # Format: File Location, rule list, 
    analysis_module.submit_sample(settings.DOWNLOAD_DIR + download.md5, rule_list)
    # TODO: Move call to analysis module
    # call([])
    download.process_state = '3'
    hunting.sess.commit()

# Check analysis statuses
check_analysis = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '3').all()
for download in check_analysis:
    # TODO: Need to check if the file exists
    status = analysis_module.check_status(settings.DOWNLOADS_DIR + download.md5)
    if status == "True":
        # True means the sample is finished
        download.process_state = '4'
        hunting.sess.commit()
