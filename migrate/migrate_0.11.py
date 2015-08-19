#!/usr/bin/env python3
# Migrates to version 0.11
import os
import lib.hunting as hunting
import logging
import logging.config

from lib.constants import VT_VERSION, VT_HOME

log_path = os.path.join(VT_HOME, "etc", "logging.ini")
try:
    logging.config.fileConfig(log_path)
    log = logging.getLogger("processDownloads")
except Exception as e:
    raise SystemExit("unable to load logging configuration file {0}: {1}".format(log_path, str(e)))

if float(VT_VERSION) >= 0.11:
    downloads = hunting.sess.query(hunting.Download).all()
    for download in downloads:
        hits = hunting.sess.query(hunting.Hit).filter(hunting.Hit.md5 == download.md5).all()
        tag_list = []
        if len(hits) > 0:
            for hit in hits:
                tag_list.extend(hit.rule.split('_'))
        else:
            log.error('Download entry existed for md5 {0}, but no Hit entry was found.'.format(download.md5))
            continue

        tags = set(tag_list)

        for t in tags:
            tag = hunting.sess.query(hunting.Tag).filter(hunting.Tag.tag == t).first()
            if tag is None:
                tag = hunting.Tag(tag=t)
                hunting.sess.add(tag)
                hunting.sess.commit()
            download.tags.append(tag)
            hunting.sess.commit()
