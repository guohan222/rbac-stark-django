# Django-STARK-RBAC

基于 Django 框架开发的两套高度解耦的底层组件：**Stark（自动化 CRUD 视图路由引擎）** 与 **RBAC（基于路由别名的权限控制到按钮级别组件）**。两者保持物理隔离，可通过适配器代码无缝融合，用于快速构建具备复杂表单流转与细粒度权限控制的企业级中后台系统

## 🛡️ RBAC 权限系统

一套严格遵循 RBAC（Role-Based Access Control）标准数据模型，并结合 Django `resolve` 反向解析机制深度优化的企业级权限与菜单拓扑引擎

### 核心特性

- **严格的 User-Role-Permission 数据解耦模型** 底层构建了规范的四层核心表结构（`Menu` -> `Permission` <-> `Role` <-> `User`）。 系统彻底切断了“用户”与“权限”的直接关联，以**角色（Role）**作为桥梁进行权限的聚合与分发。这种高度解耦的架构，使得企业在发生大规模人员调动或岗位职责变更时，只需简单调整用户的角色映射，无需逐一修改底层路由权限，极大降低了运维成本
- **基于路由别名 (Name) 的 O(1) 精准鉴权** 废弃了传统的正则路径比对。`RbacMiddleware` 中间件通过 Django 原生的 `resolve(request.path_info).view_name` 提取当前请求别名，直接在 Session 权限字典中进行精确的 Hash 匹配。原生完美支持带有动态参数（如 `<int:pk>`）的复杂 URL，杜绝了正则误判，并将鉴权时间复杂度降至 O(1)
- **动态 UI 状态与面包屑全自动推导** 在 `init_permission` 阶段，利用 ORM 的 `.values().distinct()` 单次跨表查询获取用户全量权限并固化至 Session。中间件在拦截放行时，会根据命中权限记录中的 `pid` 与 `p_name`（父级关联标识），自动装配 `request.breadcrumb_list` 与当前选中菜单状态。前端母版只需直接遍历，即可无脑实现左侧菜单联动高亮与层级面包屑导航
- **全量路由自动发现 (Autodiscover)** 通过递归提取 Django 底层的 `URLResolver` 与 `URLPattern`，并动态拼接 `namespace`。结合 `AUTO_DISCOVER_EXCLUDE` 正则白名单，一键自省并导出项目全局生效的接口与页面路由表，为“权限批量录入与分配”提供最纯净、可靠的数据源



## ⚙️ Stark：Django 自动化视图与路由引擎

一个专为 Django 框架设计的高级 CRUD（增删改查）与路由分发引擎。它通过高度抽象的面向对象设计，帮助开发者彻底告别繁琐的重复视图代码，通过极简的 Config 类配置，即可快速构建出具备复杂筛选与定制逻辑的中后台系统

###  核心特性

- **基于对象列表的多实例路由分发 (`ModelConfigMapping`)** 告别传统字典注册的单例限制。Stark 底层以 `(Model Class, Config Class, Prefix)` 结构构建路由拓扑表。原生支持同一张数据表通过配置不同的 `prefix` 前缀，派生出多套路由相互隔离、业务逻辑独立的 CRUD 页面组合
- **高可扩展的 Hook (钩子) 机制** 引擎严格遵循开闭原则 (OCP)，将页面渲染与数据流转的生命周期全面开放。内置 `get_list_display`、`get_queryset`、`get_urls` 等十余个钩子方法。开发者只需在子类中重写对应方法，即可实现诸如数据行级权限隔离、自定义扩展路由、动态列渲染等深度的业务定制
- **状态高保真的多维组合搜索** 内置 `Option` 与 `SearchGroupRow` 组件，提供对 ForeignKey、ManyToManyField 及 Choices 字段的无缝筛选支持。过滤引擎底层基于 `QueryDict` 的深拷贝流转，确保在分页、排序及跨页面跳转时，复杂的查询参数状态不会丢失
- **内存级优化的生成器渲染** 针对带有海量数据的关联表筛选场景，Stark 摒弃了将数据全量加载至内存的传统做法。前端筛选标签（如 `<a href="...">`）的组装与渲染底层完全采用 Python `yield` 生成器实现，实现按需生成，显著降低服务端的内存开销



## 🔗 组件集成与解耦缝合 (Mixins)

Stark 与 RBAC 在源码层面严格互不依赖。针对复杂的混合业务，系统通过提取公共适配器 `PermissionMixins` 实现功能缝合

在具体的业务 Config 类中，利用 Python 的多继承与 MRO (方法解析顺序) 特性混入该 Mixin。其内部通过读取 `self.site.namespace` 并探测 RBAC Session 权限字典的状态，透明接管 Stark 原生的视图配置流，从而实现对“添加、编辑、删除”等功能按钮的隐式动态鉴权与按需渲染



## 使用教程

[RBAC组件使用教程](https://github.com/guohan222/rbac-stark-django/blob/master/rbac/RBAC%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3.md)

[STARK组件使用教程](https://github.com/guohan222/rbac-stark-django/blob/master/stark/STARK%E4%BD%BF%E7%94%A8%E6%96%87%E6%A1%A3.md)
