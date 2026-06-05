from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views import View
from categories.models import Category
from .models import Contact
from products.models import Product, Image
import re

from .email import send_email
# Create your views here.


class HomePageView(View):
    def get(self, request):
        categories = Category.objects.all()

        products = Product.objects.prefetch_related("category", "image_set").all()

        context = {
            "categories": categories,
            "products": products,
        }
        return render(request, "home.html", context)


class Single_Product(View):
    def get(self, request, slug):
        categories = Category.objects.all()
        product = Product.objects.prefetch_related("category", "image_set").get(
            slug=slug
        )
        products = Product.objects.prefetch_related("category", "image_set").all()
        return render(
            request,
            "single_product.html",
            {"categories": categories, "product": product,"products":products},
        )


class ContactView(View):
    def get(self, request):
        categories = Category.objects.all()
        products = Product.objects.prefetch_related("category", "image_set").all()
        return render(
            request, "contact.html", {"categories": categories, "products": products}
        )

    def post(self, request):
        name = request.POST.get("name", "").strip()

        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        message = request.POST.get("message", "").strip()

        errors = {}

        # Name validation
        if not name:
            errors["name_error_message"] = "Name is required."
        elif len(name) < 2:
            errors["name_error_message"] = "Name must be at least 2 characters."

        # Email validation
        email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        if not email:
            errors["email_error_message"] = "Email is required."
        elif not re.match(email_regex, email):
            errors["email_error_message"] = "Enter a valid email address."

        if phone:
            if len(phone) < 10:
                errors["phone_error_message"] = "Enter a valid mobile number."

        # Message validation
        if not message:
            errors["msg_error_message"] = "Message is required."
        elif len(message) < 10:
            errors["msg_error_message"] = "Message must be at least 10 characters."

        # If any errors → return them
        if errors:
            return JsonResponse(errors, status=400)

        # ---- SUCCESS CASE ----
        # Save to DB / send email / log entry here
        send_email(name, email, phone, message)
        contact = Contact(
            name=name, email=email, phone=phone if phone else "", message=message
        )
        contact.save()

        return JsonResponse(
            {"success_message": "Your message has been sent successfully."}
        )


class RobotsView(View):
    def get(self, request):
        return render(request, "robots.txt", content_type="text/plain")


class CartView(View):
    def get(self, request):
        categories = Category.objects.all()
        products = Product.objects.prefetch_related("category", "image_set").all()
        cart = request.session.get('cart', {})
        cart_items = list(cart.values())
        for item in cart_items:
            item['subtotal'] = round(float(item['price']) * int(item['qty']), 2)
        cart_total = sum(item['subtotal'] for item in cart_items)
        return render(request, 'cart.html', {
            'categories': categories,
            'products': products,
            'cart_items': cart_items,
            'cart_total': cart_total,
        })


class AddToCartView(View):
    def post(self, request):
        product_id = request.POST.get('product_id')
        qty = int(request.POST.get('qty', 1))
        try:
            product = Product.objects.prefetch_related('image_set').get(id=product_id)
            first_image = product.image_set.first()
            image_url = first_image.image if first_image else ''

            cart = request.session.get('cart', {})
            key = str(product_id)
            if key in cart:
                cart[key]['qty'] += qty
            else:
                cart[key] = {
                    'product_id': product_id,
                    'name': product.name,
                    'price': str(product.price) if product.price else '0',
                    'qty': qty,
                    'image': image_url,
                    'slug': product.slug,
                }
            request.session['cart'] = cart
            request.session.modified = True
            cart_count = sum(item['qty'] for item in cart.values())
            return JsonResponse({'success': True, 'cart_count': cart_count, 'message': f'"{product.name}" added to cart!'})
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Product not found.'}, status=404)


class UpdateCartView(View):
    def post(self, request):
        product_id = str(request.POST.get('product_id'))
        action = request.POST.get('action')  # 'increment', 'decrement', 'remove'
        cart = request.session.get('cart', {})
        if product_id in cart:
            if action == 'increment':
                cart[product_id]['qty'] += 1
            elif action == 'decrement':
                if cart[product_id]['qty'] > 1:
                    cart[product_id]['qty'] -= 1
                else:
                    del cart[product_id]
            elif action == 'remove':
                del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True
        cart_count = sum(item['qty'] for item in cart.values())
        cart_items = list(cart.values())
        cart_total = sum(float(item['price']) * int(item['qty']) for item in cart_items)
        return JsonResponse({'success': True, 'cart_count': cart_count, 'cart_total': cart_total})
