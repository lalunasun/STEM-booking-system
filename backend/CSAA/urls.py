from django.urls import path

from CSAA import views

# 子路由
app_name = 'CSAA'
urlpatterns = [
    # ---------------------------后台管理员api-------------------------------
    path('admin/overview/count', views.admin.overview.count),  # 数据分析统计
    path('admin/overview/sysInfo', views.admin.overview.sysInfo),  # 系统信息
    path('admin/thing/list', views.admin.thing.list_api),  # 课程列表
    path('admin/thing/detail', views.admin.thing.detail),  # 课程详情
    path('admin/thing/create', views.admin.thing.create),  # 新建课程
    path('admin/thing/update', views.admin.thing.update),  # 更新课程
    path('admin/thing/delete', views.admin.thing.delete),  # 删除课程
    path('admin/lesson/list', views.admin.lesson.list_api),  # 课程列表
    path('admin/lesson/detail', views.admin.lesson.detail),  # 课程详情
    path('admin/studentLessonNote', views.admin.student_lesson_note.list_or_save),
    path('admin/dailyAdjustment/list', views.admin.daily_adjustment.list_api),
    path('admin/dailyAdjustment/saveBatch', views.admin.daily_adjustment.save_batch),
    path('admin/dailyAdjustment/revert', views.admin.daily_adjustment.revert),
    path('admin/permanentCourseChange/options', views.admin.permanent_course_change.options),
    path('admin/permanentCourseChange/list', views.admin.permanent_course_change.list_api),
    path('admin/permanentCourseChange/create', views.admin.permanent_course_change.create),
    path('admin/permanentCourseChange/revert', views.admin.permanent_course_change.revert),
    path('admin/lesson/create', views.admin.lesson.create),  # 新建课程
    path('admin/lesson/update', views.admin.lesson.update),  # 更新课程
    path('admin/lesson/delete', views.admin.lesson.delete),  # 删除课程
    path('admin/comment/list', views.admin.comment.list_api),  # 评论列表
    path('admin/comment/create', views.admin.comment.create),  # 新建评论
    path('admin/comment/update', views.admin.comment.update),  # 修改评论
    path('admin/comment/delete', views.admin.comment.delete),  # 删除评论
    path('admin/classification/list', views.admin.classification.list_api),  # 分类列表
    path('admin/classification/create', views.admin.classification.create),  # 添加分类
    path('admin/classification/update', views.admin.classification.update),  # 更新分类
    path('admin/classification/delete', views.admin.classification.delete),  # 删除分类
    path('admin/tag/list', views.admin.tag.list_api),  # Room列表
    path('admin/tag/create', views.admin.tag.create),  # 创建Room
    path('admin/tag/update', views.admin.tag.update),  # 修改Room
    path('admin/tag/delete', views.admin.tag.delete),  # 删除Room
    path('admin/time/list', views.admin.times.list_api),  # time列表
    path('admin/time/create', views.admin.times.create),  # 创建time
    path('admin/time/update', views.admin.times.update),  # 修改time
    path('admin/time/delete', views.admin.times.delete),  # 删除time
    path('admin/term/list', views.admin.term.list_api),  # time列表
    path('admin/term/create', views.admin.term.create),  # 创建time
    path('admin/term/update', views.admin.term.update),  # 修改time
    path('admin/term/delete', views.admin.term.delete),  # 删除time
    path('admin/ad/list', views.admin.ad.list_api),  # 广告列表
    path('admin/ad/create', views.admin.ad.create),  # 创建广告
    path('admin/ad/update', views.admin.ad.update),  # 修改广告
    path('admin/ad/delete', views.admin.ad.delete),  # 删除广告
    path('admin/notice/list', views.admin.notice.list_api),  # 提示列表
    path('admin/notice/create', views.admin.notice.create),  # 创建提示
    path('admin/notice/update', views.admin.notice.update),  # 修改提示
    path('admin/notice/delete', views.admin.notice.delete),  # 删除提示
    path('admin/order/list', views.admin.order.list_api),  # 订单列表
    path('admin/order/create', views.admin.order.create),  # 创建订单
    path('admin/order/update', views.admin.order.update),  # 修改订单
    path('admin/order/cancel_order', views.admin.order.cancel_order),  # 取消订单
    path('admin/order/delete', views.admin.order.delete),  # 删除订单
    path('admin/order/checkIn_order', views.admin.order.check_in_order),  # 订单入住
    path('admin/order/checkOut_order', views.admin.order.check_out_order),  # 完成订单
    path('admin/loginLog/list', views.admin.loginLog.list_api),  # 登录日志列表
    path('admin/loginLog/create', views.admin.loginLog.create),  # 创建登录日志
    path('admin/loginLog/update', views.admin.loginLog.update),  # 修改登录日志
    path('admin/loginLog/delete', views.admin.loginLog.delete),  # 删除登录日志
    path('admin/opLog/list', views.admin.opLog.list_api),  # 操作日志列表
    path('admin/errorLog/list', views.admin.errorLog.list_api),  # 错误日志列表
    path('admin/user/list', views.admin.user.list_api),  # 用户列表
    path('admin/user/create', views.admin.user.create),  # 创建用户
    path('admin/user/update', views.admin.user.update),  # 修改用户
    path('admin/user/updatePwd', views.admin.user.updatePwd),  # 修改密码
    path('admin/user/delete', views.admin.user.delete),  # 删除用户
    path('admin/user/info', views.admin.user.info),  # 用户信息
    path('admin/adminLogin', views.admin.user.admin_login),  # 管理员登录
    path('admin/student/list', views.admin.student.list_api),  # 学生列表
    path('admin/student/detail', views.admin.student.detail),
    path('admin/student/comment/create', views.admin.student.create_comment),
    path('admin/student/comment/import', views.admin.student.import_comments),
    path('admin/student/create', views.admin.student.create),  # 创建学生
    path('admin/student/update', views.admin.student.update),  # 修改学生
    path('admin/student/delete', views.admin.student.delete),  # 删除学生
    path('admin/courseAdjustment/list', views.admin.course_adjustment.list_api),
    path('admin/courseAdjustment/review', views.admin.course_adjustment.review_api),
    path('admin/courseAdjustment/recommendationOptions', views.admin.course_adjustment.recommendation_options_api),
    path('admin/courseAdjustment/addExtraRecommendation', views.admin.course_adjustment.add_extra_recommendation_api),
    path('admin/courseAdjustment/confirmMakeupSchedule', views.admin.course_adjustment.confirm_makeup_schedule_api),

    # ----------------------------前台用户api-------------------------------------------
    path('index/classification/list', views.index.classification.list_api),  # 分类列表
    path('index/tag/list', views.index.tag.list_api),  # Room列表
    path('index/ad/list', views.index.ad.list_api),  # 广告列表
    path('index/user/login', views.index.user.login),  # 用户登录
    path('index/user/register', views.index.user.register),  # 用户注册
    path('index/user/info', views.index.user.info),  # 用户信息
    path('index/user/update', views.index.user.update),  # 用户修改信息
    path('index/user/updatePwd', views.index.user.updatePwd),  # 用户修改密码
    path('index/notice/list_api', views.index.notice.list_api),  # 提示列表
    path('index/thing/list', views.index.thing.list_api),  # 课程列表
    path('index/thing/detail', views.index.thing.detail),  # 课程详情
    path('index/thing/increaseWishCount', views.index.thing.increaseWishCount),  # 添加想要数量
    path('index/thing/addWishUser', views.index.thing.addWishUser),  # 添加想要
    path('index/thing/removeWishUser', views.index.thing.removeWishUser),  # 移除想要
    path('index/thing/getWishThingList', views.index.thing.getWishThingList),  # 获取想要列表
    path('index/thing/addCollectUser', views.index.thing.addCollectUser),  # 添加收藏
    path('index/thing/removeCollectUser', views.index.thing.removeCollectUser),  # 移除收藏
    path('index/thing/getCollectThingList', views.index.thing.getCollectThingList),  # 获取收藏的课程列表
    path('index/thing/increaseRecommendCount', views.index.thing.increaseRecommendCount),  # 增加评论数量
    path('index/comment/list', views.index.comment.list_api),  # 评论列表
    path('index/comment/listMyComments', views.index.comment.list_my_comment),  # 我的评论列表
    path('index/comment/create', views.index.comment.create),  # 创建评论
    path('index/comment/delete', views.index.comment.delete),  # 删除评论
    path('index/comment/like', views.index.comment.like),  # 点赞
    path('index/order/list', views.index.order.list_api),  # 订单列表
    path('index/order/create', views.index.order.create),  # 创建订单
    path('index/order/createTrial', views.index.trial.create),
    path('index/order/cancel_order', views.index.order.cancel_order),  # 取消订单
    path('index/order/pay_order', views.index.order.pay_order),  # 完成订单
    path('index/term/list', views.index.term.list_api),
    path('index/child/list', views.index.child.list_api),
    path('index/child/create', views.index.child.create),
    path('index/courseAdjustment/list', views.index.course_adjustment.list_api),
    path('index/courseAdjustment/createCancel', views.index.course_adjustment.create_cancel_request),
    path('index/trial/create', views.index.trial.create),

]
