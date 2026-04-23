import re
from django.conf import settings
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

        # 3. 进行权限校验
        flag = False
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

        return None
