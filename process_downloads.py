#!/usr/bin/env python
from __future__ import print_function

import sys, os
import importlib
import hunting
import analysis

from subprocess import call
from configparser import ConfigParser

try:
    config = ConfigParser()
    config.read('local_settings.ini')
except ImportError:
    raise SystemExit('local_settings.ini was not found or was not accessible.')

downloads_dir = config.get('locations', 'downloads')

if not os.path.exists(downloads_dir):
    os.mkdir(downloads_dir)

# Gather md5s of malware to download
downloads = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '1').limit(1)
for download in downloads:
    # Download it
    print('Downloading ' + download.md5)
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
# Import enabled modules.
analysis_modules = []
for section in config:
    if "analysis_module_" in section:
        if not config.getboolean(section, "enabled"):
            continue

        module_name = config.get(section, "module")
        try:
            _module = importlib.import_module(module_name)
        except Exception as e:
            print("Unable to import module {0}: {1}".format(module_name, str(e)))
            continue

        class_name = config.get(section, "class")
        try:
            module_class = getattr(_module, class_name)
        except Exception as e:
            print("Unable to load module class {0}: {1}".format(module_class, str(e)))
            continue

        try:
            analysis_module = module_class(str(section))
        except Exception as e:
            print("Unable to load analysis module {0}: {1}".format(section, str(e)))
            continue

        analysis_modules.append(analysis_module)

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
    for module in analysis_modules:
        module.analyze_sample(downloads_dir + download.md5, rule_list)

    # Change state to 'processing'
    download.process_state = '3'
    hunting.sess.commit()

# Check analysis statuses
check_analysis = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '3').all()
combined_status = True
for download in check_analysis:
    for module in analysis_modules:
        combined_status = module.check_status(downloads_dir + download.md5)

    if combined_status:
        # Change state to 'completed'
        download.process_state = '4'
        hunting.sess.commit()
