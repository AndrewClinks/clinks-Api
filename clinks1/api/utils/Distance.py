from haversine import haversine


def between(from_point, to_point, convert_to_km=True):
    from_point_longitude = from_point.coords[0]
    from_point_latitude = from_point.coords[1]

    to_point_longitude = to_point.coords[0]
    to_point_latitude = to_point.coords[1]

    distance_in_meters = haversine((from_point_latitude, from_point_longitude), (to_point_latitude, to_point_longitude), unit="m")

    if convert_to_km:
        return distance_in_meters/1000

    return distance_in_meters
