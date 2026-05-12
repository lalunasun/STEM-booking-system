import mimetypes
from pathlib import Path

from django.http import FileResponse, Http404


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


def serve_frontend_asset(request, path):
    asset_path = (FRONTEND_DIST / path).resolve()
    if not str(asset_path).startswith(str(FRONTEND_DIST.resolve())):
        raise Http404("Invalid path")
    if not asset_path.exists() or asset_path.is_dir():
        raise Http404("Asset not found")

    content_type, _ = mimetypes.guess_type(str(asset_path))
    return FileResponse(open(asset_path, "rb"), content_type=content_type)


def serve_frontend_app(request, path=""):
    index_path = FRONTEND_DIST / "index.html"
    if not index_path.exists():
        raise Http404("Frontend build not found. Run npm run build first.")
    return FileResponse(open(index_path, "rb"), content_type="text/html")
