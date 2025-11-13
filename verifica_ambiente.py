#!/usr/bin/env python
"""
Script per verificare che tutte le dipendenze siano installate correttamente.
"""

import sys
import os

print("=" * 60)
print("VERIFICA AMBIENTE PYTHON")
print("=" * 60)
print(f"Python eseguibile: {sys.executable}")
print(f"Python versione: {sys.version}")
print(f"Ambiente virtuale: {os.environ.get('VIRTUAL_ENV', 'NON ATTIVO')}")
print()

print("=" * 60)
print("VERIFICA DIPENDENZE")
print("=" * 60)

dipendenze = [
    'django',
    'allauth',
    'rest_framework',
    'modeltranslation',
    'requests',
    'jwt',
    'cryptography',
    'PIL',
]

for dep in dipendenze:
    try:
        if dep == 'PIL':
            import PIL
            print(f"OK {dep}: {PIL.__version__}")
        elif dep == 'jwt':
            import jwt
            print(f"OK {dep}: {jwt.__version__}")
        elif dep == 'requests':
            import requests
            print(f"OK {dep}: {requests.__version__}")
        elif dep == 'cryptography':
            import cryptography
            print(f"OK {dep}: {cryptography.__version__}")
        elif dep == 'django':
            import django
            print(f"OK {dep}: {django.__version__}")
        elif dep == 'allauth':
            import allauth
            print(f"OK {dep}: {allauth.__version__}")
        elif dep == 'rest_framework':
            import rest_framework
            print(f"OK {dep}: {rest_framework.__version__}")
        elif dep == 'modeltranslation':
            import modeltranslation
            print(f"OK {dep}: OK")
    except ImportError as e:
        print(f"ERRORE {dep}: MANCANTE - {e}")

print()
print("=" * 60)
print("VERIFICA DJANGO SETUP")
print("=" * 60)

try:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Rhome_book.settings')
    import django
    django.setup()
    print("OK Django setup completato con successo")
    
    from django.contrib.sites.models import Site
    site = Site.objects.get(id=1)
    print(f"OK Site configurato: {site.domain}")
    
except Exception as e:
    print(f"✗ Errore Django setup: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

