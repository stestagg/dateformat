# dateformat
A simple, fast date parsing/formatting library for python

> But why another date library?

dateformat is designed to satisfy a specific set of requirements that no other library quite provides:

 * Be fast (see below for benchmarks)
 * Handle a variety of date formats from multiple sources
 * Parse and format dates in many timezones and with many timezone offsets
 * Represent the format in a way that a non-technical person may understand
 * Be explicit about the expected format to prevent heuristic errors


## dateformat ⇄ datetime (builtin python module)

Dateformat is *not* trying to be a replacement for the builtin datetime module.  `datetime.datetime` objects are used as the input/output to the parsing and formatting methods.

It is designed as a replacement for the  `datetime.datetime.strftime` and `datetime.datetime.strptime` methods, providing:

 * better timezone handling
 * a simpler/more common syntax for specifying the date formats
 * faster parsing

## dateformat ⇄ dateutil.parser.parse()

`dateutil.parser.parse`'s intent is to turn a string in an unknown format into a date.  It does that by using a variety of heuristics to try to figure out the format the date has been expressed in.

This approach is highly useful, and very flexible, but suffers from a couple of drawbacks that dateformat doesn't have:

 * There is ambiguity about what date will be produced from a given string, there are situations where that risk cannot be accepted, and it's important for the system to only accept a certain date format
 * Because of all the work that dateutil is doing to work out the format used, it's fairly slow, at just under 10x slower than `strptime`, this is very noticable over 10s - 100s thousands of dates.

## dateformat ⇄ arrow

arrow is the closest to the way dateformat works, the syntax for describing dates is very similar. Unfortunately, arrow constructs its parser every time a date is parsed, creating a significant overhead when parsing each date.

## dateformat ⇄ iso8601 / ciso8601

ciso8601 is _really_ fast.  Unfortunately both these libraries only handle a single date format, so are not useful in this situation.

# Benchmarks

the `benchmark/` dir contains some simple scripts to show how the relative libraries perform at parsing and formatting dates.

Running on a 2016 macbook pro, on Python 3.6.3 gave the following results (best of 3 runs):

(Please note, the parse time chart y-axis has been clamped to 1s, but dateparser took 16s to complete)

![chart showing relative date parse performance](https://github.com/stestagg/dateformat/raw/master/benchmark/parse_times.png)

![chart showing relative date format performance](https://github.com/stestagg/dateformat/raw/master/benchmark/format_times.png)

