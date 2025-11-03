#!/usr/bin/env python3
"""Container healthcheck script."""

from __future__ import annotations

import os
import sys
from typing import NoReturn
from urllib.error import URLError, HTTPError
from urllib.request import Request, urlopen


def main() -> NoReturn:
    port = os.environ.get("PORT", "8000")
    url = f"http://127.0.0.1:{port}/health"

    try:
        request = Request(url, method="GET")
        with urlopen(request, timeout=5) as response:
            status = response.getcode()
            if status >= 400:
                raise HTTPError(url, status, "Unhealthy response", hdrs=None, fp=None)
    except (URLError, HTTPError, TimeoutError, OSError) as exc:  # pragma: no cover
        print(f"Healthcheck failed: {exc}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
