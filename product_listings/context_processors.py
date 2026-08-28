from datetime import datetime

from django.conf import settings


def current_year(request):
    return {"current_year": datetime.now().year}


def cart_count(request):
    cart = request.session.get('cart', {})
    count = sum(int(item['qty']) for item in cart.values())
    return {"cart_count": count}


def site_meta(request):
    """Absolute URLs for the canonical link, Open Graph tags and JSON-LD.

    Those tags have to name the public domain even when the page is rendered
    behind a preview host or on localhost, so they are built from SITE_URL
    rather than from the incoming request.
    """
    base = settings.SITE_URL
    return {
        "site_url": base,
        "site_name": settings.SITE_NAME,
        "canonical_url": f"{base}{request.path}",
        "default_og_image": settings.DEFAULT_OG_IMAGE,
    }
