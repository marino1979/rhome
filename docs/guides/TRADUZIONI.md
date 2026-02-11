# 🌍 Guida alle Traduzioni

Questa guida spiega come gestire le traduzioni nel progetto Rhome Book utilizzando i comandi personalizzati Django.

## 📋 Panoramica

Il progetto supporta la traduzione in più lingue utilizzando il sistema di internazionalizzazione (i18n) di Django. Le traduzioni sono gestite tramite file `.po` (Portable Object) che vengono poi compilati in file `.mo` (Machine Object) per l'utilizzo nell'applicazione.

## 🗂️ Struttura File

I file di traduzione si trovano nella seguente struttura:

```
locale/
├── en/
│   └── LC_MESSAGES/
│       ├── django.po
│       └── django.mo
└── es/
    └── LC_MESSAGES/
        ├── django.po
        └── django.mo
```

Le lingue supportate sono definite in `Rhome_book/settings.py` nella variabile `LANGUAGES`.

## 🔧 Comandi Disponibili

### 1. Estrazione Stringhe (`extract_trans`)

**Comando**: `python manage.py extract_trans`

**Descrizione**: Estrae automaticamente tutte le stringhe marcate con `{% trans "..." %}` e `{% blocktrans %}...{% endblocktrans %}` dai template HTML e le aggiunge ai file `.po` senza bisogno di GNU gettext.

**Uso**:
```bash
# Estrae le stringhe e aggiorna i file .po
python manage.py extract_trans

# Mostra le stringhe trovate senza modificare i file (dry-run)
python manage.py extract_trans --dry-run
```

**Cosa fa**:
- Scansiona tutte le directory dei template (`templates/` e le directory `templates/` delle app)
- Trova tutte le stringhe da tradurre
- Aggiunge le nuove stringhe ai file `.po` per ogni lingua configurata
- Mantiene le stringhe già esistenti

**Quando usarlo**: Dopo aver aggiunto nuove stringhe nei template o modificato testi esistenti.

---

### 2. Traduzione Automatica (`translate_po`)

**Comando**: `python manage.py translate_po`

**Descrizione**: Traduce automaticamente i file `.po` utilizzando l'API di DeepL. Supporta solo le traduzioni con `msgstr` vuoto o tutte le traduzioni.

**Uso**:
```bash
# Traduce tutte le voci (anche quelle già tradotte)
python manage.py translate_po

# Traduce solo le voci con msgstr vuoto (consigliato)
python manage.py translate_po --only-empty

# Simula la traduzione senza salvare (dry-run)
python manage.py translate_po --dry-run

# Combina le opzioni
python manage.py translate_po --only-empty --dry-run
```

**Opzioni**:
- `--only-empty`: Traduce solo le voci con `msgstr` vuoto (consigliato per evitare sovrascrivere traduzioni manuali)
- `--dry-run`: Mostra le traduzioni senza salvare i file

**Lingue supportate**:
- Inglese (`en`)
- Spagnolo (`es`)

**Nota**: Il comando usa DeepL API. La chiave API è configurata nel file `listings/management/commands/translate_po.py`. Se necessario, aggiorna la variabile `DEEPL_API_KEY`.

**Quando usarlo**: Dopo aver estratto nuove stringhe con `extract_trans`, per tradurle automaticamente.

---

### 3. Compilazione Traduzioni (`compilemessages`)

**Comando**: `python manage.py compilemessages`

**Descrizione**: Compila i file `.po` in file `.mo` binari che Django utilizza per le traduzioni. Richiede GNU gettext installato sul sistema.

**Uso**:
```bash
python manage.py compilemessages
```

**Requisiti**:
- GNU gettext deve essere installato sul sistema
- Su Windows: scarica da [GNU gettext for Windows](https://mlocati.github.io/articles/gettext-iconv-windows.html)
- Su Linux: `sudo apt-get install gettext` (Debian/Ubuntu) o `sudo yum install gettext` (CentOS/RHEL)
- Su macOS: `brew install gettext`

**Cosa fa**:
- Legge tutti i file `.po` nella directory `locale/`
- Compila ogni file `.po` in un corrispondente file `.mo`
- I file `.mo` vengono utilizzati da Django per servire le traduzioni

**Quando usarlo**: Dopo aver tradotto le stringhe con `translate_po` o dopo aver modificato manualmente i file `.po`.

---

## 📝 Workflow Completo

Il workflow tipico per aggiungere nuove traduzioni è il seguente:

### 1. Aggiungi stringhe nei template

Nel tuo template HTML, usa i tag Django per le traduzioni:

```django
{% load i18n %}

<h1>{% trans "Benvenuto" %}</h1>
<p>{% trans "Questo è un messaggio di benvenuto" %}</p>

{% blocktrans %}
Questo è un blocco di testo più lungo che può contenere
variabili come {{ variable_name }}.
{% endblocktrans %}
```

### 2. Estrai le stringhe

```bash
python manage.py extract_trans
```

Questo comando aggiungerà le nuove stringhe ai file `.po` per tutte le lingue configurate.

### 3. Traduci le stringhe

```bash
python manage.py translate_po --only-empty
```

Questo tradurrà automaticamente solo le nuove stringhe (quelle con `msgstr` vuoto).

### 4. Compila le traduzioni

```bash
python manage.py compilemessages
```

Questo compilerà i file `.po` in `.mo` per l'utilizzo nell'applicazione.

### 5. Riavvia il server

Dopo aver compilato le traduzioni, riavvia il server Django per vedere le modifiche:

```bash
python manage.py runserver
```

---

## ✏️ Modifica Manuale delle Traduzioni

Se preferisci modificare manualmente le traduzioni:

1. Apri il file `.po` corrispondente (es. `locale/en/LC_MESSAGES/django.po`)
2. Trova la voce `msgid` che vuoi tradurre
3. Modifica il campo `msgstr` con la traduzione:

```po
#: templates/listings/listing_detail.html:45
msgid "Benvenuto"
msgstr "Welcome"
```

4. Salva il file
5. Compila le traduzioni: `python manage.py compilemessages`

---

## 🔍 Verifica Traduzioni

Per verificare che le traduzioni funzionino correttamente:

1. Assicurati che i file `.mo` siano stati generati nella directory `locale/<lingua>/LC_MESSAGES/`
2. Imposta la lingua nel browser o nell'URL Django
3. Verifica che le stringhe vengano visualizzate nella lingua corretta

---

## ⚠️ Note Importanti

- **Sempre compilare dopo le modifiche**: Dopo aver modificato i file `.po`, ricorda sempre di eseguire `compilemessages`
- **Backup**: Prima di modificare manualmente i file `.po`, fai un backup
- **Formato**: I file `.po` sono sensibili alla formattazione. Non modificare la struttura del file manualmente
- **DeepL API**: Il comando `translate_po` usa DeepL API gratuita. Assicurati di non superare i limiti di utilizzo
- **Ordine delle operazioni**: Segui sempre l'ordine: `extract_trans` → `translate_po` → `compilemessages`

---

## 🐛 Risoluzione Problemi

### Errore: "Command 'msgfmt' not found"
- **Causa**: GNU gettext non è installato
- **Soluzione**: Installa gettext seguendo le istruzioni nella sezione "Compilazione Traduzioni"

### Le traduzioni non vengono visualizzate
- **Causa**: I file `.mo` non sono stati generati o sono obsoleti
- **Soluzione**: Esegui `python manage.py compilemessages` e riavvia il server

### Le nuove stringhe non vengono estratte
- **Causa**: I tag `{% trans %}` o `{% blocktrans %}` non sono corretti nel template
- **Soluzione**: Verifica che i template abbiano `{% load i18n %}` e che i tag siano corretti

### Errore DeepL API
- **Causa**: Chiave API non valida o limite superato
- **Soluzione**: Verifica la chiave API in `listings/management/commands/translate_po.py` o traduci manualmente

---

## 📚 Risorse Aggiuntive

- [Documentazione Django i18n](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [DeepL API Documentation](https://www.deepl.com/docs-api)
- [GNU gettext Manual](https://www.gnu.org/software/gettext/manual/)

---

**Ultimo aggiornamento**: Gennaio 2026
