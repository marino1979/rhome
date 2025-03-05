from django.core.management.base import BaseCommand
from rooms.models import RoomType

class Command(BaseCommand):
    help = 'Popola i tipi di stanza base'

    def handle(self, *args, **kwargs):
        room_types = [
            {'name': 'Camera da letto', 'can_have_beds': True},
            {'name': 'Soggiorno', 'can_have_beds': True},
            {'name': 'Cucina', 'can_have_beds': False},
            {'name': 'Bagno', 'can_have_beds': False},
            {'name': 'Ingresso', 'can_have_beds': False},
            {'name': 'Studio', 'can_have_beds': True},
        ]

        for rt in room_types:
            RoomType.objects.get_or_create(
                name=rt['name'],
                defaults={'can_have_beds': rt['can_have_beds']}
            )

        self.stdout.write(self.style.SUCCESS('Tipi stanza creati con successo'))