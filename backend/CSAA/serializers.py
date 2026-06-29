import datetime
import json

from django.db.models import Q
from rest_framework import serializers

from CSAA.models import Thing, Classification, Tag, User, Comment, LoginLog, Order, OpLog, \
    Ad, Notice, ErrorLog, Lesson, Time, Term, Child, CourseAdjustment, TrialRequest, StudentLessonNote, SystemSetting, DailyStudentAdjustment, StudentComment


# 课程信息序列化
class ThingSerializer(serializers.ModelSerializer):
    """
    ReadOnlyField是一个只读字段，它只用于序列化器的输出，不能用于反序列化器的输入。
    当在序列化器中定义ReadOnlyField时，它将只读取模型实例中的相应字段的值，并将其包含在序列化的输出中。
    这意味着这title字段不能被更新或创建。
    """
    classification_title = serializers.ReadOnlyField(source='classification.title')
    time_title = serializers.ReadOnlyField(source='time.time')
    room_name = serializers.ReadOnlyField(source='tag.title')
    room_capacity = serializers.ReadOnlyField(source='tag.seat')
    enrolled_count = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()
    display_status = serializers.SerializerMethodField()

    class Meta:
        # 序列化的模型
        model = Thing
        # 序列化所有的字段
        fields = '__all__'

    def get_enrolled_count(self, obj):
        return self._room_time_enrolled_count(obj)

    def _room_time_enrolled_count(self, obj):
        cache = self.context.setdefault('room_time_enrolled_count', {})
        cache_key = (
            obj.tag_id or 'thing',
            obj.day or '',
            obj.time_id or obj.id,
        )
        if cache_key in cache:
            return cache[cache_key]

        if not obj.tag or not obj.time or not obj.day:
            cache[cache_key] = Order.objects.filter(
                thing=obj,
                child__isnull=False,
                status__in=[2, 6],
                trial_package_requests__isnull=True,
            ).count()
            return cache[cache_key]

        same_room_things = Thing.objects.filter(tag=obj.tag, day=obj.day, time=obj.time)
        cache[cache_key] = Order.objects.filter(
            thing__in=same_room_things,
            child__isnull=False,
            status__in=[2, 6],
            trial_package_requests__isnull=True,
        ).count()
        return cache[cache_key]

    def get_available_seats(self, obj):
        capacity = obj.tag.seat if obj.tag else None
        if capacity is None:
            return None

        seats = int(capacity) - self._room_time_enrolled_count(obj)
        return max(seats, 0)

    def get_display_status(self, obj):
        if str(obj.status) == '1':
            return 'Closed'

        available_seats = self.get_available_seats(obj)
        if available_seats is not None and available_seats <= 0:
            return 'Full'

        return 'Open'


# 课程详情序列化
class DetailThingSerializer(serializers.ModelSerializer):
    # 只读字段
    classification_title = serializers.ReadOnlyField(source='classification.title')

    class Meta:
        model = Thing
        # 排除多对多字段
        exclude = ('wish', 'collect',)


# 修改课程信息序列化
class UpdateThingSerializer(serializers.ModelSerializer):
    # 只读字段
    classification_title = serializers.ReadOnlyField(source='classification.title')

    class Meta:
        model = Thing
        # 排除多对多字段
        exclude = ('wish', 'collect',)


# 查询所有课程序列化
class ListThingSerializer(serializers.ModelSerializer):
    # 只读字段
    classification_title = serializers.ReadOnlyField(source='classification.title')
    time_title = serializers.ReadOnlyField(source='time.time')
    room_name = serializers.ReadOnlyField(source='tag.title')
    room_capacity = serializers.ReadOnlyField(source='tag.seat')
    enrolled_count = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()
    display_status = serializers.SerializerMethodField()

    class Meta:
        model = Thing
        # 排除字段
        exclude = ('wish', 'collect', 'description',)

    def _room_time_enrolled_count(self, obj):
        cache = self.context.setdefault('list_room_time_enrolled_count', {})
        cache_key = (
            obj.tag_id or 'thing',
            obj.day or '',
            obj.time_id or obj.id,
        )
        if cache_key in cache:
            return cache[cache_key]

        if not obj.tag or not obj.time or not obj.day:
            cache[cache_key] = Order.objects.filter(
                thing=obj,
                child__isnull=False,
                status__in=[2, 6],
                trial_package_requests__isnull=True,
            ).count()
            return cache[cache_key]

        same_room_things = Thing.objects.filter(tag=obj.tag, day=obj.day, time=obj.time)
        cache[cache_key] = Order.objects.filter(
            thing__in=same_room_things,
            child__isnull=False,
            status__in=[2, 6],
            trial_package_requests__isnull=True,
        ).count()
        return cache[cache_key]

    def get_enrolled_count(self, obj):
        return self._room_time_enrolled_count(obj)

    def get_available_seats(self, obj):
        capacity = obj.tag.seat if obj.tag else None
        if capacity is None:
            return None

        seats = int(capacity) - self._room_time_enrolled_count(obj)
        return max(seats, 0)

    def get_display_status(self, obj):
        if str(obj.status) == '1':
            return 'Closed'

        available_seats = self.get_available_seats(obj)
        if available_seats is not None and available_seats <= 0:
            return 'Full'

        return 'Open'


# 课程分类序列化
class ClassificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classification
        fields = '__all__'


# ROOM序列化
class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


# 上课时间序列化
class TimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Time
        fields = '__all__'


# term信息序列化
class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = '__all__'


# 用户序列化
class UserSerializer(serializers.ModelSerializer):
    # 处理时间格式
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = User
        fields = '__all__'


# 评论信息序列化
class CommentSerializer(serializers.ModelSerializer):
    comment_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    # 只读字段
    title = serializers.ReadOnlyField(source='thing.title')  # 标题
    username = serializers.ReadOnlyField(source='user.username')  # 用户

    class Meta:
        model = Comment
        fields = ['id', 'content', 'comment_time', 'like_count', 'thing', 'user', 'title', 'username']


# 登录日志序列化
class LoginLogSerializer(serializers.ModelSerializer):
    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = LoginLog
        fields = '__all__'


# 操作日志序列化
class OpLogSerializer(serializers.ModelSerializer):
    re_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = OpLog
        fields = '__all__'


# 错误日志序列化
class ErrorLogSerializer(serializers.ModelSerializer):
    log_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = ErrorLog
        fields = '__all__'


# 订单信息序列化
class OrderSerializer(serializers.ModelSerializer):
    order_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    expect_time = serializers.DateTimeField(format='%Y-%m-%d', required=False)
    return_time = serializers.DateTimeField(format='%Y-%m-%d', required=False)
    # 只读字段
    username = serializers.ReadOnlyField(source='user.username')
    child_name = serializers.ReadOnlyField(source='child.name')
    term_title = serializers.ReadOnlyField(source='term.title')
    # receiver_phone = serializers.ReadOnlyField(source='user.mobile')
    title = serializers.SerializerMethodField()
    trial_slots = serializers.SerializerMethodField()
    price = serializers.ReadOnlyField(source='thing.price')
    day = serializers.ReadOnlyField(source='thing.day')
    time_title = serializers.ReadOnlyField(source='thing.time.time')
    room_title = serializers.ReadOnlyField(source='thing.tag.title')
    # 文件类型序列化
    cover = serializers.FileField(source='thing.cover', required=False)

    class Meta:
        model = Order
        fields = '__all__'

    def _date_part(self, value):
        if not value:
            return None
        if hasattr(value, 'date'):
            return value.date()
        return value

    def _next_trial_date(self, order, thing):
        day_index = {
            'Mon': 0,
            'Tue': 1,
            'Wed': 2,
            'Thu': 3,
            'Fri': 4,
            'Sat': 5,
            'Sun': 6,
        }
        if not thing or thing.day not in day_index:
            return None

        base_date = self._date_part(order.order_time) or datetime.date.today()
        days_ahead = (day_index[thing.day] - base_date.weekday()) % 7
        return base_date + datetime.timedelta(days=days_ahead)

    def _trial_request(self, obj):
        return TrialRequest.objects.filter(package_order=obj).select_related(
            'robotics_class',
            'robotics_class__time',
            'robotics_class__tag',
            'coding_class',
            'coding_class__time',
            'coding_class__tag',
        ).first()

    def get_title(self, obj):
        if self._trial_request(obj):
            return 'Trial Package'
        return obj.thing.title if obj.thing else None

    def _slot_data(self, order, label, thing):
        if not thing:
            return {
                'label': label,
                'class_id': None,
                'title': 'Not configured yet',
                'date': None,
                'day': None,
                'time': None,
                'room': None,
                'status': 'not_configured',
            }
        trial_date = self._next_trial_date(order, thing)
        return {
            'label': label,
            'class_id': thing.id,
            'title': thing.title,
            'date': trial_date.strftime('%Y-%m-%d') if trial_date else None,
            'day': thing.day,
            'time': thing.time.time if thing.time else None,
            'room': thing.tag.title if thing.tag else None,
            'status': 'scheduled',
        }

    def get_trial_slots(self, obj):
        trial_request = self._trial_request(obj)
        if not trial_request:
            return []
        slots = [
            self._slot_data(obj, 'Robotics', trial_request.robotics_class),
            self._slot_data(obj, 'Coding', trial_request.coding_class),
        ]
        return slots


# lesson信息序列化
class CourseAdjustmentSerializer(serializers.ModelSerializer):
    created_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    updated_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    approved_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    student_name = serializers.ReadOnlyField(source='student.name')
    parent_username = serializers.ReadOnlyField(source='parent.username')
    parent_name = serializers.SerializerMethodField()
    parent_phone = serializers.ReadOnlyField(source='parent.mobile')
    parent_email = serializers.ReadOnlyField(source='parent.email')
    original_order_number = serializers.ReadOnlyField(source='original_order.order_number')
    original_class_title = serializers.ReadOnlyField(source='original_class.title')
    original_term_title = serializers.ReadOnlyField(source='original_term.title')
    selected_target_class_title = serializers.ReadOnlyField(source='selected_target_class.title')
    recommended_option_list = serializers.SerializerMethodField()
    admin_extra_recommendation_detail = serializers.SerializerMethodField()

    class Meta:
        model = CourseAdjustment
        fields = '__all__'

    def get_parent_name(self, obj):
        if not obj.parent:
            return None
        return obj.parent.nickname or obj.parent.username

    def _parse_json_field(self, value, default):
        if not value:
            return default
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return default

    def get_recommended_option_list(self, obj):
        return self._parse_json_field(obj.recommended_options, [])

    def get_admin_extra_recommendation_detail(self, obj):
        return self._parse_json_field(obj.admin_extra_recommendation, None)


class ParentCourseAdjustmentSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.name')
    original_order_number = serializers.ReadOnlyField(source='original_order.order_number')
    original_class_title = serializers.ReadOnlyField(source='original_class.title')
    original_term_title = serializers.ReadOnlyField(source='original_term.title')
    selected_target_class_title = serializers.ReadOnlyField(source='selected_target_class.title')
    created_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)
    updated_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = CourseAdjustment
        fields = [
            'id',
            'student',
            'student_name',
            'original_order',
            'original_order_number',
            'original_class',
            'original_class_title',
            'original_lesson_date',
            'original_day',
            'original_time',
            'original_term',
            'original_term_title',
            'request_type',
            'status',
            'parent_note',
            'selected_target_class',
            'selected_target_class_title',
            'selected_target_date',
            'selected_target_day',
            'selected_target_time',
            'selected_target_room',
            'created_time',
            'updated_time',
        ]


class LessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.ReadOnlyField(source='id')
    thing_id = serializers.ReadOnlyField(source='thing.id')
    class_name = serializers.ReadOnlyField(source='thing.title')
    day = serializers.ReadOnlyField(source='thing.day')
    time = serializers.ReadOnlyField(source='thing.time.time')
    room_id = serializers.ReadOnlyField(source='thing.tag.id')
    room_name = serializers.ReadOnlyField(source='thing.tag.title')
    room_capacity = serializers.ReadOnlyField(source='thing.tag.seat')

    # 添加学生姓名字段
    students = serializers.SerializerMethodField()
    leave_students = serializers.SerializerMethodField()
    reschedule_students = serializers.SerializerMethodField()
    try_students = serializers.SerializerMethodField()
    scheduled_students = serializers.SerializerMethodField()
    canceled_students = serializers.SerializerMethodField()
    scheduled_reschedule_students = serializers.SerializerMethodField()
    scheduled_trial_students = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = '__all__'

    def get_students(self, obj):
        return [student.name for student in obj.students.all()]

    def get_leave_students(self, obj):
        return [student.name for student in obj.leave_students.all()]

    def get_reschedule_students(self, obj):
        return [student.name for student in obj.reschedule_students.all()]

    def get_try_students(self, obj):
        return [student.name for student in obj.try_students.all()]

    def _date_part(self, value):
        if not value:
            return None
        if hasattr(value, 'date'):
            return value.date()
        return value

    def _next_trial_date(self, order, thing):
        day_index = {
            'Mon': 0,
            'Tue': 1,
            'Wed': 2,
            'Thu': 3,
            'Fri': 4,
            'Sat': 5,
            'Sun': 6,
        }
        if not order or not thing or thing.day not in day_index:
            return None

        base_date = self._date_part(order.order_time) or datetime.date.today()
        days_ahead = (day_index[thing.day] - base_date.weekday()) % 7
        return base_date + datetime.timedelta(days=days_ahead)

    def get_scheduled_students(self, obj):
        orders = Order.objects.filter(
            thing=obj.thing,
            child__isnull=False,
            term__isnull=False,
            expect_time__isnull=False,
            return_time__isnull=False,
            status=6,
        ).select_related('child', 'term')
        class_date = self.context.get('class_date')
        if class_date:
            orders = orders.filter(
                expect_time__date__lte=class_date,
                return_time__date__gte=class_date,
            )

        return [
            {
                'order_id': order.id,
                'student_id': order.child.id,
                'name': order.child.name,
                'term_id': order.term.id,
                'term_title': order.term.title,
                'expect_time': order.expect_time.strftime('%Y-%m-%d'),
                'return_time': order.return_time.strftime('%Y-%m-%d'),
                'status': order.status,
            }
            for order in orders
        ]

    def get_canceled_students(self, obj):
        adjustments = CourseAdjustment.objects.filter(
            original_class=obj.thing,
            request_type='cancel_class',
            status='approved',
            student__isnull=False,
        ).select_related('student', 'parent', 'original_term')
        class_date = self.context.get('class_date')
        if class_date:
            adjustments = adjustments.filter(original_lesson_date=class_date)

        return [
            {
                'adjustment_id': adjustment.id,
                'student_id': adjustment.student.id,
                'name': adjustment.student.name,
                'date': adjustment.original_lesson_date.strftime('%Y-%m-%d') if adjustment.original_lesson_date else None,
                'term_id': adjustment.original_term.id if adjustment.original_term else None,
                'term_title': adjustment.original_term.title if adjustment.original_term else None,
                'status': 'cancel',
            }
            for adjustment in adjustments
        ]

    def get_scheduled_reschedule_students(self, obj):
        adjustments = CourseAdjustment.objects.filter(
            selected_target_class=obj.thing,
            request_type='makeup_class',
            status='completed',
            student__isnull=False,
        ).select_related('student', 'parent', 'original_term')
        class_date = self.context.get('class_date')
        if class_date:
            adjustments = adjustments.filter(selected_target_date=class_date)

        return [
            {
                'adjustment_id': adjustment.id,
                'student_id': adjustment.student.id,
                'name': adjustment.student.name,
                'date': adjustment.selected_target_date.strftime('%Y-%m-%d') if adjustment.selected_target_date else None,
                'term_id': adjustment.original_term.id if adjustment.original_term else None,
                'term_title': adjustment.original_term.title if adjustment.original_term else None,
                'status': 'reschedule',
            }
            for adjustment in adjustments
        ]

    def get_scheduled_trial_students(self, obj):
        trial_requests = TrialRequest.objects.filter(
            Q(robotics_class=obj.thing) | Q(coding_class=obj.thing),
            child__isnull=False,
            package_order__status__in=[2, 6],
            status__in=['approved', 'scheduled'],
        ).select_related(
            'child',
            'package_order',
            'robotics_class',
            'coding_class',
        )

        students = []
        for trial_request in trial_requests:
            trial_date = self._next_trial_date(trial_request.package_order, obj.thing)
            students.append({
                'trial_request_id': trial_request.id,
                'student_id': trial_request.child.id,
                'order_id': trial_request.package_order.id if trial_request.package_order else None,
                'name': trial_request.child.name,
                'date': trial_date.strftime('%Y-%m-%d') if trial_date else None,
                'status': 'trial',
            })
        return students


class DailyLessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.ReadOnlyField(source='id')
    thing_id = serializers.ReadOnlyField(source='thing.id')
    class_name = serializers.ReadOnlyField(source='thing.title')
    day = serializers.ReadOnlyField(source='thing.day')
    time = serializers.ReadOnlyField(source='thing.time.time')
    room_id = serializers.ReadOnlyField(source='thing.tag.id')
    room_name = serializers.ReadOnlyField(source='thing.tag.title')
    room_capacity = serializers.ReadOnlyField(source='thing.tag.seat')
    scheduled_students = serializers.SerializerMethodField()
    canceled_students = serializers.SerializerMethodField()
    scheduled_reschedule_students = serializers.SerializerMethodField()
    scheduled_trial_students = serializers.SerializerMethodField()
    moved_students = serializers.SerializerMethodField()
    sick_leave_students = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            'id',
            'lesson_id',
            'thing',
            'thing_id',
            'class_name',
            'day',
            'time',
            'room_id',
            'room_name',
            'room_capacity',
            'scheduled_students',
            'canceled_students',
            'scheduled_reschedule_students',
            'scheduled_trial_students',
            'moved_students',
            'sick_leave_students',
        ]

    def get_scheduled_students(self, obj):
        orders = self.context['orders_by_thing'].get(obj.thing_id, [])
        adjusted_student_ids = self.context['adjusted_out_by_lesson'].get(obj.id, set())
        return [
            {
                'order_id': order.id,
                'student_id': order.child.id,
                'name': order.child.name,
                'term_id': order.term.id,
                'term_title': order.term.title,
                'expect_time': order.expect_time.strftime('%Y-%m-%d'),
                'return_time': order.return_time.strftime('%Y-%m-%d'),
                'status': order.status,
                'comment_done': self._has_lesson_comment(obj, order.child_id),
                'absent_marked': self._is_absent(obj, order.child_id),
            }
            for order in orders
            if order.child_id not in adjusted_student_ids
        ]

    def get_canceled_students(self, obj):
        adjustments = self.context['cancels_by_thing'].get(obj.thing_id, [])
        return [
            {
                'adjustment_id': adjustment.id,
                'student_id': adjustment.student.id,
                'name': adjustment.student.name,
                'date': adjustment.original_lesson_date.strftime('%Y-%m-%d'),
                'term_id': adjustment.original_term.id if adjustment.original_term else None,
                'term_title': adjustment.original_term.title if adjustment.original_term else None,
                'status': 'cancel',
            }
            for adjustment in adjustments
        ]

    def get_scheduled_reschedule_students(self, obj):
        adjustments = self.context['makeups_by_thing'].get(obj.thing_id, [])
        return [
            {
                'adjustment_id': adjustment.id,
                'student_id': adjustment.student.id,
                'name': adjustment.student.name,
                'date': adjustment.selected_target_date.strftime('%Y-%m-%d'),
                'term_id': adjustment.original_term.id if adjustment.original_term else None,
                'term_title': adjustment.original_term.title if adjustment.original_term else None,
                'status': 'reschedule',
                'comment_done': self._has_lesson_comment(obj, adjustment.student_id),
                'absent_marked': self._is_absent(obj, adjustment.student_id),
            }
            for adjustment in adjustments
        ]

    def get_scheduled_trial_students(self, obj):
        return [
            {
                **student,
                'comment_done': self._has_lesson_comment(obj, student.get('student_id')),
                'absent_marked': self._is_absent(obj, student.get('student_id')),
            }
            for student in self.context['trials_by_thing'].get(obj.thing_id, [])
        ]

    def get_moved_students(self, obj):
        return [
            {
                **student,
                'comment_done': self._has_lesson_comment(obj, student.get('student_id')),
                'absent_marked': self._is_absent(obj, student.get('student_id')),
            }
            for student in self.context['moved_in_by_lesson'].get(obj.id, [])
        ]

    def get_sick_leave_students(self, obj):
        return self.context['sick_leave_by_lesson'].get(obj.id, [])

    def _has_lesson_comment(self, obj, student_id):
        if not student_id:
            return False
        return (obj.id, student_id) in self.context.get('lesson_comment_keys', set())

    def _is_absent(self, obj, student_id):
        if not student_id:
            return False
        return (obj.id, student_id) in self.context.get('absent_keys', set())


class StudentLessonNoteSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.name')
    lesson_name = serializers.ReadOnlyField(source='lesson.thing.title')
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = StudentLessonNote
        fields = '__all__'

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return None
        return obj.created_by.nickname or obj.created_by.username


# 修改课程信息序列化
class UpdateLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Thing
        fields = '__all__'


# 广告序列化
class AdSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Ad
        fields = '__all__'


# 消息提示序列化
class NoticeSerializer(serializers.ModelSerializer):
    create_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = Notice
        fields = '__all__'


class SystemSettingSerializer(serializers.ModelSerializer):
    updated_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', required=False)

    class Meta:
        model = SystemSetting
        fields = '__all__'


class ChildSerializer(serializers.ModelSerializer):
    parent_name = serializers.ReadOnlyField(source="parent.nickname")
    phone = serializers.ReadOnlyField(source="parent.mobile")
    term_info = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = '__all__'

    def get_term_info(self, obj):
        lesson = self.context.get('lesson')
        student_type = self.context.get('student_type')  # 'normal', 'leave', 'reschedule', 'try'
        if not lesson:
            return None

        order_query = {
            'child': obj,
            'thing': lesson.thing,
        }

        order = Order.objects.filter(**order_query).first()
        print(order)
        if order and order.term:
            return {
                'term_id': order.term.id,
                'term_name': order.term.title if hasattr(order.term, 'title') else None,
            }
        return None


class AdminStudentSerializer(serializers.ModelSerializer):
    parent_username = serializers.ReadOnlyField(source='parent.username')
    parent_name = serializers.SerializerMethodField()
    phone = serializers.ReadOnlyField(source='parent.mobile')
    active_classes = serializers.SerializerMethodField()
    active_terms = serializers.SerializerMethodField()
    course_history = serializers.SerializerMethodField()
    absence_records = serializers.SerializerMethodField()
    schedule_changes = serializers.SerializerMethodField()
    course_comments = serializers.SerializerMethodField()
    trial_packages = serializers.SerializerMethodField()

    class Meta:
        model = Child
        fields = '__all__'

    def get_parent_name(self, obj):
        if not obj.parent:
            return None

        return obj.parent.nickname or obj.parent.username

    def _active_orders(self, obj):
        if hasattr(obj, 'prefetched_active_orders'):
            return obj.prefetched_active_orders
        return Order.objects.filter(
            child=obj,
            status__in=[2, 6],
        ).select_related('thing', 'thing__time', 'thing__tag', 'term')

    def _course_orders(self, obj):
        return Order.objects.filter(
            child=obj,
            status__in=[2, 6, 8],
        ).select_related('thing', 'thing__time', 'thing__tag', 'term').order_by('-expect_time', 'thing__day', 'thing__time__time')

    def get_active_classes(self, obj):
        classes = []
        for order in self._active_orders(obj):
            if not order.thing:
                continue

            class_parts = [order.thing.title]
            if order.thing.day:
                class_parts.append(order.thing.day)
            if order.thing.time:
                class_parts.append(order.thing.time.time)
            if order.thing.tag:
                class_parts.append(order.thing.tag.title)

            class_label = ' | '.join(class_parts)
            if class_label not in classes:
                classes.append(class_label)
        return classes

    def get_active_terms(self, obj):
        terms = []
        for order in self._active_orders(obj):
            if order.term and order.term.title not in terms:
                terms.append(order.term.title)
        return terms

    def get_course_history(self, obj):
        if self.context.get('summary_only'):
            return []
        courses = []
        today = datetime.date.today()

        for order in self._course_orders(obj):
            thing = order.thing
            term = order.term
            end_date = order.return_time.date() if order.return_time else None
            start_date = order.expect_time.date() if order.expect_time else None
            is_finished = order.status == 8 or (end_date is not None and end_date < today)

            courses.append({
                'order_id': order.id,
                'class_name': thing.title if thing else None,
                'term': term.title if term else None,
                'day': thing.day if thing else None,
                'time': thing.time.time if thing and thing.time else None,
                'room': thing.tag.title if thing and thing.tag else None,
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
                'order_status': order.status,
                'course_status': 'Finished' if is_finished else 'Active',
            })

        return courses

    def get_trial_packages(self, obj):
        if self.context.get('summary_only'):
            return []

        requests = TrialRequest.objects.filter(child=obj).select_related(
            'package_order',
            'robotics_class',
            'robotics_class__time',
            'robotics_class__tag',
            'coding_class',
            'coding_class__time',
            'coding_class__tag',
        ).order_by('-created_time', '-id')

        day_index = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}

        def slot(category, thing, package_order):
            if not thing:
                return {
                    'category': category,
                    'configured': False,
                    'class_name': None,
                    'day': None,
                    'time': None,
                    'room': None,
                    'scheduled_date': None,
                }

            scheduled_date = None
            if package_order and package_order.order_time and thing.day in day_index:
                base_date = package_order.order_time.date()
                scheduled_date = base_date + datetime.timedelta(
                    days=(day_index[thing.day] - base_date.weekday()) % 7
                )

            return {
                'category': category,
                'configured': True,
                'class_name': thing.title,
                'day': thing.day,
                'time': thing.time.time if thing.time else None,
                'room': thing.tag.title if thing.tag else None,
                'scheduled_date': scheduled_date.strftime('%Y-%m-%d') if scheduled_date else None,
            }

        return [
            {
                'trial_request_id': request.id,
                'status': request.status,
                'order_id': request.package_order_id,
                'created_time': (
                    request.created_time.strftime('%Y-%m-%d %H:%M:%S')
                    if request.created_time else None
                ),
                'courses': [
                    slot('Robotics', request.robotics_class, request.package_order),
                    slot('Coding', request.coding_class, request.package_order),
                ],
            }
            for request in requests
        ]

    def get_absence_records(self, obj):
        if self.context.get('summary_only') and hasattr(obj, 'prefetched_absences'):
            return [
                {'adjustment_id': adjustment.id}
                for adjustment in obj.prefetched_absences
            ]
        adjustments = CourseAdjustment.objects.filter(
            student=obj,
            request_type='cancel_class',
        ).select_related(
            'original_order',
            'original_class',
            'original_class__time',
            'original_class__tag',
            'original_term',
        ).order_by('-original_lesson_date', '-created_time')

        return [
            {
                'adjustment_id': adjustment.id,
                'order_id': adjustment.original_order_id,
                'class_name': adjustment.original_class.title if adjustment.original_class else None,
                'lesson_date': (
                    adjustment.original_lesson_date.strftime('%Y-%m-%d')
                    if adjustment.original_lesson_date
                    else None
                ),
                'day': adjustment.original_day or (
                    adjustment.original_class.day if adjustment.original_class else None
                ),
                'time': adjustment.original_time or (
                    adjustment.original_class.time.time
                    if adjustment.original_class and adjustment.original_class.time
                    else None
                ),
                'room': (
                    adjustment.original_class.tag.title
                    if adjustment.original_class and adjustment.original_class.tag
                    else None
                ),
                'term': adjustment.original_term.title if adjustment.original_term else None,
                'status': adjustment.status,
                'reason': adjustment.request_reason or adjustment.parent_note or None,
                'created_time': (
                    adjustment.created_time.strftime('%Y-%m-%d %H:%M:%S')
                    if adjustment.created_time
                    else None
                ),
            }
            for adjustment in adjustments
        ]

    def get_schedule_changes(self, obj):
        if self.context.get('summary_only'):
            return []

        adjustments = CourseAdjustment.objects.filter(
            student=obj,
        ).select_related(
            'original_order',
            'original_class',
            'original_class__time',
            'original_class__tag',
            'original_term',
            'selected_target_class',
            'selected_target_class__time',
            'selected_target_class__tag',
        ).order_by('-created_time', '-id')[:12]

        def class_slot(thing, fallback_day=None, fallback_time=None, fallback_room=None):
            return {
                'class_name': thing.title if thing else None,
                'day': fallback_day or (thing.day if thing else None),
                'time': fallback_time or (thing.time.time if thing and thing.time else None),
                'room': fallback_room or (thing.tag.title if thing and thing.tag else None),
            }

        records = []
        for adjustment in adjustments:
            source = class_slot(
                adjustment.original_class,
                adjustment.original_day,
                adjustment.original_time,
                None,
            )
            target = class_slot(
                adjustment.selected_target_class,
                adjustment.selected_target_day,
                adjustment.selected_target_time,
                adjustment.selected_target_room,
            )
            records.append({
                'adjustment_id': adjustment.id,
                'order_id': adjustment.original_order_id,
                'request_type': adjustment.request_type,
                'status': adjustment.status,
                'term': adjustment.original_term.title if adjustment.original_term else None,
                'lesson_date': (
                    adjustment.original_lesson_date.strftime('%Y-%m-%d')
                    if adjustment.original_lesson_date
                    else None
                ),
                'target_date': (
                    adjustment.selected_target_date.strftime('%Y-%m-%d')
                    if adjustment.selected_target_date
                    else None
                ),
                'source': source,
                'target': target,
                'reason': adjustment.request_reason or adjustment.parent_note or None,
                'admin_note': adjustment.admin_note,
                'created_time': (
                    adjustment.created_time.strftime('%Y-%m-%d %H:%M:%S')
                    if adjustment.created_time
                    else None
                ),
            })
        return records

    def get_course_comments(self, obj):
        if self.context.get('summary_only'):
            return []

        comments = StudentComment.objects.filter(
            student=obj,
        ).select_related(
            'lesson',
            'lesson__thing',
            'created_by',
        ).order_by('-created_time')[:10]

        return [
            {
                'comment_id': comment.id,
                'content': comment.content,
                'class_name': (
                    comment.lesson.thing.title
                    if comment.lesson and comment.lesson.thing
                    else None
                ),
                'lesson_date': (
                    comment.lesson_date.strftime('%Y-%m-%d')
                    if comment.lesson_date
                    else None
                ),
                'created_by': (
                    comment.created_by.nickname or comment.created_by.username
                    if comment.created_by
                    else None
                ),
                'created_time': comment.created_time.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for comment in comments
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()
    reschedule_students = serializers.SerializerMethodField()
    try_students = serializers.SerializerMethodField()
    leave_students = serializers.SerializerMethodField()
    students_num = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = '__all__'

    def _serialize_students(self, students, student_type):
        # 帮助方法来序列化不同类型的学生
        serializer = ChildSerializer(
            students,
            many=True,
            context={
                'lesson': self.instance,
                'student_type': student_type
            }
        )
        return serializer.data

    def _scheduled_orders(self, obj):
        orders = Order.objects.filter(
            thing=obj.thing,
            child__isnull=False,
            status=6,
        )
        class_date = self.context.get('class_date')
        if class_date:
            orders = orders.filter(
                expect_time__date__lte=class_date,
                return_time__date__gte=class_date,
            )
            canceled = CourseAdjustment.objects.filter(
                original_class=obj.thing,
                original_lesson_date=class_date,
                request_type='cancel_class',
                status='approved',
                student__isnull=False,
            )
            canceled_order_ids = canceled.exclude(
                original_order__isnull=True,
            ).values_list('original_order_id', flat=True)
            canceled_student_ids = canceled.filter(
                original_order__isnull=True,
            ).values_list('student_id', flat=True)
            orders = orders.exclude(id__in=canceled_order_ids).exclude(
                child_id__in=canceled_student_ids,
            )
            adjusted_out_student_ids = DailyStudentAdjustment.objects.filter(
                source_lesson=obj,
                lesson_date=class_date,
                status='active',
                adjustment_type__in=['move', 'sick_leave'],
            ).values_list('student_id', flat=True)
            orders = orders.exclude(child_id__in=adjusted_out_student_ids)
        return orders.select_related('user', 'child', 'term').order_by('child__name', 'id')

    def _serialize_order_student(self, order):
        parent = order.user
        child = order.child
        term = order.term

        return {
            'id': child.id,
            'name': child.name,
            'parent_name': (parent.nickname or parent.username) if parent else None,
            'phone': parent.mobile if parent else None,
            'term_info': {
                'term_id': term.id,
                'term_name': term.title,
            } if term else None,
            'order_id': order.id,
            'order_status': order.status,
        }

    def get_students(self, obj):
        students = [self._serialize_order_student(order) for order in self._scheduled_orders(obj)]
        class_date = self.context.get('class_date')
        if not class_date:
            return students

        moved_in = DailyStudentAdjustment.objects.filter(
            target_lesson=obj,
            lesson_date=class_date,
            status='active',
            adjustment_type='move',
            student__isnull=False,
        ).select_related('student', 'student__parent', 'source_order__term')

        seen = {student['id'] for student in students}
        for adjustment in moved_in:
            child = adjustment.student
            if child.id in seen:
                continue
            parent = child.parent
            term = adjustment.source_order.term if adjustment.source_order else None
            seen.add(child.id)
            students.append({
                'id': child.id,
                'name': child.name,
                'parent_name': (parent.nickname or parent.username) if parent else None,
                'phone': parent.mobile if parent else None,
                'term_info': {
                    'term_id': term.id,
                    'term_name': term.title,
                } if term else None,
                'adjustment_id': adjustment.id,
                'adjustment_status': 'moved',
            })

        return sorted(students, key=lambda student: student.get('name') or '')

    def get_reschedule_students(self, obj):
        completed_makeups = CourseAdjustment.objects.filter(
            selected_target_class=obj.thing,
            request_type='makeup_class',
            status='completed',
            student__isnull=False,
        ).select_related('student', 'parent', 'original_term')
        class_date = self.context.get('class_date')
        if class_date:
            completed_makeups = completed_makeups.filter(selected_target_date=class_date)
        students = []
        seen = set()

        for adjustment in completed_makeups:
            child = adjustment.student
            parent = adjustment.parent or child.parent
            key = child.id
            seen.add(key)
            students.append({
                'id': child.id,
                'name': child.name,
                'parent_name': (parent.nickname or parent.username) if parent else None,
                'phone': parent.mobile if parent else None,
                'term_info': {
                    'term_id': adjustment.original_term.id,
                    'term_name': adjustment.original_term.title,
                } if adjustment.original_term else None,
                'adjustment_id': adjustment.id,
                'makeup_date': adjustment.selected_target_date.strftime('%Y-%m-%d') if adjustment.selected_target_date else None,
                'adjustment_status': 'reschedule',
            })

        if not class_date:
            for student in obj.reschedule_students.all():
                if student.id in seen:
                    continue
                serialized = ChildSerializer(student, context={'lesson': obj, 'student_type': 'reschedule'}).data
                students.append(serialized)

        return students

    def _date_part(self, value):
        if not value:
            return None
        if hasattr(value, 'date'):
            return value.date()
        return value

    def _next_trial_date(self, order, thing):
        day_index = {
            'Mon': 0,
            'Tue': 1,
            'Wed': 2,
            'Thu': 3,
            'Fri': 4,
            'Sat': 5,
            'Sun': 6,
        }
        if not order or not thing or thing.day not in day_index:
            return None

        base_date = self._date_part(order.order_time) or datetime.date.today()
        days_ahead = (day_index[thing.day] - base_date.weekday()) % 7
        return base_date + datetime.timedelta(days=days_ahead)

    def get_try_students(self, obj):
        trial_requests = TrialRequest.objects.filter(
            Q(robotics_class=obj.thing) | Q(coding_class=obj.thing),
            child__isnull=False,
            package_order__status__in=[2, 6],
            status__in=['approved', 'scheduled'],
        ).select_related(
            'child',
            'child__parent',
            'parent',
            'package_order',
        )
        students = []
        seen = set()

        for trial_request in trial_requests:
            child = trial_request.child
            parent = trial_request.parent or child.parent
            trial_date = self._next_trial_date(trial_request.package_order, obj.thing)
            class_date = self.context.get('class_date')
            if class_date and trial_date != class_date:
                continue
            seen.add(child.id)
            students.append({
                'id': child.id,
                'name': child.name,
                'parent_name': (parent.nickname or parent.username) if parent else None,
                'phone': parent.mobile if parent else None,
                'trial_request_id': trial_request.id,
                'trial_date': trial_date.strftime('%Y-%m-%d') if trial_date else None,
                'adjustment_status': 'trial',
            })

        if not self.context.get('class_date'):
            for student in obj.try_students.all():
                if student.id in seen:
                    continue
                serialized = ChildSerializer(student, context={'lesson': obj, 'student_type': 'try'}).data
                serialized['adjustment_status'] = 'trial'
                students.append(serialized)

        return students

    def get_leave_students(self, obj):
        canceled_adjustments = CourseAdjustment.objects.filter(
            original_class=obj.thing,
            request_type='cancel_class',
            status='approved',
            student__isnull=False,
        ).select_related('student', 'parent', 'original_term')
        class_date = self.context.get('class_date')
        if class_date:
            canceled_adjustments = canceled_adjustments.filter(original_lesson_date=class_date)
        students = []
        seen = set()

        for adjustment in canceled_adjustments:
            child = adjustment.student
            parent = adjustment.parent or child.parent
            key = child.id
            seen.add(key)
            students.append({
                'id': child.id,
                'name': child.name,
                'parent_name': (parent.nickname or parent.username) if parent else None,
                'phone': parent.mobile if parent else None,
                'term_info': {
                    'term_id': adjustment.original_term.id,
                    'term_name': adjustment.original_term.title,
                } if adjustment.original_term else None,
                'adjustment_id': adjustment.id,
                'cancel_date': adjustment.original_lesson_date.strftime('%Y-%m-%d') if adjustment.original_lesson_date else None,
                'adjustment_status': 'cancel',
            })

        if not class_date:
            for student in obj.leave_students.all():
                if student.id in seen:
                    continue
                serialized = ChildSerializer(student, context={'lesson': obj, 'student_type': 'leave'}).data
                students.append(serialized)

        return students

    def get_students_num(self, obj):
        return self._scheduled_orders(obj).count()


class TrialRequestSerializer(serializers.ModelSerializer):
    child_name = serializers.ReadOnlyField(source='child.name')
    parent_name = serializers.ReadOnlyField(source='parent.username')
    robotics_title = serializers.ReadOnlyField(source='robotics_class.title')
    coding_title = serializers.ReadOnlyField(source='coding_class.title')

    class Meta:
        model = TrialRequest
        fields = '__all__'
