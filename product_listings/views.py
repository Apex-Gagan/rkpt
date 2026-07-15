import re

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

from .email import send_email
from .supabase_data import (
    fetch_categories,
    fetch_product_by_id,
    fetch_product_by_slug,
    fetch_products,
    save_contact,
)


class HomePageView(View):
    def get(self, request):
        return render(
            request,
            "home.html",
            {
                "categories": fetch_categories(),
                "products": fetch_products(),
            },
        )


class Single_Product(View):
    def get(self, request, slug):
        product = fetch_product_by_slug(slug)
        return render(
            request,
            "single_product.html",
            {
                "categories": fetch_categories(),
                "product": product,
                "products": fetch_products(),
            },
        )


class ContactView(View):
    def get(self, request):
        return render(
            request,
            "contact.html",
            {
                "categories": fetch_categories(),
                "products": fetch_products(),
            },
        )

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
            {
                "categories": fetch_categories(),
                "products": fetch_products(),
                "cart_items": cart_items,
                "cart_total": cart_total,
            },
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
                if cart[product_id]["qty"] > 1:
                    cart[product_id]["qty"] -= 1
                else:
                    del cart[product_id]
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
