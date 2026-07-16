import json

from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from . import auth as auth_helper
from . import supabase_ops as ops
from .storage import upload_image


def _catalogue_to_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    if isinstance(value, (dict,)):
        return json.dumps(value, indent=2)
    return str(value)


# ---------- Auth ---------- #

def login_view(request):
    if auth_helper.is_authenticated(request):
        return redirect("dashboard:index")
    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        if auth_helper.check_credentials(username, password):
            auth_helper.login(request)
            next_url = request.GET.get("next") or reverse("dashboard:index")
            return HttpResponseRedirect(next_url)
        error = "Invalid username or password."
    return render(request, "dashboard/login.html", {"error": error})


@require_http_methods(["GET", "POST"])
def logout_view(request):
    auth_helper.logout(request)
    return redirect("dashboard:login")


# ---------- Home ---------- #

@auth_helper.login_required
def index(request):
    try:
        counts = ops.dashboard_counts()
    except Exception as e:
        counts = {"products": 0, "categories": 0, "images": 0, "contacts": 0}
        messages.error(request, f"Could not load counts: {e}")
    return render(request, "dashboard/index.html", {"counts": counts})


# ---------- Categories ---------- #

@auth_helper.login_required
def categories_list(request):
    return render(
        request,
        "dashboard/categories_list.html",
        {"categories": ops.list_categories()},
    )


@auth_helper.login_required
def category_new(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Category name is required.")
        else:
            try:
                ops.create_category(name, request.POST.get("description", ""))
                messages.success(request, f'Category "{name}" created.')
                return redirect("dashboard:categories_list")
            except Exception as e:
                messages.error(request, f"Could not create category: {e}")
    return render(
        request,
        "dashboard/category_form.html",
        {"category": None, "mode": "new"},
    )


@auth_helper.login_required
def category_edit(request, cat_id):
    category = ops.get_category(cat_id)
    if not category:
        messages.error(request, "Category not found.")
        return redirect("dashboard:categories_list")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if not name:
            messages.error(request, "Category name is required.")
        else:
            try:
                ops.update_category(cat_id, name, request.POST.get("description", ""))
                messages.success(request, "Category updated.")
                return redirect("dashboard:categories_list")
            except Exception as e:
                messages.error(request, f"Could not update category: {e}")
    return render(
        request,
        "dashboard/category_form.html",
        {"category": category, "mode": "edit"},
    )


@auth_helper.login_required
@require_POST
def category_delete(request, cat_id):
    try:
        count = ops.category_product_count(cat_id)
        if count:
            messages.error(
                request,
                f"Cannot delete — {count} product(s) still linked to this category.",
            )
        else:
            ops.delete_category(cat_id)
            messages.success(request, "Category deleted.")
    except Exception as e:
        messages.error(request, f"Could not delete category: {e}")
    return redirect("dashboard:categories_list")


# ---------- Products ---------- #

@auth_helper.login_required
def products_list(request):
    return render(
        request,
        "dashboard/products_list.html",
        {"products": ops.list_products()},
    )


@auth_helper.login_required
def product_new(request):
    if request.method == "POST":
        try:
            new_id = ops.create_product(request.POST)
            messages.success(request, "Product created. Now add its images.")
            return redirect("dashboard:product_edit", product_id=new_id)
        except Exception as e:
            messages.error(request, f"Could not create product: {e}")
    return render(
        request,
        "dashboard/product_form.html",
        {
            "product": None,
            "images": [],
            "categories": ops.list_categories(),
            "catalogue_text": "",
            "mode": "new",
        },
    )


@auth_helper.login_required
def product_edit(request, product_id):
    product = ops.get_product(product_id)
    if not product:
        messages.error(request, "Product not found.")
        return redirect("dashboard:products_list")

    if request.method == "POST":
        try:
            ops.update_product(product_id, request.POST)
            messages.success(request, "Product updated.")
            return redirect("dashboard:product_edit", product_id=product_id)
        except Exception as e:
            messages.error(request, f"Could not update product: {e}")

    return render(
        request,
        "dashboard/product_form.html",
        {
            "product": product,
            "images": ops.list_product_images(product_id),
            "categories": ops.list_categories(),
            "catalogue_text": _catalogue_to_text(product.get("catalogue")),
            "mode": "edit",
        },
    )


@auth_helper.login_required
@require_POST
def product_delete(request, product_id):
    try:
        ops.delete_product(product_id)
        messages.success(request, "Product deleted.")
    except Exception as e:
        messages.error(request, f"Could not delete product: {e}")
    return redirect("dashboard:products_list")


# ---------- Product Images (AJAX endpoints, tied to a product) ---------- #

@auth_helper.login_required
@require_POST
def product_image_upload(request, product_id):
    """Accepts multipart file upload(s) OR a pasted image URL. Returns JSON."""
    if not ops.get_product(product_id):
        return JsonResponse({"success": False, "error": "Product not found"}, status=404)

    saved = []
    errors = []

    files = request.FILES.getlist("files")
    for f in files:
        try:
            url = upload_image(f)
            ops.add_product_image(product_id, url)
            saved.append(url)
        except Exception as e:
            errors.append(f"{f.name}: {e}")

    pasted = (request.POST.get("url") or "").strip()
    if pasted:
        try:
            ops.add_product_image(product_id, pasted)
            saved.append(pasted)
        except Exception as e:
            errors.append(f"pasted url: {e}")

    return JsonResponse(
        {
            "success": bool(saved) and not errors,
            "saved": saved,
            "errors": errors,
            "images": ops.list_product_images(product_id),
        }
    )


@auth_helper.login_required
@require_POST
def product_image_delete(request, image_id):
    try:
        ops.delete_product_image(image_id)
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


# ---------- Contacts ---------- #

@auth_helper.login_required
def contacts_list(request):
    return render(
        request,
        "dashboard/contacts_list.html",
        {"contacts": ops.list_contacts()},
    )


@auth_helper.login_required
@require_POST
def contact_delete(request, contact_id):
    try:
        ops.delete_contact(contact_id)
        messages.success(request, "Query deleted.")
    except Exception as e:
        messages.error(request, f"Could not delete: {e}")
    return redirect("dashboard:contacts_list")
