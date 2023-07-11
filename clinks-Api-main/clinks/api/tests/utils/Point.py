from geopy import Point
from geopy.distance import distance as Distance
from django.contrib.gis.geos import Point as DBPoint


def north(start_latitude, start_longitude, distance_in_kms):
    start_point = Point(start_latitude, start_longitude)
    distance = Distance(kilometers=distance_in_kms)
    new_point = distance.destination(start_point, 0)
    return new_point


def north_for_point(point, distance_in_kms, return_db_point=False):
    latitude = point.coords[1]
    longitude = point.coords[0]

    new_point = north(latitude, longitude, distance_in_kms)

    if return_db_point:
        return DBPoint(new_point.longitude, new_point.latitude)

    return new_point


def from_db_to_lat_and_lng(db_point):
    return {
        "latitude": db_point.coords[1],
        "longitude": db_point.coords[0]
    }


def from_lat_and_lng_to_db(latitude, longitude):
    return DBPoint(longitude, latitude)