import datetime
from django.utils import timezone
import dateutil.parser
from django.utils import dateparse
from dateutil.relativedelta import relativedelta
import pytz, math

from ..utils import Constants


def greater_than(date, days_ago):
    delta = timezone.now() - date
    return delta.days > days_ago


def format_string(date_string, current_format="%Y-%m-%d", new_format="%A, %B %e, %Y"):
    return datetime.datetime.strptime(date_string,  current_format).strftime(new_format)


def format(date, new_format="%d/%m/%Y, %H:%M %Z"):
    return date.strftime(new_format).replace('{S}', str(date.day) + suffix(date.day))


def to_date(date_string, current_format="%Y-%m-%d"):
    return datetime.datetime.strptime(date_string,  current_format).date()


def suffix(d):
    return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')


def validate(datetime_str):
    try:
        dateutil.parser.parse(datetime_str)
        return True
    except ValueError:
        raise Exception("Please enter a valid datetime in format 'YYYY-MM-DDTHH:mm'")


def parse(datetime_str):
    return dateutil.parser.parse(datetime_str)


def parse_date(date_str):
    return dateutil.parser.parse(date_str).date()


def today():
    return now().today()


def now(with_dublin_timezone=False):
    if with_dublin_timezone:
        return datetime.datetime.now(pytz.timezone('Europe/Dublin'))
    return timezone.now()


def last_week():
    return timezone.now()-datetime.timedelta(days=7)


def days_later(day_count, date=timezone.now()):
    return date + datetime.timedelta(days=day_count)


def days_before(day_count, date=timezone.now()):
    return date - datetime.timedelta(days=day_count)


def years_before(year_count, date=timezone.now()):
    return date - datetime.timedelta(days=year_count*365)


def tomorrow():
    return timezone.now() + datetime.timedelta(days=1)


def yesterday():
    return timezone.now() - datetime.timedelta(days=1)


def next_week(date=None):

    if not date:
        date = timezone.now()

    return date + datetime.timedelta(days=7)


def next_month():
    return timezone.now() + relativedelta(months=1)


def month_before():
    return timezone.now() - relativedelta(months=1)


def get_threshold(time_period):
    if time_period == Constants.TIME_PERIOD_TODAY:
        return now() - datetime.timedelta(days=1)
    elif time_period == Constants.TIME_PERIOD_WEEK:
        return now() - datetime.timedelta(days=7)
    elif time_period == Constants.TIME_PERIOD_MONTH:
        return now() - datetime.timedelta(days=30)
    elif time_period == Constants.TIME_PERIOD_YEAR:
        return now() - datetime.timedelta(days=365)
    else:
        return None


def create_date(day, month, year):
    return datetime.date(year=year, month=month, day=day)


def convert_to_date(datetime_to_compare):
    if isinstance(datetime_to_compare, datetime.datetime):
        return datetime.date()


def from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(timestamp)


def utc_from_timestamp(timestamp):
    return datetime.datetime.utcfromtimestamp(timestamp)


def day_difference_from_now(date):
    return get_difference(today().date(), date, Constants.DATE_DIFFERENCE_IN_DAYS)


def week_difference_from_now(date):
    return get_difference(today().date(), date, Constants.DATE_DIFFERENCE_IN_WEEKS)


def year_difference_from_now(date):
    return get_difference(today().date(), date, Constants.DATE_DIFFERENCE_IN_YEARS)


def year_difference_to_now(date):
    return get_difference(date, today().date(), Constants.DATE_DIFFERENCE_IN_YEARS)


def get_difference(starts_at, ends_at, in_format=Constants.DATE_DIFFERENCE_IN_DAYS):
    difference_delta = ends_at - starts_at

    difference_in_days = difference_delta.days

    difference = difference_in_days
    match in_format:
        case Constants.DATE_DIFFERENCE_IN_DAYS:
            difference = difference_in_days
        case Constants.DATE_DIFFERENCE_IN_WEEKS:
            difference = difference_in_days / 7
        case Constants.DATE_DIFFERENCE_IN_YEARS:
            difference = difference_in_days / 365

    return math.floor(difference)


def year_difference(starts_at, ends_at):
    difference = ends_at - starts_at
    return difference.days / 7


def minutes_before(minutes):
    return now() - datetime.timedelta(minutes=minutes)


def minutes_later(minutes):
    return now() + datetime.timedelta(minutes=minutes)


def weeks_later(weeks):
    return now() + datetime.timedelta(days=7*weeks)


def update_time(date=None, hour=None, minute=0, seconds=0):
    if hour:
        return date.replace(hour=hour, minute=minute, second=seconds)

    return date.replace(minute=minute, second=seconds)


def reset_seconds(date=None):
    if not date:
        date = now()

    return date.replace(second=0)


def date_range(start_date, end_date):
    difference = get_difference(start_date, end_date, Constants.DATE_DIFFERENCE_IN_DAYS)
    for n in range(difference+1):
        yield start_date + datetime.timedelta(n)


def combine(date, time):
    return datetime.datetime.combine(date, time, pytz.UTC)


def weekday(date=None):
    if not date:
        date = now()

    return date.strftime("%A")


def time(date=None):
    if not date:
        date = now()

    return date.strftime("%H:%M")


def to_timedelta(days=0, hours=0, minutes=0):
    return datetime.timedelta(days=days, hours=hours, minutes=minutes)


def time_in_past(time):
    date = reset_seconds(time)
    now = reset_seconds(today().time())
    return date < now


def time_difference(time_):
    date = reset_seconds(time_)
    now_ = now(True).time()
    difference = combine(today().date(), date) - combine(today().date(), now_)
    return difference.total_seconds()


# monday is 0
def next_weekday(week_day, date=None):
    if not date:
        date = today().date()

    days_ahead = week_day - date.weekday()

    if days_ahead <= 0:
        days_ahead += 7

    return date + datetime.timedelta(days_ahead)


def date_in_future(date):
    return date > today().date()


def minutes_between(starts_at, ends_at):
    difference = ends_at - starts_at
    return difference.total_seconds()/60


def convert_to_dublin_time(utctime):
    utc = utctime.replace(tzinfo=pytz.UTC)
    dublin_tmz = utc.astimezone(pytz.timezone('Europe/Dublin'))
    return dublin_tmz.strftime('%B %d, %Y %I:%M %p')