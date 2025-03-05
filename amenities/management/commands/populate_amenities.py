from django.core.management.base import BaseCommand
from amenities.models import AmenityCategory, Amenity

class Command(BaseCommand):
    help = 'Popola il database con le categorie e le amenities predefinite'

    def handle(self, *args, **kwargs):
        # Definizione delle categorie
        categories = [
            {'name': 'Essenziali', 'icon': 'fa-home', 'order': 1},
            {'name': 'Caratteristiche', 'icon': 'fa-building', 'order': 2},
            {'name': 'Posizione', 'icon': 'fa-map-marker', 'order': 3},
            {'name': 'Sicurezza', 'icon': 'fa-shield', 'order': 4},
            {'name': 'Intrattenimento', 'icon': 'fa-tv', 'order': 5},
        ]

        # Creazione categorie
        for cat_data in categories:
            category, created = AmenityCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'order': cat_data['order']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creata categoria: {category.name}'))

        # Definizione amenities per categoria
        amenities = {
            'Essenziali': [
                {'name': 'Wi-Fi', 'icon': 'fa-wifi', 'is_popular': True},
                {'name': 'Aria condizionata', 'icon': 'fa-snowflake', 'is_popular': True},
                {'name': 'Riscaldamento', 'icon': 'fa-temperature-high', 'is_popular': True},
                {'name': 'Lavatrice', 'icon': 'fa-washing-machine', 'is_popular': True},
                {'name': 'Asciugatrice', 'icon': 'fa-dryer', 'is_popular': False},
                {'name': 'Ferro da stiro', 'icon': 'fa-iron', 'is_popular': False},
                {'name': 'TV', 'icon': 'fa-tv', 'is_popular': True},
                {'name': 'Cucina', 'icon': 'fa-kitchen-set', 'is_popular': True},
                {'name': 'Frigo', 'icon': 'fa-refrigerator', 'is_popular': True},
                {'name': 'Microonde', 'icon': 'fa-microwave', 'is_popular': False},
            ],
            'Caratteristiche': [
                {'name': 'Balcone', 'icon': 'fa-door-open', 'is_popular': True},
                {'name': 'Terrazza', 'icon': 'fa-umbrella-beach', 'is_popular': True},
                {'name': 'Vista città', 'icon': 'fa-city', 'is_popular': True},
                {'name': 'Ascensore', 'icon': 'fa-elevator', 'is_popular': True},
                {'name': 'Parcheggio', 'icon': 'fa-parking', 'is_popular': True},
                {'name': 'Piscina', 'icon': 'fa-swimming-pool', 'is_popular': False},
                {'name': 'Palestra', 'icon': 'fa-dumbbell', 'is_popular': False},
                {'name': 'Giardino', 'icon': 'fa-tree', 'is_popular': False},
            ],
            'Posizione': [
                {'name': 'Centro storico', 'icon': 'fa-monument', 'is_popular': True},
                {'name': 'Vicino metro', 'icon': 'fa-train', 'is_popular': True},
                {'name': 'Vicino bus', 'icon': 'fa-bus', 'is_popular': True},
                {'name': 'Zona tranquilla', 'icon': 'fa-volume-off', 'is_popular': True},
                {'name': 'Vicino ristoranti', 'icon': 'fa-utensils', 'is_popular': True},
            ],
            'Sicurezza': [
                {'name': 'Cassaforte', 'icon': 'fa-vault', 'is_popular': True},
                {'name': 'Rilevatore fumo', 'icon': 'fa-smoke', 'is_popular': True},
                {'name': 'Estintore', 'icon': 'fa-fire-extinguisher', 'is_popular': True},
                {'name': 'Kit pronto soccorso', 'icon': 'fa-kit-medical', 'is_popular': True},
                {'name': 'Serratura smart', 'icon': 'fa-lock', 'is_popular': False},
            ],
            'Intrattenimento': [
                {'name': 'Netflix', 'icon': 'fa-tv', 'is_popular': True},
                {'name': 'Prime Video', 'icon': 'fa-tv', 'is_popular': False},
                {'name': 'Disney+', 'icon': 'fa-tv', 'is_popular': False},
                {'name': 'Playstation', 'icon': 'fa-gamepad', 'is_popular': False},
                {'name': 'Xbox', 'icon': 'fa-gamepad', 'is_popular': False},
                {'name': 'Tavolo ping pong', 'icon': 'fa-table-tennis', 'is_popular': False},
                {'name': 'Biliardo', 'icon': 'fa-billiard', 'is_popular': False},
            ],
        }

        # Creazione amenities
        for category_name, amenity_list in amenities.items():
            try:
                category = AmenityCategory.objects.get(name=category_name)
                for amenity_data in amenity_list:
                    amenity, created = Amenity.objects.get_or_create(
                        name=amenity_data['name'],
                        category=category,
                        defaults={
                            'icon': amenity_data['icon'],
                            'is_popular': amenity_data['is_popular']
                        }
                    )
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f'Creata amenity: {amenity.name} in {category.name}')
                        )

            except AmenityCategory.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Categoria {category_name} non trovata')
                )

        self.stdout.write(self.style.SUCCESS('Popolamento completato!'))