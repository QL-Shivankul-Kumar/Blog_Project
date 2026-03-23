from rest_framework.exceptions import APIException
from rest_framework import status


class AppValidationError(APIException):
    status_code  = status.HTTP_400_BAD_REQUEST
    default_detail = "Validation error."
    default_code   = "validation_error"


class ResourceNotFound(APIException):
    status_code    = status.HTTP_404_NOT_FOUND
    default_detail = "The requested resource was not found."
    default_code   = "not_found"


class CustomPermissionDenied(APIException):
    status_code    = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code   = "custom_permission_denied"


class CustomAuthFailed(APIException):
    status_code    = status.HTTP_401_UNAUTHORIZED
    default_detail = "Authentication credentials were not provided or are invalid."
    default_code   = "custom_authentication_failed"


class ConflictError(APIException):
    status_code    = status.HTTP_409_CONFLICT
    default_detail = "A conflict occurred with the current state of the resource."
    default_code   = "conflict"


class UnprocessableEntity(APIException):
    status_code    = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "The request could not be processed."
    default_code   = "unprocessable_entity"


class ThrottledError(APIException):
    status_code    = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Too many requests. Please slow down."
    default_code   = "throttled"