import functools
from stark.utils.pagination import Pagination
from stark.form.bootstrap import BootStrap

from django import forms
from django.urls import path
from django.db.models import Q
from django.http import QueryDict
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.db.models import ForeignKey, ManyToManyField



# 封装 model_class, config 与 prefix 的对应关系
class ModelConfigMapping(object):

    def __init__(self, model_class, config, prefix):
        self.model_class = model_class
        self.config = config
        self.prefix = prefix


def get_choice_text(field, head):
    """
    对于Stark组件中定义列时，choice如果想要显示中文信息，调用此方法即可
    :param field: choice字段名
    :param head: 表头名称
    :return:
    """

    def inner(self, obj=None, header=False):
        if header:
            return head

        choice_field_text = f'get_{field}_display'
        return getattr(obj, choice_field_text)()

    return inner


class SearchGroupRow(object):

    def __init__(self, title, queryset_or_tuple, option, query_dict):
        """
        :param title: 组合搜索的行标题（如：部门）
        :param queryset_or_tuple: 数据库中查出来的数据
        :param option: 对应的option配置图纸对象
        :param query_dict: 当前请求的request.GET（深拷贝）
        """
        self.title = title
        self.queryset_or_tuple = queryset_or_tuple
        self.option = option
        self.query_dict = query_dict

    def __iter__(self):
        yield '<div class="whole">'
        yield self.title
        yield '</div>'
        yield '<div class="others">'

        # 获取当前url中 该字段已有的查询值
        origin_value_list = self.query_dict.getlist(self.option.field)

        # 制造全部按钮
        total_query_dict = self.query_dict.copy()
        total_query_dict._mutable = True

        if not origin_value_list:
            yield "<a class='active' href='?%s'>全部</a>" % total_query_dict.urlencode()
        else:
            # 如果 URL 里有值，说明现在选中了某个具体部门
            # 那么“全部”按钮的使命就是：把这个字段从字典里踢出去(pop)
            total_query_dict.pop(self.option.field)
            yield "<a href='?%s'>全部</a>" % total_query_dict.urlencode()

        # 制造具体的选项按钮
        for item in self.queryset_or_tuple:
            text = self.option.get_text(item)
            value = str(self.option.get_value(item))

            query_dict = self.query_dict.copy()
            query_dict._mutable = True

            # 如果是单选配置
            if not self.option.is_multi:
                if value in origin_value_list:
                    query_dict.pop(self.option.field)
                    yield "<a class='active' href='?%s'>%s</a>" % (query_dict.urlencode(), text)
                else:
                    # 如果没被选中，就把它的值强行覆盖进去
                    query_dict[self.option.field] = value
                    yield "<a href='?%s'>%s</a>" % (query_dict.urlencode(), text)

            # 如果是多选
            else:
                multi_value_list = query_dict.getlist(self.option.field)
                if value in multi_value_list:
                    # 如果已经被选中了，多选的取消操作是从列表里 remove 掉它
                    multi_value_list.remove(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield "<a class='active' href='?%s'>%s</a>" % (query_dict.urlencode(), text)
                else:
                    # 如果没被选中，就把它的值 append 进去
                    multi_value_list.append(value)
                    query_dict.setlist(self.option.field, multi_value_list)
                    yield "<a href='?%s'>%s</a>" % (query_dict.urlencode(), text)

        yield '</div>'


# 组合搜索字段参数配置类
class Option(object):

    def __init__(self, field, is_multi=False, db_condition=None, text_func=None, value_func=None, is_choice=False):
        """
        :param field: 组合搜索的字段
        :param is_multi: 是否支持多选
        :param db_condition: 在数据库中根据该字段查询时的条件
        :param text_func: 自定义页面上按钮显示的文字
        :param value_func: 自定义拼接到url里的具体参数值
        """
        self.field = field
        self.is_multi = is_multi
        if not db_condition:
            db_condition = {}
        self.db_condition = db_condition
        self.text_func = text_func
        self.value_func = value_func

        self.is_choice = is_choice

    def get_db_condition(self, request, *args, **kwargs):
        return self.db_condition

    def get_text(self, item):
        """统一获取文字的方式"""
        if self.text_func:
            return self.text_func(item)
        if self.is_choice:
            return item[1]
        return str(item)

    def get_value(self, item):
        if self.value_func:
            return self.value_func(item)
        if self.is_choice:
            return item[0]
        return item.pk

    def get_queryset_or_tuple(self, model_class, request, *args, **kwargs):
        """根据字段去获取对应的数据"""
        # 1. 拿到真实的字段对象
        field_object = model_class._meta.get_field(self.field)
        title = field_object.verbose_name

        # 2. 获取关联数据，并实例化 SearchGroupRow
        if isinstance(field_object, ForeignKey) or isinstance(field_object, ManyToManyField):
            db_condition = self.get_db_condition(request, *args, **kwargs)
            queryset = field_object.remote_field.model.objects.filter(**db_condition)
            return SearchGroupRow(title, queryset, self, request.GET)
        else:
            # 如果是 choices，顺手把标志位改了，防止后面报错
            self.is_choice = True
            return SearchGroupRow(title, field_object.choices, self, request.GET)


# 封装列表页面所需要的所有数据
class ChangeList(object):
    def __init__(self, config, data_list, q, search_list, page_html):
        self.config = config
        self.data_list = data_list

        self.q = q
        self.search_list = search_list
        self.page_html = page_html

        self.add_btn = config.get_add_btn()
        self.action_dict = {item.__name__: item.text for item in config.get_action_list()}

        self.align_right_columns = ['操作', '编辑', '删除', ]
        self.list_display = config.get_list_display()


# 通用crud配置类，生成url和视图对应关系 + 默认配置
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
            return '编辑'

        edit_icon = f"""
        <div class="text-end pe-4">
            <a href="{self.reverse_edit_url(obj)}" class="text-decoration-none"
               style="color: #bfbfbf; transition: 0.3s;" onmouseover="this.style.color='#1677ff'"
               onmouseout="this.style.color='#bfbfbf'">
                <i class="fa-solid fa-pen-to-square"></i>
            </a>
        </div>
        """
        return mark_safe(edit_icon)

    def display_del(self, obj=None, header=False):
        if header:
            return '删除'

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
        <div class="text-end ">
            <a href="{self.reverse_edit_url(obj)}" class="text-decoration-none"
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

    order_by = []  # 字段排序方式
    list_display = []  # 显示的列
    model_form_class = None
    action_list = []  # 单选框中的操作
    search_list = []  # 允许进行关键字搜索的字段
    search_group = []  # 组合搜索字段实例化的option对象

    def __init__(self, model_class, site, prefix):
        self.model_class = model_class
        self.site = site
        self.prefix = prefix
        self.request = None

    def get_order_by(self):
        return self.order_by

    def get_list_display(self):
        """获取要显示的字段（列），预留的自定义扩展，例如：以后根据用户的不同显示不同的列"""
        value = []
        value.extend(self.list_display)
        value.append(StarkConfig.display_edit)
        value.append(StarkConfig.display_del)
        return value

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

        class AddModelForm(BootStrap, forms.ModelForm):
            class Meta:
                model = self.model_class
                fields = '__all__'

        return AddModelForm

    def get_action_list(self):
        return self.action_list

    def get_search_list(self):
        return self.search_list

    def get_search_condition(self, request):
        search_list = self.get_search_list()
        q = request.GET.get('q', '')  # 搜索条件：?q='郭'

        # 创建Q对象
        con = Q()
        # 条件之间用or连接
        con.connector = 'OR'
        if q:
            for field in search_list:
                # 相当于 Q(name__contains=search_value) | Q(email__contains=search_value)
                con.children.append((f'{field}__contains', q))
        return q, search_list, con

    def get_search_group(self):
        return self.search_group

    def get_search_group_condition(self, request):
        """获取组合搜索的条件"""
        condition = {}

        # 获取允许组合搜获的字段在url中的查询条件
        for option in self.get_search_group():
            if option.is_multi:
                values_list = request.GET.getlist(option.field)
                if not values_list:
                    continue
                condition[f'{option.field}__in'] = values_list
            else:
                value = request.GET.get(option.field)
                if not value:
                    continue
                condition[option.field] = value

        return condition

    # 批量删除操作
    def multi_delete(self, request):
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(pk__in=pk_list).delete()

    # 一切皆对象
    # multi_delete.text = '批量删除'
    # action_list.append(multi_delete)

    def get_queryset(self):
        return self.model_class.objects

    def changelist_view(self, request, *args, **kwargs):
        # 获取关键字搜索条件
        q, search_list, con = self.get_search_condition(request)
        # 多字段组合搜索的条件字典
        search_group_condition = self.get_search_group_condition(request)

        # 表中数据
        origin_queryset = self.get_queryset()
        queryset = origin_queryset.filter(con).filter(**search_group_condition).order_by(*self.get_order_by())

        # 分页
        page_object = Pagination(
            current_page=request.GET.get('page'),
            all_count=queryset.count(),
            base_url=request.path_info,
            query_params=request.GET
        )
        data_list = queryset[page_object.start:page_object.end]
        page_html = page_object.page_html()

        cl = ChangeList(self, data_list, q, search_list, page_html)

        # 组合搜索渲染的调用
        search_group_row_list = []
        search_group = self.get_search_group()  # 拿到配置的 [Option('depart',xxx,xxx), ...]
        for option_obj in search_group:
            # 疯狂榨取 Option：让它去拿数据，并吐出打包好的 Row 机器
            row = option_obj.get_queryset_or_tuple(self.model_class, request, *args, **kwargs)
            search_group_row_list.append(row)

        if request.method == 'POST':
            # 获取选择的操作
            action_func_name = request.POST.get('action')
            if action_func_name not in cl.action_dict:
                return HttpResponse('非法操作')
            action_func = getattr(self, action_func_name, None)
            ret = action_func(request)
            if ret:
                return ret
            return redirect(self.reverse_list_url())

        context = {
            'cl': cl,
            'search_group_row_list': search_group_row_list
        }

        return render(request, 'stark/changelist.html', context)

    def save(self, form, is_modify=True, *args, **kwargs):
        """在使用ModelForm保存数据之前预留的钩子方法"""
        form.save()

    def add_view(self, request):
        ModelFormClass = self.get_model_form_class()
        change_list_url = self.reverse_list_url()

        if request.method == 'GET':
            form = ModelFormClass()
            return render(request, 'stark/change.html', {'form': form, 'change_list_url': change_list_url})
        form = ModelFormClass(data=request.POST)
        if form.is_valid():
            self.save(form, False, )
            # form.save()
            return redirect(change_list_url)
        return render(request, 'stark/change.html', {'form': form, 'change_list_url': change_list_url})

    def change_view(self, request, pk):
        ModelFormClass = self.get_model_form_class()
        change_list_url = self.reverse_list_url()
        obj = self.model_class.objects.filter(pk=pk).first()

        if not obj:
            return redirect(change_list_url)

        if request.method == 'GET':
            form = ModelFormClass(instance=obj)
            return render(request, 'stark/change.html', {'form': form, 'change_list_url': change_list_url})
        form = ModelFormClass(data=request.POST, instance=obj)
        if form.is_valid():
            self.save(form,)
            return redirect(change_list_url)
        return render(request, 'stark/change.html', {'form': form, 'change_list_url': change_list_url})

    def delete_view(self, request, pk):
        self.model_class.objects.filter(pk=pk).delete()
        return JsonResponse({'status': True})

    def wrapper(self, func):
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            self.request = request
            return func(request, *args, **kwargs)

        return inner

    # 为每张表生成crud路由
    def get_urls(self):

        urlpatterns = [
            path('list/', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            path('add/', self.wrapper(self.add_view), name=self.get_add_url_name),
            path('change/<int:pk>/', self.wrapper(self.change_view), name=self.get_change_url_name),
            path('del/<int:pk>/', self.wrapper(self.delete_view), name=self.get_del_url_name),
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

    @property
    def get_list_url_name(self):
        if self.prefix:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}_{self.prefix}'
        else:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}'
        name = f'{info}_changelist'
        return name

    @property
    def get_add_url_name(self):
        if self.prefix:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}_{self.prefix}'
        else:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}'
        name = f'{info}_add'
        return name

    @property
    def get_change_url_name(self):
        if self.prefix:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}_{self.prefix}'
        else:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}'
        name = f'{info}_change'
        return name

    @property
    def get_del_url_name(self):
        if self.prefix:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}_{self.prefix}'
        else:
            info = f'{self.model_class._meta.app_label}_{self.model_class._meta.model_name}'
        name = f'{info}_del'
        return name

    def reverse_list_url(self, ):
        namespace = self.site.namespace
        name = f'{namespace}:{self.get_list_url_name}'
        list_url = reverse(name)

        params_str = self.request.GET.get('_filter')
        if params_str:
            return f'{list_url}?{params_str}'
        return list_url

    def reverse_add_url(self):
        namespace = self.site.namespace
        name = f'{namespace}:{self.get_add_url_name}'
        add_url = reverse(name)

        # 如果有 GET 参数，打包成 _filter，urlencode读取所以，request.GET没有发生改变
        params_str = self.request.GET.urlencode()  # 变成 'q=han'
        if params_str:
            q = QueryDict(mutable=True)
            q['_filter'] = params_str
            return f'{add_url}?{q.urlencode()}'  # 变成 /add/?_filter=q%3Dhan

        return add_url

    def reverse_edit_url(self, obj):
        namespace = self.site.namespace
        name = f'{namespace}:{self.get_change_url_name}'
        edit_url = reverse(name, kwargs={'pk': obj.pk})

        params_str = self.request.GET.urlencode()
        if params_str:
            q = QueryDict(mutable=True)
            q['_filter'] = params_str
            return f'{edit_url}?{q.urlencode()}'

        return edit_url

    def reverse_del_url(self, obj):
        namespace = self.site.namespace
        name = f'{namespace}:{self.get_del_url_name}'
        del_url = reverse(name, kwargs={'pk': obj.pk})
        return del_url


# 保存 数据库类 和 处理该类的对象 的对应关系 + 路由的分发
class StarkSite(object):
    def __init__(self):
        """
        1. 大字典，对里面的表进行动态路由创建，以及使用通用crud组件
        2. {userinfo类：userinfo对应的crud类对象,role类：role对应的crud类对象}
        """
        self.app_name = 'stark'
        self.namespace = 'stark'
        self._registry = []

    # 收集所有表对应的model，以及每张表的crud类
    def register(self, model_class, stark_config=None, prefix=None):
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
        # self._registry[model_class] = stark_config(model_class, self)
        self._registry.append(ModelConfigMapping(model_class, stark_config(model_class, self, prefix), prefix))
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
        for item in self._registry:
            # 获取表所在的app名和表对应的类名（小写）
            app_label = item.model_class._meta.app_label
            model_name = item.model_class._meta.model_name

            if item.prefix:
                temp = path(f'{app_label}/{model_name}/{item.prefix}/', (item.config.urls, None, None))
            else:
                temp = path(f'{app_label}/{model_name}/', (item.config.urls, None, None))

            # 示例中第二层
            urlpatterns.append(temp)

        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


site = StarkSite()
