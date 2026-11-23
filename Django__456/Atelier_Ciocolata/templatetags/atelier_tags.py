from django import template

register = template.Library()

@register.filter
def get_item(dictionar, cheie):
    return dictionar.get(cheie, '#')
