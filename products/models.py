from django.db import models
from categories.models import Category
from tinymce.models import HTMLField

# Create your models here.
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ManyToManyField(
        Category, related_name="products", blank=True, null=True
    )
    description = models.TextField(blank=True, null=True)
    description_html = HTMLField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(max_length=250, default="default-product")
    catalogue = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} | {self.id}"

    class Meta:
        verbose_name_plural = "Products"
        ordering = ["-created_at"]


class Image(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    image = models.URLField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.image} | {self.product.name}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Product Images"
