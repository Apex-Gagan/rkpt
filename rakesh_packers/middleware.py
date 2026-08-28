"""Cache policy: assets forever, pages never."""

from django.conf import settings

# One year. Safe because every static URL carries a `?v=` content stamp
# (see rakesh_packers.static_storage) — a changed file means a changed URL.
STATIC_MAX_AGE = 60 * 60 * 24 * 365

NO_STORE = "no-store, no-cache, must-revalidate, max-age=0"


class CacheControlMiddleware:
    """Stamps Cache-Control on responses that have not already chosen one.

    Pages are rendered from live Supabase reads, so a product edited in the
    dashboard has to be visible on the very next request — no CDN copy, no
    browser copy, no back/forward cache. Static assets are the opposite: they
    are versioned by URL, so they can be cached indefinitely.

    Listed first in MIDDLEWARE, which means its response phase runs last and
    it can see (and defer to) whatever the view or another middleware set.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.static_prefix = settings.STATIC_URL or "/static/"

    def __call__(self, request):
        response = self.get_response(request)

        # An explicit decision elsewhere wins — e.g. admin views use
        # @never_cache, and Django's own static handler sets its own headers.
        if response.has_header("Cache-Control"):
            return response

        if request.path.startswith(self.static_prefix) and response.status_code < 400:
            # Only a response that actually carries the asset may be marked
            # immutable. A 404 or 500 on a static URL is transient — a deploy
            # race, a missing collectstatic — and caching *that* for a year
            # would keep serving an error page from the browser and the CDN
            # long after the file is back.
            response.headers["Cache-Control"] = (
                f"public, max-age={STATIC_MAX_AGE}, immutable"
            )
        else:
            response.headers["Cache-Control"] = NO_STORE
            response.headers["Pragma"] = "no-cache"

        return response
