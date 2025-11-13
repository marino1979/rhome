# 📦 Guida Installazione Dipendenze - Rhome Book

## ⚠️ IMPORTANTE: Attiva l'ambiente virtuale PRIMA di tutto!

L'errore `ModuleNotFoundError: No module named 'allauth'` si verifica perché l'ambiente virtuale non è attivo.

## 🔧 Passi da seguire

### 1. **Attiva l'ambiente virtuale**

Apri PowerShell o CMD e vai nella directory del progetto:

```powershell
cd C:\Users\utente\Documents\python\booking_env\Rhome_book
```

**Poi attiva l'ambiente virtuale:**

```powershell
# Windows PowerShell
.\booking_env\Scripts\Activate.ps1

# OPPURE se non funziona, usa questo:
booking_env\Scripts\activate

# Se ancora non funziona, prova:
.\booking_env\Scripts\python.exe -m pip install ...
```

**Verifica che sia attivo:**
Dovresti vedere `(booking_env)` all'inizio della riga del prompt.

### 2. **Installa tutte le dipendenze**

Una volta attivato l'ambiente virtuale, esegui:

```powershell
pip install -r requirements.txt
```

Questo installerà:
- Django
- django-allauth (con tutte le dipendenze)
- djangorestframework
- django-modeltranslation
- requests
- PyJWT
- cryptography
- E tutte le altre dipendenze

### 3. **Esegui le migrazioni**

```powershell
python manage.py migrate
```

### 4. **Verifica l'installazione**

```powershell
python manage.py check
```

Dovrebbe dire "System check identified no issues"

### 5. **Avvia il server**

```powershell
python manage.py runserver
```

## 🐛 Risoluzione Problemi

### Problema: "ModuleNotFoundError: No module named 'allauth'"

**Causa**: Ambiente virtuale non attivo o pacchetti installati nel Python globale invece che nel virtualenv.

**Soluzione**:
1. Verifica che l'ambiente virtuale sia attivo: `(booking_env)` deve apparire nel prompt
2. Se non è attivo, attivalo: `booking_env\Scripts\activate`
3. Reinstalla le dipendenze: `pip install -r requirements.txt`

### Problema: Comando `activate` non funziona

**Soluzione PowerShell**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\booking_env\Scripts\Activate.ps1
```

### Verifica quale Python stai usando

```powershell
python --version
where python
```

Dovresti vedere un path che contiene `booking_env` se l'ambiente è attivo.

## ✅ Verifica rapida

Esegui questo comando per verificare:

```powershell
python -c "import sys; print('Python:', sys.executable); import allauth; print('allauth OK')"
```

Se funziona, vedrai:
```
Python: C:\Users\utente\Documents\python\booking_env\Scripts\python.exe
allauth OK
```

Se fallisce, significa che l'ambiente virtuale non è attivo o i pacchetti non sono installati.

## 📝 Note

- **SEMPRE** attiva l'ambiente virtuale prima di eseguire `python manage.py`
- Se installi pacchetti con `pip`, assicurati che l'ambiente virtuale sia attivo
- L'ambiente virtuale è nella directory `booking_env` alla stessa altezza di `Rhome_book`

