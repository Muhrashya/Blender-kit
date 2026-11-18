"""
Backward-compatible shim re-exporting all unified v3.0 handlers from mcp/blender_kit_mcp/handlers/.
Supports both package-relative and top-level sys.path imports inside Blender.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

try:
    from .handlers import *  # noqa: F401,F403
except ImportError:
    from handlers import *  # noqa: F401,F403
