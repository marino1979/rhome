# ⚠️ IMPORTANTE: Riavvia il server Django

## Problema
Il server Django sta ancora usando la configurazione vecchia con allauth attivo.

## Soluzione

### 1. **FERMA il server Django**
   - Premi `Ctrl+C` o `Ctrl+BREAK` nella finestra del terminale dove sta girando il server
   - Assicurati che il server sia completamente fermato

### 2. **Pulisci la cache**
   ```powershell
   # Rimuovi cache Python
   Get-ChildItem -Path . -Recurse -Filter "*.pyc" | Remove-Item -Force
   Get-ChildItem -Path . -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
   ```

### 3. **Riavvia il server**
   ```powershell
   python manage.py runserver
   ```

### 4. **Pulisci la cache del browser**
   - Premi `Ctrl+Shift+Delete` nel browser
   - Scegli "Cached images and files"
   - Oppure premi `Ctrl+F5` per un refresh completo

### 5. **Riprova**
   - Vai su `http://127.0.0.1:8000/accounts/login/`
   - Dovrebbe funzionare senza errori

## Verifica
Se ancora non funziona, verifica che il file `Rhome_book/settings.py` non contenga più allauth:
```powershell
Get-Content "Rhome_book\settings.py" | Select-String -Pattern "^    'allauth" 
```
Non dovrebbe restituire nessun risultato.

