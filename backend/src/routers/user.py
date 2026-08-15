import base64
import json

from fastapi import APIRouter

from backend.src.services.download_service import CookieManager
from backend.src.shanbei_api import ShanbayAPI

router = APIRouter(prefix="/api/user", tags=["用户"])


def _decode_jwt_payload(token: str) -> dict | None:
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None


def _extract_auth_token(cookie: str) -> str | None:
    for part in cookie.split(";"):
        if "=" in part:
            key, value = part.split("=", 1)
            if key.strip() == "auth_token":
                return value.strip().strip('"')
    return None


async def _get_user_status() -> dict:
    try:
        cookie = CookieManager().get_cookie("COOKIE")
    except Exception:  # noqa: BLE001
        return {"logged_in": False, "username": None, "avatar_url": None}

    if not cookie:
        return {"logged_in": False, "username": None, "avatar_url": None}

    token = _extract_auth_token(cookie)
    payload = _decode_jwt_payload(token) if token else None
    username = payload.get("username") if payload else None

    if not username:
        return {"logged_in": False, "username": None, "avatar_url": None}

    api = ShanbayAPI(cookie)
    try:
        book = await api.get_default_material_book()
        logged_in = book is not None
    except Exception:  # noqa: BLE001
        logged_in = False
    finally:
        await api.close()

    return {
        "logged_in": logged_in,
        "username": username if logged_in else None,
        "avatar_url": None,
    }


@router.get("/status")
async def user_status():
    return await _get_user_status()
