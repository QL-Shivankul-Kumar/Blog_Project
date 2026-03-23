import time
import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger("api.logger")


def _mask_authorization(headers: dict) -> dict:
    masked = dict(headers)
    auth = masked.get("Authorization") or masked.get("HTTP_AUTHORIZATION")
    if auth:
        parts = auth.split()
        masked["Authorization"] = f"{parts[0]} ******" if len(parts) == 2 else "******"
    return masked


def _get_client_ip(request) -> str:
    x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _get_request_body(request) -> str:
    try:
        body = request.body
        if not body:
            return "None"
        decoded = body.decode("utf-8")
        try:
            parsed = json.loads(decoded)
            for key in ("password", "confirm_password", "old_password",
                        "new_password", "confirm_new_password", "token"):
                if key in parsed:
                    parsed[key] = "******"
            return json.dumps(parsed)
        except json.JSONDecodeError:
            return decoded
    except Exception:
        return "Unable to read body"


def _extract_api_message(response) -> str:
    try:
        if hasattr(response, "data"):
            return response.data.get("message", "-")
        content = response.content.decode("utf-8")
        return json.loads(content).get("message", "-")
    except Exception:
        return "-"


def _build_user_info(request) -> str:
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        return f"Id: {user.id} | Email: {user.email} | Role: {user.role}"
    return "Anonymous"


class RequestResponseLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        req_headers = {
            key[5:].replace("_", "-").title(): value
            for key, value in request.META.items()
            if key.startswith("HTTP_")
        }
        req_headers  = _mask_authorization(req_headers)
        request_body = _get_request_body(request)

        response = self.get_response(request)

        execution_time = time.time() - start_time
        now = datetime.now(timezone.utc).strftime("%I:%M:%S %p (UTC)")
        separator  = "*" * 70

        log_entry = (
            f"\n{separator}\n"
            f"{now} | IP [{_get_client_ip(request)}] {request.build_absolute_uri()} ({request.method})\n"
            f"USER [{_build_user_info(request)}]\n"
            f"REQUEST_HEADERS: {req_headers}\n"
            f"REQUEST BODY: {request_body}\n"
            f"RESPONSE_HEADERS: {dict(response.items())}\n"
            f"API_MSG ~ {_extract_api_message(response)}\n"
            f"STATUS_CODE ~ {response.status_code} | "
            f"EXECUTION_TIME [{execution_time:.6f} Seconds]\n"
            f"{separator}"
        )

        if response.status_code >= 500:
            logger.error(log_entry)
        elif response.status_code >= 400:
            logger.warning(log_entry)
        else:
            logger.info(log_entry)

        return response