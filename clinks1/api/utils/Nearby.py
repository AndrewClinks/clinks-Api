from django.db.models.functions import Cast
from ..delivery_distance.models import DeliveryDistance
from django.contrib.gis.db.models import PointField
from django.db.models import F
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import fromstr, Point


def _get(queryset, point_field, point, annotate_distance=False, max_delivery_distance=None):
    if not max_delivery_distance:
        max_delivery_distance = DeliveryDistance.objects.order_by("-ends").first()

        if not max_delivery_distance:
            return queryset
        else:
            max_delivery_distance = max_delivery_distance.ends

    queryset = queryset.annotate(point_geo=Cast(f"{point_field}", PointField(geography=True))).filter(
        point_geo__distance_lte=(point, max_delivery_distance*1000))

    if annotate_distance:
        point_in_srid = fromstr(f'POINT({point.coords[0]} {point.coords[1]})', srid=4326)
        queryset = queryset.annotate(distance=Distance("point_geo", point_in_srid))

    return queryset


def venues(queryset, point):
    return _get(queryset, "address__point", point)


def menu_items(queryset, point):
    return _get(queryset, "menu__venue__address__point", point, True)


def items(queryset, point):
    return _get(queryset, "menu_items__menu__venue__address__point", point)


def drivers(queryset, order, max_distance):
    from ..driver.models import Driver
    venue_point = Point(order.data["venue_address"]["longitude"], order.data["venue_address"]["latitude"])
    return _get(queryset, "last_known_location", venue_point, max_delivery_distance=max_distance)