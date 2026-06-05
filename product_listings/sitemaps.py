from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from products.models import Product


# Static pages sitemap
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


# Dynamic Product sitemap
class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse("single-product", kwargs={"slug": obj.slug})
