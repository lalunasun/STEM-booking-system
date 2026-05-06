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

    class Meta:
        # 序列化的模型
        model = Thing
        # 序列化所有的字段
        fields = '__all__'


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

    class Meta:
        model = Thing
        # 排除字段
        exclude = ('wish', 'collect', 'description',)


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
    # 文件类型序列化
    cover = serializers.FileField(source='thing.cover', required=False)

    class Meta:
        model = Order
        fields = '__all__'


# lesson信息序列化
class LessonSerializer(serializers.ModelSerializer):
    class_name = serializers.ReadOnlyField(source='thing.title')
    day = serializers.ReadOnlyField(source='thing.day')
    time = serializers.ReadOnlyField(source='thing.time.time')

    # 添加学生姓名字段
    students = serializers.SerializerMethodField()
    leave_students = serializers.SerializerMethodField()
    reschedule_students = serializers.SerializerMethodField()
    try_students = serializers.SerializerMethodField()

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


class LessonDetailSerializer(serializers.ModelSerializer):
    students = serializers.SerializerMethodField()
    reschedule_students = serializers.SerializerMethodField()
    try_students = serializers.SerializerMethodField()
    leave_students = serializers.SerializerMethodField()

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

    def get_students(self, obj):
        return self._serialize_students(obj.students.all(), 'normal')

    def get_reschedule_students(self, obj):
        return self._serialize_students(obj.reschedule_students.all(), 'reschedule')

    def get_try_students(self, obj):
        return self._serialize_students(obj.try_students.all(), 'try')

    def get_leave_students(self, obj):
        return self._serialize_students(obj.leave_students.all(), 'leave')
