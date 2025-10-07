from django import template

register = template.Library()

@register.filter
def to(value, arg):
    """Generates a range from value to arg (inclusive)"""
    return range(value, arg + 1)
