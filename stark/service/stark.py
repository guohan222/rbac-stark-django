
from types import FunctionType

from stark.form.bootstrap import BootStrap

from django import forms
from django.urls import path
from django.urls import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.utils.safestring import mark_safe


# 通用crud类
class StarkConfig(object):

    def display_checkbox(self, obj=None, header=False):
        # 自定义要展示的列，然而这个列要想在表中显示肯定要有表head，表body
        # 而表head要显示标题，body要显示数据，
        # 所以在自定义时要区分，什么时候给表head展示指定自定义的标题，什么时候给表body展示自定义的数据
        # 即自定义列的函数要有head与否的区分标识
        if header:
            return '选择'
        return mark_safe(f"<input type='checkbox' name='pk' value='{obj.pk}' />")

    def display_edit(self, obj=None, header=False):
        if header:
            return '操作'

        edit_icon = f"""
        <div class="text-end pe-4">
            <a href="{self.reverse_edit_url(obj)}" class="text-decoration-none me-3"
               style="color: #bfbfbf; transition: 0.3s;" onmouseover="this.style.color='#1677ff'"
               onmouseout="this.style.color='#bfbfbf'">
                <i class="fa-solid fa-pen-to-square"></i>
            </a>
        </div>
        """
        return mark_safe(edit_icon)

    def display_del(self, obj=None, header=False):
        if header:
            return '操作'

        del_icon = f"""
        <div class="text-end pe-4">
            <a href="#" class="text-decoration-none"
                style="color: #bfbfbf; transition: 0.3s;" onmouseover="this.style.color='#ff4d4f'"
                onmouseout="this.style.color='#bfbfbf'"
                data-bs-toggle="modal"
                data-bs-target="#deleteModal"
                data-name="{obj}"
                data-url="{self.reverse_del_url(obj)}">
                <i class="fa-solid fa-trash"></i>
            </a>
        </div>
        """
        return mark_safe(del_icon)

    def display_edit_del(self, obj=None, header=False):
        if header:
            return '操作'

        edit_del_icon = f"""
        <div class="text-end pe-4">
            <a href="{self.reverse_edit_url(obj)}" class="text-decoration-none me-3"
               style="color: #bfbfbf; transition: 0.3s;" onmouseover="this.style.color='#1677ff'"
               onmouseout="this.style.color='#bfbfbf'">
                <i class="fa-solid fa-pen-to-square"></i>
            </a>
            <a href="#" class="text-decoration-none"
                style="color: #bfbfbf; transition: 0.3s;" onmouseover="this.style.color='#ff4d4f'"
                onmouseout="this.style.color='#bfbfbf'"
                data-bs-toggle="modal"
                data-bs-target="#deleteModal"
                data-name="{obj}"
                data-url="{self.reverse_del_url(obj)}">
                <i class="fa-solid fa-trash"></i>
            </a>
        </div>

        """
        return mark_safe(edit_del_icon)

    order_by = []
    list_display = []
    model_form_class = None
    action_list = []    # 单选框中操作


    def __init__(self, model_class, site):
        self.model_class = model_class
        self.site = site


    def get_order_by(self):
        return self.order_by

    def get_list_display(self):
        """获取要显示的字段（列），预留的自定义扩展，例如：以后根据用户的不同显示不同的列"""
        return self.list_display

    def get_add_btn(self):
        add_btn = f"""
            <a href="{self.reverse_add_url()}" class="btn btn-sm px-3"
                style="border: 1px solid #d9d9d9; color: #595959; background: #fff; transition: all 0.3s;"
                onmouseover="this.style.borderColor='#1677ff'; this.style.color='#1677ff';"
                onmouseout="this.style.borderColor='#d9d9d9'; this.style.color='#595959';">
                <i class="fa-solid fa-plus"></i> 添加
            </a>
        """
        return mark_safe(add_btn)

    def get_model_form_class(self):
        if self.model_form_class:
            return self.model_form_class

        class AddModelForm(BootStrap,forms.ModelForm):
            class Meta:
                model = self.model_class
                fields = '__all__'
        return AddModelForm

    def get_action_list(self):
        return self.action_list

    # 单选框操作
    def multi_delete(self,request):
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(pk__in=pk_list).delete()

    # 一切皆对象
    multi_delete.text = '批量删除'
    action_list.append(multi_delete)






    def changelist_view(self, request):
        # 获取要展示的列
        list_display = self.get_list_display()
        # 添加按钮
        add_btn = self.get_add_btn()
        # 表中数据
        queryset = self.model_class.objects.all(*self.get_order_by())
        # 能够进行批量操作的内容
        action_list = self.get_action_list()
        action_dict = {item.__name__:item.text for item in action_list}     # 前端多选框展示text，后端通过反射由的name找到对应的函数   ？

        align_right_columns = ['操作']


        # 表头
        header_list = []
        if list_display:
            for field_or_func in list_display:
                # 区分要展示的列是自定义的还是表中的字段
                if isinstance(field_or_func, FunctionType):
                    # 给自定义列的函数，表示现在函数功能是表头
                    verbose_name = field_or_func(self, obj=None, header=True)
                else:
                    verbose_name = self.model_class._meta.get_field(field_or_func).verbose_name

                header_list.append(verbose_name)
        else:
            # 如果没有指定要展示的列，则展示，该表名、该表查询出来的所有对象（__str__）
            header_list.append(self.model_class._meta.model_name)

        # 表body [[1,gh], [2,ghh],]
        body_list = []
        for row in queryset:
            # 每一行数据
            tr_list = []
            if not list_display:
                tr_list.append(row)
                body_list.append(tr_list)
                continue

            # 反射，获取该对象中要展示的属性（字段） or  自定义列的数据内容
            for field_or_func in list_display:
                if isinstance(field_or_func, FunctionType):
                    tr_list.append(field_or_func(self, obj=row))
                else:
                    tr_list.append(getattr(row, field_or_func))
            body_list.append(tr_list)

        if request.method == 'POST':
            # 获取选择的操作
            action_func_name = request.POST.get('action')
            if action_func_name not in action_dict:
                return HttpResponse('非法操作')
            action_func = getattr(self, action_func_name, None)
            ret = action_func(request)
            if ret:
                return ret
            return redirect(self.reverse_list_url())


        return render(
            request,
            'stark/changelist.html',
            {
                'header_list': header_list,
                'body_list': body_list,
                'add_btn':add_btn,
                'align_right_columns':align_right_columns,
                'action_dict':action_dict
            }
        )

    def add_view(self, request):
        ModelFormClass = self.get_model_form_class()
        change_list_url = self.reverse_list_url()

        if request.method == 'GET':
            form = ModelFormClass()
            return render(request,'stark/change.html',{'form':form,'change_list_url':change_list_url})
        form = ModelFormClass(data=request.POST)
        if form.is_valid():
            form.save()
            return redirect(change_list_url)
        return render(request,'stark/change.html',{'form':form,'change_list_url':change_list_url})

    def change_view(self, request, pk):
        ModelFormClass = self.get_model_form_class()
        change_list_url = self.reverse_list_url()
        obj = self.model_class.objects.filter(pk=pk).first()

        if not obj:
            return redirect(change_list_url)

        if request.method == 'GET':
            form = ModelFormClass(instance=obj)
            return render(request, 'stark/change.html', {'form': form, 'change_list_url': change_list_url})
        form = ModelFormClass(data=request.POST,instance=obj)
        if form.is_valid():
            form.save()
            return redirect(change_list_url)
        return render(request, 'stark/change.html', {'form': form, 'change_list_url': change_list_url})

    def delete_view(self, request, pk):
        self.model_class.objects.filter(pk=pk).delete()
        return JsonResponse({'status':True})


    # 为每张表生成crud路由
    def get_urls(self):
        # noinspection PyProtectedMember
        prefix = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}'

        urlpatterns = [
            path('list/', self.changelist_view, name=f'{prefix}_changelist'),
            path('add/', self.add_view, name=f'{prefix}_add'),
            path('edit/<int:pk>/', self.change_view, name=f'{prefix}_change'),
            path('del/<int:pk>/', self.delete_view, name=f'{prefix}_del'),
        ]

        # 检测‘自己(self)’的crud类，有没有在extra_url函数中自定义其他功能的url
        extra = self.extra_url()
        urlpatterns.extend(extra)

        return urlpatterns

    def extra_url(self):
        # 该配置类里目前只提供crud
        return []

    @property
    def urls(self):
        return self.get_urls()


    def reverse_list_url(self,):
        app_label = self.model_class._meta.app_label
        model_name= self.model_class._meta.model_name
        namespace = self.site.namespace
        name = f'{namespace}:{app_label}_{model_name}_changelist'
        list_url = reverse(name)
        return list_url

    def reverse_add_url(self):
        app_label = self.model_class._meta.app_label
        model_name= self.model_class._meta.model_name
        namespace = self.site.namespace
        name = f'{namespace}:{app_label}_{model_name}_add'
        add_url = reverse(name)
        return add_url

    def reverse_edit_url(self,obj):
        app_label = self.model_class._meta.app_label
        model_name= self.model_class._meta.model_name
        namespace = self.site.namespace
        name = f'{namespace}:{app_label}_{model_name}_change'
        edit_url = reverse(name,kwargs={'pk':obj.pk})
        return edit_url


    def reverse_del_url(self,obj):
        app_label = self.model_class._meta.app_label
        model_name= self.model_class._meta.model_name
        namespace = self.site.namespace
        name = f'{namespace}:{app_label}_{model_name}_del'
        del_url = reverse(name,kwargs={'pk':obj.pk})
        return del_url








# 表的注册，路由的动态生成
class StarkSite(object):
    def __init__(self):
        """
        1. 大字典，对里面的表进行动态路由创建，以及使用通用crud组件
        2. {userinfo类：userinfo对应的crud类对象,role类：role对应的crud类对象}
        """
        self.app_name = 'stark'
        self.namespace = 'stark'
        self._registry = {}

    # 收集所有表对应的model，以及每张表的crud类
    def register(self, model_class, stark_config=None):
        """
        判断表注册时是否有待带自己的crud类，
        没有则用通用的StarkConfig，
        当然如果有带，通过继承也可以使用StarkConfig中有，而自带中没有的方法  —— （因此可在基本crud之外，根据该表的需求自定义其他操作）

        :param model_class: 表对应的模型
        :param stark_config: 每张表对应的自己的crud类
        :return:
        """
        if not stark_config:
            stark_config = StarkConfig

        # ！！！进行实例化
        self._registry[model_class] = stark_config(model_class, self)
        print(self._registry)

    # 给每张表造crud路由
    def get_urls(self):
        """
        目标效果：
            urlpatterns = [
                path('stark/',([
                                    path('app01/userinfo/',([
                                                                path('list/',view,name),
                                                                path('add/',view,name),
                                                                ...
                                                            ],None,None)),
                                    path(),
                                    ...
                               ],appname,namespace))
            ]
        """

        urlpatterns = []
        for model_class, stark_config in self._registry.items():
            # 获取表所在的app名和表对应的类名（小写）
            app_label = model_class._meta.app_label
            model_name = model_class._meta.model_name

            # 示例中第二层
            urlpatterns.append(path(f'{app_label}/{model_name}/', (stark_config.urls, None, None)))

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


site = StarkSite()
