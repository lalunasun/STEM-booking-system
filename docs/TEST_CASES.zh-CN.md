# CSAA Booking System 测试案例

最后更新：2026-05-12

本文档用于记录 CSAA 选课系统的手动测试案例。

## 测试数据说明

- 本地数据库：`backend/db.sqlite3`
- 本地数据库不会提交到 Git。
- 本地管理员登录：
  - 用户名：`test`
  - 密码：`test`
- 当前教室默认容量：`4`
- 计入容量的有效订单状态：
  - `Paid`
  - `Scheduled`
- 不计入容量的订单状态：
  - `Pending payment`
  - `Canceled`
  - `Done`

## 状态说明

- `Pending`：计划测试，尚未完成。
- `Passed`：已测试，通过。
- `Failed`：已测试，目前失败。
- `Blocked`：因为数据或环境缺失，暂时无法测试。

## TC-001 管理员登录

状态：`Passed`

目的：

验证本地管理员可以登录。

步骤：

1. 打开 `http://127.0.0.1:8080/adminLogin`。
2. 输入用户名 `test`。
3. 输入密码 `test`。
4. 点击登录。

预期结果：

- 进入后台 dashboard。
- 顶部显示管理员名称。

备注：

- 本地管理员账号已在 2026-05-12 重置为 `test/test`。

## TC-002 启动本地前后端

状态：`Passed`

目的：

验证本地服务可以启动。

步骤：

1. 启动 Django 后端到 `127.0.0.1:8000`。
2. 启动 Vite 前端到 `127.0.0.1:8080`。
3. 打开后台页面。
4. 打开家长端 portal 页面。

预期结果：

- 后端监听 `8000`。
- 前端监听 `8080`。
- 后台和家长端页面都能加载。

备注：

- 前端建议使用 `NODE_OPTIONS=--max-old-space-size=8192` 启动，减少 Vite 内存崩溃。

## TC-003 后台周课程表

状态：`Passed`

目的：

验证后台课程表可以正确显示周视图课程。

步骤：

1. 管理员登录。
2. 打开 `Schedule`。
3. 确认默认是 Week。
4. 向下滚动课程表。
5. 鼠标悬停在有学生的课程上。
6. 点击课程。

预期结果：

- 默认显示周视图。
- 左侧显示时间轴。
- 滚动时星期表头保留。
- 午餐行更紧凑并有视觉分隔。
- 不同课程有不同颜色。
- hover 后展开学生名字。
- 点击课程进入 lesson/detail。

## TC-004 课程详情学生显示

状态：`Passed`

目的：

验证课程详情页显示 paid/scheduled 学生。

步骤：

1. 打开后台 Schedule。
2. 点击一个有有效学生的课程。
3. 查看课程详情页。

预期结果：

- Normal Students 显示有效学生。
- 显示学生姓名、家长、电话、term。
- 学生数量和 paid/scheduled 订单一致。

## TC-005 Term 名称编辑

状态：`Passed`

目的：

验证管理员可以编辑 term 名称和日期。

步骤：

1. 管理员登录。
2. 打开 `Term`。
3. 点击某个 term 的 `Edit`。
4. 修改 term 名称。
5. 保存。

预期结果：

- 保存成功。
- 列表显示新名称。
- 日期字段保持有效。

备注：

- 2026-05-11 已修复 update 时日期格式未规范化的问题。

## TC-006 Student 管理模块

状态：`Passed`

目的：

验证管理员可以从学生维度管理孩子信息。

步骤：

1. 管理员登录。
2. 打开 `Student`。
3. 按学生或家长搜索。
4. 给某个家长新增学生。
5. 修改学生姓名或年龄。
6. 删除测试学生。

预期结果：

- Student 列表正常加载。
- 显示家长姓名和电话。
- 有 active class/term 时可以显示。
- 新增、编辑、删除可用。

## TC-007 家长端选课首页

状态：`Passed`

目的：

验证家长端按照“先课程，再时间”的逻辑展示。

步骤：

1. 打开 `http://127.0.0.1:8080/index/portal`。
2. 选择课程卡片，例如 `Creator`。
3. 查看该课程的可选星期和时段。
4. 点击某个时段的 `Choose for Child`。

预期结果：

- 课程按课程名聚合。
- `scratch` 和 `Scratch` 这种大小写不同的课程会合并。
- 时段按星期分组。
- 每个时段显示 room、price、status、剩余座位。
- 点击时段进入课程详情。

## TC-008 家长端 Full / Open 显示

状态：`Passed`

目的：

验证教室满员后家长端显示 `Full`。

计划测试数据：

- 课程：`Creator`
- 时间：`Tue 16:00-17:00`
- 教室：`Room1`
- 容量：`4`
- Term：`2026 spring`

2026-05-12 已创建测试数据：

| Order ID | Order Number | Parent | Parent Phone | Child | Age | Status | Term | Amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | 1778597103741 | donut |  | donut_kid1 | 10 | Paid | 2026 spring | 400 |
| 25 | 1778597103750 | donut |  | donut_kid2 | 7 | Paid | 2026 spring | 400 |
| 26 | 1778597103765 | parent_01 | 555-01001 | parent_01_kid_1_age_5 | 5 | Paid | 2026 spring | 400 |
| 27 | 1778597103774 | parent_01 | 555-01001 | parent_01_kid_2_age_6 | 6 | Paid | 2026 spring | 400 |

步骤：

1. 为同一个课程/时间/教室创建 4 个 paid 订单。
2. 打开家长端 portal。
3. 选择 `Creator`。
4. 找到 `Tuesday 16:00-17:00`。

预期结果：

- 剩余座位显示 `0`。
- 状态显示 `Full`。
- 后台课程表也显示 `FULL`。

实际结果：

- API 返回 `available_seats: 0`。
- API 返回 `display_status: Full`。
- 课程手动状态仍保持 `status: 0`，Full 由动态容量计算得出。

备注：

- 修复了一个旧逻辑：家长端课程列表接口以前会把满员课程直接保存为 `status: 1`。
- Full 应该是动态显示结果，不应该覆盖管理员手动设置的课程状态。

## TC-009 预定课程 -> 付款 -> 排课流程

状态：`Pending`

目的：

验证核心业务流程。

步骤：

1. 家长选择课程类型。
2. 家长选择星期和时段。
3. 家长登录或注册。
4. 家长选择孩子。
5. 家长确认 term 和金额。
6. 系统创建 `Pending payment` 订单。
7. 管理员标记为 `Paid`。
8. 管理员标记为 `Scheduled`。
9. 打开后台 Schedule。
10. 打开家长订单历史。

预期结果：

- 先生成 pending 订单。
- paid 订单计入有效容量。
- scheduled 订单显示在后台周课程表。
- 家长仍能看到历史购买记录。

## TC-010 后台 Link 按钮

状态：`Passed`

目的：

验证后台顶部 `Link` 可以打开家长端 portal。

步骤：

1. 管理员登录。
2. 点击顶部 `Link`。

预期结果：

- 浏览器打开 `/index/portal`。
- 家长端 portal 正常加载。

备注：

- Link 目前是原生 `<a>` 链接。

## TC-011 隐藏未完成后台模块

状态：`Passed`

目的：

验证未完成入口不会导致后台点击坏掉。

步骤：

1. 管理员登录。
2. 查看左侧导航。
3. 点击每个可见模块。

预期结果：

- 可见模块都有对应页面。
- 未完成模块不显示。

当前隐藏：

- Comment(St2)
- Log(St2/3)
- Analysis(St2/3)

## TC-012 默认课程图片

状态：`Passed`

目的：

验证主要课程都有默认封面。

课程封面：

- Creator
- Wedo
- Spike
- Scratch JR
- Scratch
- Roblox
- Python
- Java
- Trial

步骤：

1. 打开家长端 portal。
2. 查看课程卡片。
3. 打开课程详情页。

预期结果：

- 课程卡片图片显示。
- 课程详情图片显示。
- Scratch 和 Python 使用新的默认图片。

## TC-013 Trial 试听包流程

状态：`Pending`

目的：

验证 Trial 不走普通 Class 报名，而是作为 3 次试听包进行选择。

业务规则：

- Trial 默认包含 3 次课。
- 三次课分别对应 Robotics、Coding、Math。
- Math 课程暂未完整开放时，可以显示占位或联系管理员。
- 试听学生最终应进入具体课程时段的 `Trial Students`。
- 试听学生占用对应 `Room + Day + Time` 容量。

步骤：

1. 家长登录。
2. 打开家长端 Trial 入口。
3. 选择一个孩子。
4. 查看系统推荐的 Robotics 试听时段。
5. 查看系统推荐的 Coding 试听时段。
6. 查看 Math 试听占位。
7. 分别选择 Robotics 和 Coding 试听时间。
8. 提交 Trial 试听申请。
9. 管理员确认 Trial 申请。
10. 打开后台 Schedule 和课程详情页。

预期结果：

- Trial 不进入普通 Class 订单确认页。
- Robotics 和 Coding 推荐项只显示有空位时段。
- Math 尚未配置时不阻塞整个流程，但需要清楚提示。
- 管理员确认后，学生显示在目标课程的 `Trial Students` 中。
- 主课表能看到试听学生标记。
- 目标教室容量包含试听学生。
