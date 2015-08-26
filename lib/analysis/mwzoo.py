import hashlib
import lib.analysis
import subprocess
import os, time
import logging
import logging.config
from lib.analysis import analysis
from subprocess import Popen

class MWZoo(analysis.AnalysisModule):

    def _get_index_path(self, _hash):
        return os.path.join('/opt/mwzoo/index/md5/', _hash[0:3], _hash)

    def _sample_exists(self, _hash):
        """Returns True if a given hash already exists in the zoo, False otherwise."""
        logging.debug("Looking up hash {0}".format(_hash))
        path = self._get_index_path(_hash)
        logging.debug('Index path is {0}'.format(path))
        if os.path.islink(path) and not os.path.exists(os.path.realpath(path)):
            logging.warning("index is corrupted: {0} is broken link".format(path))
            return False

        return os.path.exists(path)

    def _get_file_hash(self, _filename):
        logging.debug('Building hash for file {0}'.format(_filename))
        m = hashlib.md5()
        with open(_filename, 'rb') as f:
            m.update(f.read())
        return m.hexdigest()

    '''
    This submits the sample to our malware zoo for analysis. We use an external
    process for this submission.
    '''
    def analyze_sample(self, filename='', tags=[]):
        # When we submit the sample to the mwzoo, it will create a copy of that sample
        # in its directory structure.
        formatted_tags = []
        for tag in tags:
            formatted_tags.append('-t')
            formatted_tags.append(tag)

        subdir = ''
        if len(tags) > 0:
            subdir = "_".join(sorted(tags))
        # The data directory for the file
        mwzoo_dirname = '/opt/mwzoo/data/vt/' + subdir

        '''
        For reference, here is the add-sample command for our mwzoo:
        usage: add-sample [-h] [--enable-download] -t TAGS -s SOURCE
                          [--comment COMMENT] [-d SUBDIRECTORY] [--disable-analysis]
                          input_data [input_data ...]

        Add a given file or download by hash from VirusTotal.

        positional arguments:
          input_data            The files or hashes or add. Accepts file paths and
                                                                      md5, sha1 and/or sha256 hashes.

        optional arguments:
          -h, --help            show this help message and exit
          --enable-download     Enable downloading files from VirusTotal.
          -t TAGS, --tags TAGS  Add the given tag to the sample. Multiple -t options
                                are allowed.
          -s SOURCE, --source SOURCE
                                Record the original source of the file.
          --comment COMMENT     Record a comment about the sample.
          -d SUBDIRECTORY, --subdirectory SUBDIRECTORY
                                File the sample in the given subdirectory. Defaults to
                                processing the file where it's at.
          --disable-analysis    Do not analyze files, just add them.
        '''
        fhash = self._get_file_hash(filename)
        if self._sample_exists(fhash):
            logging.info('Sample already exists: {0}'.format(fhash))
            return False

        logging.info('Launching add-sample for file {0}'.format(filename))
        subprocess.call( ['/usr/bin/python', '/opt/mwzoo/bin/add-sample', '-s', 'vt', '--comment', 'VirusTotal automated download'] + formatted_tags + [ '-d', mwzoo_dirname, filename ] )

        # Then we need to call the analyze function for the mwzoo. The -d option
        # tells it not to launch the sandbox analysis.
        logging.info('Launching mwzoo analyze for file {0}'.format(filename))
        Popen( ['/usr/bin/python', '/opt/mwzoo/bin/analyze', '-d', 'cuckoo', mwzoo_dirname + "/" + os.path.basename(filename)] )
        # Dumb hack to make sure the .running file is created in the mwzoo
        time.sleep(1)
        return True

    '''
    This checks the status of the mwzoo analysis.
    True - analysis complete
    False - analysis not complete
    '''
    def check_status(self, filename='', tags=[]):
        subdir = ''
        if len(tags) > 0:
            subdir = "_".join(sorted(tags))
        # The data directory for the file
        mwzoo_dirname = '/opt/mwzoo/data/vt/' + subdir
        # If .analysis is NOT found, analysis has not yet started:
        fhash = self._get_file_hash(filename)
        if self._sample_exists(fhash):
            # Check for the .analysis dir
            if os.path.isdir(os.path.realpath(self._get_index_path(fhash)) + '.analysis'):
                logging.debug('Analysis directory found for sample: {0}'.format(os.path.basename(filename)))
            else:
                logging.debug('Analysis has not yet started for sample: {0}'.format(os.path.basename(filename)))
                return False

        # If the name.running file is present the analysis is still running.
        if os.path.isfile(mwzoo_dirname + os.path.basename(filename) + '.running'):
            # Still running
            logging.debug('Analysis is still running for sample: {0}'.format(os.path.basename(filename)))
            return False
        else:
            logging.debug('Running file not found for sample: {0}'.format(os.path.basename(filename)))

        # Otherwise, analysis is complete!
        logging.info('Analysis complete for {0}'.format(filename))
        return True

    '''
    Called at the end of the processing.
    We want to remove the file from the vt-hunter downloads directory
    since it is now stored in our mwzoo instead.
    '''
    def cleanup(self, filename='', tags=[]):
        # Remove the malware file
        logging.info("Removing {0}".format(filename))
        os.remove(filename)

