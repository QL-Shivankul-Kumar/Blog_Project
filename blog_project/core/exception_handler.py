from rest_framework.views import exception_handler
from rest_framework.exceptions import (
    ValidationError, AuthenticationFailed, NotAuthenticated,
    PermissionDenied, NotFound, MethodNotAllowed, Throttled,
)
from rest_framework.response import Response
from rest_framework import status
from core.constants.messages import GenericMessages, PermissionMessages
from core.exceptions import (
    AppValidationError, ResourceNotFound,
    CustomPermissionDenied,
    CustomAuthFailed,
    ConflictError, UnprocessableEntity,
)

def _format_validation_errors(detail):
    if isinstance(detail, list):
        return {"non_field_errors": [str(e) for e in detail]}
    if isinstance(detail, dict):
        formatted = {}
        for field, errors in detail.items():
            if isinstance(errors, list):
                formatted[field] = [str(e) for e in errors]
            else:
                formatted[field] = str(errors)
        return formatted
    return {"detail": str(detail)}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, (
        AppValidationError, ResourceNotFound,
        CustomPermissionDenied, CustomAuthFailed,
        ConflictError, UnprocessableEntity,
    )):
        return Response(
            {
                "success": False,
                "message": str(exc.detail),
                "errors":  {"detail": str(exc.detail)},
            },
            status=exc.status_code,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {
                "success": False,
                "message": GenericMessages.VALIDATION_ERR,
                "errors":  _format_validation_errors(exc.detail),
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return Response(
            {
                "success": False,
                "message": PermissionMessages.AUTH_REQUIRED,
                "errors":  {"detail": str(exc.detail)},
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            {
                "success": False,
                "message": PermissionMessages.FORBIDDEN,
                "errors":  {"detail": str(exc.detail)},
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, NotFound):
        return Response(
            {
                "success": False,
                "message": GenericMessages.NOT_FOUND,
                "errors":  {"detail": str(exc.detail)},
            },
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, MethodNotAllowed):
        return Response(
            {
                "success": False,
                "message": f"Method '{exc.args[0]}' not allowed.",
                "errors":  {"detail": str(exc.detail)},
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    if isinstance(exc, Throttled):
        return Response(
            {
                "success": False,
                "message": GenericMessages.THROTTLED,
                "errors":  {"detail": str(exc.detail)},
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )


    if response is not None:
        return Response(
            {
                "success": False,
                "message": str(exc),
                "errors":  response.data,
            },
            status=response.status_code,
        )

    return Response(
        {
            "success": False,
            "message": GenericMessages.SERVER_ERROR,
            "errors":  {"detail": str(exc)},
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )