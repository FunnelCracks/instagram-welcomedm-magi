"""
Bot de bienvenida para Instagram
Usa instagrapi (no necesita navegador, funciona en la nube)
"""

import os
import time
import random
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from db import init_db, find_new_followers, save_known_followers, is_already_messaged, mark_as_messaged

load_dotenv()

IG_USERNAME   = os.getenv("IG_USERNAME", "")
IG_PASSWORD   = os.getenv("IG_PASSWORD", "")
WELCOME_MSG   = os.getenv("WELCOME_MESSAGE", "Hola {username}! Gracias por seguirme.")
MAX_DMS_HOUR  = int(os.getenv("MAX_DMS_PER_HOUR", "15"))
SESSION_FILE  = "session.json"

DM_DELAY_MIN  = 60    # segundos mínimos entre DMs
DM_DELAY_MAX  = 180   # segundos máximos entre DMs


def login() -> Client:
    cl = Client()
    cl.delay_range = [2, 5]  # delays automáticos entre requests

    # Intentar cargar sesión guardada primero
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("[Login] Sesión restaurada correctamente.")
            return cl
        except LoginRequired:
            print("[Login] Sesión expirada, iniciando sesión nueva...")

    # Login normal
    cl.login(IG_USERNAME, IG_PASSWORD)
    cl.dump_settings(SESSION_FILE)
    print("[Login] Sesión iniciada y guardada.")
    return cl


def get_followers(cl: Client) -> list[dict]:
    user_id = cl.user_id_from_username(IG_USERNAME)
    followers_raw = cl.user_followers(user_id, amount=0)  # 0 = todos
    followers = [
        {"id": str(uid), "username": user.username}
        for uid, user in followers_raw.items()
    ]
    print(f"[Seguidores] Total: {len(followers)}")
    return followers


def send_dm(cl: Client, user_id: str, username: str) -> bool:
    message = WELCOME_MSG.format(username=username)
    try:
        cl.direct_send(message, user_ids=[int(user_id)])
        print(f"  ✓ Mensaje enviado a @{username}")
        return True
    except ClientError as e:
        print(f"  ✗ Error enviando a @{username}: {e}")
        return False


def run_once():
    print("\n[Bot] Iniciando ciclo...")

    cl = login()

    print("[Bot] Obteniendo seguidores...")
    current_followers = get_followers(cl)

    new_followers = find_new_followers(current_followers)
    print(f"[Bot] Nuevos seguidores a contactar: {len(new_followers)}")

    dms_sent = 0

    for follower in new_followers:
        if dms_sent >= MAX_DMS_HOUR:
            print(f"[Bot] Límite de {MAX_DMS_HOUR} mensajes alcanzado por este ciclo.")
            break

        uid   = follower["id"]
        uname = follower.get("username", uid)

        if is_already_messaged(uid):
            continue

        success = send_dm(cl, uid, uname)

        if success:
            mark_as_messaged(uid, uname)
            dms_sent += 1

            if dms_sent < len(new_followers):
                delay = random.uniform(DM_DELAY_MIN, DM_DELAY_MAX)
                print(f"  → Esperando {delay/60:.1f} minutos...")
                time.sleep(delay)
        else:
            time.sleep(random.uniform(15, 30))

    save_known_followers(current_followers)
    print(f"[Bot] Ciclo terminado. Mensajes enviados: {dms_sent}\n")


if __name__ == "__main__":
    init_db()
    run_once()
