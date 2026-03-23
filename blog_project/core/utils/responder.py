from rest_framework.response import Response
from core.constants.messages import HTTP_200_OK, HTTP_400_BAD_REQUEST


def success_response(data=None, message=None, status_code=HTTP_200_OK):
    payload = {"success": True}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)


def error_response(message, errors=None, status_code=HTTP_400_BAD_REQUEST):
    payload = {"success": False, "message": message}
    if errors is not None:
        payload["errors"] = errors
    return Response(payload, status=status_code)