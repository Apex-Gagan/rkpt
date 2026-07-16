from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.index, name="index"),

    path("categories/", views.categories_list, name="categories_list"),
    path("categories/new/", views.category_new, name="category_new"),
    path("categories/<int:cat_id>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:cat_id>/delete/", views.category_delete, name="category_delete"),

    path("products/", views.products_list, name="products_list"),
    path("products/new/", views.product_new, name="product_new"),
    path("products/<int:product_id>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
    path(
        "products/<int:product_id>/images/upload/",
        views.product_image_upload,
        name="product_image_upload",
    ),
    path(
        "products/images/<int:image_id>/delete/",
        views.product_image_delete,
        name="product_image_delete",
    ),

    path("contacts/", views.contacts_list, name="contacts_list"),
    path("contacts/<int:contact_id>/delete/", views.contact_delete, name="contact_delete"),
]
