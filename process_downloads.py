#!/usr/bin/env python3
import sys, os, time
import importlib
import lib.analysis
import argparse
import logging
import logging.config
import lib.hunting as hunting

from lib.constants import VT_PROCESSOR_VERSION, VT_HOME
from subprocess import call
from configparser import ConfigParser

downloads_dir = ''

log_path = os.path.join(VT_HOME, "etc", "logging.ini")
try:
    logging.config.fileConfig(log_path)
    log = logging.getLogger("processDownloads")
except Exception as e:
    raise SystemExit("unable to load logging configuration file {0}: {1}".format(log_path, str(e)))

def processor_init():
    global config
    global downloads_dir

    log.debug("Running VT Processor version {0}".format(VT_PROCESSOR_VERSION))
    try:
        config = ConfigParser()
        config.read(os.path.join(VT_HOME, "etc", "vt.ini"))
    except ImportError:
        raise SystemExit('vt.ini was not found or was not accessible.')

    downloads_dir = config.get('locations', 'downloads')

    if not os.path.exists(downloads_dir):
        os.mkdir(downloads_dir)

    os.environ["http_proxy"] = config.get("proxy", "http")
    os.environ["https_proxy"] = config.get("proxy", "https")


def download_files():
    # Gather md5s of malware to download
    downloads = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '1').limit(1)
    for download in downloads:
        # Download it
        log.debug('Downloading {0}'.format(download.md5))
        rcode = call(["./vtmis.py", "-d", download.md5])
        if rcode > 0:
            log.error('Error: MD5 {0} not downloaded with downloader script.'.format(download.md5))
            download.process_state = '6'
            hunting.sess.commit()
        else:
            log.debug("File {0} downloaded successfully.".format(download.md5))
            download.process_state = '2'
            hunting.sess.commit()


def load_modules():
    analysis_modules = []
    for section in config:
        if "analysis_module_" in section:
            if not config.getboolean(section, "enabled"):
                continue

            module_name = config.get(section, "module")
            try:
                _module = importlib.import_module(module_name)
            except Exception as e:
                log.error("Unable to import module {0}: {1}".format(module_name, str(e)))
                continue

            class_name = config.get(section, "class")
            try:
                module_class = getattr(_module, class_name)
            except Exception as e:
                log.error("Unable to load module class {0}: {1}".format(module_class, str(e)))
                continue

            try:
                analysis_module = module_class(str(section))
            except Exception as e:
                log.error("Unable to load analysis module {0}: {1}".format(section, str(e)))
                continue

            analysis_modules.append(analysis_module)

    return analysis_modules

# Submit the sample for automated analysis
# Import enabled modules.
def run_analysis(analysis_modules=[]):
    to_analysis = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '2').all()
    for download in to_analysis:
        log.debug('Submitting {0} for analysis'.format(download.md5))
        rule_list = []
        hits = hunting.sess.query(hunting.Hit).filter(hunting.Hit.md5 == download.md5).all()
        if len(hits) > 0:
            for hit in hits:
                rule_list.append(hit.rule)
        else:
            log.error('Error with MD5 {0} - No rules available in Hits database.'.format(download.md5))
            download.process_state = '6'
            hunting.sess.commit()
            continue

        rtags = []
        for rule in rule_list:
            rtags.extend(rule.split('_'))
        tags = set(rtags)

        # Format: File Location, rule list,
        for module in analysis_modules:
            module.analyze_sample(downloads_dir + download.md5, tags)

        # Change state to 'processing'
        download.process_state = '3'
        hunting.sess.commit()

# Check analysis statuses
def check_analysis():
    check_analysis = hunting.sess.query(hunting.Download).filter(hunting.Download.process_state == '3').all()
    combined_status = True
    for download in check_analysis:
        rule_list = []
        hits = hunting.sess.query(hunting.Hit).filter(hunting.Hit.md5 == download.md5).all()
        if len(hits) > 0:
            for hit in hits:
                rule_list.append(hit.rule)

        rtags = []
        for rule in rule_list:
            rtags.extend(rule.split('_'))
        tags = set(rtags)

        for module in analysis_modules:
            combined_status = combined_status and module.check_status(downloads_dir + download.md5, tags)

        if combined_status:
            # Change state to 'completed'
            download.process_state = '4'
            hunting.sess.commit()
            for module in analysis_modules:
                module.cleanup(downloads_dir + download.md5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version="You are running VT processor {0}".format(VT_PROCESSOR_VERSION))
    args = parser.parse_args()

    running = True
    processor_init()
    analysis_modules = load_modules()

    while running:
        try:
            download_files()
            run_analysis(analysis_modules)
            check_analysis()
            # Sleep for a bit
            time.sleep(5)
        except KeyboardInterrupt:
            log.info('Caught kill signal, shutting down.')
            running = False
            # TODO: Find a way to clean up running processes
