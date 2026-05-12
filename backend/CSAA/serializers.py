from rest_framework import serializers

from CSAA.models import Thing, Classification, Tag, User, Comment, LoginLog, Order, OpLog, \
    Ad, Notice, ErrorLog, Lesson, Time, Term, Child


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
        if not obj.tag or not obj.time or not obj.day:
            return Order.objects.filter(
                thing=obj,
                child__isnull=False,
                status__in=[2, 6],
            ).count()

        same_room_things = Thing.objects.filter(tag=obj.tag, day=obj.day, time=obj.time)
        return Order.objects.filter(
            thing__in=same_room_things,
            child__isnull=False,
            status__in=[2, 6],
        ).count()

    def get_available_seats(self, obj):
        capacity = obj.tag.seat if obj.tag else None
        if capacity is None:
            return None

        seats = int(capacity) - self._room_time_enrolled_count(obj)
        return max(seats, 0)

    def get_display_status(self, obj):
        available_seats = self.get_available_seats(obj)
        if available_seats is not None and available_seats <= 0:
            return 'Full'

        if str(obj.status) == '1':
            return 'Closed'

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
        if not obj.tag or not obj.time or not obj.day:
            return Order.objects.filter(
                thing=obj,
                child__isnull=False,
                status__in=[2, 6],
            ).count()

        same_room_things = Thing.objects.filter(tag=obj.tag, day=obj.day, time=obj.time)
        return Order.objects.filter(
            thing__in=same_room_things,
            child__isnull=False,
            status__in=[2, 6],
        ).count()

    def get_enrolled_count(self, obj):
        return self._room_time_enrolled_count(obj)

    def get_available_seats(self, obj):
        capacity = obj.tag.seat if obj.tag else None
        if capacity is None:
            return None

        seats = int(capacity) - self._room_time_enrolled_count(obj)
        return max(seats, 0)

    def get_display_status(self, obj):
        available_seats = self.get_available_seats(obj)
        if available_seats is not None and available_seats <= 0:
            return 'Full'

        if str(obj.status) == '1':
            return 'Closed'

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
    title = serializers.ReadOnlyField(source='thing.title')
    price = serializers.ReadOnlyField(source='thing.price')
    day = serializers.ReadOnlyField(source='thing.day')
    time_title = serializers.ReadOnlyField(source='thing.time.time')
    room_title = serializers.ReadOnlyField(source='thing.tag.title')
    # 文件类型序列化
    cover = serializers.FileField(source='thing.cover', required=False)

    class Meta:
        model = Order
        fields = '__all__'


# lesson信息序列化
class LessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.ReadOnlyField(source='id')
    thing_id = serializers.ReadOnlyField(source='thing.id')
    class_name = serializers.ReadOnlyField(source='thing.title')
    day = serializers.ReadOnlyField(source='thing.day')
    time = serializers.ReadOnlyField(source='thing.time.time')
    room_capacity = serializers.ReadOnlyField(source='thing.tag.seat')

    # 添加学生姓名字段
    students = serializers.SerializerMethodField()
    leave_students = serializers.SerializerMethodField()
    reschedule_students = serializers.SerializerMethodField()
    try_students = serializers.SerializerMethodField()
    scheduled_students = serializers.SerializerMethodField()

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

    def get_scheduled_students(self, obj):
        orders = Order.objects.filter(
            thing=obj.thing,
            child__isnull=False,
            term__isnull=False,
            expect_time__isnull=False,
            return_time__isnull=False,
            status=6,
        ).select_related('child', 'term')

        return [
            {
                'order_id': order.id,
                'name': order.child.name,
                'term_id': order.term.id,
                'term_title': order.term.title,
                'expect_time': order.expect_time.strftime('%Y-%m-%d'),
                'return_time': order.return_time.strftime('%Y-%m-%d'),
                'status': order.status,
            }
            for order in orders
        ]


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

    class Meta:
        model = Child
        fields = '__all__'

    def get_parent_name(self, obj):
        if not obj.parent:
            return None

        return obj.parent.nickname or obj.parent.username

    def _active_orders(self, obj):
        return Order.objects.filter(
            child=obj,
            status__in=[2, 6],
        ).select_related('thing', 'thing__time', 'thing__tag', 'term')

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
        return Order.objects.filter(
            thing=obj.thing,
            child__isnull=False,
            status=6,
        ).select_related('user', 'child', 'term').order_by('child__name', 'id')

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
        return [self._serialize_order_student(order) for order in self._scheduled_orders(obj)]

    def get_reschedule_students(self, obj):
        return self._serialize_students(obj.reschedule_students.all(), 'reschedule')

    def get_try_students(self, obj):
        return self._serialize_students(obj.try_students.all(), 'try')

    def get_leave_students(self, obj):
        return self._serialize_students(obj.leave_students.all(), 'leave')

    def get_students_num(self, obj):
        return self._scheduled_orders(obj).count()
