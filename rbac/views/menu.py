

from rbac import models
from rbac.service.routes import get_all_url_dict
from rbac.form.menu import MenuModelForm, SecondMenuModelForm, PermissionModelForm, MultiAddPermissionForm, MultiEditPermissionForm


from django.urls import reverse
from django.conf import settings
from collections import OrderedDict
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError
from django.utils.module_loading import import_string



# Create your views here.


def menu_list(request):
    """菜单列表页"""
    # 一、二级菜单id
    mid = request.GET.get('mid')
    sid = request.GET.get('sid')

    try:
        mid = int(mid)  # 尝试转数字
        if not models.Menu.objects.filter(pk=mid).exists():
            mid = 0  # 数字是对的，但数据库没这条数据，归零
    except (TypeError, ValueError):
        mid = 0  # 传了 None 或乱七八糟的字母，直接归零
    try:
        sid = int(sid)
        if not models.Permission.objects.filter(pk=sid).exists():
            sid = 0
    except (TypeError, ValueError):
        sid = 0

    # 一级菜单对象
    menu_objs = models.Menu.objects.all()
    # 二级菜单对象
    second_menu_objs = models.Permission.objects.filter(menu_id=mid)
    # 非菜单权限对象
    permission_objs = models.Permission.objects.filter(pid_id=sid)

    content = {
        'mid': mid,
        'sid': sid,
        'menu_objs': menu_objs,
        'second_menu_objs': second_menu_objs,
        'permission_objs': permission_objs,
    }

    return render(request, 'rbac/menu_list.html', content)


def menu_add(request):
    """添加一级菜单"""
    if request.method == 'GET':
        form = MenuModelForm()
        return render(request, 'rbac/change.html', {'form': form})

    form = MenuModelForm(data=request.POST)
    if form.is_valid():
        form.save()
        return redirect('rbac:menu_list')
    return render(request, 'rbac/change.html', {'form': form})


def menu_edit(request, menu_id):
    """编辑一级菜单"""
    menu_obj = models.Menu.objects.filter(id=menu_id).first()
    if not menu_obj:
        return redirect('rbac:menu_list')

    if request.method == 'GET':
        form = MenuModelForm(instance=menu_obj)
        return render(request, 'rbac/change.html', {'form': form})

    form = MenuModelForm(data=request.POST, instance=menu_obj)
    if form.is_valid():
        form.save()
        return redirect('rbac:menu_list')
    return render(request, 'rbac/change.html', {'form': form})


def menu_del(request, menu_id):
    """删除一级菜单"""
    models.Menu.objects.filter(pk=menu_id).delete()
    return redirect('rbac:menu_list')


def second_menu_add(request):
    """增加二级菜单"""
    if request.method == 'GET':
        form = SecondMenuModelForm()
        return render(request, 'rbac/change.html', {'form': form})
    form = SecondMenuModelForm(data=request.POST)
    if form.is_valid():
        menu_id = form.instance.menu_id
        form.save()
        url = reverse('rbac:menu_list')
        return redirect(f'{url}?mid={menu_id}')

    return render(request, 'rbac/change.html', {'form': form})


def second_menu_edit(request, menu_id):
    """编辑二级菜单"""
    second_menu_obj = models.Permission.objects.filter(pk=menu_id).first()
    if not second_menu_obj:
        return redirect('rbac:menu_list')

    if request.method == 'GET':
        form = SecondMenuModelForm(instance=second_menu_obj)
        return render(request, 'rbac/change.html', {'form': form})

    form = SecondMenuModelForm(data=request.POST, instance=second_menu_obj)
    if form.is_valid():
        menu_id = form.instance.menu_id
        form.save()
        url = reverse('rbac:menu_list')
        return redirect(f'{url}?mid={menu_id}')

    return render(request, 'rbac/change.html', {'form': form})


def second_menu_del(request, menu_id):
    """删除二级菜单"""
    second_menu_obj = models.Permission.objects.filter(pk=menu_id).first()
    mid = None
    if second_menu_obj:
        mid = second_menu_obj.menu_id

    models.Permission.objects.filter(pk=menu_id).delete()
    url = reverse('rbac:menu_list')
    return redirect(f'{url}?mid={mid}')



# 非菜单管理

def permission_add(request):
    """增加非菜单权限"""
    if request.method == 'GET':
        form = PermissionModelForm()
        return render(request,'rbac/change.html',{'form':form})

    form = PermissionModelForm(data=request.POST)
    if form.is_valid():
        mid = form.instance.pid.menu_id
        sid = form.instance.pid_id
        form.save()
        url = reverse('rbac:menu_list')
        return redirect(f'{url}?mid={mid}&sid={sid}')
    return render(request, 'rbac/change.html', {'form': form})



def permission_edit(request,per_id):
    """编辑非菜单权限"""
    per_obj = models.Permission.objects.filter(pk=per_id).first()
    if not per_obj:
        return redirect('rbac:menu_list')

    if request.method == 'GET':
        form = PermissionModelForm(instance=per_obj)
        return render(request, 'rbac/change.html', {'form': form})
    form = PermissionModelForm(data=request.POST,instane=per_obj)
    if form.is_valid():
        mid = form.instance.pid.menu_id
        sid = form.instance.pid_id
        form.save()
        url = reverse('rbac:menu_list')
        return redirect(f'{url}?mid={mid}&sid={sid}')
    return render(request, 'rbac/change.html', {'form': form})




def permission_del(request,per_id):
    """删除非菜单权限"""
    per_obj = models.Permission.objects.filter(pk=per_id).first()

    mid = None
    sid = None
    if per_obj:
        mid = per_obj.pid.menu_id
        sid = per_obj.pid_id

    models.Permission.objects.filter(pk=per_id).delete()
    url = reverse('rbac:menu_list')
    return redirect(f'{url}?mid={mid}&sid={sid}')




# 非菜单批量管理
def multi_permissions(request):
    """
    批量操作权限
    :param request:
    :return:
    """
    post_type = request.GET.get('type')
    generate_formset_class = formset_factory(MultiAddPermissionForm, extra=0)
    update_formset_class = formset_factory(MultiEditPermissionForm, extra=0)

    generate_formset = None
    update_formset = None

    # ================= 1. 批量添加逻辑 =================
    if request.method == 'POST' and post_type == 'generate':
        formset = generate_formset_class(data=request.POST)
        if formset.is_valid():
            object_list = []
            post_row_list = formset.cleaned_data
            has_error = False
            for i in range(0, formset.total_form_count()):
                row_dict = post_row_list[i]

                # 🔥 修复1：数据清洗，把空字符串强转为 None，防止外键报错
                for key, value in row_dict.items():
                    if value == "":
                        row_dict[key] = None

                try:
                    new_object = models.Permission(**row_dict)
                    new_object.validate_unique()
                    object_list.append(new_object)
                except ValidationError as e:
                    # 如果是正常的验证错误（比如名字重复），正常更新给前端
                    formset.errors[i].update(e)
                    generate_formset = formset
                    has_error = True
                except Exception as e:
                    # 🔥 修复2：捕获底层报错，防止 update() 引发黄页崩溃
                    formset.errors[i].setdefault('__all__', []).append(str(e))
                    generate_formset = formset
                    has_error = True

            if not has_error:
                models.Permission.objects.bulk_create(object_list, batch_size=100)
        else:
            generate_formset = formset

    # ================= 2. 批量更新逻辑 =================
    if request.method == 'POST' and post_type == 'update':
        formset = update_formset_class(data=request.POST)
        if formset.is_valid():
            post_row_list = formset.cleaned_data
            for i in range(0, formset.total_form_count()):
                row_dict = post_row_list[i]
                permission_id = row_dict.pop('id')

                # 🔥 修复1：数据清洗，把空字符串强转为 None
                for key, value in row_dict.items():
                    if value == "":
                        row_dict[key] = None

                try:
                    row_object = models.Permission.objects.filter(id=permission_id).first()
                    for k, v in row_dict.items():
                        setattr(row_object, k, v)
                    row_object.validate_unique()
                    row_object.save()
                except ValidationError as e:
                    formset.errors[i].update(e)
                    update_formset = formset
                except Exception as e:
                    # 🔥 修复2：捕获底层报错
                    formset.errors[i].setdefault('__all__', []).append(str(e))
                    update_formset = formset
        else:
            update_formset = formset

    # 1. 获取项目中所有的URL
    all_url_dict = get_all_url_dict()
    """
    {
        'rbac:role_list':{'name': 'rbac:role_list', 'url': '/rbac/role/list/'},
        'rbac:role_add':{'name': 'rbac:role_add', 'url': '/rbac/role/add/'},
        ....
    }
    """
    router_name_set = set(all_url_dict.keys())

    # 2. 获取数据库中所有的URL
    permissions = models.Permission.objects.all().values('id', 'title', 'name', 'url', 'menu_id', 'pid_id')
    permission_dict = OrderedDict()
    permission_name_set = set()
    for row in permissions:
        permission_dict[row['name']] = row
        permission_name_set.add(row['name'])
    """
    {
        'rbac:role_list': {'id':1,'title':'角色列表',name:'rbac:role_list',url.....},
        'rbac:role_add': {'id':1,'title':'添加角色',name:'rbac:role_add',url.....},
        ...
    }
    """

    for name, value in permission_dict.items():
        router_row_dict = all_url_dict.get(name)  # {'name': 'rbac:role_list', 'url': '/rbac/role/list/'},
        if not router_row_dict:
            continue
        if value['url'] != router_row_dict['url']:
            value['url'] = '路由和数据库中不一致'

    # 3. 应该添加、删除、修改的权限有哪些？
    # 3.1 计算出应该增加的name
    if not generate_formset:
        generate_name_list = router_name_set - permission_name_set
        generate_formset = generate_formset_class(
            initial=[row_dict for name, row_dict in all_url_dict.items() if name in generate_name_list])

    # 3.2 计算出应该删除的name
    delete_name_list = permission_name_set - router_name_set
    delete_row_list = [row_dict for name, row_dict in permission_dict.items() if name in delete_name_list]

    # 3.3 计算出应该更新的name
    if not update_formset:
        update_name_list = permission_name_set & router_name_set
        update_formset = update_formset_class(
            initial=[row_dict for name, row_dict in permission_dict.items() if name in update_name_list])

    return render(
        request,
        'rbac/multi_permissions.html',
        {
            'generate_formset': generate_formset,
            'delete_row_list': delete_row_list,
            'update_formset': update_formset,
        }
    )


def multi_permissions_del(request, pk):
    """
    批量页面的权限删除
    :param request:
    :param pk:
    :return:
    """

    models.Permission.objects.filter(id=pk).delete()
    return redirect('rbac:menu_list')


def distribute_permissions(request):
    """
    用户、角色、权限分配
    :param request:
    :return:
    """
    user_id = request.GET.get('uid')
    role_id = request.GET.get('rid')
    user_class = import_string(settings.USER_MODEL_PATH)

    try:
        user_id = int(user_id)  # 尝试转数字
        if not user_class.objects.filter(pk=user_id).exists():
            user_id = 0
    except (TypeError, ValueError):
        user_id = 0  # 传了 None 或乱七八糟的字母，直接归零
    try:
        role_id = int(role_id)
        if not models.Role.objects.filter(pk=role_id).exists():
            role_id = 0
    except (TypeError, ValueError):
        role_id = 0


    if request.method == 'POST':
        post_type = request.POST.get('type')

        # 用户分配角色
        if post_type == 'role':
            # 获取前端打钩的所有角色 ID
            role_id_list = request.POST.getlist('roles')
            if user_id:
                user_obj = user_class.objects.filter(pk=user_id).first()
                if user_obj:
                    # Django ORM 操作关系管理对象：.set() 会自动帮你清空旧的关系，绑定新的关系
                    user_obj.roles.set(role_id_list)

        elif post_type == 'permission':
            # 获取前端打钩的所有权限 ID
            permission_id_list = request.POST.getlist('permissions')
            if role_id:
                role_obj = models.Role.objects.filter(pk=role_id).first()
                if role_obj:
                    role_obj.permissions.set(permission_id_list)



    # 获取选中用户的角色信息 及 全部用户、角色信息
    user_obj = user_class.objects.filter(pk=user_id).first()
    user_has_roles_dict = {item.pk:None for item in user_obj.roles.all()} if user_obj else {}
    all_users = user_class.objects.all()
    all_roles = models.Role.objects.all()


    # 获取选中角色的权限信息
    role_obj = models.Role.objects.filter(pk=role_id).first()
    role_has_permissions_dict = {item.pk:None for item in role_obj.permissions.all()} if role_obj else {}


    # 菜单与非菜单组装树
    all_permissions = {}
    # 二级菜单字典
    second_menu_dict = {}
    # 所有一级菜单
    menu_objs = models.Menu.objects.values('id','title')
    # 所有权限
    permission_objs = list(models.Permission.objects.values('id','title','menu_id','pid_id'))

    for item in menu_objs:
        item['children'] = []
        all_permissions[item['id']] = item

    # 将二级菜单挂载到一级菜单下&构建二级菜单字典
    for item in permission_objs:
        menu_id = item['menu_id']
        if not menu_id:
            continue
        item['children'] = []
        all_permissions[menu_id]['children'].append(item)
        second_menu_dict[item['id']] = item

    # 将非菜单权限挂载到二级菜单下
    for item in permission_objs:
        pid_id = item['pid_id']
        if not pid_id:
            continue
        second_menu_dict[pid_id]['children'].append(item)


    context = {
        'user_id':user_id,
        'role_id':role_id,
        'all_users':all_users,
        'all_roles':all_roles,
        'all_permissions':all_permissions,
        'user_has_roles_dict':user_has_roles_dict,
        'role_has_permissions_dict':role_has_permissions_dict,
    }

    return render(request,'rbac/distribute_permissions.html',context)
