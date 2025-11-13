"""
Management command per sincronizzare i calendari esterni tramite iCal.
Può essere eseguito manualmente o tramite cron job.
"""

from django.core.management.base import BaseCommand
from calendar_rules.services.ical_sync import ICalSyncService


class Command(BaseCommand):
    help = 'Sincronizza tutti i calendari esterni attivi tramite iCal'

    def add_arguments(self, parser):
        parser.add_argument(
            '--calendar-id',
            type=int,
            help='Sincronizza solo un calendario specifico (ID)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forza la sincronizzazione anche se non necessaria',
        )

    def handle(self, *args, **options):
        from calendar_rules.models import ExternalCalendar
        
        calendar_id = options.get('calendar_id')
        force = options.get('force', False)
        
        if calendar_id:
            # Sincronizza un calendario specifico
            try:
                calendar = ExternalCalendar.objects.get(pk=calendar_id)
                
                if not calendar.is_active and not force:
                    self.stdout.write(
                        self.style.WARNING(f'Calendario {calendar.name} non è attivo. Usa --force per sincronizzarlo comunque.')
                    )
                    return
                
                if not calendar.needs_sync() and not force:
                    self.stdout.write(
                        self.style.WARNING(f'Calendario {calendar.name} non necessita sincronizzazione. Usa --force per forzarla.')
                    )
                    return
                
                self.stdout.write(f'Sincronizzazione calendario: {calendar.name}...')
                service = ICalSyncService(calendar)
                success, error = service.sync()
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Calendario {calendar.name} sincronizzato con successo')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'✗ Errore sincronizzazione {calendar.name}: {error}')
                    )
                    
            except ExternalCalendar.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Calendario con ID {calendar_id} non trovato')
                )
        else:
            # Sincronizza tutti i calendari attivi
            self.stdout.write('Sincronizzazione di tutti i calendari esterni attivi...')
            stats = ICalSyncService.sync_all_active()
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Riepilogo sincronizzazione:')
            self.stdout.write(f'  Totale calendari: {stats["total"]}')
            self.stdout.write(
                self.style.SUCCESS(f'  Sincronizzati: {stats["synced"]}')
            )
            self.stdout.write(
                self.style.WARNING(f'  Saltati: {stats["skipped"]}')
            )
            self.stdout.write(
                self.style.ERROR(f'  Errori: {stats["errors"]}')
            )
            self.stdout.write('='*50)

