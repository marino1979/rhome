from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Bed

@receiver([post_save, post_delete], sender=Bed)
def update_listing_totals(sender, instance, **kwargs):
    listing = instance.listing
    listing.total_beds = listing.count_total_beds()
    listing.total_sleeps = listing.count_total_sleeps()
    listing.save()