# amenities/widgets.py
from django.forms.widgets import Select
from django.template import loader
from django.utils.safestring import mark_safe
from icons.models import Icon, IconCategory
from django.db.models import Prefetch

class IconSelectWidget(Select):
    template_name = 'admin/widgets/icon_select.html'
    
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        
        # Prepara le choices per il Select
        categories = IconCategory.objects.prefetch_related('icons').all()
        
        # Crea una lista di tuples (value, label) per le choices
        choices = []
        for category in categories:
            for icon in category.icons.all():
                # Usa icon.name invece di icon.class_name
                choices.append((icon.name, f"{category.name} - {icon.name}"))
        
        self.choices = choices
        
        context.update({
            'categories': categories,
            'selected_value': value or '',
            'widget': {
                'name': name,
                'is_hidden': self.is_hidden,
                'required': self.is_required,
                'value': value,
                'attrs': self.build_attrs(self.attrs, attrs),
                'template_name': self.template_name,
            }
        })
        
        return context

    def render(self, name, value, attrs=None, renderer=None):
        print("\n=== DEBUG RENDER ===")
        print(f"Rendering widget con value: {value}")
        html = super().render(name, value, attrs, renderer)
        print("=== FINE RENDER ===\n")
        return html
    
    class Media:
        css = {
            'all': [
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css',
                'admin/css/icon-picker.css',
            ]
        }
        js = ['admin/js/icon-picker.js']