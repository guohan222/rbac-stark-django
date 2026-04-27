from django.conf import settings



class PermissionMixins(object):
    """
    权限拦截基类
    连接  Stark 的页面渲染能力 和 RBAC 的权限校验能力
    实现粒度根据权限粒度控制到按钮，代替前端页面使用filter
    """

    def has_permission(self,url_name):
        """根据name判断是否具有该权限"""
        # 继承该类的子类config在stark组件中会利用装饰器在config中进行request的封装
        permission_dict = self.request.session.get(settings.PERMISSION_SESSION_KEY)

        # 根据别名进行比对
        url_name = f'{self.site.namespace}:{url_name}'
        if permission_dict and url_name in permission_dict:
            return True
        return False

    def get_add_btn(self):
        """劫持添加按钮，根据权限决定是否要进行展示，实现粒度控制到按钮"""
        # 注意：Stark 的 url_name 生成通常是 property，不要加括号
        if self.has_permission(self.get_add_url_name):
            # 在多继承里，super() 不是简单地找“父类”，而是找 MRO 链条里的下一个类
            return super().get_add_btn()
        return ''

    def get_list_display(self):
        """劫持操作列，剔除没有权限的编辑和删除按钮"""

        # 先去调用 StarkConfig 原本的逻辑，拿到默认要展示的所有列
        value = super().get_list_display()

        result = []
        for item in value:
            # 如果是函数或方法 (可调用的对象)
            if callable(item):
                if item.__name__ == 'display_edit' and not self.has_permission(self.get_change_url_name):
                    continue
                if item.__name__ == 'display_del' and not self.has_permission(self.get_del_url_name):
                    continue

            # 无论是字符串，还是通过了权限校验的函数，都加进来
            result.append(item)

        return result

        """
        for item in value:

            if isinstance(item, str):
                result.append(item)
                continue

            if item.__name__ == 'display_edit':
                # 拿编辑的 name 去比对，没权限就 continue 跳过，不把它加进队伍里
                if not self.has_permission(self.get_change_url_name()):
                    continue

            if item.__name__ == 'display_del':
                if not self.has_permission(self.get_del_url_name()):
                    continue

            # 校验通过的，放行进入新队伍
            result.append(item)

        return result
        
        """









