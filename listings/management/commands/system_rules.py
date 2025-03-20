from django.core.management.base import BaseCommand
from listings.models import SystemRule  # Sostituisci con il percorso effettivo al tuo modello
import datetime

class Command(BaseCommand):
    help = 'Popola le regole di sistema predefinite'

    def handle(self, *args, **kwargs):
        # Elimina le regole esistenti se si vuole ripartire da zero
        # SystemRule.objects.all().delete()
        
        # Controllo per non creare duplicati
        if not SystemRule.objects.filter(title="Check-in").exists():
            SystemRule.objects.create(
                title="Check-in",
                description="Orario di arrivo consentito",
                time_from=datetime.time(15, 0),  # 15:00
                time_to=datetime.time(20, 0),    # 20:00
                order=1
            )
            self.stdout.write(self.style.SUCCESS('Creata regola Check-in'))
        
        if not SystemRule.objects.filter(title="Check-out").exists():
            SystemRule.objects.create(
                title="Check-out",
                description="Orario di partenza richiesto",
                time_from=datetime.time(10, 0),  # 10:00
                order=2
            )
            self.stdout.write(self.style.SUCCESS('Creata regola Check-out'))
        
        if not SystemRule.objects.filter(title="Feste").exists():
            SystemRule.objects.create(
                title="Feste",
                is_allowed=False,
                description="Non sono consentite feste o eventi",
                order=3
            )
            self.stdout.write(self.style.SUCCESS('Creata regola Feste'))
        
        if not SystemRule.objects.filter(title="Foto/Video").exists():
            SystemRule.objects.create(
                title="Foto/Video",
                is_allowed=True,
                description="È consentito scattare foto o registrare video",
                order=4
            )
            self.stdout.write(self.style.SUCCESS('Creata regola Foto/Video'))
        
        self.stdout.write(self.style.SUCCESS('Popolamento regole predefinite completato'))