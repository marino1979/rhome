from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Bed

@receiver([post_save, post_delete], sender=Bed)
def update_listing_totals(sender, instance, **kwargs):
    listing = instance.listing
    listing.total_beds = listing.count_total_beds()
    listing.total_sleeps = listing.count_total_sleeps()
    # Use update_fields to prevent triggering post_save signals on Listing
    # This prevents infinite recursion if Listing has its own post_save signals
    listing.save(update_fields=['total_beds', 'total_sleeps'])