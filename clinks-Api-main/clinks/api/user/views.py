from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import update_last_login
from rest_framework import status

from django.contrib.auth.hashers import check_password, make_password
from rest_framework.views import APIView

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import User
from .serializers import UserDetailSerializer, password_validate

from ..admin.models import Admin
from ..admin.serializers import AdminDetailSerializer

from ..customer.models import Customer
from ..customer.serializers import CustomerDetailSerializer

from ..driver.models import Driver
from ..driver.serializers import DriverDetailSerializer

from ..company_member.models import CompanyMember
from ..company_member.serializers import CompanyMemberAuthSerializer

from rest_framework.exceptions import PermissionDenied

from ..tasks import send_mail

from ..utils import (
    Token,
    Constants,
)

from ..utils.Permissions import IsAuthenticated

from ..utils.Views import SmartAPIView

from ..utils import DateUtils


class Login(SmartAPIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return self.respond_with("Invalid request, please provide an 'email' and 'password' field",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        invalid_credentials_response = self.respond_with(
                                        "A user with this email and password combination does not exist.",
                                        status_code=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)

            if not check_password(password, user.password):
                return invalid_credentials_response

            check_if_user_active(user)

            data = get_detailed(user)
            update_last_login(None, user)
            data[Constants.USER_AUTH_TOKENS] = Token.create(user)
            return Response(data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return invalid_credentials_response


class Logout(SmartAPIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):
        if "refresh" not in request.data:
            return self.respond_with("Please provide a refresh token",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        refresh_token = request.data["refresh"]
        outstanding_token = OutstandingToken.objects.filter(token=refresh_token, user=request.user)\
                                                    .exclude(blacklistedtoken__token__token=refresh_token)\
                                                    .first()

        if not outstanding_token:
            return self.respond_with("No refresh token found",
                                     status_code=status.HTTP_404_NOT_FOUND)

        BlacklistedToken.objects.create(token=outstanding_token)

        return Response(status=status.HTTP_204_NO_CONTENT)


# refresh view in simple-jwt doesn't save token to outstanding table
# when refreshing token
# https://github.com/davesque/django-rest-framework-simplejwt/issues/25
class Refresh(SmartAPIView):

    def post(self, request):
        if "refresh" not in request.data:
            return self.respond_with("Please provide a refresh token",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        refresh_token = request.data["refresh"]

        outstanding_token = OutstandingToken.objects.filter(token=refresh_token)\
                                                    .exclude(blacklistedtoken__token__token=refresh_token)\
                                                    .first()

        if not outstanding_token:
            return self.respond_with("No refresh token found",
                                     status_code=status.HTTP_404_NOT_FOUND)

        if not outstanding_token.user:
            return self.respond_with("Invalid refresh token",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        check_if_user_active(outstanding_token.user)

        BlacklistedToken.objects.create(token=outstanding_token)

        tokens = Token.create(outstanding_token.user)

        return Response(data=tokens, status=status.HTTP_200_OK)


class RequestPasswordReset(SmartAPIView):

    def post(self, request):

        if "email" not in request.data:
            return self.respond_with("Please provide an email",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        email = request.data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return self.respond_with("This email does not belong to a valid user",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        check_if_user_active(user)

        send_mail.delay_on_commit("send_code", user.id)

        return Response(status=status.HTTP_204_NO_CONTENT)


class ResetPassword(SmartAPIView):

    def post(self, request):

        if "email" not in request.data or "password" not in request.data:
            return self.respond_with("Please provide an email and password",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if "verification_code" not in request.data:
            return self.respond_with("Please provide a verification code",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        email = request.data["email"]
        password = request.data["password"]
        verification_code = request.data["verification_code"]

        try:
            password_validate(password, False)
        except Exception as e:
            return self.respond_with(str(e), status_code=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return self.respond_with("This email does not belong to a user",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        if user.verification_code != verification_code:
            return self.respond_with("Invalid verification code",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        check_if_user_active(user)

        user.password = make_password(password)
        user.verification_code = None
        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class Info(APIView):

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user

        check_if_user_active(user)

        user.last_seen = DateUtils.now()
        user.save()

        data = get_detailed(user)

        return Response(data, status=status.HTTP_200_OK)


class RequestVerifyEmail(SmartAPIView):

    permission_classes = (IsAuthenticated, )

    def post(self, request):
        user = request.user

        check_if_user_active(user)

        send_mail.delay_on_commit("send_account_verification_code", user.id)

        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyEmail(SmartAPIView):

    permission_classes = (IsAuthenticated,)

    def post(self, request):

        if "verification_code" not in request.data:
            return self.respond_with("Please provide a verification code",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        verification_code = request.data["verification_code"]

        if not verification_code:
            return self.respond_with("Please provide a verification code",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        user = request.user

        check_if_user_active(user)

        if user.verification_code != verification_code:
            return self.respond_with("Invalid verification code",
                                     status_code=status.HTTP_400_BAD_REQUEST)

        user.verification_code = None
        user.email_verified = True

        user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


def get_detailed(user):
    data = {}

    if user.role == Constants.USER_ROLE_ADMIN:
        admin = Admin.objects.get(user=user)
        admin_data = AdminDetailSerializer(admin).data
        data[Constants.USER_ROLE_ADMIN] = admin_data

    if user.role == Constants.USER_ROLE_CUSTOMER:
        customer = Customer.objects.get(user=user)
        customer_data = CustomerDetailSerializer(customer).data
        data[Constants.USER_ROLE_CUSTOMER] = customer_data

    if user.role == Constants.USER_ROLE_DRIVER:
        driver = Driver.objects.get(user=user)
        driver_data = DriverDetailSerializer(driver).data
        data[Constants.USER_ROLE_DRIVER] = driver_data

    if user.role == Constants.USER_ROLE_COMPANY_MEMBER:
        company_member = CompanyMember.objects.get(user=user)
        company_member_data = CompanyMemberAuthSerializer(company_member).data
        data[Constants.USER_ROLE_COMPANY_MEMBER] = company_member_data

    else:
        data["user"] = UserDetailSerializer(user).data

    return data


def check_if_user_active(user):
    if user.status != Constants.USER_STATUS_ACTIVE:
        raise PermissionDenied("Your account is no longer active")
