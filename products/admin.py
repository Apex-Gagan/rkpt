from django.contrib import admin
from .models import Product, Image


class ImageInline(admin.TabularInline):
    model = Image
    extra = 3  # number of empty image fields


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ImageInline]


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image", "created_at")
