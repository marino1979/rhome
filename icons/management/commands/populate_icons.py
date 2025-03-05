# icons/management/commands/populate_icons.py

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from icons.models import IconCategory, Icon

class Command(BaseCommand):
    help = 'Popola il database con le icone Font Awesome Free'

    def handle(self, *args, **options):
        self.stdout.write("Inizio popolamento icone")
        
        # Prima puliamo il database
        Icon.objects.all().delete()
        IconCategory.objects.all().delete()
        
        # Categorie e icone verificate Font Awesome Free
        categories = {
            'Essenziali': [
                ('Wifi', 'fas fa-wifi'),
                ('Aria Condizionata', 'fas fa-snowflake'),
                ('TV', 'fas fa-tv'),
                ('Chiave', 'fas fa-key'),
                ('Casa', 'fas fa-home'),
            ],
            'Cucina': [
                ('Posate', 'fas fa-utensils'),
                ('Caffè', 'fas fa-mug-hot'),
                ('Acqua', 'fas fa-glass-water'),
                ('Fuoco', 'fas fa-fire'),
                ('Forno', 'fas fa-fire-burner'),
            ],
            'Bagno': [
                ('Vasca', 'fas fa-bath'),
                ('WC', 'fas fa-toilet'),
                ('Doccia', 'fas fa-shower'),
                ('Kit Cortesia', 'fas fa-pump-soap'),
                ('Asciugamani', 'fas fa-scroll'),
            ],
            'Camera': [
                ('Letto', 'fas fa-bed'),
                ('Vestiti', 'fas fa-shirt'),
                ('Armadio', 'fas fa-door-closed'),
                ('Ventilatore', 'fas fa-fan'),
                ('Notte', 'fas fa-moon'),
            ],
            'Spazi Comuni': [
                ('Divano', 'fas fa-couch'),
                ('Persone', 'fas fa-users'),
                ('TV', 'fas fa-tv'),
                ('Luce', 'fas fa-lightbulb'),
                ('Scrivania', 'fas fa-desk'),
            ],
            'Esterni': [
                ('Parcheggio', 'fas fa-square-parking'),
                ('Albero', 'fas fa-tree'),
                ('Piscina', 'fas fa-water-ladder'),
                ('Bicicletta', 'fas fa-bicycle'),
                ('Giardino', 'fas fa-leaf'),
            ],
            'Servizi': [
                ('Campanello', 'fas fa-bell'),
                ('Trasporto', 'fas fa-car'),
                ('Mappa', 'fas fa-map'),
                ('Informazioni', 'fas fa-circle-info'),
                ('Telefono', 'fas fa-phone'),
            ],
            'Sicurezza': [
                ('Telecamera', 'fas fa-video'),
                ('Allarme', 'fas fa-bell-on'),
                ('Pronto Soccorso', 'fas fa-kit-medical'),
                ('Sicurezza', 'fas fa-shield'),
                ('Lucchetto', 'fas fa-lock'),
            ],
            'Extra': [
                ('Check', 'fas fa-check'),
                ('Stella', 'fas fa-star'),
                ('Cuore', 'fas fa-heart'),
                ('Regalo', 'fas fa-gift'),
                ('Corona', 'fas fa-crown'),
            ]
        }

        for cat_name, icons in categories.items():
            self.stdout.write(f"Creo categoria: {cat_name}")
            
            category = IconCategory.objects.create(
                name=cat_name,
                slug=slugify(cat_name)
            )
            
            for icon_name, fa_class in icons:
                self.stdout.write(f"Creo icona: {icon_name} in {cat_name}")
                
                Icon.objects.create(
                    name=icon_name,
                    category=category,
                    icon_type='fa',
                    fa_class=fa_class,
                    is_active=True
                )

        # Verifica finale
        total_categories = IconCategory.objects.count()
        total_icons = Icon.objects.count()
        self.stdout.write(f"\nCreazione completata:")
        self.stdout.write(f"- Categorie create: {total_categories}")
        self.stdout.write(f"- Icone create: {total_icons}")
        
        self.stdout.write(self.style.SUCCESS('\nPopolamento completato con successo!'))