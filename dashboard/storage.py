import mimetypes
import os
import re
import uuid
from urllib.parse import urlparse

from product_listings.supabase_client import get_client


def bucket_name():
    return os.environ.get("SUPABASE_STORAGE_BUCKET", "product-images")


def _ensure_bucket(client, name):
    """Create the storage bucket (public) if it doesn't already exist. Safe to call repeatedly."""
    try:
        client.storage.get_bucket(name)
        return
    except Exception:
        pass
    try:
        client.storage.create_bucket(
            name,
            options={"public": True},
        )
    except Exception:
        pass


def _slugify(value):
    value = re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-")
    return value.lower() or "file"


def upload_image(uploaded_file):
    """
    Upload a Django UploadedFile-like object to the Supabase Storage bucket.
    Returns the public URL string.
    """
    client = get_client()
    name = bucket_name()
    _ensure_bucket(client, name)

    original = getattr(uploaded_file, "name", "upload.bin")
    stem, ext = os.path.splitext(original)
    ext = (ext or "").lower()
    safe_stem = _slugify(stem)[:40] or "img"
    path = f"products/{uuid.uuid4().hex}-{safe_stem}{ext}"

    content_type = (
        getattr(uploaded_file, "content_type", None)
        or mimetypes.guess_type(original)[0]
        or "application/octet-stream"
    )

    data = uploaded_file.read()
    client.storage.from_(name).upload(
        path=path,
        file=data,
        file_options={"content-type": content_type, "upsert": "false"},
    )
    return client.storage.from_(name).get_public_url(path).rstrip("?")


def delete_by_url(url):
    """Best-effort delete of a stored object by its public URL. Silent on failure."""
    if not url:
        return
    client = get_client()
    name = bucket_name()
    try:
        parsed = urlparse(url)
        marker = f"/object/public/{name}/"
        idx = parsed.path.find(marker)
        if idx == -1:
            return
        object_path = parsed.path[idx + len(marker):]
        if object_path:
            client.storage.from_(name).remove([object_path])
    except Exception:
        pass
