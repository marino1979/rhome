from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    try:
        return int(float(value)) * int(float(arg))
    except (ValueError, TypeError):
        return 0