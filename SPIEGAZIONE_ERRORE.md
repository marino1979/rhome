# 📚 Spiegazione Errore: NoReverseMatch

## 🎯 Cosa significa l'errore?

```
NoReverseMatch at /accounts/register/
Reverse for 'socialaccount_login' not found. 
'socialaccount_login' is not a valid view function or pattern name.
```

## 🔍 Analisi dell'Errore

### 1. **NoReverseMatch** 
- Significa che Django sta cercando di **risolvere un nome di URL** (reverse URL lookup)
- Nel template c'è un tag `{% url 'socialaccount_login' ... %}` che cerca di trovare l'URL corrispondente
- Django non trova questo nome URL nelle URL registrate

### 2. **Dove succede**
- **Pagina**: `/accounts/register/`
- **Template**: Durante il rendering del template `registration/register.html`
- **Riga**: Probabilmente una riga con `{% url 'socialaccount_login' provider='google' %}`

### 3. **Perché succede**
- Nel template c'è ancora un riferimento a `socialaccount_login`
- Django cerca questo URL nella lista delle URL registrate
- Ma `socialaccount_login` non è registrato perché:
  - Allauth non è in `INSTALLED_APPS` (è commentato)
  - Le URL di allauth sono disabilitate
  - Django non trova l'URL → Errore `NoReverseMatch`

## 🔄 Come funziona Django URL Resolution

1. **Template viene renderizzato** → Django trova `{% url 'socialaccount_login' ... %}`
2. **Django cerca l'URL** → Scansiona tutte le URL registrate in `urls.py`
3. **Non trova l'URL** → `socialaccount_login` non esiste nelle URL
4. **Errore** → `NoReverseMatch` perché Django non può risolvere l'URL

## 🔍 Cosa dobbiamo verificare

1. **Nel template c'è ancora il riferimento?**
   - Cerchiamo `{% url 'socialaccount_login'` nel file
   - Se c'è, dobbiamo rimuoverlo

2. **Django sta usando un template cached?**
   - Il server potrebbe avere template compilati in cache
   - Anche se il file è corretto, Django usa una versione vecchia

3. **Django sta caricando un template diverso?**
   - Potrebbe caricare template da allauth invece del nostro
   - Con `APP_DIRS: False` dovrebbe caricare solo i nostri template

## 🎯 Il Problema Reale

Il template **sul disco è corretto** (non contiene `socialaccount_login`), ma Django sta ancora usando una **versione cached** o sta caricando un **template diverso** che contiene quel riferimento.

## ✅ Soluzione

1. **Riavviare il server** per pulire la cache
2. **Verificare che Django carichi il nostro template** e non uno di allauth
3. **Se necessario, rimuovere completamente il codice** che fa riferimento a socialaccount

