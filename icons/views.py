# icons/views.py
from django.http import JsonResponse
from .models import Icon, IconCategory

def icon_list(request):
    """
    Restituisce la lista di tutte le icone attive con le loro informazioni
    """
    icons = Icon.objects.filter(is_active=True).select_related('category').values(
        'id',
        'name',
        'icon_type',
        'fa_class',
        'custom_icon',
        'category__name',
        'category__slug'
    )
    
    # Formattazione della risposta
    formatted_icons = []
    for icon in icons:
        icon_data = {
            'id': icon['id'],
            'name': icon['name'],
            'type': icon['icon_type'],
            'category': {
                'name': icon['category__name'],
                'slug': icon['category__slug']
            }
        }
        
        # Aggiungiamo il path dell'icona in base al tipo
        if icon['icon_type'] == 'fa':
            icon_data['value'] = icon['fa_class']
        else:
            icon_data['value'] = icon['custom_icon']
            
        formatted_icons.append(icon_data)
    
    return JsonResponse({'icons': formatted_icons})

def icon_categories(request):
    """
    Restituisce la lista di tutte le categorie di icone
    """
    categories = IconCategory.objects.values('id', 'name', 'slug').order_by('order', 'name')
    return JsonResponse({'categories': list(categories)})