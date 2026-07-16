"""CRUD helpers used by the admin dashboard.

Table names match those already used in product_listings.supabase_data:
    - Category
    - Products
    - Product_Images (columns: id, product_id, image, created_at)
    - Contact       (columns: id, name, email, phone, message, created_at)
"""

import json
import re

from product_listings.supabase_client import get_client


# ---------- helpers ---------- #

def _slugify(value):
    value = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").lower()).strip("-")
    return value or "product"


def _to_decimal_or_none(v):
    if v in (None, ""):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _to_int_or_none(v):
    if v in (None, ""):
        return None
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _catalogue_from_form(raw):
    """Accept a JSON string or newline/comma-separated URL list. Returns list/dict or None."""
    if not raw:
        return None
    raw = raw.strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        pass
    parts = [p.strip() for p in re.split(r"[\n,]+", raw) if p.strip()]
    return parts or None


# ---------- Categories ---------- #

def list_categories():
    client = get_client()
    return (
        client.table("Category").select("*").order("id").execute().data or []
    )


def get_category(cat_id):
    client = get_client()
    res = client.table("Category").select("*").eq("id", cat_id).limit(1).execute()
    return (res.data or [None])[0]


def create_category(name, description):
    client = get_client()
    payload = {"name": name.strip(), "description": (description or "").strip() or None}
    client.table("Category").insert(payload).execute()


def update_category(cat_id, name, description):
    client = get_client()
    payload = {"name": name.strip(), "description": (description or "").strip() or None}
    client.table("Category").update(payload).eq("id", cat_id).execute()


def delete_category(cat_id):
    client = get_client()
    client.table("Category").delete().eq("id", cat_id).execute()


def category_product_count(cat_id):
    client = get_client()
    res = (
        client.table("Products")
        .select("id", count="exact")
        .eq("category_id", cat_id)
        .execute()
    )
    return res.count or 0


# ---------- Products ---------- #

def list_products():
    """Returns products with joined category name and image count."""
    client = get_client()
    prods = (
        client.table("Products")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )
    if not prods:
        return []

    cat_ids = list({p["category_id"] for p in prods if p.get("category_id")})
    cat_map = {}
    if cat_ids:
        cats = (
            client.table("Category").select("id,name").in_("id", cat_ids).execute().data
            or []
        )
        cat_map = {c["id"]: c["name"] for c in cats}

    prod_ids = [p["id"] for p in prods]
    img_rows = (
        client.table("Product_Images")
        .select("product_id")
        .in_("product_id", prod_ids)
        .execute()
        .data
        or []
    )
    img_counts = {}
    for r in img_rows:
        img_counts[r["product_id"]] = img_counts.get(r["product_id"], 0) + 1

    for p in prods:
        p["category_name"] = cat_map.get(p.get("category_id"))
        p["image_count"] = img_counts.get(p["id"], 0)
    return prods


def get_product(product_id):
    client = get_client()
    res = (
        client.table("Products").select("*").eq("id", product_id).limit(1).execute()
    )
    return (res.data or [None])[0]


def list_product_images(product_id):
    client = get_client()
    return (
        client.table("Product_Images")
        .select("*")
        .eq("product_id", product_id)
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )


def _product_payload(form):
    name = (form.get("name") or "").strip()
    slug = (form.get("slug") or "").strip() or _slugify(name)
    description = (form.get("description") or "").strip() or None
    description_html = (form.get("description_html") or "").strip() or None
    price = _to_decimal_or_none(form.get("price"))
    size = (form.get("size") or "").strip() or None
    category_id = _to_int_or_none(form.get("category_id"))
    catalogue = _catalogue_from_form(form.get("catalogue"))

    payload = {
        "name": name,
        "slug": slug,
        "description": description,
        "description_html": description_html,
        "price": price,
        "size": size,
        "category_id": category_id,
        "catalogue": catalogue,
    }
    return payload


def create_product(form):
    client = get_client()
    payload = _product_payload(form)
    res = client.table("Products").insert(payload).execute()
    row = (res.data or [None])[0]
    return row["id"] if row else None


def update_product(product_id, form):
    client = get_client()
    payload = _product_payload(form)
    client.table("Products").update(payload).eq("id", product_id).execute()


def delete_product(product_id):
    """Deletes the product, its Product_Images rows, and best-effort deletes uploaded files."""
    from .storage import delete_by_url  # avoid circular

    client = get_client()
    images = list_product_images(product_id)
    for img in images:
        delete_by_url(img.get("image"))
    client.table("Product_Images").delete().eq("product_id", product_id).execute()
    client.table("Products").delete().eq("id", product_id).execute()


# ---------- Product Images ---------- #

def add_product_image(product_id, url):
    client = get_client()
    client.table("Product_Images").insert(
        {"product_id": product_id, "image": url}
    ).execute()


def delete_product_image(image_id):
    from .storage import delete_by_url

    client = get_client()
    row = (
        client.table("Product_Images")
        .select("*")
        .eq("id", image_id)
        .limit(1)
        .execute()
        .data
        or [None]
    )[0]
    if row:
        delete_by_url(row.get("image"))
    client.table("Product_Images").delete().eq("id", image_id).execute()


# ---------- Contacts ---------- #

def list_contacts():
    client = get_client()
    return (
        client.table("Contact")
        .select("*")
        .order("id", desc=True)
        .execute()
        .data
        or []
    )


def delete_contact(contact_id):
    client = get_client()
    client.table("Contact").delete().eq("id", contact_id).execute()


# ---------- Dashboard summary ---------- #

def dashboard_counts():
    client = get_client()
    def _count(table):
        return (
            client.table(table).select("id", count="exact").limit(1).execute().count
            or 0
        )
    return {
        "products": _count("Products"),
        "categories": _count("Category"),
        "images": _count("Product_Images"),
        "contacts": _count("Contact"),
    }
