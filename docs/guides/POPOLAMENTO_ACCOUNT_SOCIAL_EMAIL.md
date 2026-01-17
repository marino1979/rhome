# 📧 Come vengono popolati Account Sociali e Indirizzi Email

## Panoramica

I modelli **SocialAccount** e **EmailAddress** vengono popolati **automaticamente** da `django-allauth` quando gli utenti interagiscono con il sistema di autenticazione. Non è necessario inserirli manualmente nell'admin.

---

## 🔐 Account Sociali (SocialAccount)

### Quando viene creato

Il record `SocialAccount` viene creato **automaticamente** quando:

1. **Un utente fa login con un provider social** (Google, Facebook, etc.)
   - L'utente clicca su "Accedi con Google" o "Accedi con Facebook"
   - Viene reindirizzato al provider OAuth
   - Dopo l'autorizzazione, viene reindirizzato di nuovo al sito
   - `django-allauth` crea automaticamente:
     - Un record `User` (se non esiste già)
     - Un record `SocialAccount` collegato all'utente

### Campi popolati automaticamente

- **`user`**: Collegamento all'utente Django
- **`provider`**: Nome del provider (es. "google", "facebook")
- **`uid`**: ID univoco dell'utente nel provider social
- **`date_joined`**: Data/ora di creazione dell'account social
- **`extra_data`**: Dati aggiuntivi dal provider (JSON)

### Esempio di flusso

```
1. Utente clicca "Accedi con Google"
2. Reindirizzamento a Google OAuth
3. Utente autorizza l'applicazione
4. Google reindirizza a /accounts/google/login/callback/
5. django-allauth crea automaticamente:
   - User (se non esiste)
   - SocialAccount (collegato all'utente)
   - EmailAddress (con l'email di Google)
```

---

## 📧 Indirizzi Email (EmailAddress)

### Quando viene creato

Il record `EmailAddress` viene creato **automaticamente** in diversi scenari:

#### 1. Registrazione normale (form di registrazione)

Quando un utente si registra tramite il form `/accounts/register/`:

```python
# users/views.py - register()
user = form.save()  # Crea User
# Crea EmailAddress per django-allauth
EmailAddress.objects.get_or_create(
    user=user,
    email=email,
    defaults={
        'verified': False,  # Non verificata al momento della registrazione
        'primary': True,    # Prima email = primaria
    }
)
```

**Nota:** La view `register()` crea automaticamente `EmailAddress` per mantenere la coerenza con django-allauth e permettere funzionalità future come la verifica email.

**Configurazione attuale:**
- `ACCOUNT_EMAIL_REQUIRED = True` → Email obbligatoria
- `ACCOUNT_EMAIL_VERIFICATION = 'optional'` → Verifica opzionale

#### 2. Login Social

Quando un utente fa login con un provider social:

- `django-allauth` recupera l'email dal provider
- Crea automaticamente un record `EmailAddress` con:
  - `email`: Email recuperata dal provider
  - `verified`: `True` se il provider ha verificato l'email, altrimenti `False`
  - `primary`: `True` se è la prima email associata all'utente

#### 3. Verifica Email (se abilitata)

Se `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`:

- Quando un utente si registra, riceve un'email di verifica
- Cliccando sul link, `verified` viene impostato a `True`

### Campi popolati automaticamente

- **`user`**: Collegamento all'utente Django
- **`email`**: Indirizzo email
- **`verified`**: `True` se l'email è verificata, `False` altrimenti
- **`primary`**: `True` se è l'email principale dell'utente
- **`created`**: Data/ora di creazione

---

## 🔄 Flusso Completo di Registrazione

### Scenario 1: Registrazione normale

```
1. Utente compila form di registrazione
2. Sistema crea User (users/views.py)
3. django-allauth crea automaticamente EmailAddress:
   - email: dall'input del form
   - verified: False (se ACCOUNT_EMAIL_VERIFICATION = 'optional')
   - primary: True
```

### Scenario 2: Login con Google

```
1. Utente clicca "Accedi con Google"
2. Autorizzazione OAuth
3. django-allauth crea automaticamente:
   - User (se non esiste)
   - SocialAccount:
     - provider: "google"
     - uid: ID Google dell'utente
   - EmailAddress:
     - email: email Google
     - verified: True (Google verifica le email)
     - primary: True
```

### Scenario 3: Login con Facebook

```
1. Utente clicca "Accedi con Facebook"
2. Autorizzazione OAuth
3. django-allauth crea automaticamente:
   - User (se non esiste)
   - SocialAccount:
     - provider: "facebook"
     - uid: ID Facebook dell'utente
   - EmailAddress:
     - email: email Facebook
     - verified: False (Facebook non verifica sempre)
     - primary: True
```

---

## ⚙️ Configurazione Attuale

Nel file `Rhome_book/settings.py`:

```python
# Email obbligatoria
ACCOUNT_EMAIL_REQUIRED = True

# Verifica email opzionale
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# Auto-signup per social login
SOCIALACCOUNT_AUTO_SIGNUP = True

# Login social con GET
SOCIALACCOUNT_LOGIN_ON_GET = True
```

**Cosa significa:**
- Gli utenti **devono** fornire un'email alla registrazione
- La verifica email è **opzionale** (non blocca l'accesso)
- Il login social crea automaticamente l'account
- Il login social funziona con una semplice richiesta GET

---

## 📊 Visualizzazione nell'Admin

Nell'admin Django, puoi vedere:

### Menu: "Autenticazione e Autorizzazione"

1. **Users** → Tutti gli utenti
2. **Groups** → Gruppi di permessi
3. **Permissions** → Permessi
4. **Social Applications** → Configurazione OAuth (Google, Facebook)
5. **Social Accounts** → Account social collegati agli utenti
6. **Email Addresses** → Indirizzi email degli utenti

### Relazioni

- **User** → **SocialAccount** (OneToMany)
- **User** → **EmailAddress** (OneToMany)
- **SocialAccount** → **SocialApp** (ForeignKey)

---

## 🔍 Verifica Manuale

Puoi verificare i record creati con il Django shell:

```python
# Attiva il virtual environment
cd C:\Users\utente\Documents\python\booking_env\Rhome_book
.\Scripts\activate

# Apri Django shell
python manage.py shell

# Importa i modelli
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User

# Vedi tutti gli account social
SocialAccount.objects.all()

# Vedi tutti gli indirizzi email
EmailAddress.objects.all()

# Vedi gli account social di un utente specifico
user = User.objects.get(username='nome_utente')
user.socialaccount_set.all()  # Account social
user.emailaddress_set.all()    # Indirizzi email
```

---

## ✅ Riepilogo

| Modello | Quando viene creato | Popolato da |
|---------|-------------------|-------------|
| **SocialAccount** | Login con provider social | django-allauth automaticamente |
| **EmailAddress** | Registrazione normale o login social | django-allauth automaticamente |

**Non è necessario inserire manualmente questi record!** Vengono creati automaticamente dal sistema quando gli utenti si registrano o fanno login.

---

## 🎯 Cosa puoi fare nell'Admin

Nell'admin puoi:

1. **Visualizzare** gli account social e le email degli utenti
2. **Modificare** lo stato di verifica delle email (campo `verified`)
3. **Impostare** un'email come primaria (campo `primary`)
4. **Eliminare** account social o email (se necessario)

Ma **non devi crearli manualmente** - vengono popolati automaticamente dal sistema!

