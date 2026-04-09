"""
VÍA 1: Meta Graph API (oficial)
================================
Requisitos previos:
  1. App en developers.facebook.com con permisos:
     - instagram_basic
     - instagram_manage_messages
     - instagram_manage_insights  (para leer seguidores)
  2. Token de larga duración (60 días, renovable).
  3. Cuenta de Instagram Business conectada a una Página de Facebook.

Limitaciones conocidas:
  - El endpoint /followers requiere aprobación de App Review avanzada.
  - El envío de DMs vía API solo funciona si el usuario te escribió primero
    (ventana de 7 días) O si tienes acceso a "Human Agent" o "Mensajes Patrocinados".
  - Para cuentas pequeñas, Meta suele rechazar el App Review. En ese caso usa browser_approach.py.
"""

import os
import time
import requests
from dotenv import load_dotenv
from db import init_db, find_new_followers, save_known_followers, is_already_messaged, mark_as_messaged

load_dotenv()

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
IG_USER_ID   = os.getenv("INSTAGRAM_USER_ID")
WELCOME_MSG  = os.getenv("WELCOME_MESSAGE", "Hola {username}! Gracias por seguirme.")
BASE_URL     = "https://graph.facebook.com/v19.0"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict) -> dict:
    params["access_token"] = ACCESS_TOKEN
    r = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(endpoint: str, payload: dict) -> dict:
    payload["access_token"] = ACCESS_TOKEN
    r = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=15)
    r.raise_for_status()
    return r.json()


# ── Obtener seguidores con paginación ──────────────────────────────────────────

def get_all_followers() -> list[dict]:
    """
    Endpoint: GET /{ig-user-id}/followers
    Requiere permiso: instagram_manage_insights
    Devuelve lista de {"id": "...", "username": "..."}
    """
    followers = []
    params = {"fields": "id,username", "limit": 50}
    endpoint = f"/{IG_USER_ID}/followers"

    while True:
        data = _get(endpoint, params)
        followers.extend(data.get("data", []))

        # Paginación cursor-based
        next_cursor = data.get("paging", {}).get("cursors", {}).get("after")
        if not next_cursor or not data.get("paging", {}).get("next"):
            break
        params["after"] = next_cursor
        time.sleep(1)  # respetar rate limits

    return followers


# ── Enviar DM ─────────────────────────────────────────────────────────────────

def send_dm(recipient_id: str, username: str) -> bool:
    """
    Endpoint: POST /{ig-user-id}/messages
    Requiere permiso: instagram_manage_messages
    NOTA: Solo funciona si el usuario interactuó contigo en los últimos 7 días.
    """
    message = WELCOME_MSG.format(username=username)
    try:
        _post(f"/{IG_USER_ID}/messages", {
            "recipient": {"id": recipient_id},
            "message": {"text": message},
        })
        print(f"  ✓ DM enviado a @{username} ({recipient_id})")
        return True
    except requests.HTTPError as e:
        print(f"  ✗ Error enviando DM a @{username}: {e.response.text}")
        return False


# ── Verificar token ───────────────────────────────────────────────────────────

def check_token():
    """Imprime info del token y avisa si está por expirar."""
    data = _get("/debug_token", {
        "input_token": ACCESS_TOKEN,
        "access_token": ACCESS_TOKEN,
    })
    info = data.get("data", {})
    expires = info.get("expires_at", 0)
    days_left = (expires - time.time()) / 86400 if expires else 0
    print(f"Token válido: {info.get('is_valid')} | Expira en: {days_left:.0f} días")
    if days_left < 7:
        print("  ⚠️  Token próximo a vencer. Renuévalo.")


# ── Flujo principal ───────────────────────────────────────────────────────────

def run_once():
    print("\n[API] Iniciando ciclo de verificación...")
    check_token()

    print("[API] Obteniendo seguidores...")
    current_followers = get_all_followers()
    print(f"[API] Total seguidores encontrados: {len(current_followers)}")

    new_followers = find_new_followers(current_followers)
    print(f"[API] Nuevos seguidores a contactar: {len(new_followers)}")

    for follower in new_followers:
        uid = follower["id"]
        uname = follower.get("username", uid)

        if is_already_messaged(uid):
            continue

        success = send_dm(uid, uname)
        if success:
            mark_as_messaged(uid, uname)

        # Delay entre mensajes (8-15 segundos) para simular comportamiento humano
        delay = __import__("random").uniform(8, 15)
        print(f"  → Esperando {delay:.1f}s antes del próximo DM...")
        time.sleep(delay)

    # Actualizar base de datos con todos los seguidores conocidos
    save_known_followers(current_followers)
    print("[API] Ciclo completado.\n")


if __name__ == "__main__":
    init_db()
    run_once()
