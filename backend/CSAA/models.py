from django.db import models


class User(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    ROLE_CHOICES = (
        ('0', 'administrator'),
        ('1', 'parent'),
        ('2', 'teacher')
    )
    STATUS_CHOICES = (
        ('0', 'effective'),
        ('1', 'expired'),
    )
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=50, null=True)
    password = models.CharField(max_length=50, null=True)
    role = models.CharField(max_length=2, blank=True, null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    nickname = models.CharField(blank=True, null=True, max_length=20)
    avatar = models.ImageField(upload_to='avatar/', null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    description = models.TextField(max_length=200, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    score = models.IntegerField(default=0, blank=True, null=True)
    push_email = models.CharField(max_length=40, blank=True, null=True)
    push_switch = models.BooleanField(blank=True, null=True, default=False)
    admin_token = models.CharField(max_length=32, blank=True, null=True)
    token = models.CharField(max_length=32, blank=True, null=True)


    class Meta:
        db_table = "b_user"

class Child(models.Model):
    id = models.BigAutoField(primary_key=True)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='parent_child')
    name = models.CharField(max_length=30, blank=False, null=False)
    age = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "b_child"



# Room 表
class Tag(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    seat = models.PositiveIntegerField(blank=True, null=True)
    create_time = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = "b_tag"

# 上课时间 表
class Time(models.Model):
    id = models.BigAutoField(primary_key=True)
    time = models.CharField(max_length=100, blank=True, null=True) #enter time like 9:00-10:00/9:00-11:00...
    class Meta:
        db_table = "b_time"

# 学期 表
class Term(models.Model):
    id = models.BigAutoField(primary_key=True)
    expect_time = models.DateTimeField(null=True, blank=True)  # 学期开始日期
    return_time = models.DateTimeField(null=True, blank=True)  # 学期结束日期
    title = models.CharField(max_length=100, blank=True, null=True)  # 标题
    price = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = "b_term"



# 课程分类表
class Classification(models.Model):
    list_display = ("title", "id")  # 设置后台显示的内容
    id = models.BigAutoField(primary_key=True)  # id
    title = models.CharField(max_length=100, blank=True, null=True)  # 标题
    create_time = models.DateTimeField(auto_now_add=True, null=True)  # 创建时间

    # 当它作为外键的时候，显示标题
    def __str__(self):
        return self.title

    class Meta:
        db_table = "b_classification"


# Class Infomation
class Thing(models.Model):
    STATUS_CHOICES = (
        ('0', 'available'),
        ('1', 'unavailable'),
    )
    id = models.BigAutoField(primary_key=True)
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='classification_thing')
    tag = models.ForeignKey(Tag,  on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='tag_thing')  # Classroom
    title = models.CharField(max_length=100, blank=True, null=True)  # name of the class
    cover = models.ImageField(upload_to='cover/', null=True)  #cover picture of the class
    description = models.TextField(max_length=1000, blank=True, null=True)
    price = models.CharField(max_length=50, blank=True, null=True)
    day = models.CharField(max_length=5, blank=True, null=True) # weekday like MON,TUE ,WED
    time = models.ForeignKey(Time, on_delete=models.CASCADE, blank=True, null=True,
                                       related_name='classification_time')  # time like 9:00-11:00
    repertory = models.CharField(max_length=50, blank=True, null=True)  # student number of the class

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='0')
    create_time = models.DateTimeField(auto_now_add=True, null=True)
    pv = models.IntegerField(default=0)
    recommend_count = models.IntegerField(default=0)
    wish = models.ManyToManyField(User, blank=True, related_name="wish_things")
    wish_count = models.IntegerField(default=0)
    collect = models.ManyToManyField(User, blank=True, related_name="collect_things")
    collect_count = models.IntegerField(default=0)

    class Meta:
        db_table = "b_thing"


# 评论信息表
class Comment(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    content = models.CharField(max_length=200, blank=True, null=True)  # 评论内容
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_comment')  # 用户
    thing = models.ForeignKey(Thing, on_delete=models.CASCADE, null=True, related_name='thing_comment')  # 课程
    comment_time = models.DateTimeField(auto_now_add=True, null=True)  # 评论时间
    like_count = models.IntegerField(default=0)  # 点赞数量

    class Meta:
        db_table = "b_comment"


# 登录日志表
class LoginLog(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    username = models.CharField(max_length=50, blank=True, null=True)  # 用户名
    ip = models.CharField(max_length=100, blank=True, null=True)  # ip地址
    ua = models.CharField(max_length=200, blank=True, null=True)  # ua
    log_time = models.DateTimeField(auto_now_add=True, null=True)  # 时间

    class Meta:
        db_table = "b_login_log"


# 操作日志
class OpLog(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    re_ip = models.CharField(max_length=100, blank=True, null=True)  # ip地址
    re_time = models.DateTimeField(auto_now_add=True, null=True)  # 时间
    re_url = models.CharField(max_length=200, blank=True, null=True)  # 操作路径
    re_method = models.CharField(max_length=10, blank=True, null=True)  # 请求方法
    re_content = models.CharField(max_length=200, blank=True, null=True)  # 内容
    access_time = models.CharField(max_length=10, blank=True, null=True)  # 访问时间

    class Meta:
        db_table = "b_op_log"


# 错误日志
class ErrorLog(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    ip = models.CharField(max_length=100, blank=True, null=True)  # ip地址
    url = models.CharField(max_length=200, blank=True, null=True)  # 请求路径
    method = models.CharField(max_length=10, blank=True, null=True)  # 请求方法
    content = models.CharField(max_length=200, blank=True, null=True)  # 内容
    log_time = models.DateTimeField(auto_now_add=True, null=True)  # 时间

    class Meta:
        db_table = "b_error_log"


# 订单信息表
class Order(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    order_number = models.CharField(max_length=13, blank=True, null=True)  # 订单号
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='user_order')  # 用户

    thing = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, related_name='thing_order')  # 课程
    count = models.IntegerField(default=1)  # 占位数
    num = models.PositiveIntegerField(default=0) #课时数
    child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, related_name='child_order')

    expect_time = models.DateTimeField(null=True, blank=True)  # 学期开始日期
    return_time = models.DateTimeField(null=True, blank=True)  # 学期结束日期
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, related_name='term_order')
    amount = models.CharField(max_length=10, blank=True, null=True)


    status = models.PositiveIntegerField(blank=True, null=True)  # 订单状态： 1未支付 2已支付 7订单取消  6已排课 8学期结束
    order_time = models.DateTimeField(auto_now_add=True, null=True)  # 报名时间
    pay_time = models.DateTimeField(null=True)  # 支付时间
    receiver_name = models.CharField(max_length=20, blank=True, null=True)  # 姓名
    receiver_address = models.CharField(max_length=50, blank=True, null=True)  # 地址
    receiver_phone = models.CharField(max_length=20, blank=True, null=True)  # 电话
    remark = models.CharField(max_length=30, blank=True, null=True)  # 备注

    class Meta:
        db_table = "b_order"


class Lesson(models.Model):
    id = models.BigAutoField(primary_key=True)
    thing = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, related_name='thing_lesson')
    students_num = models.PositiveIntegerField(default=0)
    students = models.ManyToManyField(Child, blank=True, related_name='students_lesson') #正课学生
    leave_students = models.ManyToManyField(Child, blank=True, related_name='leave_lesson') #请假学生
    reschedule_students = models.ManyToManyField(Child, blank=True, related_name='reschedule_lesson') #补课学生
    try_students = models.ManyToManyField(Child, blank=True, related_name='try_lesson') #试课学生


    class Meta:
        db_table = "b_lesson"


class StudentLessonNote(models.Model):
    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='lesson_notes')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='student_notes')
    lesson_date = models.DateField()
    note = models.TextField(max_length=1000, blank=True, default='')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_student_lesson_notes',
    )
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "b_student_lesson_note"
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'lesson', 'lesson_date'],
                name='unique_student_lesson_note',
            ),
        ]


class StudentComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='admin_comments')
    content = models.TextField(max_length=2000)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_student_comments',
    )
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "b_student_comment"
        indexes = [
            models.Index(
                fields=['student', '-created_time'],
                name='b_student_c_student_d9bd8c_idx',
            ),
        ]


class DailyStudentAdjustment(models.Model):
    ADJUSTMENT_TYPE_CHOICES = (
        ('move', 'Move'),
        ('sick_leave', 'Sick Leave'),
    )
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('reverted', 'Reverted'),
    )

    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='daily_adjustments')
    lesson_date = models.DateField()
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    source_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='daily_adjustments_out',
    )
    target_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='daily_adjustments_in',
    )
    source_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='daily_adjustments',
    )
    lesson_count_delta = models.IntegerField(default=0)
    reason = models.CharField(max_length=300, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_daily_adjustments',
    )
    reverted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reverted_daily_adjustments',
    )
    created_time = models.DateTimeField(auto_now_add=True)
    reverted_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "b_daily_student_adjustment"
        indexes = [
            models.Index(
                fields=['lesson_date', 'status'],
                name='b_daily_stu_lesson__4246d1_idx',
            ),
            models.Index(
                fields=['student', 'lesson_date'],
                name='b_daily_stu_student_7f6588_idx',
            ),
        ]


class PermanentCourseChange(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('reverted', 'Reverted'),
    )

    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(Child, on_delete=models.CASCADE, related_name='permanent_course_changes')
    effective_date = models.DateField()
    source_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='permanent_changes_out')
    target_order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='permanent_changes_in')
    source_lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='permanent_changes_out')
    target_lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='permanent_changes_in')
    original_source_return_time = models.DateTimeField()
    transferred_lesson_count = models.PositiveIntegerField(default=0)
    reason = models.CharField(max_length=500, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_permanent_course_changes',
    )
    reverted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reverted_permanent_course_changes',
    )
    created_time = models.DateTimeField(auto_now_add=True)
    reverted_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'b_permanent_course_change'
        indexes = [
            models.Index(fields=['student', 'status'], name='b_perm_chg_student_status_idx'),
            models.Index(fields=['effective_date', 'status'], name='b_perm_chg_date_status_idx'),
        ]


class CourseAdjustment(models.Model):
    REQUEST_TYPE_CHOICES = (
        ('cancel_class', 'Cancel Class'),
        ('makeup_class', 'Makeup Class'),
        ('admin_manual_reschedule', 'Admin Manual Reschedule'),
    )
    SOURCE_CHOICES = (
        ('parent', 'Parent'),
        ('admin', 'Admin'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('makeup_available', 'Makeup Available'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )

    id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, related_name='course_adjustments')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='course_adjustments')
    original_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_adjustments')
    source_adjustment = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='makeup_records')
    original_class = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_adjustments')
    original_lesson_date = models.DateField(null=True, blank=True)
    original_day = models.CharField(max_length=10, blank=True, null=True)
    original_time = models.CharField(max_length=50, blank=True, null=True)
    original_term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name='course_adjustments')
    request_type = models.CharField(max_length=40, choices=REQUEST_TYPE_CHOICES, default='cancel_class')
    request_reason = models.TextField(max_length=1000, blank=True, null=True)
    request_source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='parent')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    recommended_options = models.TextField(max_length=2000, blank=True, null=True)
    admin_extra_recommendation = models.TextField(max_length=1000, blank=True, null=True)
    selected_target_class = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, blank=True, related_name='target_course_adjustments')
    selected_target_date = models.DateField(null=True, blank=True)
    selected_target_day = models.CharField(max_length=10, blank=True, null=True)
    selected_target_time = models.CharField(max_length=50, blank=True, null=True)
    selected_target_room = models.CharField(max_length=100, blank=True, null=True)
    admin_note = models.TextField(max_length=1000, blank=True, null=True)
    parent_note = models.TextField(max_length=1000, blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_course_adjustments')
    approved_time = models.DateTimeField(null=True, blank=True)
    created_time = models.DateTimeField(auto_now_add=True, null=True)
    updated_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = "b_course_adjustment"


class TrialRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('scheduled', 'Scheduled'),
        ('canceled', 'Canceled'),
    )

    id = models.BigAutoField(primary_key=True)
    parent = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='trial_requests')
    child = models.ForeignKey(Child, on_delete=models.CASCADE, null=True, related_name='trial_requests')
    robotics_class = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_robotics_requests')
    coding_class = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_coding_requests')
    math_class = models.ForeignKey(Thing, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_math_requests')
    package_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_package_requests')
    robotics_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_robotics_requests')
    coding_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_coding_requests')
    math_order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True, related_name='trial_math_requests')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    parent_note = models.TextField(max_length=1000, blank=True, null=True)
    admin_note = models.TextField(max_length=1000, blank=True, null=True)
    created_time = models.DateTimeField(auto_now_add=True, null=True)
    updated_time = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        db_table = "b_trial_request"

# 广告信息表
class Ad(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    image = models.ImageField(upload_to='ad/', null=True)  # 图片
    link = models.CharField(max_length=500, blank=True, null=True)  # 链接
    create_time = models.DateTimeField(auto_now_add=True, null=True)  # 创建时间

    class Meta:
        db_table = "b_ad"


# 消息提醒
class Notice(models.Model):
    id = models.BigAutoField(primary_key=True)  # id
    title = models.CharField(max_length=100, blank=True, null=True)  # 标题
    content = models.CharField(max_length=1000, blank=True, null=True)  # 内容
    create_time = models.DateTimeField(auto_now_add=True, null=True)  # 创建时间

    class Meta:
        db_table = "b_notice"
