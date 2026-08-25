import difflib
import json
import re

from django.utils.text import slugify

from .supabase_client import get_client


class _RelatedManager:
    """Mimics Django's related-manager surface used by templates
    (`.all`, `.first`, iteration). Templates call these as methods."""

    def __init__(self, items):
        self._items = list(items or [])

    def all(self):
        return self._items

    def first(self):
        return self._items[0] if self._items else None

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)

    def __bool__(self):
        return bool(self._items)


class CategoryObj:
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name")
        self.description = data.get("description")
        self.created_at = data.get("created_at")
        # anchors like `#cat-cake-boxes` — used by the nav, footer and homepage
        self.slug = slugify(self.name or "") or f"category-{self.id}"

    @property
    def anchor(self):
        return f"cat-{self.slug}"

    def __str__(self):
        return self.name or ""


class ImageObj:
    def __init__(self, data):
        self.id = data.get("id")
        self.image = data.get("image")
        self.created_at = data.get("created_at")


class ProductObj:
    def __init__(self, data, images=None, category=None):
        self.id = data.get("id")
        self.name = data.get("name")
        self.description = data.get("description")
        self.description_html = data.get("description_html")
        self.price = data.get("price")
        self.size = data.get("size")
        self.slug = data.get("slug")
        self.created_at = data.get("created_at")

        raw_catalogue = data.get("catalogue")
        if isinstance(raw_catalogue, str) and raw_catalogue.strip():
            try:
                raw_catalogue = json.loads(raw_catalogue)
            except (json.JSONDecodeError, TypeError):
                raw_catalogue = None
        self.catalogue = raw_catalogue

        self.image_set = _RelatedManager(images or [])
        # single-FK on Supabase, but templates iterate `.category.all` (legacy M2M)
        self.category = _RelatedManager([category] if category else [])


def fetch_categories():
    client = get_client()
    resp = client.table("Category").select("*").order("id").execute()
    return [CategoryObj(row) for row in (resp.data or [])]


def fetch_products():
    client = get_client()

    prod_resp = (
        client.table("Products")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    products_data = prod_resp.data or []
    if not products_data:
        return []

    product_ids = [p["id"] for p in products_data]
    img_resp = (
        client.table("Product_Images")
        .select("*")
        .in_("product_id", product_ids)
        .order("created_at", desc=True)
        .execute()
    )
    images_by_product = {}
    for row in img_resp.data or []:
        images_by_product.setdefault(row["product_id"], []).append(ImageObj(row))

    category_ids = list({p["category_id"] for p in products_data if p.get("category_id")})
    categories_by_id = {}
    if category_ids:
        cat_resp = (
            client.table("Category").select("*").in_("id", category_ids).execute()
        )
        categories_by_id = {c["id"]: CategoryObj(c) for c in (cat_resp.data or [])}

    return [
        ProductObj(
            p,
            images=images_by_product.get(p["id"], []),
            category=categories_by_id.get(p.get("category_id")),
        )
        for p in products_data
    ]


def fetch_product_by_slug(slug):
    client = get_client()
    prod_resp = (
        client.table("Products").select("*").eq("slug", slug).limit(1).execute()
    )
    if not prod_resp.data:
        return None
    row = prod_resp.data[0]
    return _hydrate_product(row)


def fetch_product_by_id(product_id):
    client = get_client()
    prod_resp = (
        client.table("Products").select("*").eq("id", product_id).limit(1).execute()
    )
    if not prod_resp.data:
        return None
    return _hydrate_product(prod_resp.data[0])


def _hydrate_product(row):
    client = get_client()
    img_resp = (
        client.table("Product_Images")
        .select("*")
        .eq("product_id", row["id"])
        .order("created_at", desc=True)
        .execute()
    )
    images = [ImageObj(i) for i in (img_resp.data or [])]

    category = None
    if row.get("category_id"):
        cat_resp = (
            client.table("Category")
            .select("*")
            .eq("id", row["category_id"])
            .limit(1)
            .execute()
        )
        if cat_resp.data:
            category = CategoryObj(cat_resp.data[0])

    return ProductObj(row, images=images, category=category)


def save_contact(name, email, phone, message):
    client = get_client()
    phone_val = None
    if phone:
        try:
            phone_val = int("".join(ch for ch in str(phone) if ch.isdigit()) or 0)
        except (TypeError, ValueError):
            phone_val = None
    payload = {
        "name": name,
        "email": email or None,
        "phone": phone_val,
        "message": message,
    }
    client.table("Contact").insert(payload).execute()


# --------------------------------------------------------------------------
# Category grouping / related products
# --------------------------------------------------------------------------

# Words shared by nearly every product on a packaging catalogue — matching on
# them would make every product "related" to every other one.
_COMMON_WORDS = {
    "box",
    "boxes",
    "packaging",
    "packing",
    "packer",
    "packers",
    "custom",
    "customised",
    "customized",
    "printed",
    "printing",
    "pack",
    "the",
    "and",
    "with",
    "for",
}


def _name_tokens(name):
    return {
        token
        for token in re.findall(r"[a-z0-9]+", (name or "").lower())
        if len(token) > 2 and token not in _COMMON_WORDS
    }


def _name_similarity(a, b):
    """0-ish for unrelated names, higher the more two product names overlap.
    Shared distinctive words dominate; character ratio breaks ties."""
    shared = len(_name_tokens(a) & _name_tokens(b))
    ratio = difflib.SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()
    return shared * 3 + ratio


def group_products_by_category(categories=None, products=None):
    """Bucket products under their category, in category order.

    Returns a list of ``{"category", "products", "count", "anchor", "name"}``
    dicts. Empty categories are skipped and products without a category land in
    a trailing "More Packaging" group, so every group on the page has stock.
    """
    categories = fetch_categories() if categories is None else categories
    products = fetch_products() if products is None else products

    buckets = {category.id: [] for category in categories}
    uncategorised = []
    for product in products:
        category = product.category.first()
        if category is not None and category.id in buckets:
            buckets[category.id].append(product)
        else:
            uncategorised.append(product)

    groups = [
        {
            "category": category,
            "name": category.name,
            "anchor": category.anchor,
            "products": buckets[category.id],
            "count": len(buckets[category.id]),
        }
        for category in categories
        if buckets[category.id]
    ]

    if uncategorised:
        groups.append(
            {
                "category": None,
                "name": "More Packaging",
                "anchor": "cat-more",
                "products": uncategorised,
                "count": len(uncategorised),
            }
        )

    return groups


def fetch_related_products(product, limit=8, products=None):
    """Products worth showing under `product` — same category first, then the
    ones whose names look alike ("Cake Box" ↔ "Cake Box 10 Inch")."""
    if product is None:
        return []

    catalogue = fetch_products() if products is None else products
    own_category = product.category.first()
    own_category_id = own_category.id if own_category else None

    scored = []
    for candidate in catalogue:
        if candidate.id == product.id:
            continue
        candidate_category = candidate.category.first()
        score = _name_similarity(product.name, candidate.name)
        if (
            own_category_id is not None
            and candidate_category is not None
            and candidate_category.id == own_category_id
        ):
            score += 10
        scored.append((score, candidate))

    scored.sort(key=lambda item: (-item[0], item[1].name or ""))
    return [candidate for _, candidate in scored[:limit]]
