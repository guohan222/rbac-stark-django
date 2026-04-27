import re
from django.conf import settings
from django.urls import resolve
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

class RbacMiddleware(MiddlewareMixin):

    def process_request(self,request):
        """
        验证用户
        :return:
        """
        request.breadcrumb_list = []
        request.current_selected_permission = 0

        # 1. 判断当前请求url是否在白名单中
        current_url = request.path_info
        for reg in settings.VALID_URL:
            if re.match(reg,current_url):
                return None

        # 2. 获取用户具有的权限（未登录过，则为空）
        permission_dict = request.session.get(settings.PERMISSION_SESSION_KEY)
        # print(f'中间件中：{permission_dict}')
        if not permission_dict:
            return redirect('/login/')


        # 4. 反向解析出URL的name
        try:
            current_url_name = resolve(current_url).view_name
        except Exception:
            # 如果访问了一个连 URL 路由都没配的地址，直接 404
            current_url_name = None


        # 5. 进行权限校验
        flag = False

        # 直接判断在不在权限字典里
        if current_url_name in permission_dict:
            flag = True
            # 直接把当前匹配到的权限信息拿出来
            item = permission_dict[current_url_name]

            # 获取二级菜单id (如果有pid代表当前权限url为非二级菜单)
            request.current_selected_permission = item['pid'] or item['id']
            # 导航条 (面包屑)
            if item['pid']:
                # 如果有 pid，说明它是子权限，要把它的父级也加进面包屑
                request.breadcrumb_list.append(permission_dict[item['p_name']])
            # 把自己加进面包屑
            request.breadcrumb_list.append(item)

        if not flag:
            return HttpResponse('无权访问')

        return None





        """
        # =====================================================================
        # 
        # 废弃原因：
        # 1. 无法完美兼容 Django 2.x+ 的 path 动态路由语法 (如 <int:pk>)
        # 2. 每次请求需遍历全量权限字典并执行正则匹配，时间复杂度为 O(N)，性能较差
        # 3. 路由路径一旦修改，数据库权限表必须同步修改，解耦性差
        # 
        # 现已全面重构为：基于 resolve(current_url).url_name 的别名 (name) 精准匹配
        # 时间复杂度降为 O(1)，且完全免疫 URL 路径的变更
        # =====================================================================
        """

        """
        for item in permission_dict.values():
            reg = f'^{item['url']}$'
            if re.match(reg,current_url):
                flag = True
                # 获取二级菜单id(如果有pid代表当前权限url为非二级菜单)
                request.current_selected_permission = item['pid'] or item['id']

                # 导航条
                if item['pid']:
                    request.breadcrumb_list.append(permission_dict[item['p_name']])
                request.breadcrumb_list.append(item)
                print(request.breadcrumb_list)

                break

        if not flag:
            return HttpResponse('无权访问')
        """



