from django.db.models import Count
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import Course, Thing
from CSAA.serializers import CourseSerializer


@api_view(['GET'])
def list_api(request):
    keyword = str(request.GET.get('keyword') or '').strip()
    courses = Course.objects.all()
    if keyword:
        courses = courses.filter(title__icontains=keyword)
    data = []
    for course in courses.order_by('title'):
        item = CourseSerializer(course).data
        item['instance_count'] = Thing.objects.filter(title__iexact=course.title).count()
        data.append(item)
    return APIResponse(code=0, msg='OK', data=data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def create(request):
    title = str(request.data.get('title') or '').strip()
    if not title:
        return APIResponse(code=1, msg='Course name is required')
    if Course.objects.filter(title__iexact=title).exists():
        return APIResponse(code=1, msg='Course name already exists')
    active = request.data.get('active', True) not in ['false', False, '0', 0]
    course = Course.objects.create(title=title, active=active)
    return APIResponse(code=0, msg='Course created', data=CourseSerializer(course).data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def update(request):
    try:
        course = Course.objects.get(pk=request.GET.get('id'))
    except Course.DoesNotExist:
        return APIResponse(code=1, msg='Course does not exist')
    title = str(request.data.get('title') or '').strip()
    if not title:
        return APIResponse(code=1, msg='Course name is required')
    if Course.objects.filter(title__iexact=title).exclude(pk=course.pk).exists():
        return APIResponse(code=1, msg='Course name already exists')
    old_title = course.title
    course.title = title
    course.active = request.data.get('active', course.active) not in ['false', False, '0', 0]
    course.save()
    if old_title.lower() != title.lower():
        Thing.objects.filter(title__iexact=old_title).update(title=title)
    return APIResponse(code=0, msg='Course updated', data=CourseSerializer(course).data)


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def delete(request):
    ids = [value for value in str(request.GET.get('ids') or '').split(',') if value]
    courses = list(Course.objects.filter(id__in=ids))
    if not courses:
        return APIResponse(code=1, msg='Course does not exist')
    linked = [course.title for course in courses if Thing.objects.filter(title__iexact=course.title).exists()]
    if linked:
        return APIResponse(code=1, msg=f'Cannot delete a course with class instances: {", ".join(linked)}')
    Course.objects.filter(id__in=ids).delete()
    return APIResponse(code=0, msg='Course deleted')
