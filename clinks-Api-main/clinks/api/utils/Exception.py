from rest_framework.exceptions import APIException
from django.utils.encoding import force_str
from rest_framework import status


class CustomValidation(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'A server error occurred.'

    def __init__(self, data, status_code):
        if status_code is not None:
            self.status_code = status_code

        if data is not None:
            self.detail = data

        else:
            self.detail = {'detail': force_str(self.default_detail)}


def raiseError(data, status_code=500):
    raise CustomValidation(data, status_code)