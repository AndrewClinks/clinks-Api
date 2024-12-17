from rest_framework_simplejwt.tokens import RefreshToken
import uuid, secrets


def create(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def unique():
    return uuid.UUID(bytes=secrets.token_bytes(16))
