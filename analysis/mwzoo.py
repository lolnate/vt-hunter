import analysis
from subprocess import Popen

class MWZoo(analysis.AnalysisModule):

    def analyze_sample(self, filename='', tags=[]):
        Popen( ['/bin/echo', '"Opening file ' + filename + '"'] )

    def check_status(self, filename=''):
        Popen( ['/bin/echo', '"Getting status of file ' + filename + '"'] )
        return False
