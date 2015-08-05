import re

valid_rule_statuses = [ 'prod', 'dev', 'test']

def convert_msg_to_html(msg):
    html_msg = ""
    re_breaks = re.compile('\n')
    html_msg = re_breaks.sub("<br />", msg)
    return html_msg

def get_rule_status(rule):
    for subset in rule.split("_"):
        if subset in valid_rule_statuses:
            return subset
    return "dev"
