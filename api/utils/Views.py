from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import CursorPagination, PageNumberPagination
from rest_framework.exceptions import APIException

from django.db import transaction

from ..utils import Message, QueryParams, Constants, Export, Exception as CustomException

import logging
logger = logging.getLogger('clinks-api-live')

class SmartAPIView(APIView):

    query_params = QueryParams

    def not_found(self, text="Object not found"):
        return Response(Message.create(text), status=status.HTTP_404_NOT_FOUND)

    def respond_with(self, text, key="detail", status_code=status.HTTP_200_OK):
        return Response(Message.create(text, key), status=status_code)

    def raise_exception(self, text, key="detail"):
        raise CustomException.raiseError(Message.create(text, key),
                                         status_code=status.HTTP_400_BAD_REQUEST)

    def get_admin_from_request(self):
        return self.request.user.admin

    def get_company_member_from_request(self):
        return self.request.user.company_member

    def get_customer_from_request(self):
        return self.request.user.customer

    def get_driver_from_request(self):
        return self.request.user.driver

    def is_admin_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_ADMIN

    def is_super_admin_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_ADMIN and self.request.user.admin.role == Constants.ADMIN_ROLE_ADMIN

    def is_admin_staff_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_ADMIN and self.request.user.admin.role == Constants.ADMIN_ROLE_STAFF

    def is_customer_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_CUSTOMER

    def is_driver_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_DRIVER

    def is_company_member_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_COMPANY_MEMBER

    def is_company_member_admin_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_COMPANY_MEMBER and self.request.user.company_member.role == Constants.COMPANY_MEMBER_ROLE_ADMIN

    def is_company_member_staff_request(self):
        if self.is_anonymous_request():
            return False

        return self.request.user.role == Constants.USER_ROLE_COMPANY_MEMBER and self.request.user.company_member.role == Constants.COMPANY_MEMBER_ROLE_STAFF

    def is_authenticated_request(self):
        return not self.is_anonymous_request()

    def is_anonymous_request(self):
        return self.request.user.is_anonymous

    def get_permission_denied_response(self, request, action):
        return self.respond_with("You do not have permission to access this",
                                 status_code=status.HTTP_403_FORBIDDEN)

    def prepare_request_data(self):

        if self.is_customer_request():

            if hasattr(self.request.data, "_mutable"):
                self.request.data._mutable = True

            if hasattr(self.request.data, "_mutable"):
                self.request.data._mutable = False


class SmartDetailAPIView(SmartAPIView):

    model = None
    edit_serializer = None
    detail_serializer = None
    deletable = False
    partial = True

    def queryset(self, request, id):
        objects = QueryParams.get_str(request, "objects")

        if objects == "all":
            return self.model.all_objects.filter(id=id)
        elif objects == "deleted":
            return self.model.all_objects.filter(id=id, deleted_at__isnull=False)

        return self.model.objects.filter(id=id)

    def get(self, request, id):

        if not self.has_permission(request, "GET"):
            return self.get_permission_denied_response(request, "GET")

        queryset = self.queryset(request, id)

        instance = queryset.first()

        if not instance:
            return self.get_instance_not_found_response(request, "GET")

        if not self.get_detail_serializer(request, instance):
            return self.get_missing_serializer_response(request, "GET")

        detail_serializer_class = self.get_detail_serializer(request, instance)

        data = detail_serializer_class(instance).data

        data = self.override_response_data(request, data)

        return self.get_response(instance, data, 'GET')

    @transaction.atomic
    def patch(self, request, id):

        if not self.has_permission(request, "PATCH"):
            return self.get_permission_denied_response(request, "PATCH")

        queryset = self.queryset(request, id)

        instance = queryset.first()

        if not instance:
            return self.get_instance_not_found_response(request, "GET")

        if not self.get_edit_serializer(request, instance):
            return self.get_missing_serializer_response(request, "PATCH")

        # edit_serializer_class = self.get_edit_serializer(request, instance)
        #data = request.data
        #data = self.override_patch_data(request, data)
        # edit_serializer = edit_serializer_class(data=data, partial=self.partial, instance=instance)
        edit_serializer = self.get_edit_serializer(request, instance)
        
        edit_serializer.is_valid(raise_exception=True)
        instance = edit_serializer.update(instance, edit_serializer.validated_data)
        detail_serializer_class = self.get_detail_serializer(request, instance)

        # This calls to_representation on the OrderCompanyMemberEditSerializer
        data = detail_serializer_class(instance).data
        data = self.override_response_data(request, data)

        return self.get_response(instance, data, 'PATCH')

    @transaction.atomic
    def delete(self, request, id):

        if not self.deletable:
            return self.get_permission_denied_response(request, "DELETE")

        if not self.has_permission(request, "DELETE"):
            return self.get_permission_denied_response(request, "DELETE")

        queryset = self.queryset(request, id)

        instance = queryset.first()

        if not instance:
            return self.get_instance_not_found_response(request, "DELETE")

        handle_delete = self.handle_delete(instance)
        if isinstance(handle_delete, Response):
            return handle_delete

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_edit_serializer(self, request, instance):
        return self.edit_serializer

    def get_detail_serializer(self, request, instance):
        return self.detail_serializer

    def get_permission_denied_response(self, request, action):
        return self.respond_with("You do not have permission to access this",
                                 status_code=status.HTTP_403_FORBIDDEN)

    def get_instance_not_found_response(self, request, action):
        return self.respond_with("An object with this id does not exist",
                                 status_code=status.HTTP_403_FORBIDDEN)

    def get_missing_serializer_response(self, request, action):
        message = None
        serializer_type = ""
        if action == "GET":
            serializer_type = "Detail serializer"
        elif action == "PATCH":
            serializer_type = "Edit serializer"

        message = f"{serializer_type} is not defined"
        return self.respond_with(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def handle_delete(self, instance):
        instance.delete()

    def add_filters(self, queryset, request):
        return queryset

    def has_permission(self, request, method):
        return True

    def override_patch_data(self, request, data):
        return data

    def override_response_data(self, request, data):
        return data

    def get_response(self, instance, data, method):
        return Response(data, status=status.HTTP_200_OK)


# Pagination Classes
class PageBasedPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000


class CursorSetPagination(CursorPagination):
    page_size = 20
    ordering = ('-created_at')


class CursorSetOrderPagination(CursorPagination):
    page_size = 20
    ordering = ['-order', 'id']


class CustomPagination(CursorPagination):
    page_size = 20
    ordering = ["id"]

    def __init__(self, ordering):
        self.ordering = ordering


class PaginationAPIView(SmartAPIView):
    max_page_size = 40
    min_page_size = 5
    default_page_size = 20

    pagination_class = CursorSetPagination

    allow_disable_pagination = False

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """

        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                pagination_type = QueryParams.get_str(self.request, "pagination_type")
                order_by = QueryParams.get_str(self.request, "order_by")

                if pagination_type == "page":
                    self._paginator = PageBasedPagination()
                else:
                    # check if it is an instance or class
                    if isinstance(self.pagination_class, type):
                        self._paginator = self.pagination_class()
                    else:
                        self._paginator = self.pagination_class


                # todo cursor pagination ordering doesn't support nesting e.g. order_by 'user__id' will cause crash
                # order_by = QueryParams.get_str(self.request, "order_by")
                # if order_by:
                #     self._paginator.ordering = [order_by]

        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            raise APIException()

        self.set_page_size()

        order_by = QueryParams.get_str(self.request, "order_by")
        if order_by:
            queryset = queryset.order_by(order_by)

        page = self.paginator.paginate_queryset(queryset, self.request, view=self)
        return page

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        assert self.paginator is not None
        return self.paginator.get_paginated_response(data)

    def set_page_size(self, extra=None):

        page_size = self.request.GET.get('page_size')

        if not page_size:
            return

        size = int(page_size)

        if size < self.min_page_size:
            size = self.min_page_size

        if size > self.max_page_size:
            size = self.max_page_size

        self.paginator.page_size = size

    def paginated_response(self, queryset, serializer_class):
        if hasattr(serializer_class, "optimise"):
            queryset = serializer_class().optimise(queryset)
        else:
            print(f"\033[93m{serializer_class} query not optimised\x1b[0m")
            pass

        if QueryParams.get_str(self.request, 'export'):
            return Export.queryset(queryset, self.request)

        if self.allow_disable_pagination and QueryParams.get_bool(self.request, 'paginated') is False:

            order_by = QueryParams.get_str(self.request, "order_by")
            if order_by:
                queryset = queryset.order_by(order_by)
            elif isinstance(self.paginator.ordering, list) or isinstance(self.paginator.ordering, tuple):
                queryset = queryset.order_by(*self.paginator.ordering)
            else:
                queryset = queryset.order_by(self.paginator.ordering)

            data = serializer_class(queryset, many=True).data
            return Response(data)

        page = self.paginate_queryset(queryset)

        serializer = serializer_class(page, many=True)

        return self.get_paginated_response(serializer.data)


class SmartPaginationAPIView(PaginationAPIView):
    model = None
    create_serializer = None
    detail_serializer = None
    list_serializer = None

    def queryset(self, request):
        objects = QueryParams.get_str(request, "objects")

        if objects == "all":
            return self.model.all_objects.filter()
        elif objects == "deleted":
            return self.model.all_objects.filter(deleted_at__isnull=False)

        return self.model.objects.filter()

    def get(self, request):

        if not self.has_permission(request, "GET"):
            return self.get_permission_denied_response(request, "GET")

        queryset = self.queryset(request)

        queryset = self.add_filters(queryset, request)

        if not self.get_list_serializer(request, queryset):
            return self.get_missing_serializer_response(request, "GET")

        serializer_class = self.get_list_serializer(request, queryset)

        return self.paginated_response(queryset, serializer_class)

    @transaction.atomic
    def post(self, request):
        logger.info(f"Order POST request: {request.data}")
        if not self.has_permission(request, "POST"):
            return self.get_permission_denied_response(request, "POST")

        if not self.get_create_serializer(request):
            return self.get_missing_serializer_response(request, "POST")

        create_serializer_class = self.get_create_serializer(request)

        data = request.data
        data = self.override_post_data(request, data)

        create_serializer = create_serializer_class(data=data)
        create_serializer.is_valid(raise_exception=True)
        instance = create_serializer.save()

        detail_serializer_class = self.get_detail_serializer(request, instance)
        data = detail_serializer_class(instance).data

        return self.post_response(request, instance, data)

    def post_response(self, request, instance, data):
        return Response(data, status=status.HTTP_201_CREATED)

    def get_create_serializer(self, request):
        return self.create_serializer

    def get_list_serializer(self, request, queryset):
        return self.list_serializer

    def get_detail_serializer(self, request, instance):
        return self.detail_serializer

    def get_permission_denied_response(self, request, action):
        return self.respond_with("You do not have permission to access this",
                                 status_code=status.HTTP_403_FORBIDDEN)

    def get_missing_serializer_response(self, request, action):
        message = None
        serializer_type = ""
        if action == "GET":
            serializer_type = "List serializer"
        elif action == "POST":
            serializer_type = "Create serializer"

        message = f"{serializer_type} is not defined"
        return self.respond_with(message, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_filters(self, queryset, request):
        return queryset

    def has_permission(self, request, method):
        return True

    def override_post_data(self, request, data):
        return data

    def raise_exception(self, text, key="detail", status_code=status.HTTP_400_BAD_REQUEST):
        from ..utils import Exception as CustomException
        raise CustomException.raiseError(Message.create(text, key), status_code=status_code)

