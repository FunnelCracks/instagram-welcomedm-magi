"""
Bot de bienvenida para Instagram
Usa instagrapi (no necesita navegador, funciona en la nube)
"""

import os
import time
import random
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
from db import init_db, find_new_followers, save_known_followers, is_already_messaged, mark_as_messaged

SESSION_FILE  = "session.json"
DM_DELAY_MIN  = 60    # segundos mínimos entre DMs
DM_DELAY_MAX  = 180   # segundos máximos entre DMs


def get_config():
    """Lee las variables de entorno en el momento de ejecutar, no al importar."""
    username = os.getenv("IG_USERNAME", "").strip()
    password = os.getenv("IG_PASSWORD", "").strip()
    message  = os.getenv("WELCOME_MESSAGE", "Hola! Gracias por seguirme.").replace('\\n', '\n')
    max_dms  = int(os.getenv("MAX_DMS_PER_HOUR", "15"))
    print(f"[Config] Usuario: '{username}' | Password cargada: {'Sí' if password else 'No'}")
    return username, password, message, max_dms


def login(username: str, password: str) -> Client:
    cl = Client()
    cl.delay_range = [2, 5]  # delays automáticos entre requests

    # Intentar cargar sesión guardada primero
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            print("[Login] Sesión restaurada correctamente.")
            return cl
        except LoginRequired:
            print("[Login] Sesión expirada, iniciando sesión nueva...")

    # Login normal
    cl.login(username, password)
    cl.dump_settings(SESSION_FILE)
    print("[Login] Sesión iniciada y guardada.")
    return cl


def get_followers(cl: Client, username: str) -> list[dict]:
    user_id = cl.user_id_from_username(username)
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

    ig_username, ig_password, welcome_msg, max_dms = get_config()

    cl = login(ig_username, ig_password)

    print("[Bot] Obteniendo seguidores...")
    current_followers = get_followers(cl, ig_username)

    new_followers = find_new_followers(current_followers)
    print(f"[Bot] Nuevos seguidores a contactar: {len(new_followers)}")

    dms_sent = 0

    for follower in new_followers:
        if dms_sent >= max_dms:
            print(f"[Bot] Límite de {max_dms} mensajes alcanzado por este ciclo.")
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
