from collections import defaultdict
import random
import time
import datetime

import dateformat
import arrow
import iso8601
import ciso8601
import dateutil.parser
import dateparser


def make_list_of_dates(n=1e4):
    dates = []
    for i in range(int(n)):
        timestamp = random.random() * (time.time() * 2)
        dates.append(datetime.datetime.utcfromtimestamp(timestamp))
    return dates


def format_date_list(dates):
    format = dateformat.DateFormat("YYYY-MM-DD hh:mm:ss")
    return [format.format(date) for date in dates]


def benchmark(fn, values):
    before = time.clock()
    fn(values)
    after = time.clock()
    taken = (after - before) * 1000
    fn_name = fn.__name__.replace("parse_", "")
    return (after - before) * 1000


def parse_dateformat(dates):
    format = dateformat.DateFormat("YYYY-MM-DD hh:mm:ss")
    for date in dates:
        assert isinstance(format.parse(date), datetime.datetime)


def parse_strptime(dates):
    for date in dates:
        assert isinstance(datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S"), datetime.datetime)


def parse_dateutil(dates):
    for date in dates:
        assert isinstance(dateutil.parser.parse(date), datetime.datetime)


def parse_dateparser(dates):
    for date in dates:
        assert isinstance(dateparser.parse(date), datetime.datetime)


def parse_dateparser_guided(dates):
    for date in dates:
        assert isinstance(dateparser.parse(date, date_formats=['%Y-%m-%d %H:%M:%S']), datetime.datetime)



def parse_iso8601(dates):
    for date in dates:
        assert isinstance(iso8601.parse_date(date), datetime.datetime)


def parse_ciso8601(dates):
    for date in dates:
        assert isinstance(ciso8601.parse_datetime(date), datetime.datetime)


def parse_arrow(dates):
    for date in dates:
        assert isinstance(arrow.get(date, "YYYY-MM-DD hh:mm:ss"), arrow.Arrow)


def main():
    dates = make_list_of_dates()
    date_strings = format_date_list(dates)
    fns = [
        parse_dateformat, 
        parse_strptime, 
        parse_dateutil, 
        parse_arrow, 
        parse_dateparser, 
        parse_dateparser_guided,
        parse_iso8601, 
        parse_ciso8601
    ]

    # fns = [
    #     parse_dateformat, 
    # ]

    timings = defaultdict(list)
    for i in range(3):
        random.shuffle(fns)
        for fn in fns:
            timings[fn].append(benchmark(fn, date_strings))

    print("method,time_ms")
    for fn, times in timings.items():
        fastest = min(times)
        fn_name = fn.__name__.replace("parse_", "")
        print(f"{fn_name},{fastest}")


if __name__ == '__main__':
    main()