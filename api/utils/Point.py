from django.contrib.gis.geos import Point, Polygon


def get_coordinate(value):
    try:
        return float(value)
    except:
        return 0


def get(request, srid=None):
    if "longitude" not in request.GET or "latitude" not in request.GET:
        return None

    longitude = get_coordinate(request.query_params.get('longitude', 0))
    latitude = get_coordinate(request.query_params.get('latitude', 0))

    point = Point(longitude, latitude)
    if srid:
        point = Point(longitude, latitude, srid=srid)

    return point
