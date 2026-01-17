"""
Comando personalizzato Django: extract_trans

Estrae le stringhe {% trans "..." %} e {% blocktrans %}...{% endblocktrans %}
dai template HTML e le aggiunge ai file .po senza bisogno di GNU gettext.

USO:
    python manage.py extract_trans
        → estrae le stringhe e aggiorna i file .po

    python manage.py extract_trans --dry-run
        → mostra le stringhe trovate senza modificare i file

Dopo l'uso, eseguire:
    python manage.py translate_po --only-empty
    python manage.py compilemessages (richiede gettext solo per compilare)
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
import polib
from datetime import datetime


class Command(BaseCommand):
    help = 'Estrae le stringhe {% trans %} dai template e le aggiunge ai file .po'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Mostra le stringhe senza modificare i file')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Directory dei template
        template_dirs = [
            os.path.join(settings.BASE_DIR, 'templates'),
        ]

        # Aggiungi le directory delle app
        for app in ['listings', 'bookings', 'account', 'amenities', 'rooms', 'users']:
            app_template_dir = os.path.join(settings.BASE_DIR, app, 'templates')
            if os.path.exists(app_template_dir):
                template_dirs.append(app_template_dir)

        # Estrai tutte le stringhe
        all_strings = {}

        for template_dir in template_dirs:
            if os.path.exists(template_dir):
                self.stdout.write(f"[SCAN] Scansione: {template_dir}")
                strings = self.extract_from_directory(template_dir)
                all_strings.update(strings)

        self.stdout.write(f"\n[INFO] Trovate {len(all_strings)} stringhe uniche\n")

        if dry_run:
            self.stdout.write("[DRY-RUN] Stringhe trovate:\n")
            for string, locations in sorted(all_strings.items()):
                self.stdout.write(f"  - {string}")
                for loc in locations:
                    self.stdout.write(f"      -> {loc}")
            return

        # Aggiorna i file .po per ogni lingua
        languages = [code for code, name in settings.LANGUAGES if code != 'it']

        for lang_code in languages:
            po_path = os.path.join(settings.BASE_DIR, 'locale', lang_code, 'LC_MESSAGES', 'django.po')
            self.update_po_file(po_path, all_strings, lang_code)

        self.stdout.write(self.style.SUCCESS("\n[OK] Estrazione completata!"))
        self.stdout.write("Ora esegui: python manage.py translate_po --only-empty")

    def extract_from_directory(self, directory):
        """Estrae le stringhe da tutti i file HTML nella directory"""
        strings = {}

        for root, dirs, files in os.walk(directory):
            # Ignora directory nascoste e di backup
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']

            for filename in files:
                if filename.endswith('.html'):
                    filepath = os.path.join(root, filename)
                    file_strings = self.extract_from_file(filepath)

                    for string in file_strings:
                        if string not in strings:
                            strings[string] = []
                        rel_path = os.path.relpath(filepath, settings.BASE_DIR)
                        if rel_path not in strings[string]:
                            strings[string].append(rel_path)

        return strings

    def extract_from_file(self, filepath):
        """Estrae le stringhe {% trans %} da un singolo file"""
        strings = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"[WARN] Errore lettura {filepath}: {e}"))
            return strings

        # Pattern per {% trans "string" %} e {% trans 'string' %}
        trans_pattern = r'\{%\s*trans\s+["\'](.+?)["\']\s*%\}'
        matches = re.findall(trans_pattern, content)
        strings.extend(matches)

        # Pattern per {% blocktrans %}...{% endblocktrans %}
        blocktrans_pattern = r'\{%\s*blocktrans\s*%\}(.+?)\{%\s*endblocktrans\s*%\}'
        block_matches = re.findall(blocktrans_pattern, content, re.DOTALL)
        for match in block_matches:
            # Pulisci il contenuto del blocktrans
            clean_match = ' '.join(match.split())
            if clean_match:
                strings.append(clean_match)

        return strings

    def update_po_file(self, po_path, strings, lang_code):
        """Aggiorna il file .po aggiungendo le nuove stringhe"""

        # Crea la directory se non esiste
        os.makedirs(os.path.dirname(po_path), exist_ok=True)

        # Carica o crea il file .po
        if os.path.exists(po_path):
            po = polib.pofile(po_path)
            self.stdout.write(f"[FILE] Aggiornamento: {po_path}")
        else:
            po = polib.POFile()
            po.metadata = {
                'Project-Id-Version': 'Rhome Book',
                'Report-Msgid-Bugs-To': '',
                'POT-Creation-Date': datetime.now().strftime('%Y-%m-%d %H:%M%z'),
                'PO-Revision-Date': datetime.now().strftime('%Y-%m-%d %H:%M%z'),
                'Last-Translator': '',
                'Language-Team': '',
                'Language': lang_code,
                'MIME-Version': '1.0',
                'Content-Type': 'text/plain; charset=UTF-8',
                'Content-Transfer-Encoding': '8bit',
                'Plural-Forms': 'nplurals=2; plural=(n != 1);',
            }
            self.stdout.write(f"[FILE] Creazione: {po_path}")

        # Ottieni le stringhe già presenti
        existing_msgids = {entry.msgid for entry in po}

        # Aggiungi le nuove stringhe
        added = 0
        for string, locations in strings.items():
            if string and string not in existing_msgids:
                entry = polib.POEntry(
                    msgid=string,
                    msgstr='',
                    occurrences=[(loc, '') for loc in locations]
                )
                po.append(entry)
                added += 1
                self.stdout.write(f"  [+] Aggiunta: {string[:50]}...")

        # Salva il file
        po.save(po_path)
        self.stdout.write(f"  [SAVED] {added} nuove stringhe aggiunte a {lang_code}")
