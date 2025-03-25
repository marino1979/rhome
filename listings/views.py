from django.shortcuts import render, get_object_or_404
from .models import Listing

def listing_list(request):
    """Vista per mostrare tutti gli annunci attivi"""
    listings = Listing.objects.filter(status='active')
    return render(request, 'listings/listing_list.html', {
        'listings': listings
    })

def listing_detail(request, slug):
    """Vista per mostrare il dettaglio di un singolo annuncio"""
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    # Crea la lista di opzioni per gli ospiti
    guest_options = range(1, listing.max_guests + 1)
    
    return render(request, 'listings/listing_detail.html', {
        'listing': listing,
        'guest_options': guest_options
    })
def listing_create(request):
    return render(request, 'listing_create.html')

#
