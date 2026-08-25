"""Static file URLs that carry a content stamp.

Vercel serves `static/` straight off the deployment filesystem, so there is no
manifest/hashing step to rename files. Instead every URL that `{% static %}`
emits gets a `?v=` stamp derived from the file itself. Filenames stay stable,
but the URL changes the moment the file does — which is what lets the CDN and
the browser cache each asset for a year without ever serving a stale one.
"""

import hashlib
import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage
from django.core.exceptions import SuspiciousFileOperation


class VersionedStaticFilesStorage(StaticFilesStorage):
    _STAMP_LENGTH = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stamps = {}

    def _absolute_path(self, name):
        """Where `name` actually lives — STATIC_ROOT first, then the finders
        (third-party apps such as tinymce ship their own static dirs)."""
        try:
            path = self.path(name)
        except (SuspiciousFileOperation, ValueError):
            path = None
        if path and os.path.exists(path):
            return path
        return finders.find(name)

    def _stamp(self, name):
        path = self._absolute_path(name)
        if not path:
            return ""
        try:
            stat = os.stat(path)
        except OSError:
            return ""
        digest = hashlib.md5(
            f"{stat.st_mtime_ns}:{stat.st_size}".encode(), usedforsecurity=False
        )
        return digest.hexdigest()[: self._STAMP_LENGTH]

    def _cached_stamp(self, name):
        # In DEBUG the file is edited while the process lives, so re-stat every
        # time; in production the deployment is immutable, so stat once.
        if settings.DEBUG:
            return self._stamp(name)
        if name not in self._stamps:
            self._stamps[name] = self._stamp(name)
        return self._stamps[name]

    def url(self, name):
        url = super().url(name)
        stamp = self._cached_stamp(name)
        if not stamp:
            return url
        return f"{url}{'&' if '?' in url else '?'}v={stamp}"
