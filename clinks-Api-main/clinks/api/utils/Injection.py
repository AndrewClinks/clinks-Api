from ..venue.models import Venue
from django.db.models import OuterRef, Subquery, Aggregate


class Array(Subquery):
    template = 'ARRAY(%(subquery)s)'


def add_venue_ids_to_company_members(queryset):
    from ..staff.models import Staff
    subquery = Staff.objects.filter(company_member__user_id=OuterRef("user_id"), deleted_at__isnull=True)
    queryset = queryset.annotate(venues=Array(subquery.values("venue_id")))
    return queryset
