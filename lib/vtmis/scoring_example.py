valid_campaigns = [ "mightybear", "dancingdragon", "sillysand", "pretentiouspanda" ]

def get_scoring_dict():
    return { 
            "unattrib" : { "score" : 1, "list" : [ "unattrib", "misc" ] },
            "named" : { "score" : 5, "list" : valid_campaigns
                },
            "top_campaign" : { "score" : 7, "list" :
                [ "dancingdragon", "pretentiouspanda" ]
                },
            "specific_malz" : { "score" : 5, "list" :
                [ "pipeline", "dridex", "gh0st" ]
                }, 
            "somewhat_special" : { "score" : 3, "list" :
                [ "sharinggroup" ]
                },
            "super_special" : { "score" : 9, "list" :
                [ "incident", "malwarefamily" ] 
                }
            }

def get_string_score(rule):
    score = 0
    scoring = get_scoring_dict()
    rule_list = rule.split("_")
    for item in sorted(set(rule_list)):
        for key in scoring.keys():
            if item in scoring[key]['list']:
                score += scoring[key]['score']
    return score

def get_rule_campaign(rule):
    items = rule.split("_")
    for subset in items:
        if subset in valid_campaigns:
            return subset
    return "unknown"
