# CSAA Booking System 需求文档

版本：0.1
最后更新：2026-05-11

## 1. 项目目标

本系统用于管理学生课程报名、排课、订单、教室容量，以及未来的请假、补课和调课流程。

系统分为三个入口：

- 管理员 Dashboard：管理员用于创建教室、时间、term、课程、用户/学生、订单和课程表。
- 家长手机/网页端 Link：家长用于注册登录、创建孩子、购买课程、选择时间、查询课程记录，后续提交请假/调课。
- Guest 访客端：访客可以浏览课程，但报名之前必须注册或登录。

当前优先级：

- Phase 1：完成并稳定 Web 管理后台，使用测试数据验证核心逻辑。
- Phase 1.5：完成家长手机网页端基础流程。
- Phase 2：请假/调课、提醒、补课推荐和高级教室匹配规则。

## 2. 用户角色

### 管理员

管理员可以：

- 管理教室。
- 管理时间段。
- 管理课程分类。
- 管理 term。
- 管理课程。
- 管理用户和学生。
- 查看周课程表。
- 查看课程详情和已报名学生。
- 查看和更新订单。
- 查看课程 Available / Full / Unavailable 状态。
- 后续审批请假/调课申请。

### 家长

家长可以：

- 注册和登录。
- 创建一个或多个孩子。
- 浏览课程。
- 为选中的孩子购买课程。
- 查看订单和课程记录。
- 后续提交请假/调课申请。
- 后续接收提醒。

### Guest 访客

访客可以：

- 浏览课程列表和课程详情。

访客不可以：

- 报名课程。
- 创建订单。
- 提交请假/调课。
- 查看个人课程记录。

## 3. 核心业务对象：Student

当前系统登录账号是家长账号，但核心业务对象应该是学生。

当前模型：

```text
User(parent) -> Child
Order -> User + Child + Class + Term
```

未来产品逻辑中，应该把 `Child` 理解为 `Student`。

推荐概念模型：

```text
Parent/User
  -> Student/Child
      -> Orders
      -> Enrollments
      -> Attendance
      -> Reschedule Requests
      -> Lesson Records
```

重要规则：

- Parent 是登录账号和联系人。
- Student 才是报名、排课、查询、调课和课时统计的对象。
- 一个家长可以有多个学生。
- 一个学生可以有多个课程和 term。
- 管理端搜索和报表应该以学生为中心，而不是以家长为中心。

管理端需要改进：

- 新增 Student 页面。
- 目前可以继续使用已有 `Child` 模型。
- 显示学生姓名、年龄、家长、电话、当前课程、term、剩余课时和备注。
- 后续可以让老师登陆 添加学生的上课表现作为记录

家长端需要的行为：

- 家长登录后先选择要操作的孩子。
- 所有报名、订单、请假、调课操作都必须带 `child_id`。

## 4. Room 教室模块

管理员创建教室。

教室字段：

- 教室名称
- 容量

当前规则：

- 每个教室默认 4 个座位。
- 未来不同教室可以有不同容量。

重要容量规则：

- 满员判断应该基于共享教室占用：

```text
Room + Day + Time
```

而不是只看单个课程。

例子：

- 如果 Creator 和 Scratch 同一时间都在 Room1，它们共享同一个 4 人容量。
- 如果 Room1 周二 16:00-17:00 已经有 4 个有效学生，则该时间该教室下所有兼容课程都应显示 Full。

## 5. Time 时间模块

管理员创建标准时间段。

规则：

- 周一休息。
- 周二到周五：
  - 16:00-17:00
  - 17:00-18:00
  - 18:00-19:00
  - 19:00-20:00
- 周六、周日：
  - 09:00-10:00
  - 10:00-11:00
  - 11:00-12:00
  - 12:00-13:00 午休
  - 13:00-14:00
  - 14:00-15:00
  - 15:00-16:00
  - 16:00-17:00
  - 17:00-18:00

课程表 UI：

- 使用周视图时间网格。
- 向下滚动时保留星期表头。
- 12:00-13:00 显示为紧凑的午餐分隔行。

## 6. Category 课程分类模块

课程归属于分类。

计划分类：

- Coding
- Robotics
- Trial
- StemDay
- Math
- Language
- Competition

当前系统可能仍存在旧分类名，例如 Lego。后续需要统一命名。

## 7. Term 模块

Term 表示一个课程周期。

Term 字段：

- Term 名称
- 开始日期
- 结束日期
- 价格，可选
- 总周数/总课时数，未来字段
- 假期排除，未来字段

规则：

- Term 用于计算总课时和剩余课时。
- Term 周数应根据日期自动计算。
- 管理员必须可以手动调整周数，因为春假和不定期假期会影响实际课次数。
- 报名时应选择 term。

未来改进：

- Class 需要明确支持 term 关系。

## 8. Class 课程模块

课程字段：

- 课程名称
- Category
- Term，未来必需字段
- Room
- Day
- Time
- Price
- Status
- Cover image
- Description

当前状态概念：

- Available：管理员开放且未满员。
- Unavailable：管理员手动关闭。
- Full：根据有效学生数量和容量动态计算。

重要未来修正：

- Full 应该基于共享教室容量：

```text
Room + Day + Time active student count >= room.seat
```

有效状态通常包括：

- Paid
- Scheduled

无效状态通常不包括：

- Canceled
- Done

Pending payment 是否占位仍需确认。

## 9. 教室和课程兼容规则

这是未来调课系统的核心规则。

业务理解：

- Robotics/搭建课程通常需要固定教室和设备。
- Coding 课程相对灵活。
- 教室更像年龄/level 分组，而不是单一课程教室。
- 一个教室同一时间可以包含搭建课程和兼容 Coding 课程。

当前兼容规则草案：

| Level | 搭建课程 | 兼容 Coding |
| --- | --- | --- |
| Junior | Creator | Scratch JR / Scratch |
| Middle | Wedo | Scratch / Roblox |
| Senior | Spike | Roblox / Python / Java |

待确认问题：

- 每个 Room 属于哪个 level？
- 每个年龄对应哪个 level？
- Coding 学生是否可以跨 level？
- Trial 是否占正式座位？
- StemDay、Math、Language、Competition 是否共享同样规则？

## 10. Order 订单模块

Order 表示家长为学生购买某个课程/term。

当前状态：

- Pending payment
- Paid
- Scheduled
- Canceled
- Done

规则：

- Paid 和 Scheduled 应计入有效报名。
- Canceled 不计入。
- Done 是历史记录，不计入当前容量。
- Pending payment 是否占位仍需确认。

Order 应保留家长和学生的历史购买记录。

## 11. Schedule 课程表模块

管理员课程表是核心运营视图。

当前功能：

- 默认周视图。
- 左侧时间轴。
- 星期列。
- sticky 星期表头。
- 紧凑课程行。
- 课程颜色区分。
- 行内显示学生摘要。
- hover 下拉显示学生名字，一行一个。
- 午餐分隔行。
- FULL 标记。
- 点击课程进入课程详情。

未来改进：

- Full 逻辑需要使用 Room + Day + Time 共享容量。
- 增加按教室、分类、term、学生筛选。
- 更清楚地显示 room grouping。
- 支持学生个人课表视图。

## 12. 查询模块

系统需要以学生为中心的查询功能。

需要查询的字段：

- 课程名称
- 上课时间
- 学生姓名
- 家长姓名
- 家长电话
- Term
- 课程开始日期
- 课程结束日期
- 总课时数
- 已使用课时数
- 剩余课时数
- 订单状态
- 请假/调课记录

推荐后台查询结果：

| Student | Parent | Course | Day/Time | Term | Total Lessons | Used | Remaining |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 13. 请假、补课、调课

Phase 2 功能。

规则：

- 家长必须至少提前 48 小时请假。
- 学生在课程/term 结束前有 2 次调课机会。
- 请假通过后应生成一次补课/调课资格。

调课推荐需要考虑：

- 学生年龄/level。
- 原课程类型。
- 目标教室兼容性。
- 目标时间容量。
- 搭建课程固定教室规则。
- Coding 课程灵活教室规则。
- 共享教室占用人数。

调课记录字段：

- Student
- Parent
- Original class
- Original date/time
- Original term
- Request type
- Reason
- Requested target date/time
- Assigned target class
- Status: pending / approved / rejected / completed / canceled
- Admin note
- Created time
- Updated time

课程表显示：

- 正常学生正常显示。
- 调课学生使用特殊标记，例如绿色星号。
- 请假学生和试听学生在课程详情中单独显示。

## 14. 家长手机网页端

第一版手机端应做成 mobile web app，不先做原生 App。

Phase 1.5 手机端功能：

- 登录/注册。
- 选择孩子。
- 创建孩子。
- 浏览课程。
- 查看课程详情。
- 为选中的孩子报名。
- 选择 term。
- 查看订单。
- 查看孩子当前课程。

Phase 2 手机端功能：

- 请假申请。
- 调课申请。
- 选择补课选项。
- 接收提醒。

## 15. 提醒功能

高级功能。

提醒类型：

- 上课提醒。
- Term 即将结束提醒。
- 剩余课时提醒。
- 补课提醒。
- 调课处理结果提醒。
- 推荐课程提醒。

可能渠道：

- 站内消息。
- Email。
- SMS / WhatsApp / WeChat，后续决定。

## 16. 课程推荐

高级功能。

推荐依据：

- 学生年龄。
- 当前 level。
- 已完成课程。
- 可上课时间。
- 教室容量。
- 剩余课时。
- 家长购买历史。

## 17. 当前已完成内容

已完成或部分完成：

- 本地前后端运行。
- GitHub 仓库。
- Admin login。
- 基础 Room / Time / Category / Term / Class / User / Order 页面。
- 周课程表。
- 课程详情学生列表。
- Paid / Scheduled / Done 状态区分。
- Schedule FULL 标记。
- Class 列表动态状态。
- Student 管理页面，暂时沿用现有 Child 模型。
- Time 排序。
- 本地测试数据创建。
- 本地图片文件恢复。

## 18. 已知风险

- Full 逻辑需要升级为共享 Room/Time 容量。
- Class 需要更清楚的 term 关系。
- 测试数据需要按照真实教室兼容规则重建。
- 上传图片是本地文件，不会自动进入 GitHub。
- 家长手机端尚未开始。
- 调课规则需要先确认再实现。

## 19. 建议下一步

Web 管理后台：

1. 将 Full 逻辑升级为共享 Room + Day + Time 容量。
2. 按真实教室兼容规则重建测试课程数据。
3. 新增以学生为中心的查询模块。
4. 明确 Class-Term 关系。
5. 持续更新本文档。

手机端：

1. 家长登录/注册。
2. 孩子选择和孩子管理。
3. 课程列表和课程详情。
4. 报名流程。
5. 订单/课程记录页面。

Phase 2：

1. 请假申请。
2. 调课申请。
3. 补课推荐。
4. 提醒系统。
5. 课程推荐。
