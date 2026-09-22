import datetime
from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from CSAA.models import Child, Course, Lesson, Order, RoomCoursePermission, Tag, Term, Thing, Time, User


class RoomPermissionTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username='rule-admin', role='0', admin_token='rule-test-token')
        self.headers = {'HTTP_ADMINTOKEN': self.admin.admin_token}
        self.term = Term.objects.create(title='Fall', expect_time=datetime.datetime(2026, 9, 1),
                                        return_time=datetime.datetime(2026, 12, 31))
        self.room = Tag.objects.create(title='Room 3', seat=2)
        self.time = Time.objects.create(time='16:00-17:00')
        self.spike = Course.objects.create(title='Spike')
        self.scratch = Course.objects.create(title='Scratch')
        self.thing = Thing.objects.create(title='Spike', tag=self.room, time=self.time, day='Tue')

    def save_rule(self, courses):
        return self.client.post('/CSAA/admin/tag/coursePermissions', {
            'room': self.room.id, 'term': self.term.id,
            'course_ids': [course.id for course in courses], 'note': 'School confirmed',
        }, content_type='application/json', **self.headers)

    def slots(self):
        return self.client.get('/CSAA/admin/student/availableSlots', {
            'term': self.term.id, 'course': 'Scratch', 'day': 'Tue', 'time': self.time.id,
        }, **self.headers).json()['data']

    def enroll(self, name='New student'):
        return self.client.post('/CSAA/admin/student/quickCreate', {
            'name': name, 'term': self.term.id, 'course': 'Scratch',
            'room': self.room.id, 'day': 'Tue', 'time': self.time.id,
        }, **self.headers).json()

    def test_preview_does_not_change_rules_and_requires_admin(self):
        url = '/CSAA/admin/tag/coursePermissions'
        params = {'room': self.room.id, 'term': self.term.id}
        self.assertEqual(self.client.get(url, params).status_code, 403)
        result = self.client.get(url, params, **self.headers).json()['data']
        self.assertFalse(result['configured'])
        self.assertEqual(result['suggested_course_ids'], [self.spike.id])
        self.assertFalse(RoomCoursePermission.objects.exists())

    def test_rule_recommends_without_creating_and_materializes_on_enrollment(self):
        self.assertEqual(self.slots(), [])
        self.assertEqual(self.save_rule([self.spike, self.scratch]).json()['code'], 0)
        slot = self.slots()[0]
        self.assertTrue(slot['new_class'])
        self.assertEqual(slot['available_seats'], 2)
        self.assertFalse(Thing.objects.filter(title='Scratch').exists())
        self.assertEqual(self.enroll()['code'], 0)
        thing = Thing.objects.get(title='Scratch')
        self.assertTrue(Lesson.objects.filter(thing=thing).exists())
        self.assertEqual(Order.objects.get(child__name='New student').thing, thing)
        self.assertEqual(self.enroll('Second student')['code'], 0)
        self.assertEqual(Thing.objects.filter(title='Scratch').count(), 1)
        self.assertEqual(self.enroll('Third student')['code'], 1)
        self.assertFalse(Child.objects.filter(name='Third student').exists())

    def test_rule_removal_blocks_stale_selection_but_preserves_enrollment(self):
        self.save_rule([self.scratch])
        self.assertEqual(self.enroll()['code'], 0)
        thing = Thing.objects.get(title='Scratch')
        self.save_rule([])
        self.assertEqual(self.slots(), [])
        self.assertEqual(self.enroll('Blocked')['code'], 1)
        result = self.client.post('/CSAA/admin/student/quickCreate', {
            'name': 'Stale selection', 'term': self.term.id, 'thing': thing.id,
        }, **self.headers).json()
        self.assertEqual(result['code'], 1)
        self.assertEqual(Order.objects.count(), 1)
        self.assertTrue(Thing.objects.filter(pk=thing.pk).exists())

    def test_rules_are_term_specific_and_invalid_save_is_atomic(self):
        self.save_rule([self.scratch])
        response = self.client.post('/CSAA/admin/tag/coursePermissions', {
            'room': self.room.id, 'term': self.term.id, 'course_ids': [999999],
        }, content_type='application/json', **self.headers)
        self.assertEqual(response.json()['code'], 1)
        self.assertTrue(RoomCoursePermission.objects.get().courses.filter(pk=self.scratch.pk).exists())
        other = Term.objects.create(title='Spring')
        result = self.client.get('/CSAA/admin/student/availableSlots', {
            'term': other.id, 'course': 'Scratch',
        }, **self.headers).json()
        self.assertEqual(result['data'], [])

    def test_capacity_includes_other_courses_overlapping_times_and_terms(self):
        full_year = Term.objects.create(title='Full year', expect_time=self.term.expect_time,
                                        return_time=datetime.datetime(2027, 6, 30))
        self.thing.time = Time.objects.create(time='16:30-17:30')
        self.thing.save()
        Thing.objects.create(title='Roblox', tag=self.room, time=self.time, day='Tue')
        for number in range(2):
            child = Child.objects.create(name=f'Existing {number}')
            Order.objects.create(child=child, thing=self.thing, term=full_year, status=6,
                                 expect_time=full_year.expect_time, return_time=full_year.return_time)
        self.save_rule([self.scratch])
        self.assertEqual(self.slots()[0]['available_seats'], 0)
        self.assertEqual(self.enroll()['code'], 1)
        self.assertFalse(Thing.objects.filter(title='Scratch').exists())

    def test_no_recommendation_for_closed_class_or_unknown_slot(self):
        self.save_rule([self.scratch])
        Thing.objects.create(title='Scratch', tag=self.room, time=self.time, day='Tue', status='1')
        self.assertEqual(self.slots(), [])
        self.assertEqual(self.enroll()['code'], 1)
        self.assertEqual(Order.objects.count(), 0)

    def test_saved_student_is_in_schedule(self):
        self.save_rule([self.scratch])
        self.enroll()
        result = self.client.get('/CSAA/admin/lesson/list', {'date': '2026-09-08'}).json()
        lesson = next(item for item in result['data'] if item['class_name'] == 'Scratch')
        self.assertEqual(lesson['scheduled_students'][0]['name'], 'New student')

    def test_initialize_current_permissions_previews_and_merges(self):
        args = ['--as-of', '2026-09-08', '--allow', 'Room 3=Scratch']
        call_command('initialize_current_room_permissions', *args, stdout=StringIO())
        self.assertFalse(RoomCoursePermission.objects.exists())
        call_command('initialize_current_room_permissions', *args, '--apply', stdout=StringIO())
        rule = RoomCoursePermission.objects.get(room=self.room, term=self.term)
        self.assertEqual(set(rule.courses.values_list('title', flat=True)), {'Spike', 'Scratch'})
        self.assertEqual(Thing.objects.count(), 1)
        call_command('initialize_current_room_permissions', *args, '--apply', stdout=StringIO())
        self.assertEqual(RoomCoursePermission.objects.count(), 1)

    def test_current_allowed_class_instance_cannot_be_deleted(self):
        self.save_rule([self.spike, self.scratch])

        response = self.client.post(
            f'/CSAA/admin/thing/delete?ids={self.thing.id}',
            **self.headers,
        ).json()

        self.assertEqual(response['code'], 1)
        self.assertIn('Room course permissions', response['msg'])
        self.assertTrue(Thing.objects.filter(pk=self.thing.pk).exists())

    def test_class_instance_can_be_deleted_after_permission_is_removed(self):
        self.save_rule([self.spike])
        self.save_rule([self.scratch])

        response = self.client.post(
            f'/CSAA/admin/thing/delete?ids={self.thing.id}',
            **self.headers,
        ).json()

        self.assertEqual(response['code'], 0)
        self.assertFalse(Thing.objects.filter(pk=self.thing.pk).exists())
