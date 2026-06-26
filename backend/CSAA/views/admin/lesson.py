import datetime
from collections import defaultdict

from django.db.models import Q
from rest_framework.decorators import api_view, authentication_classes

from CSAA import utils
from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Classification, Thing, Tag, Lesson, Order, CourseAdjustment, TrialRequest, DailyStudentAdjustment
from CSAA.serializers import ThingSerializer, UpdateThingSerializer, LessonSerializer, LessonDetailSerializer, DailyLessonSerializer


# 查询课程数据
@api_view(['GET'])  # 装饰器，只接受get请求
def list_api(request):
    if request.method == 'GET':  # 可以不用判断请求方式
        class_date = None
        date_value = request.GET.get('date')
        if date_value:
            try:
                class_date = datetime.date.fromisoformat(date_value)
            except ValueError:
                return APIResponse(code=1, msg='Invalid class date')

        lessons = Lesson.objects.filter(
            thing__status='0',
        ).select_related(
            'thing',
            'thing__time',
            'thing__tag',
        ).prefetch_related(
            'students',
            'leave_students',
            'reschedule_students',
            'try_students',
        )
        if class_date:
            day_code = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][class_date.weekday()]
            lessons = lessons.filter(thing__day=day_code)

        if not class_date:
            serializer = LessonSerializer(lessons, many=True)
            return APIResponse(code=0, msg='查询成功', data=serializer.data)

        lessons = list(lessons)
        thing_ids = [lesson.thing_id for lesson in lessons]

        orders_by_thing = defaultdict(list)
        orders = Order.objects.filter(
            thing_id__in=thing_ids,
            child__isnull=False,
            term__isnull=False,
            expect_time__date__lte=class_date,
            return_time__date__gte=class_date,
            status=6,
        ).select_related('child', 'term')
        for order in orders:
            orders_by_thing[order.thing_id].append(order)

        cancels_by_thing = defaultdict(list)
        cancels = CourseAdjustment.objects.filter(
            original_class_id__in=thing_ids,
            original_lesson_date=class_date,
            request_type='cancel_class',
            status='approved',
            student__isnull=False,
        ).select_related('student', 'original_term')
        for adjustment in cancels:
            cancels_by_thing[adjustment.original_class_id].append(adjustment)

        makeups_by_thing = defaultdict(list)
        makeups = CourseAdjustment.objects.filter(
            selected_target_class_id__in=thing_ids,
            selected_target_date=class_date,
            request_type='makeup_class',
            status='completed',
            student__isnull=False,
        ).select_related('student', 'original_term')
        for adjustment in makeups:
            makeups_by_thing[adjustment.selected_target_class_id].append(adjustment)

        trials_by_thing = defaultdict(list)
        trials = TrialRequest.objects.filter(
            Q(robotics_class_id__in=thing_ids)
            | Q(coding_class_id__in=thing_ids)
            | Q(math_class_id__in=thing_ids),
            child__isnull=False,
            package_order__status__in=[2, 6],
            status__in=['approved', 'scheduled'],
        ).select_related(
            'child',
            'package_order',
            'robotics_class',
            'coding_class',
            'math_class',
        )
        day_index = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
        for trial in trials:
            base_date = trial.package_order.order_time.date()
            for thing in [trial.robotics_class, trial.coding_class, trial.math_class]:
                if not thing or thing.id not in thing_ids:
                    continue
                trial_date = base_date + datetime.timedelta(
                    days=(day_index[thing.day] - base_date.weekday()) % 7
                )
                if trial_date != class_date:
                    continue
                trials_by_thing[thing.id].append({
                    'trial_request_id': trial.id,
                    'student_id': trial.child.id,
                    'order_id': trial.package_order_id,
                    'name': trial.child.name,
                    'date': trial_date.strftime('%Y-%m-%d'),
                    'status': 'trial',
                })

        adjusted_out_by_lesson = defaultdict(set)
        moved_in_by_lesson = defaultdict(list)
        sick_leave_by_lesson = defaultdict(list)
        daily_adjustments = DailyStudentAdjustment.objects.filter(
            lesson_date=class_date,
            status='active',
        ).select_related(
            'student',
            'source_order__term',
            'source_lesson',
            'target_lesson',
        )
        for adjustment in daily_adjustments:
            adjusted_out_by_lesson[adjustment.source_lesson_id].add(adjustment.student_id)
            term = adjustment.source_order.term if adjustment.source_order else None
            item = {
                'adjustment_id': adjustment.id,
                'student_id': adjustment.student_id,
                'name': adjustment.student.name,
                'date': class_date.strftime('%Y-%m-%d'),
                'term_id': term.id if term else None,
                'term_title': term.title if term else None,
                'reason': adjustment.reason,
                'lesson_count_delta': adjustment.lesson_count_delta,
            }
            if adjustment.adjustment_type == 'move' and adjustment.target_lesson_id:
                moved_in_by_lesson[adjustment.target_lesson_id].append(item)
            elif adjustment.adjustment_type == 'sick_leave':
                sick_leave_by_lesson[adjustment.source_lesson_id].append(item)

        serializer = DailyLessonSerializer(
            lessons,
            many=True,
            context={
                'orders_by_thing': orders_by_thing,
                'cancels_by_thing': cancels_by_thing,
                'makeups_by_thing': makeups_by_thing,
                'trials_by_thing': trials_by_thing,
                'adjusted_out_by_lesson': adjusted_out_by_lesson,
                'moved_in_by_lesson': moved_in_by_lesson,
                'sick_leave_by_lesson': sick_leave_by_lesson,
            },
        )
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 课程详情
@api_view(['GET'])
def detail(request):
    try:
        lesson_id = request.GET.get('lesson_id')
        if lesson_id:
            lesson = Lesson.objects.get(pk=lesson_id)
        else:
            pk = request.GET.get('id', -1)
            thing = Thing.objects.get(pk=pk)
            lesson = Lesson.objects.get(thing=thing)
    except Lesson.DoesNotExist:
        utils.log_error(request, '课程不存在')
        return APIResponse(code=1, msg='课程不存在')

    if request.method == 'GET':
        class_date = request.GET.get('date')
        if class_date:
            try:
                class_date = datetime.date.fromisoformat(class_date)
            except ValueError:
                return APIResponse(code=1, msg='Invalid class date')

        serializer = LessonDetailSerializer(
            lesson,
            context={'class_date': class_date},
        )
        return APIResponse(code=0, msg='查询成功', data=serializer.data)


# 创建课程
@api_view(['POST'])  # 直接受post请求
@authentication_classes([AdminTokenAuthtication])  # 管理员身份验证
def create(request):
    serializer = LessonSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='创建成功', data=serializer.data)
    else:
        print(serializer.errors)
        utils.log_error(request, '输入课程参数错误')
    return APIResponse(code=1, msg='创建失败')


# 修改课程
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        pk = request.GET.get('id', -1)
        lesson = Lesson.objects.get(pk=pk)
    except Lesson.DoesNotExist:
        return APIResponse(code=1, msg='课程不存在')

    serializer = UpdateLessonSerializer(lesson, data=request.data)
    if serializer.is_valid():
        serializer.save()
        return APIResponse(code=0, msg='查询成功', data=serializer.data)
    else:
        # print(serializer.errors)
        utils.log_error(request, '输入课程修改参数错误')

    return APIResponse(code=1, msg='更新失败')


# 删除课程
@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    try:
        ids = request.GET.get('ids')
        ids_arr = ids.split(',')
        Lesson.objects.filter(id__in=ids_arr).delete()
    except Lesson.DoesNotExist:
        return APIResponse(code=1, msg='课程不存在')
    return APIResponse(code=0, msg='删除成功')
