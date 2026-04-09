"""
Scheduler: ejecuta el bot cada hora (o el intervalo configurado en .env).

Uso:
  python scheduler.py --mode api       # usa Meta Graph API
  python scheduler.py --mode browser   # usa Playwright (recomendado para empezar)
  python scheduler.py --mode browser --run-now  # ejecuta una vez inmediatamente y luego agenda
"""

import os
import time
import argparse
import schedule
from dotenv import load_dotenv

load_dotenv(override=False)

INTERVAL = int(os.getenv("CHECK_INTERVAL_MINUTES", "60"))
print(f"[Scheduler] CHECK_INTERVAL_MINUTES={os.getenv('CHECK_INTERVAL_MINUTES', 'no encontrado')}")


def job(mode: str):
    if mode == "api":
        from api_approach import run_once
    else:
        from browser_approach import run_once
    try:
        run_once()
    except Exception as e:
        print(f"[Scheduler] Error en ciclo: {e}")


def main():
    parser = argparse.ArgumentParser(description="Instagram Welcome Bot Scheduler")
    parser.add_argument(
        "--mode", choices=["api", "browser"], default="browser",
        help="Método a usar: 'api' (Meta Graph API) o 'browser' (Playwright)"
    )
    parser.add_argument(
        "--run-now", action="store_true",
        help="Ejecutar inmediatamente además de agendar"
    )
    args = parser.parse_args()

    print(f"[Scheduler] Modo: {args.mode.upper()}")
    print(f"[Scheduler] Verificando cada {INTERVAL} minutos.")
    print("[Scheduler] Presiona Ctrl+C para detener.\n")

    if args.run_now:
        print("[Scheduler] Ejecutando ciclo inicial...")
        job(args.mode)

    schedule.every(INTERVAL).minutes.do(job, mode=args.mode)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
