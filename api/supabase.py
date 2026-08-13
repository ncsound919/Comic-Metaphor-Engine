"""Lazy Supabase client singleton.

Returns None (dev mode) when SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are
unset, so local dev and CI run without any Supabase configuration.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client


@lru_cache(maxsize=1)
def get_sb() -> Optional[Client]:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url and not key:
        return None
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must both be set")
    return create_client(url, key)
