from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .supabase_data import fetch_products


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "contact",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return fetch_products()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse("single-product", kwargs={"slug": obj.slug})
