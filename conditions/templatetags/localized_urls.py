from django import template

from conditions.context_processors import EN_TO_ES_SEGMENTS, _translate_path_segments


register = template.Library()


@register.filter
def spanish_path_for(path: str) -> str:
    translated = _translate_path_segments(path, EN_TO_ES_SEGMENTS)
    if translated == "/":
        return "/es/"
    return f"/es{translated}"
