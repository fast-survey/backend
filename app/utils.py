import re
import time


def combine(username, survey_name):
    """Build unique survey identifier from username and survey_name."""
    return f'{username}.{survey_name}'


def isregex(value):
    """Check if a given value is a valid regular expression."""
    try:
        re.compile(value)
        return True
    except:
        return False


def now():
    """Return current unixtime utc timestamp integer."""
    return int(time.time())
