from rbac.views import role, menu

from django.urls import path, include

app_name = 'rbac'

urlpatterns = [
    path('role/list/', role.role_list, name='role_list'),
    path('role/add/', role.role_add, name='role_add'),
    path('role/edit/<int:role_id>/', role.role_edit, name='role_edit'),
    path('role/del/<int:role_id>/', role.role_del, name='role_del'),

    # 一级菜单管理
    path('menu/list/', menu.menu_list, name='menu_list'),
    path('menu/add/', menu.menu_add, name='menu_add'),
    path('menu/edit/<int:menu_id>/', menu.menu_edit, name='menu_edit'),
    path('menu/del/<int:menu_id>/', menu.menu_del, name='menu_del'),

    # 二级菜单管理
    path('second/menu/add/', menu.second_menu_add, name='second_menu_add'),
    path('second/menu/edit/<int:menu_id>/', menu.second_menu_edit, name='second_menu_edit'),
    path('second/menu/del/<int:menu_id>/', menu.second_menu_del, name='second_menu_del'),

    # 非菜单管理
    path('permission/add/', menu.permission_add, name='permission_add'),
    path('permission/edit/<int:per_id>/', menu.permission_edit, name='permission_edit'),
    path('permission/del/<int:per_id>/', menu.permission_del, name='permission_del'),

    # 权限批量管理
    path('multi/permissions/', menu.multi_permissions, name='multi_permissions'),
    path('multi/permissions/del/<int:pk>/', menu.multi_permissions_del, name='multi_permissions_del'),

    # 用户-角色-权限分配
    path('distribute/permissions/',menu.distribute_permissions,name='distribute_permissions')
]
