import analysis

class AnalysisModule(object):

    def __init__(self, config_section, *args, **kwargs):
        assert isinstance(config_section, str)
        self.config_section = config_section

    def analyze_sample(self, filename='',tags=[]):
        raise NotImplementedError("This analysis module was not implemented.") 

    def check_status(self, filename=''):
        raise NotImplementedError("This analysis module was not implemented.")
