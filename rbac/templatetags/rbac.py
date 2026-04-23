import re
from django.conf import settings
from django.template import Library

register = Library()


@register.inclusion_tag('rbac/inclusion/static_menu.html')
def menu(request):
    """生成一级菜单"""

    menu_list = request.session.get(settings.MENU_SESSION_KEY)
    # 选中
    for item in menu_list:
        reg = f'^{item['url']}$'
        if re.match(reg, request.path_info):
            item['class'] = 'active'

    return {'menu_list': menu_list}


@register.inclusion_tag('rbac/inclusion/mutil_menu.html')
def menu(request):
    """生成二级菜单"""

    menu_dict = request.session.get(settings.MENU_SESSION_KEY)

    # 选则
    for item in menu_dict.values():
        # 将所有二级菜单隐藏
        item['class'] = 'hidden'  # 注释掉则，菜单页收缩为手动挡
        for child in item['children']:

            if child['id'] == request.current_selected_permission:
                child['class'] = 'active'
                # 将这个一级菜单下所有二级菜单进行展示
                item['class'] = ''

    return {'menu_list': [i for i in menu_dict.values()]}


@register.inclusion_tag('rbac/inclusion/breadcrumb.html')
def breadcrumb(request):
    """导航条"""
    return {'breadcrumb_list': request.breadcrumb_list}


@register.filter
def has_permission(request, name):
    """根据url别名判断是否具有权限"""
    if name in request.session.get(settings.PERMISSION_SESSION_KEY):
        return True
    return False
