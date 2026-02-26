from django import template

register = template.Library()

@register.filter(name='div')
def div(value, arg):
    """Divise une valeur par un argument."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None
