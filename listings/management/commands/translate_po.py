"""
Comando personalizzato Django: translate_po

Questo comando traduce automaticamente i file .po del progetto
(usualmente in locale/<lingua>/LC_MESSAGES/django.po)
utilizzando l'API di DeepL.

Funziona su tutte le lingue definite nella variabile TARGETS.
Per ogni voce msgid, traduce e sovrascrive msgstr.

USO:
    python manage.py translate_po
        → traduce tutti i msgstr (anche se già compilati)

    python manage.py translate_po --only-empty
        → traduce solo le voci con msgstr vuoto

    python manage.py translate_po --dry-run
        → simula la traduzione, stampa ma non salva

    python manage.py translate_po --only-empty --dry-run
        → mostra solo le traduzioni mancanti, senza toccare i file

Dopo l'uso, ricordarsi di compilare i messaggi:
    python manage.py compilemessages

⚠️ È richiesto:
- avere i file django.po nelle cartelle corrette
- impostare una chiave DeepL valida nella variabile DEEPL_API_KEY
"""

from django.core.management.base import BaseCommand
import polib
import requests
import time
import os

DEEPL_API_KEY = 'dee4f3b5-ef0c-4819-a840-ccecc390e001:fx'
DEEPL_API_URL = 'https://api-free.deepl.com/v2/translate'

TARGETS = [
    ('en', 'EN'),
    ('es', 'ES')
]

def translate_text(text, target_lang):
    if not text.strip():
        return ''
    response = requests.post(DEEPL_API_URL, data={
        'auth_key': DEEPL_API_KEY,
        'text': text,
        'source_lang': 'IT',
        'target_lang': target_lang
    })
    response.raise_for_status()
    return response.json()['translations'][0]['text']

def translate_po_file(locale_code, deepl_code, only_empty=False, dry_run=False):
    po_path = os.path.join('locale', locale_code, 'LC_MESSAGES', 'django.po')
    if not os.path.exists(po_path):
        print(f"⚠️ File non trovato: {po_path}")
        return

    print(f"🔄 Traducendo {po_path} (solo vuoti: {only_empty}, dry-run: {dry_run})")
    po = polib.pofile(po_path)

    for entry in po:
        if entry.msgid and not entry.obsolete and not entry.msgid.startswith('['):
            if only_empty and entry.msgstr:
                continue
            try:
                traduzione = translate_text(entry.msgid, deepl_code)
                print(f"✅ {entry.msgid} → {traduzione}")
                if not dry_run:
                    entry.msgstr = traduzione
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ Errore con '{entry.msgid}': {e}")

    if not dry_run:
        po.save()
        print(f"💾 File aggiornato: {po_path}")
    else:
        print(f"🧪 Dry-run attivo: nessuna modifica salvata per {locale_code}")

class Command(BaseCommand):
    help = 'Traduce i file .po usando DeepL'

    def add_arguments(self, parser):
        parser.add_argument('--only-empty', action='store_true', help='Traduce solo msgstr vuoti')
        parser.add_argument('--dry-run', action='store_true', help='Simula la traduzione senza salvare i file')

    def handle(self, *args, **options):
        only_empty = options['only_empty']
        dry_run = options['dry_run']
        for locale_code, deepl_code in TARGETS:
            translate_po_file(locale_code, deepl_code, only_empty, dry_run)
        self.stdout.write(self.style.SUCCESS("✅ Traduzione completata!"))
