# 🔐 Configurazione OAuth per Login Social (Facebook e Google)

## 📋 Prerequisiti

Prima di configurare il login social, devi:

1. **Installare le dipendenze**:
```bash
pip install -r requirements.txt
```

2. **Eseguire le migrazioni**:
```bash
python manage.py migrate
```

3. **Creare/aggiornare il Site**:
```bash
python manage.py shell
```
Poi nel shell:
```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'  # o il tuo dominio in produzione
site.name = 'Rhome Book'
site.save()
```

## 🔑 Configurazione Google OAuth

### 1. Crea un progetto su Google Cloud Console

1. Vai a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuovo progetto o seleziona un progetto esistente
3. Abilita l'**Google+ API** (se non già abilitata)

### 2. Crea le credenziali OAuth 2.0

1. Vai su **APIs & Services > Credentials**
2. Clicca su **Create Credentials > OAuth client ID**
3. Se è la prima volta, configura la schermata di consenso OAuth
4. Come tipo di applicazione, seleziona **Web application**
5. Configura:
   - **Name**: Rhome Book (o il nome che preferisci)
   - **Authorized JavaScript origins**: 
     - Per sviluppo: `http://localhost:8000`
     - Per produzione: `https://tuodominio.com`
   - **Authorized redirect URIs**:
     - Per sviluppo: `http://localhost:8000/accounts/google/login/callback/`
     - Per produzione: `https://tuodominio.com/accounts/google/login/callback/`

6. Salva e copia il **Client ID** e **Client Secret**
CLient ID 743759743853-hd3l5gultmbi18rcanh7onhdkb2qea9r.apps.googleusercontent.com
Secret: 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
### 3. Configura in Django

Aggiungi le variabili d'ambiente o in `settings.py` (non consigliato per produzione):

```python
# In settings.py, aggiungi:
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': 'TUO_GOOGLE_CLIENT_ID',
            'secret': 'TUO_GOOGLE_CLIENT_SECRET',
            'key': ''
        }
    }
}
```

**OPPURE** (CONSIGLIATO) usa variabili d'ambiente:

Crea un file `.env` nella root del progetto:
```
GOOGLE_CLIENT_ID=tuo_client_id_qui
GOOGLE_CLIENT_SECRET=tuo_client_secret_qui
FACEBOOK_APP_ID=tuo_app_id_qui
FACEBOOK_APP_SECRET=tuo_app_secret_qui
```

Poi in `settings.py`:
```python
import os
from decouple import config

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID', default=''),
            'secret': config('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        }
    }
}
```

## 📘 Configurazione Facebook OAuth

### 1. Crea un'app su Facebook Developers

1. Vai a [Facebook Developers](https://developers.facebook.com/)
2. Clicca su **My Apps > Create App**
3. Seleziona **Consumer** come tipo di app
4. Compila le informazioni base dell'app

### 2. Configura Facebook Login

1. Nel dashboard dell'app, vai su **Add Product**
2. Aggiungi **Facebook Login**
3. Vai su **Settings > Basic**
4. Aggiungi:
   - **App Domains**: `localhost` (sviluppo) o il tuo dominio (produzione)
   - **Site URL**: 
     - Sviluppo: `http://localhost:8000`
     - Produzione: `https://tuodominio.com`
5. Vai su **Settings > Advanced**
6. Aggiungi nelle **Valid OAuth Redirect URIs**:
   - Sviluppo: `http://localhost:8000/accounts/facebook/login/callback/`
   - Produzione: `https://tuodominio.com/accounts/facebook/login/callback/`

### 3. Ottieni App ID e Secret

1. Vai su **Settings > Basic**
2. Copia **App ID** e **App Secret**

### 4. Configura in Django

In `settings.py`:

```python
SOCIALACCOUNT_PROVIDERS = {
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': [
            'id',
            'first_name',
            'last_name',
            'middle_name',
            'name',
            'name_format',
            'picture',
            'short_name',
            'email'
        ],
        'EXCHANGE_TOKEN': True,
        'LOCALE_FUNC': lambda request: 'it_IT',
        'VERIFIED_EMAIL': False,
        'VERSION': 'v18.0',
        'APP': {
            'client_id': config('FACEBOOK_APP_ID', default=''),
            'secret': config('FACEBOOK_APP_SECRET', default=''),
        }
    }
}
```

## 🔧 Configurazione tramite Admin Django

**Alternativa più semplice**: Configura tramite l'admin Django invece di modificare settings.py:

1. Dopo aver installato django-allauth, vai su `/admin/`
2. Aggiungi un **Site** se non esiste (Sites > Sites)
3. Vai su **Social Applications** (Social Accounts > Social applications)
4. Clicca **Add Social Application**
5. Compila:
   - **Provider**: Seleziona Google o Facebook
   - **Name**: Nome dell'applicazione
   - **Client id**: Il Client ID / App ID
   - **Secret key**: Il Client Secret / App Secret
   - **Sites**: Seleziona il sito (sposta da "Available sites" a "Chosen sites")
6. Salva

## ✅ Verifica Configurazione

1. Avvia il server: `python manage.py runserver`
2. Vai su `/accounts/login/`
3. Dovresti vedere i bottoni "Accedi con Google" e "Accedi con Facebook"
4. Clicca su uno di essi per testare

## 🚨 Note Importanti

- **NON committare mai** Client ID e Secret nel repository Git
- Usa variabili d'ambiente o un file `.env` (non committato)
- In produzione, usa HTTPS
- Aggiorna gli URI di redirect quando cambi dominio
- Per Google, assicurati che la schermata di consenso OAuth sia pubblicata (per utenti esterni)

## 📚 Risorse Utili

- [Django Allauth Docs](https://django-allauth.readthedocs.io/)
- [Google OAuth Setup](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Setup](https://developers.facebook.com/docs/facebook-login/web)

