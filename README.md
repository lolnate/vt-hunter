VT Hunter Configuration
-----------------------

1. Copy local_settings_example.py to local_settings.py. Open local_settings.py and modify as necessary.
2. Configure fetchmail to use the fetchmail_processor.py script.
	a) copy fetchmailrc-example to ~/.fetchmailrc
	b) modify ~/.fetchmailrc to include your information
		* You might need to run fetchmail -B 1 -v to find the new SSL fingerprint of the email server and put that in fetchmailrc
3. Copy campaign_translation_example.db to campaign_translation.db. Modify as necessary. See campaign translation section for details.
4. Copy vtmis/scoring_example.py to vtmis/scoring.py. Modify vtmis/scoring.py to include weights for your custom campaigns.
5. The database will be created the first time you run anything that uses it.

## Dependencies
* sqlalchemy
* requests

## Campaign Translation
campaign_translation.db contains mappings to do string substitution on campaign names. You might use this if you don't want to put your internal campaign names on VirusTotal in any form (such as a yara rule name). This will allow you to provide an "external_name" (the fake name), which will then be converted to the "internal_name" when the data is processed.

As a further example. Our internal name for a specific campaign is "Mighty Bear". We want to track this campaign name in a yara rule on VT, so we create a fake name called "campaign1". Our rule is then named "rule prod_campaign1_pivy_strings". We also create a campaign_translation.db entry as so:

```
{
    "campaign1" : "mightybear",
}
```

Now when we receive alerts and the emails are processed, this substitution will occur.

One last note. Unless you have a specific reason (such as some tagging scheme), it is probably a good idea to remove underscores from your campaign names. Underscores are used internally to separate rule names into tags. This might split your campaign name into two or more separate tags you don't want.

## Scoring
scoring.py can be implemented in any way you see fit. The default implementation takes tags for the VT yara hit (based on the yara rule name) and assigns points based on the keywords found. Certain campaigns can be assigned a greater weight, while there is also room for keywords based on specific malware or other special keywords you can define. The result is computed and returned via the get_string_score(rule) function.

## The Process
1. Run fetchmail. The -B option lets you limit the number of emails. This is also intended to be placed in a cron job.
2. Process the emails with email_to_db.py
3. Run process_emails.py.
4. Retrieve RT tickets with process_rt.py
5. Download and submit samples to the mwzoo with process_downloads.py

## Optional malware selection process
* TODO: Configure "no review", aka direct download from email hits. Based on keywords from the rule name perhaps?
* TODO: Create a shell review script to download samples
* TODO: Modularize process_emails.py.
