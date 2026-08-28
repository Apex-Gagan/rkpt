from django.urls import path
from django.views.generic import RedirectView

from .views import *


urlpatterns = [
    path("", HomePageView.as_view(), name="home"),
    path("product/<slug>", Single_Product.as_view(), name="single-product"),
    # Product pages have always been served without a trailing slash, but the
    # old og:url tags advertised one — so shared links land on a 404. Redirect
    # them permanently instead of losing the traffic.
    path(
        "product/<slug>/",
        RedirectView.as_view(pattern_name="single-product", permanent=True),
    ),
    path("contact-us", ContactView.as_view(), name="contact"),
    path("robots.txt", RobotsView.as_view(), name="robots"),
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/add/", AddToCartView.as_view(), name="add-to-cart"),
    path("cart/update/", UpdateCartView.as_view(), name="update-cart"),
]
