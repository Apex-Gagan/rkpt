from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils.dateparse import parse_datetime

from .supabase_data import fetch_products

_SPLIT = urlsplit(settings.SITE_URL)


class _CanonicalSite:
    """Stand-in for ``django.contrib.sites.Site``.

    The sitemap view builds every ``<loc>`` from the Host header of the request
    that fetched it, so a preview deploy — or a crawler arriving on the apex
    domain instead of ``www`` — would publish a whole sitemap of non-canonical
    URLs. Pinning the domain to SITE_URL keeps ``<loc>`` and ``<link rel=
    canonical>`` in agreement.
    """

    domain = _SPLIT.netloc


class CanonicalSitemap(Sitemap):
    protocol = _SPLIT.scheme or "https"

    def get_urls(self, page=1, site=None, protocol=None):
        return super().get_urls(
            page=page, site=_CanonicalSite(), protocol=self.protocol
        )


class StaticViewSitemap(CanonicalSitemap):
    changefreq = "weekly"

    def items(self):
        return ["home", "contact"]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == "home" else 0.6


class ProductSitemap(CanonicalSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        """One entry per reachable product page.

        Slugs are not unique in the catalogue, and ``fetch_product_by_slug``
        answers with the first match — so listing every product would publish
        the same URL twice and point crawlers at a page that renders different
        content than the row it came from. Keep the first occurrence only, and
        drop rows that have no real slug of their own.
        """
        seen = set()
        unique = []
        for product in fetch_products():
            slug = (product.slug or "").strip()
            if not slug or slug == "default-product" or slug in seen:
                continue
            seen.add(slug)
            unique.append(product)
        return unique

    def lastmod(self, obj):
        # Supabase hands back `created_at` as an ISO-8601 string; the sitemap
        # template runs it through the `date` filter, which silently drops
        # anything that is not a real datetime.
        return parse_datetime(obj.created_at) if obj.created_at else None

    def location(self, obj):
        return reverse("single-product", kwargs={"slug": obj.slug})
