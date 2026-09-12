"""Skip decorators for optional dependencies."""

from __future__ import annotations

import importlib.util
import unittest

HAS_SHAPELY = importlib.util.find_spec("shapely") is not None

requires_shapely = unittest.skipUnless(HAS_SHAPELY, "requires the optional shapely dependency")
