"""
Comando personalizzato Django: compile_po

Compila i file .po in file .mo senza bisogno di GNU gettext.
Usa la libreria Python 'polib' per leggere i .po e
il modulo standard 'gettext' per scrivere i .mo.

USO:
    python manage.py compile_po
        -> compila tutti i file .po in .mo

Questo comando sostituisce 'python manage.py compilemessages'
quando GNU gettext non e' installato.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import os
import polib


class Command(BaseCommand):
    help = 'Compila i file .po in .mo senza GNU gettext'

    def handle(self, *args, **options):
        locale_path = os.path.join(settings.BASE_DIR, 'locale')

        if not os.path.exists(locale_path):
            self.stdout.write(self.style.ERROR(f"[ERROR] Directory locale non trovata: {locale_path}"))
            return

        compiled_count = 0

        # Cerca tutti i file .po
        for lang_dir in os.listdir(locale_path):
            lang_path = os.path.join(locale_path, lang_dir)
            if not os.path.isdir(lang_path):
                continue

            po_path = os.path.join(lang_path, 'LC_MESSAGES', 'django.po')
            mo_path = os.path.join(lang_path, 'LC_MESSAGES', 'django.mo')

            if not os.path.exists(po_path):
                continue

            try:
                self.stdout.write(f"[COMPILE] {po_path}")

                # Carica il file .po
                po = polib.pofile(po_path)

                # Compila in .mo
                po.save_as_mofile(mo_path)

                compiled_count += 1
                self.stdout.write(f"  [OK] -> {mo_path}")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [ERROR] {e}"))

        if compiled_count > 0:
            self.stdout.write(self.style.SUCCESS(f"\n[OK] Compilati {compiled_count} file .mo"))
            self.stdout.write("Riavvia il server Django per vedere le traduzioni.")
        else:
            self.stdout.write(self.style.WARNING("[WARN] Nessun file .po trovato da compilare"))
