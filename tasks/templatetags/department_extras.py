from django import template

register = template.Library()

@register.filter
def abbreviate_department_name(value):
    """
    Abbreviate long department name words to fit better in the tree nodes.
    Replaces 'Научно-исследовательский/ая/ое' with 'НИ'
    """
    if not value:
        return value
    
    replacements = [
        ('Научно-исследовательский', 'НИ'),
        ('Научно-исследовательская', 'НИ'),
        ('Научно-исследовательское', 'НИ'),
    ]
    
    result = value
    for old, new in replacements:
        result = result.replace(old, new)
    
    return result
