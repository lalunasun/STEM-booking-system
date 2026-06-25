from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Child, Lesson, StudentLessonNote, User
from CSAA.serializers import StudentLessonNoteSerializer


@api_view(['GET', 'POST'])
@authentication_classes([AdminTokenAuthtication])
def list_or_save(request):
    if request.method == 'GET':
        lesson_date = parse_date(request.GET.get('date', ''))
        if not lesson_date:
            return APIResponse(code=1, msg='A valid lesson date is required')

        notes = StudentLessonNote.objects.filter(
            lesson_date=lesson_date,
        ).select_related('student', 'lesson', 'lesson__thing', 'created_by')
        return APIResponse(
            code=0,
            msg='Query successful',
            data=StudentLessonNoteSerializer(notes, many=True).data,
        )

    lesson_date = parse_date(str(request.data.get('lesson_date', '')))
    student_id = request.data.get('student_id')
    lesson_id = request.data.get('lesson_id')
    note_text = str(request.data.get('note', '')).strip()
    if not lesson_date or not student_id or not lesson_id:
        return APIResponse(code=1, msg='Student, lesson, and lesson date are required')

    try:
        student = Child.objects.get(id=student_id)
        lesson = Lesson.objects.get(id=lesson_id)
    except (Child.DoesNotExist, Lesson.DoesNotExist):
        return APIResponse(code=1, msg='Student or lesson does not exist')

    admin = None
    admin_id = request.data.get('admin_user_id')
    if admin_id:
        admin = User.objects.filter(id=admin_id, role='0').first()

    record, _ = StudentLessonNote.objects.update_or_create(
        student=student,
        lesson=lesson,
        lesson_date=lesson_date,
        defaults={'note': note_text, 'created_by': admin},
    )
    return APIResponse(
        code=0,
        msg='Note saved',
        data=StudentLessonNoteSerializer(record).data,
    )
