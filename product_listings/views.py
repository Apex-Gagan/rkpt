import re

from django.http import Http404, JsonResponse
from django.shortcuts import render
from django.views import View

from .email import send_email
from .supabase_data import (
    featured_products,
    fetch_categories,
    fetch_product_by_id,
    fetch_product_by_slug,
    fetch_products,
    fetch_related_products,
    group_products_by_category,
    save_contact,
)


def storefront_context(**extra):
    """Categories, products and their grouping — needed by every page that
    renders the shared header, mega menu and footer."""
    categories = fetch_categories()
    products = fetch_products()
    context = {
        "categories": categories,
        "products": products,
        "category_groups": group_products_by_category(categories, products),
    }
    context.update(extra)
    return context


# The homepage shows a slice of the catalogue, not the whole thing: 74 cards
# is a long page to scroll and a lot to download before anyone has expressed an
# interest. The full grid lives on /products/.
HOME_PRODUCT_LIMIT = 24

# How many products each category shows on the unfiltered /products/ page.
CATEGORY_PREVIEW_LIMIT = 12


class HomePageView(View):
    def get(self, request):
        context = storefront_context()
        context["featured"] = featured_products(
            context["category_groups"], limit=HOME_PRODUCT_LIMIT
        )
        context["home_product_limit"] = HOME_PRODUCT_LIMIT
        return render(request, "home.html", context)


class ProductsView(View):
    """The full catalogue, optionally narrowed to one category.

    Filtering happens here rather than by hiding cards in the browser, so each
    category is a real URL a visitor can link to and a crawler can index, and a
    narrowed page only sends the products it actually shows.
    """

    def get(self, request):
        context = storefront_context()
        groups = context["category_groups"]

        slug = (request.GET.get("category") or "").strip()
        active = None
        if slug:
            active = next((g for g in groups if g["slug"] == slug), None)
            if active is None:
                # An unknown category would otherwise be an endless supply of
                # thin, indexable URLs.
                raise Http404("No such category")

        context["active_group"] = active
        context["visible_groups"] = [active] if active else groups
        context["total_count"] = len(context["products"])
        # Unfiltered, this page covers every category, so each one shows a
        # preview and links through. Baskets alone is 107 products — rendering
        # every category in full would be a ~200-card page that buries the
        # smaller categories below it.
        context["preview_limit"] = None if active else CATEGORY_PREVIEW_LIMIT
        # Django's `slice` filter takes a Python-slice string, not an int.
        context["preview_slice"] = None if active else f":{CATEGORY_PREVIEW_LIMIT}"
        return render(request, "products.html", context)


class Single_Product(View):
    def get(self, request, slug):
        product = fetch_product_by_slug(slug)
        if product is None:
            raise Http404("Product not found")
        context = storefront_context(product=product)
        context["related_products"] = fetch_related_products(
            product, limit=8, products=context["products"]
        )
        return render(request, "single_product.html", context)


class ContactView(View):
    def get(self, request):
        return render(request, "contact.html", storefront_context())

    def post(self, request):
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message = request.POST.get("message", "").strip()

        errors = {}

        if not name:
            errors["name_error_message"] = "Name is required."
        elif len(name) < 2:
            errors["name_error_message"] = "Name must be at least 2 characters."

        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not email:
            errors["email_error_message"] = "Email is required."
        elif not re.match(email_regex, email):
            errors["email_error_message"] = "Enter a valid email address."

        if phone and len(phone) < 10:
            errors["phone_error_message"] = "Enter a valid mobile number."

        if not message:
            errors["msg_error_message"] = "Message is required."
        elif len(message) < 10:
            errors["msg_error_message"] = "Message must be at least 10 characters."

        if errors:
            return JsonResponse(errors, status=400)

        send_email(name, email, phone, message)
        try:
            save_contact(name, email, phone, message)
        except Exception:
            pass

        return JsonResponse(
            {"success_message": "Your message has been sent successfully."}
        )


class RobotsView(View):
    def get(self, request):
        return render(request, "robots.txt", content_type="text/plain")


class CartView(View):
    def get(self, request):
        cart = request.session.get("cart", {})
        cart_items = list(cart.values())
        for item in cart_items:
            item["subtotal"] = round(float(item["price"]) * int(item["qty"]), 2)
        cart_total = sum(item["subtotal"] for item in cart_items)
        return render(
            request,
            "cart.html",
            storefront_context(cart_items=cart_items, cart_total=cart_total),
        )


class AddToCartView(View):
    def post(self, request):
        product_id = request.POST.get("product_id")
        qty = int(request.POST.get("qty", 1))

        product = fetch_product_by_id(product_id)
        if product is None:
            return JsonResponse(
                {"success": False, "message": "Product not found."}, status=404
            )

        first_image = product.image_set.first()
        image_url = first_image.image if first_image else ""

        cart = request.session.get("cart", {})
        key = str(product_id)
        if key in cart:
            cart[key]["qty"] += qty
        else:
            cart[key] = {
                "product_id": product_id,
                "name": product.name,
                "price": str(product.price) if product.price is not None else "0",
                "qty": qty,
                "image": image_url,
                "slug": product.slug,
            }
        request.session["cart"] = cart
        request.session.modified = True
        cart_count = sum(item["qty"] for item in cart.values())
        return JsonResponse(
            {
                "success": True,
                "cart_count": cart_count,
                "message": f'"{product.name}" added to cart!',
            }
        )


class UpdateCartView(View):
    def post(self, request):
        product_id = str(request.POST.get("product_id"))
        action = request.POST.get("action")  # 'increment', 'decrement', 'remove'
        cart = request.session.get("cart", {})
        if product_id in cart:
            if action == "increment":
                cart[product_id]["qty"] += 1
            elif action == "decrement":
                # Clamp at 1 rather than deleting. The page keeps showing a
                # quantity of 1 after this call, so deleting here left the row
                # on screen while the item was already gone from the session —
                # and removed it without the user ever asking. Removal is the
                # trash button's job.
                cart[product_id]["qty"] = max(1, cart[product_id]["qty"] - 1)
            elif action == "remove":
                del cart[product_id]
        request.session["cart"] = cart
        request.session.modified = True
        cart_count = sum(item["qty"] for item in cart.values())
        cart_items = list(cart.values())
        cart_total = sum(float(item["price"]) * int(item["qty"]) for item in cart_items)
        return JsonResponse(
            {"success": True, "cart_count": cart_count, "cart_total": cart_total}
        )
