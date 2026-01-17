# 🔐 Configurazione OAuth per Social Login

## ✅ Installazione completata

Il social login è stato configurato nel progetto. Ora devi solo configurare le credenziali OAuth per Google e Facebook.

## 📋 Passi per configurare OAuth

### 1. Configurare il Site in Django Admin

1. Vai su `http://127.0.0.1:8000/admin/`
2. Vai su **Sites** → **Sites**
3. Modifica il sito esistente (di solito `example.com`):
   - **Domain name**: `127.0.0.1:8000` (per sviluppo locale) o il tuo dominio in produzione
   - **Display name**: `Rhome Book`
4. Salva

### 2. Configurare Google OAuth

1. Vai su [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o seleziona uno esistente
3. Vai su **APIs & Services** → **Credentials**
4. Clicca su **Create Credentials** → **OAuth client ID**
5. Se richiesto, configura la **OAuth consent screen**:
   - **Application name**: Rhome Book
   - **User support email**: la tua email
   - **Authorized domains**: lascia vuoto per sviluppo locale
   - **Developer contact**: la tua email
6. Crea le **OAuth Client ID**:
   - **Application type**: Web application
   - **Name**: Rhome Book Web Client
   - **Authorized JavaScript origins**:
     - `http://127.0.0.1:8000` (sviluppo)
     - `http://localhost:8000` (sviluppo)
   - **Authorized redirect URIs**:
     - `http://127.0.0.1:8000/accounts/google/login/callback/`
     - `http://localhost:8000/accounts/google/login/callback/`
7. Copia **Client ID** e **Client Secret**
8. Vai su Django Admin → **Social applications**
9. Clicca su **Add social application**
10. Compila:
    - **Provider**: Google
    - **Name**: Google OAuth
    - **Client id**: (incolla il Client ID)
    - **Secret key**: (incolla il Client Secret)
    - **Sites**: Seleziona il sito (127.0.0.1:8000)
11. Salva

### 3. Configurare Facebook OAuth

1. Vai su [Facebook Developers](https://developers.facebook.com/)
2. Clicca su **My Apps** → **Create App**
3. Seleziona **Consumer** come tipo di app
4. Compila:
   - **App name**: Rhome Book
   - **App contact email**: la tua email
5. Vai su **Settings** → **Basic**
6. Aggiungi **App Domains**: `127.0.0.1` (per sviluppo)
7. Vai su **Products** → **Facebook Login** → **Settings**
8. Aggiungi **Valid OAuth Redirect URIs**:
   - `http://127.0.0.1:8000/accounts/facebook/login/callback/`
   - `http://localhost:8000/accounts/facebook/login/callback/`
9. Vai su **Settings** → **Basic** e copia:
   - **App ID**
   - **App Secret** (clicca su "Show")
10. Vai su Django Admin → **Social applications**
11. Clicca su **Add social application**
12. Compila:
    - **Provider**: Facebook
    - **Name**: Facebook OAuth
    - **Client id**: (incolla l'App ID)
    - **Secret key**: (incolla l'App Secret)
    - **Sites**: Seleziona il sito (127.0.0.1:8000)
13. Salva

## 🚀 Test

1. Riavvia il server Django:
   ```bash
   python manage.py runserver
   ```

2. Vai su:
   - `http://127.0.0.1:8000/accounts/login/`
   - `http://127.0.0.1:8000/accounts/register/`

3. Dovresti vedere i pulsanti **Google** e **Facebook**

4. Clicca su un pulsante e verifica che il login funzioni

## ⚠️ Note importanti

- **Per sviluppo locale**: Usa `127.0.0.1:8000` o `localhost:8000`
- **Per produzione**: Dovrai aggiungere il dominio reale in:
  - Google Cloud Console (Authorized domains, JavaScript origins, Redirect URIs)
  - Facebook Developers (App Domains, Valid OAuth Redirect URIs)
  - Django Admin (Site domain)
- **Facebook**: Potrebbe richiedere la verifica dell'app per utenti esterni
- **Google**: Potrebbe mostrare un warning di sicurezza per app non verificate (normale in sviluppo)

## 🔧 Troubleshooting

### Errore "Redirect URI mismatch"
- Verifica che gli URI redirect in Google/Facebook corrispondano esattamente a quelli in Django
- Includi sia `127.0.0.1:8000` che `localhost:8000`

### I pulsanti non appaiono
- Verifica che le Social Applications siano configurate correttamente in Django Admin
- Verifica che il sito sia configurato correttamente
- Controlla che `SOCIALACCOUNT_PROVIDERS` sia configurato in `settings.py`

### Errore durante il login
- Controlla i log del server Django per errori dettagliati
- Verifica che le credenziali (Client ID e Secret) siano corrette
- Assicurati che il sito in Django Admin corrisponda al dominio usato

