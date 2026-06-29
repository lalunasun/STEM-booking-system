from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminOrTeacherTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, Lesson, StudentAttendance, StudentComment


@api_view(['POST'])
@authentication_classes([AdminOrTeacherTokenAuthtication])
def mark_absent(request):
    lesson_date = parse_date(str(request.data.get('lesson_date', '')))
    student_id = request.data.get('student_id')
    lesson_id = request.data.get('lesson_id')
    is_absent = str(request.data.get('is_absent', 'true')).lower() in ('true', '1', 'yes')

    if not lesson_date or not student_id or not lesson_id:
        return APIResponse(code=1, msg='Student, lesson, and lesson date are required')

    try:
        student = Child.objects.get(pk=student_id)
        lesson = Lesson.objects.get(pk=lesson_id)
    except (Child.DoesNotExist, Lesson.DoesNotExist, TypeError, ValueError):
        return APIResponse(code=1, msg='Student or lesson does not exist')

    if is_absent:
        if StudentComment.objects.filter(
            student=student,
            lesson=lesson,
            lesson_date=lesson_date,
        ).exists():
            return APIResponse(code=1, msg='Comment already exists for this student and class')

        record, _ = StudentAttendance.objects.update_or_create(
            student=student,
            lesson=lesson,
            lesson_date=lesson_date,
            defaults={
                'is_absent': True,
                'marked_by': getattr(request, 'user', None),
            },
        )
        return APIResponse(
            code=0,
            msg='Attendance updated',
            data={
                'id': record.id,
                'student': student.id,
                'lesson': lesson.id,
                'lesson_date': lesson_date.strftime('%Y-%m-%d'),
                'is_absent': record.is_absent,
            },
        )

    StudentAttendance.objects.filter(
        student=student,
        lesson=lesson,
        lesson_date=lesson_date,
    ).delete()
    return APIResponse(
        code=0,
        msg='Attendance updated',
        data={
            'student': student.id,
            'lesson': lesson.id,
            'lesson_date': lesson_date.strftime('%Y-%m-%d'),
            'is_absent': False,
        },
    )
