from django.conf import settings


def init_permission(request, user_obj):
    """
    用户权限初始化
    :param request:
    :param user_obj:
    :return:
    """

    # 根据用户角色获取所有权限
    permission_queryset = user_obj.roles.filter(permissions__isnull=False).values(
        'permissions__id',
        'permissions__title',
        'permissions__url',
        'permissions__name',

        'permissions__pid',
        'permissions__pid__name',

        'permissions__menu_id',
        'permissions__menu__title',
        'permissions__menu__icon',
    ).distinct()

    # 权限列表
    # permission_list = []
    permission_dict = {}
    # 菜单
    menu_dict = {}
    # menu_list = []

    for item in permission_queryset:
        # 权限列表
        permission_dict[item['permissions__name']] = {
            'id':item['permissions__id'],
            'title':item['permissions__title'],
            'url':item['permissions__url'],
            'pid':item['permissions__pid'],
            'p_name':item['permissions__pid__name'],
        }
        # permission_list.append({'id':item['permissions__id'],'pid':item['permissions__pid'],'url':item['permissions__url']})

        # 构建二级菜单
        menu_id = item['permissions__menu_id']
        if not menu_id:
            continue

        node = {'id': item['permissions__id'],'title': item['permissions__title'],'url': item['permissions__url'],'pid': item['permissions__pid'],}
        if menu_id not in menu_dict:
            menu_dict[menu_id] = {
                'title': item['permissions__menu__title'],
                'icon': item['permissions__menu__icon'],
                'children': [node]
            }
        else:
            menu_dict[menu_id]['children'].append(node)

    print(f'权限信息初始化中：{menu_dict}')

    # 将用户权限中是菜单的加入session
    request.session[settings.MENU_SESSION_KEY] = menu_dict
    # 将用户权限写入session
    request.session[settings.PERMISSION_SESSION_KEY] = permission_dict
