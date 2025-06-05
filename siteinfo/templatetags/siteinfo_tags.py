from django import template

register = template.Library()


@register.simple_tag
def get_info_cls(value: str, base_class: str = 'col-md-7') -> str:
    """Return info element class"""
    c = base_class
    if value == '':
        c += ' text-muted'
    return c


@register.simple_tag
def get_info_val(value: str) -> str:
    """Return info element value"""
    if value == '':
        value = '(Empty value)'
    return value
