# dateformat ![build status](https://travis-ci.org/stestagg/dateformat.svg?branch=master)

`dateformat` does two things:  turn `datetime` objects into strings, and turn strings into `datetime` objects.
It's goal is to do these things simply and well, and to satisfy the following criteria:

 * Be fast enough (see below for benchmarks)
 * Handle a variety of date formats from multiple sources
 * Parse and format dates in many timezones and with many timezone offsets
 * Represent the expected format in a way that a non-technical person may understand
 * Be explicit about the expected format to prevent heuristic errors

> "But why another date library?"

There isn't currently a python library I've been able to find that matches these 
requirements well enough for my use-cases.  [`Arrow`](http://arrow.readthedocs.io/en/latest/)
 comes closest, but still isn't quite suitable performance-wise.

# Usage

All functionality is based around DateFormat() objects:

### `def __init__(self, spec, is_24hour=None)`

create a dateformat object from the provided spec string.

```
>>> from dateformat import DateFormat

>>> date_format = DateFormat("YYYY-MM-DD hh:mm:ss.SSSS+HH:MM")
```

If `is_24hour` is not provided, the format will be in 12-hour mode if an am/pm 
part is present in the spec, otherwise, dates will be in 24-hour mode.

DateFormat instances have two methods:

### `def parse(self, data)`

Parse a string(`data`) containing a date into a datetime object.

```
>>> date = date_format.parse("2017-06-03 15:32:00.2364-02:00")
datetime.datetime(2017, 6, 3, 15, 32, 0, 236400, tzinfo=datetime.timezone(datetime.timedelta(-1, 79200)))
```

### `def format(self, date)`

Format the passed in `datetime.datetime` object (`date`) as a string:

```
>>> print(date_format.format(date))
2017-06-03 15:32:00.2364-02:00
```

## Timezones

If any part of the format provides a timezone, or UTC offset, then parsing 
produces dates with a timezone indicating the relevant UTC offset.

Likewise, if a dateformat has a timezone part, then dates passed to `.format()`
must include a tzinfo value.

If pytz is available, then some level of named timezone support is provided.

## Leading zeros

All numeric parts of the date format are zero-padded to the number of characters
in the spec.  I.e.  'DD' means that the day of the month is zero-padded to 2-digits.

During parsing, a missing leading zero is usually ignored, but if there is no separator
between parts (for example:  YYYYMMDD), then a missing leading zero will cause an error or bad value.

Currently, all formatted dates are zero-padded, in the future, this may be controllable.

## Date format specification
| Part | Example | Description |
|---------|---------|---------------|
| `+HHMM` | -0515 | A UTC offset provided as a 2-digit hour, and 2-digit minute, with no separator |
| `+HH:MM` | -05:15 | A UTC offset provided as a 2-digit hour, and 2-digit minute, with a ':' separator |
| `+HH` | -05 | A UTC offset provided as a 2-digit hour only |
| `Dddddd` | Monday | The full locale-specific day of the week (Note, this value is ignored during date parsing, but added during date format) |
| `Ddd` | Mon | The locale-specific short name for the day of the week (Ignored during parsing) |
| `DD` | 05 | The zero-padded day of the month. |
| `MMMMM` | September | Month as locale’s full name |
| `MMM` | Sep | Month as locale’s abbreviated name |
| `YYYY` | 2017 | Year with century as a number |
| `YY` | 17 | Year without century as a zero-padded number |
| `hh` | 09 | Hour as a zero-padded number |
| `mm` | 06 | Minute as a zero-padded number |
| `ss` | 45 | Second as a zero-padded number |
| `SSSSSS` | 123456 | Microsecond as a zero-padded decimal number |
| `SSSS`   | 1234 | 100-microseconds as a zero-padded number |
| `SSS` | 123 | milliseconds as a zero-padded number |
| `SS` | 12 | 10-milliseconds as a zero-padded number |
| `am` `Am` `AM` `pm` `Pm` `PM` | am | either AM or PM depending on the hour.  `.format()` matches the case of the spec.  If present, the dateformat will default to 12-hour mode |
| `of` | | Ignored during parsing, added during formtting |
| `st` | th | The appropriate suffix for the day of the month, for example '1_st_ July', '2_nd_ March' |
| `␣` | T | (Unicode OPEN BOX - U+2423) Matches either the character 'T' or a space ' '.  During formatting, 'T' is always used (this is provided to improve flexibility when parsing iso8601 formats) |
| space | | Matches one or more spaces during parsing.  During formatting, one space will be output |
| any of `:/-.,TZ()` | | Ignored during parsing, output as-is during formatting |


# Examples

| Format                   | Example                |
|--------------------------|------------------------|
| `YYYY-MM-DDThh:mm:ss`    | 2017-06-06T09:45:15.   |
| `YYYYMMDDhhmmss`         | 20170606094515.        |
| `YYYYMMDDhhmmss.SSSSSSZ` | 20170606094515.123456Z |
| `MM/DD/YY hh:mm+HHMM`    | 06/06/17 09:45-0500    |


# Library comparison

## dateformat ⇄ datetime (builtin python module)

Dateformat is *not* trying to be a replacement for the builtin datetime module.  `datetime.datetime` objects are used as the input/output to the parsing and formatting methods.

It is designed as a replacement for the  `datetime.datetime.strftime` and `datetime.datetime.strptime` methods, providing:

 * better timezone handling
 * a simpler/more common syntax for specifying the date formats
 * slightly faster parsing

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

