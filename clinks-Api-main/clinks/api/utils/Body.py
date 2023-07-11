from rest_framework import status

from ..utils import Message, DateUtils, Exception as CustomException


def get_int(request, key, default_value=None, raise_exception=False):

    value = get(request, key, raise_exception)

    if value is None:
        return default_value

    try:
        return int(value)

    except Exception as e:
        if raise_exception:
            raise CustomException.raiseError(Message.create(f"{key} value must be a valid integer"),
                                             status_code=status.HTTP_400_BAD_REQUEST)

        return default_value


def get(request, key, raise_exception=False):

    if key not in request.data:

        if raise_exception:
            raise_not_found_exception(key)

        return None

    return request.data.get(key)


def raise_not_found_exception(key):
    raise CustomException.raiseError(Message.create(f"{key} is required."), status_code=status.HTTP_400_BAD_REQUEST)
