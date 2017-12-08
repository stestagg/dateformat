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


def make_list_of_dates(n=1e5):
    dates = []
    for i in range(int(n)):
        timestamp = random.random() * (time.time() * 2)
        dates.append(datetime.datetime.utcfromtimestamp(timestamp))
    return dates


def benchmark(fn, values):
    before = time.clock()
    fn(values)
    after = time.clock()
    return (after - before) * 1000


def format_dateformat(dates):
    format = dateformat.DateFormat("YYYY-MM-DD hh:mm:ss")
    for date in dates:
        assert isinstance(format.format(date), str)


def format_strftime(dates):
    for date in dates:
        assert isinstance(date.strftime("%Y-%m-%d %H:%M:%S"), str)


def format_arrow(dates):
    for date in dates:
        assert isinstance(date.format("YYYY-MM-DD hh:mm:ss"), str)


def prepare_arrow(dates):
    return [arrow.get(date) for date in dates]


preparers = {
    format_arrow: prepare_arrow
}


def main():
    dates = make_list_of_dates()
    fns = [format_dateformat, format_strftime, format_arrow]

    timings = defaultdict(list)
    for i in range(3):
        random.shuffle(fns)
        for fn in fns:
            these_dates = dates
            if fn in preparers:
                these_dates = preparers[fn](dates)
            timings[fn].append(benchmark(fn, these_dates))

    print("method,time_ms")
    for fn, times in timings.items():
        fastest = min(times)
        fn_name = fn.__name__.replace("format_", "")
        print(f"{fn_name},{fastest}")


if __name__ == '__main__':
    main()