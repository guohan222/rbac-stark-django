from types import FunctionType,MethodType
from django.template import Library

register = Library()


def header_list(cl):
    if cl.list_display:
        for field_or_func in cl.list_display:
            # 区分要展示的列是自定义的还是表中的字段
            # if callable(field_or_func):
            if isinstance(field_or_func, FunctionType):
                # 给自定义列的函数，表示现在函数功能是表头
                verbose_name = field_or_func(cl.config, obj=None, header=True)
            else:
                verbose_name = cl.config.model_class._meta.get_field(field_or_func).verbose_name

            yield verbose_name
    else:
        # 如果没有指定要展示的列，则展示，该表名、该表查询出来的所有对象（__str__）
        yield cl.config.model_class._meta.model_name


def body_list(cl):
    for row in cl.data_list:
        # 每一行数据
        tr_list = []
        if not cl.list_display:
            tr_list.append(row)
            yield tr_list
            continue

        # 反射，获取该对象中要展示的属性（字段） or  自定义列的数据内容
        for field_or_func in cl.list_display:
            # if callable(field_or_func):
            if isinstance(field_or_func, FunctionType):
                tr_list.append(field_or_func(cl.config, obj=row))
            else:
                tr_list.append(getattr(row, field_or_func))
        yield tr_list


@register.inclusion_tag('stark/inclusion/table.html')
def table(cl):
    return {
        'header_list': header_list(cl),
        'body_list': body_list(cl),
        'cl': cl
    }
