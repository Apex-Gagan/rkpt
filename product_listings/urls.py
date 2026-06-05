from django.urls import path
from .views import *
from .sitemaps import StaticViewSitemap, ProductSitemap


urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("product/<slug>", Single_Product.as_view(), name="single-product"),
    path("contact-us", ContactView.as_view(), name="contact"),
    path("robots.txt", RobotsView.as_view(), name="robots"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="add-to-cart"),
    path("cart/update/", UpdateCartView.as_view(), name="update-cart"),
    # sitemap url
]
