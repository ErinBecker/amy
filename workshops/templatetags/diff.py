from django import template
from django.db.models import Q
from django.utils.safestring import mark_safe

from reversion.helpers import generate_patch_html

register = template.Library()


@register.simple_tag
def semantic_diff(left, right, field):
    return mark_safe(generate_patch_html(left, right, field, cleanup='semantic'))


@register.simple_tag
def relation_diff(left, right, field):
    model = field.related_model
    if field.many_to_one or field.one_to_one:
        # {left,right}.field_dict[field.name] is an integer or does not exist
        # Cast it to a list(empty or single itemed)
        if left.field_dict.get(field.name):
            try:
                left_PKs = [model.objects.get(pk=left.field_dict.get(field.name))]
            except model.DoesNotExist:
                left_PKs = [left.field_dict.get(field.name)]
        else:
            left_PKs = []
        if right.field_dict.get(field.name):
            try:
                right_PKs = [model.objects.get(pk=right.field_dict.get(field.name))]
            except model.DoesNotExist:
                right_PKs = [right.field_dict.get(field.name)]
        else:
            right_PKs = []
    else:
        left_PKs = []
        for pk in left.field_dict.get(field.name, []):
            try:
                left_PKs.append(model.objects.get(pk=pk))
            except model.DoesNotExist:
                left_PKs.append(pk)
        right_PKs = []
        for pk in right.field_dict.get(field.name, []):
            try:
                right_PKs.append(model.objects.get(pk=pk))
            except model.DoesNotExist:
                right_PKs.append(pk)
    # Relations that exist only in the current version
    additions = [obj for obj in right_PKs if obj not in left_PKs]
    # Relations that exist only in the previous version
    deletions = [obj for obj in left_PKs if obj not in right_PKs]
    # Relations that exist only in both versions
    consistent = [obj for obj in left_PKs if obj in right_PKs]
    add_label = ''.join('<a class="label label-success" href="{}">+{}</a>'.format(
            obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else '#',
            obj
        )
        for obj in additions
    )
    delete_label = ''.join('<a class="label label-danger" href="{}">-{}</a>'.format(
            obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else '#',
            obj
        )
        for obj in deletions
    )
    consistent_label = ''.join('<a class="label label-default" href="{}">{}</a>'.format(
            obj.get_absolute_url() if hasattr(obj, 'get_absolute_url') else '#',
            obj
        )
        for obj in consistent
    )
    return mark_safe(''.join([consistent_label, add_label,delete_label]))
