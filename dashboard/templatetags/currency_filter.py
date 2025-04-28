from django import template

register = template.Library()

@register.filter
def currency (value):
    try:
        return f"P{value:,.2f}"
    except{ValueError, TypeError}:
        return value
