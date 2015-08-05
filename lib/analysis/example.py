import analysis

class Example(analysis.AnalysisModule):

    def analyze_sample(self, filename='', tags=[]):
        # Do any analysis steps you want here. This could launch an external
        # script or be entirely self contained.
        print('Opening file: ' + filename)

    def check_status(self, filename=''):
        # This determines when a file has completed analysis. If you don't
        # want to deal with this, just return True
        print('Analysis completed.')
        return True
