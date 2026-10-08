import datetime as dt

from django.test import TestCase

from CSAA.models import Child, Course, Lesson, Order, PermanentCourseChange, RoomCoursePermission, Tag, Term, Thing, Time, User
from CSAA.room_permissions import candidate_classes
from CSAA.serializers import AdminStudentSerializer, TimeSerializer
from CSAA.views.admin.daily_adjustment import _occupied_count
from CSAA.views.admin.student import _active_enrollment_count


class ScheduleRegressionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username='regression-admin', role='0', admin_token='regression-token')
        self.headers = {'HTTP_ADMINTOKEN': self.admin.admin_token}
        self.student = Child.objects.create(name='Regression Student')
        self.term = Term.objects.create(title='Regression Year', expect_time=dt.datetime(2026, 9, 8),
                                        return_time=dt.datetime(2027, 6, 27, 23, 59, 59))
        self.room = Tag.objects.create(title='Regression Room', seat=4)
        self.time = Time.objects.create(time='16:00-17:00')
        self.course, _ = Course.objects.get_or_create(title='Spike')
        self.source = Thing.objects.create(title='Spike', tag=self.room, time=self.time, day='Tue', status='0')
        self.source_lesson = Lesson.objects.create(thing=self.source)
        self.order = Order.objects.create(order_number='REGRESSION001', child=self.student, thing=self.source,
                                         term=self.term, status=6, num=20, expect_time=self.term.expect_time,
                                         return_time=self.term.return_time)
        self.target = Thing.objects.create(title='Spike', tag=self.room, day='Sat',
                                          time=Time.objects.create(time='9:00-10:00'), status='0')
        self.target_lesson = Lesson.objects.create(thing=self.target)

    def change(self, **overrides):
        payload = {
            'student_id': self.student.id, 'source_lesson_id': self.source_lesson.id,
            'source_date': '2026-10-06', 'effective_date': '2026-10-10',
            'target_lesson_id': self.target_lesson.id, 'reason': 'Confirmed with parent',
        }
        payload.update(overrides)
        return self.client.post('/CSAA/admin/permanentCourseChange/create', payload, **self.headers).json()

    def scheduled(self, date):
        response = self.client.get('/CSAA/admin/lesson/list', {'date': date}).json()
        return [row for row in response['data'] if any(
            child.get('student_id') == self.student.id for child in row.get('scheduled_students', [])
        )]

    def test_null_class_order_does_not_break_quick_add_or_existing_student_search(self):
        orphan = Order.objects.create(child=self.student, thing=None, term=self.term, status=6,
                                      expect_time=dt.datetime(2026, 6, 1), return_time=dt.datetime(2026, 9, 1))
        params = {'term': self.term.id, 'course': 'Spike', 'day': 'Sat', 'time': self.target.time_id}
        for student_id in (None, self.student.id):
            if student_id:
                params['student'] = student_id
            response = self.client.get('/CSAA/admin/student/availableSlots', params, **self.headers).json()
            self.assertEqual(response['code'], 0)
            self.assertEqual(response['data'][0]['available_seats'], 4)
        self.assertEqual(_active_enrollment_count(self.target, self.term, orders=[orphan]), 0)
        created = self.client.post('/CSAA/admin/student/quickCreate', {
            'name': 'Added Student', 'term': self.term.id, 'thing': self.target.id,
        }, **self.headers).json()
        self.assertEqual(created['code'], 0, created)
        self.assertTrue(Order.objects.filter(pk=orphan.pk).exists())

    def test_equivalent_times_are_one_candidate_and_share_room_capacity(self):
        padded = Time.objects.create(time='09:00-10:00')
        duplicate = Thing.objects.create(title='Spike', tag=self.room, time=padded, day='Sat', status='0')
        duplicate_lesson = Lesson.objects.create(thing=duplicate)
        for index, thing in enumerate([self.target, duplicate]):
            child = Child.objects.create(name=f'Time Regression {index}')
            Order.objects.create(child=child, thing=thing, term=self.term, status=6,
                                 expect_time=self.term.expect_time, return_time=self.term.return_time)
        for time_id in [self.target.time_id, padded.id]:
            candidates = candidate_classes(self.term, 'Spike', 'Sat', time_id)
            self.assertEqual(len(candidates), 1)
            self.assertEqual(_active_enrollment_count(candidates[0], self.term), 2)
        for lesson in [self.target_lesson, duplicate_lesson]:
            self.assertEqual(_occupied_count(lesson, dt.date(2026, 10, 10)), 2)

    def test_time_creation_normalizes_and_rejects_semantic_duplicates(self):
        duplicate = TimeSerializer(data={'time': '09:00-10:00'})
        self.assertFalse(duplicate.is_valid())
        valid = TimeSerializer(data={'time': '8:00-9:00'})
        self.assertTrue(valid.is_valid(), valid.errors)
        self.assertEqual(valid.save().time, '08:00-09:00')
        self.assertFalse(TimeSerializer(data={'time': '25:00-26:00'}).is_valid())

    def test_permanent_change_replaces_selected_old_occurrence_and_preserves_history(self):
        response = self.change()
        self.assertEqual(response['code'], 0, response)
        self.order.refresh_from_db()
        self.assertEqual(self.order.return_time.date(), dt.date(2026, 10, 4))
        self.assertEqual(len(self.scheduled('2026-09-29')), 1)
        self.assertEqual(self.scheduled('2026-10-06'), [])
        self.assertEqual(len(self.scheduled('2026-10-10')), 1)
        self.assertEqual(self.scheduled('2026-10-13'), [])
        self.assertEqual(len(self.scheduled('2026-10-17')), 1)
        context = {'as_of_date': dt.date(2026, 10, 3)}
        data = AdminStudentSerializer(self.student, context=context).data
        self.assertEqual(len(data['active_classes']), 1)
        self.assertIn('Sat', data['active_classes'][0])
        self.assertIn('From 2026-10-10', data['active_classes'][0])
        self.assertEqual(len(data['course_history']), 2)

    def test_future_week_change_keeps_current_week_class(self):
        response = self.change(effective_date='2026-10-17')
        self.assertEqual(response['code'], 0, response)
        self.order.refresh_from_db()
        self.assertEqual(self.order.return_time.date(), dt.date(2026, 10, 11))
        self.assertEqual(len(self.scheduled('2026-10-06')), 1)
        self.assertEqual(self.scheduled('2026-10-13'), [])
        self.assertEqual(len(self.scheduled('2026-10-17')), 1)

    def test_revert_restores_original_enrollment_after_explicit_cutoff(self):
        response = self.change()
        self.assertEqual(response['code'], 0)
        result = self.client.post('/CSAA/admin/permanentCourseChange/revert', {
            'id': response['data']['id'],
        }, **self.headers).json()
        self.assertEqual(result['code'], 0)
        self.order.refresh_from_db()
        self.assertEqual(self.order.return_time, self.term.return_time)
        self.assertEqual(self.order.num, 20)
        self.assertEqual(len(self.scheduled('2026-10-06')), 1)
        self.assertEqual(self.scheduled('2026-10-10'), [])

    def test_invalid_source_date_is_rejected_without_changes(self):
        for date in ['2026-10-07', '2026-02-30', '']:
            self.assertEqual(self.change(source_date=date)['code'], 1)
        self.order.refresh_from_db()
        self.assertEqual(self.order.return_time, self.term.return_time)
        self.assertFalse(PermanentCourseChange.objects.exists())

    def test_full_virtual_target_does_not_leave_empty_class_on_failure(self):
        other_course = Course.objects.create(title='Regression Coding')
        rule = RoomCoursePermission.objects.create(room=self.room, term=self.term)
        rule.courses.add(self.course, other_course)
        self.room.seat = 1
        self.room.save()
        Order.objects.create(child=Child.objects.create(name='Other Student'), thing=self.target,
                             term=self.term, status=6, expect_time=self.term.expect_time,
                             return_time=self.term.return_time)
        response = self.change(target_lesson_id='', target_room_id=self.room.id,
                               target_time_id=self.target.time_id, course=other_course.title)
        self.assertEqual(response['code'], 1)
        self.assertIn('full', response['msg'])
        self.assertFalse(Thing.objects.filter(title=other_course.title).exists())
        self.assertFalse(PermanentCourseChange.objects.exists())

    def test_closed_time_alias_does_not_generate_virtual_course(self):
        coding = Course.objects.create(title='Regression Coding')
        rule = RoomCoursePermission.objects.create(room=self.room, term=self.term)
        rule.courses.add(coding)
        padded = Time.objects.create(time='09:00-10:00')
        Thing.objects.create(title=coding.title, tag=self.room, time=padded, day='Sat', status='1')
        self.assertEqual(candidate_classes(self.term, coding.title, 'Sat', self.target.time_id), [])
