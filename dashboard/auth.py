import os
from functools import wraps

from django.http import HttpResponseRedirect
from django.urls import reverse

SESSION_KEY = "dashboard_authenticated"


def env_credentials():
    return (
        os.environ.get("ADMIN_USERNAME", ""),
        os.environ.get("ADMIN_PASSWORD", ""),
    )


def check_credentials(username, password):
    expected_user, expected_pass = env_credentials()
    if not expected_user or not expected_pass:
        return False
    return username == expected_user and password == expected_pass


def is_authenticated(request):
    return bool(request.session.get(SESSION_KEY))


def login(request):
    request.session[SESSION_KEY] = True
    request.session.modified = True


def logout(request):
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True


def login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not is_authenticated(request):
            return HttpResponseRedirect(
                reverse("dashboard:login") + f"?next={request.path}"
            )
        return view_func(request, *args, **kwargs)

    return _wrapped
