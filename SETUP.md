# Setup Guide — Instagram Welcome Bot

## Instalación rápida (5 minutos)

```bash
cd ~/instagram-welcome-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

Edita `.env` con tus valores:
```
WELCOME_MESSAGE=Hola {username}! Gracias por seguirme. Cualquier consulta escríbeme aquí.
IG_USERNAME=tu_usuario_sin_arroba
MAX_DMS_PER_HOUR=15
```

---

## VÍA 2 (recomendada para empezar): Playwright

### Paso 1: Guardar tu sesión de Instagram
```bash
python browser_approach.py --save-session
```
- Se abre Chrome visible
- Inicia sesión en Instagram normalmente
- Presiona ENTER en la terminal
- Las cookies se guardan en `cookies.json` (no las subas a git)

### Paso 2: Probar que funciona
```bash
python browser_approach.py
```

### Paso 3: Correr el scheduler cada hora
```bash
python scheduler.py --mode browser --run-now
```

---

## VÍA 1: Meta Graph API (oficial, más trabajo de setup)

### Paso 1: Crear App en Meta
1. Ve a https://developers.facebook.com/apps/
2. Crea una app tipo "Business"
3. Agrega el producto "Instagram Graph API"
4. En permisos solicita:
   - `instagram_basic`
   - `instagram_manage_messages`
   - `instagram_manage_insights` (para /followers — requiere App Review)

### Paso 2: Obtener token de larga duración
```bash
# Token de corta duración (desde el Graph API Explorer)
SHORT_TOKEN="tu_token_corto"
APP_ID="tu_app_id"
APP_SECRET="tu_app_secret"

curl "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=${APP_ID}&\
client_secret=${APP_SECRET}&\
fb_exchange_token=${SHORT_TOKEN}"
```
Copia el `access_token` resultante (válido 60 días) a tu `.env`.

### Paso 3: Obtener tu Instagram User ID
```bash
curl "https://graph.facebook.com/v19.0/me/accounts?access_token=TU_TOKEN"
# Usa el page_id de tu Página de Facebook

curl "https://graph.facebook.com/v19.0/{PAGE_ID}?fields=instagram_business_account&access_token=TU_TOKEN"
# El id resultante es tu IG_USER_ID
```

### Paso 4: Correr el scheduler
```bash
python scheduler.py --mode api --run-now
```

---

## Renovar token de Meta (cada ~50 días)
```bash
curl "https://graph.facebook.com/v19.0/oauth/access_token?\
grant_type=fb_exchange_token&\
client_id=${APP_ID}&\
client_secret=${APP_SECRET}&\
fb_exchange_token=${TU_TOKEN_ACTUAL}"
```

## Renovar sesión de Playwright (si expira la sesión)
```bash
python browser_approach.py --save-session
```
