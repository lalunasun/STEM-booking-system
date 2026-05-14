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

## 3. 核心业务对象：Student （New20260511）

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

### 10.1 预定课程、付款、排课流程

家长端报名流程应为：

1. Guest 或家长浏览可报名课程。
2. 家长先选择课程类型。
3. 家长再选择具体星期和时间段。
4. 如果尚未登录，家长需要登录或注册。
5. 家长选择要上课的孩子。
6. 家长选择或确认 term。
7. 系统创建订单，订单状态为 `Pending payment`。
8. 家长完成付款；本地测试阶段也可以由管理员手动标记付款完成。
9. 订单状态变为 `Paid`。
10. 管理员查看 paid 订单，并确认该学生进入课程表。
11. 订单状态变为 `Scheduled`。
12. 管理员周课程表显示该课程和学生名字。

容量规则：

- `Paid` 和 `Scheduled` 订单计入当前有效占位。
- `Pending payment` 暂时不占位，除非后续业务决定需要短暂锁座。
- `Canceled` 和 `Done` 不计入当前容量，但保留历史记录。
- 同一个 `Room + Day + Time` 的有效人数达到教室容量后，课程应显示 `Full`。

管理员测试流程：

1. 创建或选择一个家长。
2. 在该家长下创建或选择一个孩子。
3. 为该孩子创建对应课程/term 的订单。
4. 将订单标记为 `Paid`。
5. 将订单标记为 `Scheduled`。
6. 检查管理员周课程表和家长订单历史。

### 10.2 Trial 试听包流程

Trial 不应作为普通 Class 直接报名。它更像一个独立的试听包/体验产品，在家长端可见，但创建订单和排课逻辑应与常规课程分开。

Trial 试听包默认包含 3 次课：

1. Robotics 一次。
2. Coding 一次。
3. Math 一次。

当前业务规则：

- 家长端可以看到 Trial 试听入口。
- 家长选择 Trial 后，系统不直接进入普通 Class 注册流程。
- 家长需要选择孩子。
- 系统为该孩子推荐 3 类试听时段：
  - Robotics 可用时段。
  - Coding 可用时段。
  - Math 可用时段。
- 家长可以分别选择 3 次试听课的时间。
- 推荐时段必须有空余容量，并应落在可预约时间范围内。
- Trial 最终占位发生在被选中的具体课程时段中，而不是 Trial 本身。
- 管理员课表和课程详情中，Trial 学生应显示在 `Trial Students` 中。
- Trial 学生同样占用目标 `Room + Day + Time` 的容量。
- Math 课程目前可以先保留入口和数据结构，若尚未创建可用课程，则显示 `Coming soon` 或提示联系管理员。

推荐规则初稿：

- Robotics 试听优先推荐 Robotics 分类下有空位的课程。
- Coding 试听优先推荐 Coding 分类下有空位的课程。
- Math 试听未来推荐 Math 分类下有空位的课程。
- 不推荐已经 Full 的时段。
- 不推荐与该学生已有 active class 冲突的时段。
- 后续可根据学生年龄/level 优化推荐。

后续实现建议：

1. 新增 Trial package / Trial request 数据结构。
2. 家长端新增 Trial 选择页，显示三类试听选择。
3. 管理员端新增 Trial 申请审核/确认入口。
4. 确认后将学生加入对应课程的 `Trial Students`。
5. 主课表显示试听学生并计入容量。

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

## 16.5 调课、取消课程、补课工作流（Phase 2 重点）

本模块先在 Web 家长端完成业务闭环，确认逻辑稳定后再迁移到手机端/mobile web。第一阶段不追求一次性完成全部功能，应先完成可测试的最小闭环。

### 16.5.1 核心规则

- 家长发起取消/调课申请必须至少提前 48 小时。
- 如果距离上课不足 48 小时，系统应提示家长通过电话或邮件直接联系管理员处理特殊情况。
- 每个学生在一个 term 内可调课次数需要被记录；当前初步规则为 term 结束前有 2 次调课机会。
- 已批准的取消课程会生成一次可补课机会。
- 补课必须安排在原订单/term 的日期范围内，除非管理员手动特批。
- 补课学生会占用目标教室人数容量。
- 管理员确认排课后，补课学生显示在目标课程的 Rescheduled Students 中，并在主课表中使用特殊标记。
- 原课程应保留历史记录，不能直接删除购买和排课历史。

### 16.5.2 家长端流程

家长端应从“已购买且正在使用的课程”进入调课流程。

推荐入口：

- My Orders / My Courses 中显示学生当前 active classes。
- 家长选择某个孩子。
- 家长进入某个已购买、已付款、正在使用的课程。
- 页面显示课程日历，能看到该学生在 term 内的上课日期。

家长端取消课程流程：

1. 家长选择孩子。
2. 家长进入该孩子正在上的课程。
3. 家长在课程日历中选择要取消的某一次课。
4. 系统检查是否提前 48 小时。
5. 如果不足 48 小时，提示家长电话/邮件联系管理员，不允许直接提交普通申请。
6. 如果满足 48 小时，家长点击 Cancel Class。
7. 系统弹出确认窗口，说明取消后需要管理员审批。
8. 家长确认后，系统创建取消课程申请。
9. 系统发送取消课程申请邮件给管理员。
10. 申请状态为 Pending admin review。

管理员批准取消后：

1. 原课程该学生本次课标记为 absent/canceled by request。
2. 系统生成一次 makeup eligibility。
3. 家长端显示可选择补课。
4. 系统默认推荐 2 个可选补课时段。

家长端补课申请流程：

1. 家长看到系统推荐的 2 个可选时段。
2. 推荐时段必须在 term 范围内。
3. 推荐时段必须满足教室容量。
4. 推荐时段应尽量匹配课程类型、年龄/level 和教室兼容规则。
5. 家长选择一个补课时段。
6. 家长确认提交补课申请。
7. 系统发送课程调整申请给管理员。
8. 申请状态为 Pending admin review。

### 16.5.3 管理员端流程

管理员需要新增课程调整管理模块，建议命名为 Reschedule Requests 或 Course Adjustments。

管理员模块需要显示：

- Request ID
- Student
- Parent
- Parent phone/email
- Original class
- Original class date/time
- Original term
- Request type: cancel class / makeup class / admin manual reschedule
- Request reason
- Request status
- Recommended makeup options
- Selected makeup option
- Admin decision
- Admin note
- Created time
- Updated time

管理员处理取消课程申请：

1. 查看家长提交的取消申请。
2. 检查是否满足 48 小时规则。
3. 可批准或拒绝。
4. 批准后，系统记录原课程取消/请假状态。
5. 系统生成补课资格。
6. 系统给家长端开放补课选择。
7. 系统可发送审批结果通知给家长。

管理员处理补课申请：

1. 查看家长选择的补课时段。
2. 检查目标课程是否在 term 范围内。
3. 检查目标教室容量。
4. 检查课程类型、年龄/level、教室兼容规则。
5. 管理员批准后，系统将学生加入目标课程 Rescheduled Students。
6. 目标课程人数容量增加。
7. 主课表显示该学生为调课/补课学生。
8. 系统通知家长申请已确认。

### 16.5.4 系统推荐补课时段规则

系统默认推荐 2 个可选补课时段。推荐逻辑初稿：

- 必须在原订单 term 的 start/end 日期范围内。
- 必须是当前日期之后的课程。
- 必须有可用容量。
- 必须不与学生已有课程冲突。
- 优先推荐同课程名称、同课程类型的时段。
- 如果同课程无可用时段，再考虑兼容课程/教室。
- Robotics/building 课程优先固定教室和设备。
- Coding 课程可根据年龄/level 和容量更灵活推荐。
- 推荐结果应显示课程名、日期、星期、时间、教室、剩余座位。

已确认规则：

- 不允许补到不同课程名但同 level 的课程；补课应尽量保持同课程名。
- 默认不允许跨 term 补课。
- 如果学生已经报名了下一个 term，管理员可以允许补课延期到下一个 term。
- 如果家长不接受系统推荐的 2 个时段，家长可以在申请留言中说明偏好，或直接电话联系管理员。
- 家长留言/电话沟通后的特殊安排由管理员手动标注和处理。
- 管理员需要可以手动添加第三个推荐补课选项。
- 管理员添加的第三个选项应同样检查容量、term 范围和课程冲突；如需强制安排，必须填写 admin note。

### 16.5.5 管理员手动调课

管理员需要有手动调课能力，用于电话/邮件特殊情况或不足 48 小时的请求。

管理员手动调课初步流程：

1. 管理员搜索学生。
2. 管理员查看该学生当前 active classes 和课程日历。
3. 管理员选择原课程日期。
4. 管理员选择目标补课日期/课程。
5. 系统提示容量、term 范围、课程兼容性和冲突检查结果。
6. 管理员可以强制确认，但需要填写 admin note。
7. 系统生成 admin manual reschedule 记录。
8. 学生进入目标课程 Rescheduled Students。
9. 目标课程占用容量。
10. 家长端能看到调整后的补课记录。

### 16.5.6 管理员 Note 和课表标记

管理员需要可以在课程调整过程中添加 note，用于记录电话沟通、特殊原因、手动安排和例外审批。

Note 显示需求：

- Course Adjustments 列表显示 admin note 摘要。
- 调课详情页显示完整 admin note 和 parent note。
- 主课表中被管理员特殊标记的课程/学生应显示 note 标识。
- hover 或点击课程详情时可以查看 note 内容。
- note 不应替代正式状态；状态仍然使用 pending / approved / rejected / completed / canceled。

### 16.5.7 数据模型草案

后续可能需要新增 RescheduleRequest / CourseAdjustment 模型。

建议字段：

- id
- student/child
- parent/user
- original_order
- original_class
- original_lesson_date
- original_day
- original_time
- original_term
- request_type
- request_reason
- request_source: parent / admin
- status: pending / approved / rejected / completed / canceled
- recommended_options
- admin_extra_recommendation
- selected_target_class
- selected_target_date
- selected_target_day
- selected_target_time
- selected_target_room
- admin_note
- parent_note
- approved_by
- approved_time
- created_time
- updated_time

### 16.5.8 分阶段实现建议

第一步：需求和数据模型确认。

第二步：家长端在已购买课程中显示课程日历和 Cancel Class 按钮。

第三步：创建取消课程申请，不直接改排课。

第四步：管理员 Course Adjustments 列表可审批取消申请。

第五步：批准后生成补课资格，并给家长推荐 2 个补课时段。

第六步：家长选择补课时段并提交申请。

第七步：管理员审批补课申请并排课。

第八步：主课表和课程详情显示 Rescheduled Students，并计入容量。

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
