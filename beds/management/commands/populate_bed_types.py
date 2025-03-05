from django.core.management.base import BaseCommand
from beds.models import BedType

class Command(BaseCommand):
    help = 'Popola il database con i tipi di letto predefiniti'

    def handle(self, *args, **kwargs):
        bed_types = [
            {
                'name': 'Matrimoniale',
                'description': 'Letto matrimoniale standard',
                'capacity': 2,
                'dimensions': '160x200'
            },
            {
                'name': 'Singolo',
                'description': 'Letto singolo',
                'capacity': 1,
                'dimensions': '90x200'
            },
            {
                'name': 'Divano letto matrimoniale',
                'description': 'Divano convertibile in letto matrimoniale',
                'capacity': 2,
                'dimensions': '160x190'
            },
            {
                'name': 'Divano letto singolo',
                'description': 'Divano convertibile in letto singolo',
                'capacity': 1,
                'dimensions': '80x190'
            },
            {
                'name': 'King Size',
                'description': 'Letto matrimoniale grande',
                'capacity': 2,
                'dimensions': '180x200'
            },
            {
                'name': 'Queen Size',
                'description': 'Letto matrimoniale medio',
                'capacity': 2,
                'dimensions': '150x200'
            },
            {
                'name': 'A castello',
                'description': 'Letto a castello con due posti singoli',
                'capacity': 2,
                'dimensions': '90x200'
            },
            {
                'name': 'Brandina',
                'description': 'Letto pieghevole singolo',
                'capacity': 1,
                'dimensions': '80x190'
            },
            {
                'name': 'Lettino bimbi',
                'description': 'Lettino con sponde per bambini',
                'capacity': 1,
                'dimensions': '60x120'
            }
        ]

        for bed_type_data in bed_types:
            bed_type, created = BedType.objects.get_or_create(
                name=bed_type_data['name'],
                defaults={
                    'description': bed_type_data['description'],
                    'capacity': bed_type_data['capacity'],
                    'dimensions': bed_type_data['dimensions']
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Creato tipo letto: {bed_type.name} ({bed_type.capacity} posti)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Il tipo letto {bed_type.name} esisteva già')
                )