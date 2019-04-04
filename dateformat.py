import calendar
import datetime
import math
import time
import re


try:
    import pytz
except ImportError:
    HAVE_PYTZ = False
else:
    HAVE_PYTZ = True


__version__ = "0.9.7"


RE_0_TO_60 = "[0-6]?[0-9]"  # In some special cases, e.g. seconds, can actually be '60'
RE_00_TO_31 = "(?:[0-2][0-9])|(?:3[0-1])"
RE_0_TO_31 = "(?:[0-2]?[0-9])|(?:3[0-1])"
RE_0_TO_12 = "(?:0?[0-9])|(?:1[0-2])"
RE_00_TO_12 = "(?:0[0-9])|(?:1[0-2])"
RE_0_TO_24 = "(?:[0-1]?[0-9])|(?:2[0-4])"

SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR = SECONDS_IN_MINUTE * 60
SECONDS_IN_DAY = SECONDS_IN_HOUR * 24


ISOFORMAT_DATE = "YYYY-MM-DD"
# This format explicitly leaves out the micro/milli/nano second component,
# as the precision of the sub-second measurement in iso8601 is undefined,
# and it is easy to add in the correct .SSSS component  once the precision
# is agreed/known
ISOFORMAT_TIME = "hh:mm:ss"
ISOFORMAT_DATETIME = f'{ISOFORMAT_DATE}␣{ISOFORMAT_TIME}'

ISOFORMAT_BASIC_DATE = "YYYY[MM][DD]"
ISOFORMAT_BASIC_TIME = "hhmmss"


RAISE = object()


class DateFormatPart:

    """
    Responsible for an element of a date format, both parsing, and formatting.

    For example, to parse 4-digit years, a DateFormatPart with format_str of
    'YYYY' exists. This part has the logic to extract the year from a string,
    and to format the year as a 4-digit string from a date.
    """

    PARSER_RE_CONTAINS_GROUP = True
    VALUE_MATCHES_DATE_COMPONENT_INT = False

    def __init__(self, format_str, re_str):
        self.format_str = format_str  # What to look for in the format spec (e.g. YYYY)
        self._parser_re_pattern = re_str  # Re that matches this date value (e.g. \d{4})

    def parser_re(self, format):
        """
        Date parsing is done by matching the string to a regular expression
        before converting each component to a date-relevant value.
        This method returns the part of the full regular-expression pattern
        that should match against the value.
        """
        return f'({self._parser_re_pattern})'

    def partition_spec(self, string):
        """
        Given a string of the form:  "YYYY-MM-DD", and assuming this part
        matches on 'MM',
        return a tuple of the form ("YYYY-", "MM", "-DD"), as per the standard
         string.partition function
        """
        return string.partition(self.format_str)

    def __repr__(self):
        return f"<{type(self).__name__}: '{self.format_str}'>"

    def format_part(self, format):
        raise NotImplementedError(
            f"{type(self)} has not implemented 'format_part'"
        )

    def install_chain_handlers(self, format):
        pass


class IgnorePart(DateFormatPart):

    """
    Used for separators (T for example), during parsing, the matched value is
    ignored (but checked for presence)
    """

    PARSER_RE_CONTAINS_GROUP = False

    def __init__(self, *args, format_value=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.format_value = self.format_str if format_value is None else format_value

    def parser_re(self, format):
        return self._parser_re_pattern

    def format_part(self, format):
        return self.format_value


class DayOfMonthSuffixPart(IgnorePart):

    SUFFIXES = {1: 'st', 2: 'nd', 3: 'rd'}

    def add_format_context(self, format, date, context):
        if date.day in {11, 12, 13}:  # Special case
            context['day_of_month_suffix'] = 'th'
        else:
            last = date.day % 10
            context['day_of_month_suffix'] = self.SUFFIXES.get(last, 'th')

    def format_part(self, format):
        return '{day_of_month_suffix}'

    def install_chain_handlers(self, format):
        format.format_chain.append(self.add_format_context)


class SimplePart(DateFormatPart):

    VALUE_MATCHES_DATE_COMPONENT_INT = True

    def __init__(self, format_str, re_str, datepart):
        self.datepart = datepart
        super().__init__(format_str, re_str)

    def format_part(self, format):
        return f'{{date.{self.datepart}:0>{len(self.format_str)}}}'


class HourPart(SimplePart):

    HOUR_24_to_12 = [
        12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11,
        12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
    ]

    def __init__(self, format_str):
        super().__init__(format_str, None, "hour")

    def parser_re(self, format):
        re_part = RE_0_TO_24 if format.is_24hour else RE_0_TO_12
        return f"({re_part})"

    def format_part(self, format):
        if format.is_24hour:
            return super().format_part(format)
        return '{HourPart.HOUR_24_to_12[date.hour]:0>2g}'


class ShortYearPart(SimplePart):

    VALUE_MATCHES_DATE_COMPONENT_INT = False

    def got_value(self, context, value):
        year = int(value)
        if year > 69:  # python datetime uses 70 as the cutoff
            year += 1900
        else:
            year += 2000
        context[self.datepart] = year

    def format_part(self, format):
        return '{date.year % 100:0>2}'


class MonthNamePart(SimplePart):

    VALUE_MATCHES_DATE_COMPONENT_INT = False

    TO_NUM = dict((calendar.month_name[i].lower(), i) for i in range(1, 13))
    FROM_NUM = calendar.month_name

    def __init__(self, format_str, re_str):
        super().__init__(format_str, re_str, datepart="month")

    def got_value(self, context, value):
        context['month'] = self.TO_NUM[value.lower()]

    def format_part(self, format):
        return '{MonthNamePart.FROM_NUM[date.month]}'


class ShortMonthNamePart(MonthNamePart):

    # Short months to include 4-letter full month names too, as this sometimes can be used
    TO_NUM = dict(((calendar.month_abbr[i].lower(), i) for i in range(1, 13)), june=6, july=7)
    FROM_NUM = calendar.month_abbr

    def format_part(self, format):
        return '{ShortMonthNamePart.FROM_NUM[date.month]}'


class WeekdayNamePart(IgnorePart):

    FROM_NUM = list(calendar.day_name)

    def format_part(self, format):
        return '{WeekdayNamePart.FROM_NUM[date.weekday()]}'


class ShortWeekdayNamePart(IgnorePart):

    FROM_NUM = list(calendar.day_abbr)

    def format_part(self, format):
        return '{ShortWeekdayNamePart.FROM_NUM[date.weekday()]}'


class MicrosecondPart(DateFormatPart):

    def __init__(self, format_str, re_str, value_multiplier):
        self.multiplier = value_multiplier
        super().__init__(format_str, re_str)

    def got_value(self, context, value):
        context['microsecond'] = int(value) * self.multiplier

    def format_part(self, format):
        return f'{{ int(round(date.microsecond / {self.multiplier}, 0)):0>{len(self.format_str)}g}}'


class FractionalSecond(DateFormatPart):

    def got_value(self, context, value):
        context['microsecond'] = int(float('0.' + value) * 1000000)

    def format_part(self, format):
        return '{date.microsecond.__format__("0>06g").rstrip("0") or "0"}'



EPOCH = datetime.datetime(1970, 1, 1)
if HAVE_PYTZ:
    EPOCH_UTC = datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC)

class TimestampPart(DateFormatPart):

    def __init__(self, format_str, value_divisor):
        self.divisor = value_divisor
        max_digits = 10 + math.ceil(math.log10(value_divisor))
        re_str = r'\d{1,%s}' % max_digits
        super().__init__(format_str, re_str)

    def got_value(self, context, value):
        utc_val = datetime.datetime.utcfromtimestamp(int(value) / self.divisor)
        context["year"] = utc_val.year
        context["month"] = utc_val.month
        context["day"] = utc_val.day
        context["hour"] = utc_val.hour
        context["minute"] = utc_val.minute
        context["second"] = utc_val.second
        if self.divisor > 1:
            context["microsecond"] = utc_val.microsecond

    def format_part(self, format):
        if HAVE_PYTZ:
            return f'{{int((date - (EPOCH_UTC if date.tzinfo else EPOCH)).total_seconds() * {self.divisor}) }}'
        return f'{{int((date - EPOCH).total_seconds() * {self.divisor}) }}'


class AmPmPart(DateFormatPart):
    RE = "am|pm"

    def __init__(self, format_str):
        super().__init__(format_str, self.RE)

    def got_value(self, context, value):
        context["is_pm"] = value.lower() == "pm"

    def install_chain_handlers(self, format):
        format.parse_chain.insert(0, self.prepare_parse_context)

    def prepare_parse_context(self, parser, context, value):
        hour = context.get("hour", 12)
        if context.pop("is_pm"):
            if hour != 12:
                hour = hour + 12
        else:
            if hour == 12:
                hour = 0
        context['hour'] = hour
        return value

    def format_part(self, format):
        if self.format_str.isupper():
            return '{"PM" if date.hour % 24 >= 12 else "AM"}'
        elif self.format_str.islower():
            return '{"pm" if date.hour % 24 >= 12 else "am"}'
        else:
            return '{"Pm" if date.hour % 24 >= 12 else "Am"}'


class UTCOffsetPart(DateFormatPart):

    def __init__(self, format_str, re_str, parser, to_str_format):
        self.parser = parser
        self.to_str_format = to_str_format
        super().__init__(format_str, re_str)

    def got_value(self, context, value):
        sign, hours, minutes = self.parser(value)
        hours, minutes = int(hours), int(minutes)
        total_minutes = minutes + (hours * 60)

        difference = datetime.timedelta(hours=hours, minutes=minutes)
        if sign == "-":
            difference = -difference
        context["tzinfo"] = datetime.timezone(difference)

    def add_format_context(self, format, date, context):
        utc_offset = date.utcoffset()
        total_seconds = utc_offset.total_seconds()
        hours = int(total_seconds / SECONDS_IN_HOUR)
        remaining = (total_seconds - (hours * SECONDS_IN_HOUR))
        minutes = remaining / SECONDS_IN_MINUTE
        context.update({
            "utc_sign": "-" if total_seconds < 0 else "+",
            "utc_hours_abs": abs(hours),
            "utc_mins_abs": abs(minutes),
        })

    def install_chain_handlers(self, format):
        format.format_chain.append(self.add_format_context)

    def format_part(self, format):
        return self.to_str_format


if HAVE_PYTZ:
    class NamedTimezeonePart(DateFormatPart):

        FULL_TZ_NAME_RE = r"(?:[A-Z_]{2,12}?/)+?[A-Z\-_]{3,20}[+-]?\d{0,2}"
        SHORT_TZ_NAME_RE = r"[A-Z]{1}[A-Z+\-_\d]{0,8}"
        RE = f"{FULL_TZ_NAME_RE}|{SHORT_TZ_NAME_RE}"

        def __init__(self, format_str):
            super().__init__(format_str, self.RE)

        def got_value(self, context, value):
            context["tzinfo"] = pytz.timezone(value)

        def fixup_parsed_timezone(self, format, context, date):
            """
            The correct timezone has been identified first-time round, BUT
            pytz can't localize the date correctly without knowing what the
            year/month/day is, due to the fickle nature of humans.
            So extract the timezone, and re-localize correctly
            """
            timezone = date.tzinfo
            date = date.replace(tzinfo=None)
            return timezone.localize(date)

        def install_chain_handlers(self, format):
            format.parse_chain.append(self.fixup_parsed_timezone)
            format.format_chain.append(self.add_format_context)

        def add_format_context(self, format, date, context):
            if not date.tzinfo:
                raise ValueError("Cannot format timezone for non-timezone aware dates")

            zone = getattr(date.tzinfo, "zone", None)
            if zone:
                context['timezone_name'] = zone
            else:
                tz_name = date.tzinfo.tzname(date)
                if not tz_name:
                    raise ValueError(f"Cannot get a timezone name for: {date.tzinfo}")
                context['timezone_name'] = tz_name

        def format_part(self, format):
            return '{timezone_name}'



class DateFormat:

    # The order matters here, for example. YYYY must match before YY
    # (Or the dateformat will end up looking for two short-years right after each other
    # rather than one long year
    FORMAT_STR_TOKENS = [
        TimestampPart('UNIX_TIMESTAMP', value_divisor=1),
        TimestampPart('UNIX_MILLISECONDS', value_divisor=1000),
        TimestampPart('UNIX_MICROSECONDS', value_divisor=1000000),
        TimestampPart('UNIX_NANOSECONDS', value_divisor=1000000000),
        UTCOffsetPart("+HHMM", r"[\+\-]\d{4}",
                      parser=lambda val: (val[0], val[1:3], val[3:5]),
                      to_str_format="{utc_sign}{utc_hours_abs:0>2g}{utc_mins_abs:0>2g}"),
        UTCOffsetPart("+HH:MM", r"[\+\-]\d{2}:\d{2}",
                      parser=lambda val: (val[0], val[1:3], val[4:6]),
                      to_str_format="{utc_sign}{utc_hours_abs:0>2g}:{utc_mins_abs:0>2g}"),
        UTCOffsetPart("+HH", r"[\+\-]\d{2}",
                      parser=lambda val: (val[0], val[1:3], 0),
                      to_str_format="{utc_sign}{utc_hours_abs:0>2g}"),
        WeekdayNamePart("Dddddd", r'[MSTFW]\w{5,8}'),
        WeekdayNamePart("Ddddd", r'[MSTFW]\w{5,8}'),
        ShortWeekdayNamePart("Ddd", r'[MSTFW]\w{2}'),
        SimplePart("[MM]", RE_00_TO_12, "month"),
        SimplePart("[DD]", RE_00_TO_31, "day"),
        SimplePart("DD", RE_0_TO_31, "day"),

        MonthNamePart("MMMMM", r'[ADFJMNOS]\w{2,8}'),
        ShortMonthNamePart("MMM", r'[ADFJMNOS]\w{2,3}'),
        SimplePart("MM", RE_0_TO_12, "month"),
        SimplePart("YYYY", r"\d{4}", "year"),
        ShortYearPart("YY", r"\d{2}", "year"),
        HourPart("hh"),
        SimplePart("mm", RE_0_TO_60, "minute"),
        SimplePart("ss", RE_0_TO_60, "second"),
        MicrosecondPart("SSSSSS", r"\d{6}", value_multiplier=1),
        MicrosecondPart("SSSS", r"\d{4}", value_multiplier=100),
        MicrosecondPart("SSS", r"\d{3}", value_multiplier=1000),
        MicrosecondPart("SS", r"\d{2}", value_multiplier=10000),
        FractionalSecond("S", r"\d{1,9}"),

        AmPmPart("AM"),AmPmPart("Am"),AmPmPart("am"),
        AmPmPart("PM"),AmPmPart("Pm"),AmPmPart("pm"),
        IgnorePart(" ", r"\s+?"),
        IgnorePart('of', 'of'),
        DayOfMonthSuffixPart('st', '(?:st|nd|rd|th)'),
        IgnorePart("␣", r"[T ]", format_value="T")
    ]
    if HAVE_PYTZ:
        for timezone in {"UTC", "GMT", "Europe/London", "Zulu"}:
            FORMAT_STR_TOKENS.append(NamedTimezeonePart(timezone))
    for char in ":/-.,TZ()":
        FORMAT_STR_TOKENS.append(IgnorePart(char, re.escape(char)))

    def __init__(self, spec, is_24hour=None):
        self.spec_str = spec
        self.tokens = self._tokenize_spec(spec)
        if is_24hour is None:
            self.is_24hour = not any(isinstance(t, AmPmPart) for t in self.tokens)
        else:
            self.is_24hour = is_24hour

        # Pre-calculate some properties
        full_date_re = "".join(token.parser_re(self) for token in self.tokens)
        self._parser_re = re.compile("^%s$" % full_date_re, re.I)
        self.re_tokens = [t for t in self.tokens if t.PARSER_RE_CONTAINS_GROUP]
        self.format_code = self._make_format_code()
        self.parse_chain = [None]
        self.format_chain = []
        for token in self.tokens:
            token.install_chain_handlers(self)

    def _make_format_code(self):
        fstring_data = "".join(token.format_part(self) for token in self.tokens)
        src = f"f'{fstring_data}'"
        return compile(src, src, 'eval')

    def _tokenize_spec(self, bit):
        for component in self.FORMAT_STR_TOKENS:
            before, match, after = component.partition_spec(bit)
            if not match:
                continue
            parts = (component, )
            if before:
                parts = self._tokenize_spec(before) + parts
            if after:
                parts = parts + self._tokenize_spec(after)
            return parts
        if bit:
            raise ValueError(f"Could not parse: {bit}")
        return ()

    def matches_format(self, data):
        if not isinstance(data, str):
            return False
        return self._parser_re.match(data) is not None

    def parse(self, data, default=RAISE):
        matches = self._parser_re.match(data)
        if matches is None:
            if default is RAISE:
                raise ValueError(f"date '{data}' does not match format '{self.spec_str}'")
            return default
        parts = matches.groups()
        today = datetime.date.today()
        context = {"year": today.year, "month": today.month, "day": today.day}
        for token, value in zip(self.re_tokens, parts):
            if token.VALUE_MATCHES_DATE_COMPONENT_INT:
                context[token.datepart] = int(value)
            else:
                token.got_value(context, value)
        result = None
        for handler in self.parse_chain:
            if handler is None:
                result = datetime.datetime(**context)
            else:
                result = handler(self, context, result)
        return result

    def format(self, date):
        """
        Given a datetime.datetime object, return a string representing this date/time,
        formatted according to this dateformat.
        """
        context = {'date': date}
        for handler in self.format_chain:
            handler(self, date, context)
        return eval(self.format_code, globals(), context)



if __name__ == "__main__":
    d = datetime.datetime.utcnow().replace(tzinfo=pytz.UTC)
    df = DateFormat(f"Dddddd {ISOFORMAT_DATETIME}.SSSS+HHMM")
    print(df.format(d))
