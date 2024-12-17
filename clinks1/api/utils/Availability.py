from ..availability.models import Availability

from ..utils import DateUtils


def status():
    today = DateUtils.today().date()
    weekday = DateUtils.weekday()

    availability_today = Availability.objects.filter(date__day=today.day, date__month=today.month).first()
    availability = availability_today

    if availability_today is None:
        availability = Availability.objects.filter(day__iexact=weekday).first()

    if availability.closed:
        return _respond_with(False, "Sorry we are closed")

    starts_at = availability.starts_at
    ends_at = availability.ends_at

    if DateUtils.time_difference(starts_at) > 0:
        return _respond_with(False, "Whoops we are not open yet")

    if DateUtils.time_difference(ends_at) < 0:
        return _respond_with(False, "Sorry we are closed, come back tomorrow")

    return _respond_with(True, "It is open!")


def _respond_with(available, reason):
    return {
        "available": available,
        "reason": reason
    }
