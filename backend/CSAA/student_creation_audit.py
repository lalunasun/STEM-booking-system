import json

from CSAA.models import OpLog


STUDENT_CREATED_EVENT = 'student_created'


def record_student_created(student, source, actor=None):
    OpLog.objects.create(
        re_url=STUDENT_CREATED_EVENT,
        re_method='EVENT',
        re_content=json.dumps({
            'student_id': student.id,
            'source': source,
            'actor_id': actor.id if actor else None,
        }),
    )
