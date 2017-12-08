import datetime
import random
import time
from collections import namedtuple
import pytz

from dateformat import DateFormat


Equivalent = namedtuple("EquivalentFormat", ['datetime', 'dateformat'])


EQUIVALENT_FORMATS = [
	Equivalent("%A %d. %B %Y", DateFormat("Ddddd DD. MMMMM YYYY")),
	Equivalent("%Y-%m-%dT%H:%M:%S.%fZ", DateFormat("YYYY-MM-DDThh:mm:ss.SSSSSSZ")),
	Equivalent("%m/%d/%y %I:%M:%S%p", DateFormat("MM/DD/YY hh:mm:ssPM")),
	Equivalent("%y%m%d%H%M%S%z", DateFormat("YYMMDDhhmmss+HHMM")),
]

ALL_TIMEZONES = [pytz.timezone(tz) for tz in pytz.all_timezones]

def yield_dates(n=1e5):
    while True:
        timestamp = random.random() * (time.time() * 2)
        tz = random.choice(ALL_TIMEZONES)
        yield tz.localize(datetime.datetime.utcfromtimestamp(timestamp))


REPORT_EVERY = 5e4

def main():
	for count, date in enumerate(yield_dates()):
		if count % REPORT_EVERY == 0:
			print(f"Tested {count}")
		for equivalent in EQUIVALENT_FORMATS:
			datetime_str = datetime.datetime.strftime(date, equivalent.datetime)
			dateformat_str = equivalent.dateformat.format(date)
			assert datetime_str == dateformat_str, f"{dateformat_str} != {datetime_str}"
			if count % REPORT_EVERY == 0:
				print(f" - '{dateformat_str}' == '{datetime_str}'")

			dateformat_date = equivalent.dateformat.parse(datetime_str)
			datetime_date = datetime.datetime.strptime(datetime_str, equivalent.datetime)
			assert dateformat_date == datetime_date, f'{dateformat_date} != {datetime_date}'
			if count % REPORT_EVERY == 0:
				print(f" - '{dateformat_date}' == '{datetime_date}'")


if __name__ == '__main__':
	main()
