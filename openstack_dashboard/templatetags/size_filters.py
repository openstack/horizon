from django import template

register = template.Library()

@register.filter(name='mb_to_gb')
def mb_to_gb(value, precision=2):
    """
    Convert megabytes (MB) to gigabytes (GB) and format as 'X.XX GB'.
    Usage in template: {{ size_ram|mb_to_gb }}.
    """
    try:
        if value is None or value == '':
            return ''
        mb = float(value)
        gb = mb / 1024.0
        return f"{gb:.{int(precision)}f} GB"
    except Exception:
        # Fall back to the original value if conversion fails
        return value