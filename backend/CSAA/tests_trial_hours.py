import datetime

from django.test import TestCase

from CSAA.models import Course, Lesson, RoomCoursePermission, Tag, Term, Thing, Time, User
from CSAA.views.admin.trial_booking import _flexible_start_times


class TrialBusinessHoursTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='trial-hours-admin', role='0', admin_token='trial-hours-token',
        )
        self.headers = {'HTTP_ADMINTOKEN': self.admin.admin_token}
        self.term = Term.objects.create(
            title='Trial Hours Term',
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2027, 6, 30, 23, 59, 59),
        )
        self.room = Tag.objects.create(title='Trial Hours Room', seat=6)
        creator = Course.objects.create(title='Creator')
        permission = RoomCoursePermission.objects.create(
            room=self.room, term=self.term, updated_by=self.admin,
        )
        permission.courses.add(creator)

    def options(self, date, mode='flexible'):
        return self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': date, 'mode': mode,
        }, **self.headers).json()

    def test_weekday_flexible_slots_end_at_closing_time(self):
        data = self.options('2026-10-06')['data']
        room_slots = [item for item in data if item['room_id'] == self.room.id]
        self.assertEqual(
            [(item['start'], item['end']) for item in room_slots],
            [
                ('16:00', '17:30'),
                ('16:30', '18:00'),
                ('17:00', '18:30'),
                ('17:30', '19:00'),
            ],
        )
        self.assertFalse(any(item['start'] == '18:00' for item in room_slots))

    def test_weekend_flexible_slots_include_half_hour_start(self):
        data = self.options('2026-10-10')['data']
        room_slots = [item for item in data if item['room_id'] == self.room.id]
        self.assertIn(('09:30', '11:00'), [
            (item['start'], item['end']) for item in room_slots
        ])
        self.assertEqual(room_slots[-1]['end'], '18:00')

    def test_existing_class_that_ends_after_closing_is_not_offered(self):
        late_time = Time.objects.create(time='18:00-19:00')
        Lesson.objects.create(thing=Thing.objects.create(
            title='Creator', tag=self.room, time=late_time, day='Tue', status='0',
        ))
        result = self.options('2026-10-06', mode='existing')
        self.assertEqual(result['code'], 0)
        self.assertEqual(result['data'], [])

    def test_server_rejects_a_late_flexible_start_even_if_posted_directly(self):
        self.assertNotIn(datetime.time(18, 0), _flexible_start_times(datetime.date(2026, 10, 6)))
        result = self.client.post('/CSAA/admin/trialBooking/create', {
            'student_name': 'Late Trial Student',
            'sessions': [
                {
                    'mode': 'flexible', 'subject': 'Robotics', 'date': '2026-10-06',
                    'room_id': self.room.id, 'start': '18:00',
                },
                {
                    'mode': 'flexible', 'subject': 'Robotics', 'date': '2026-10-10',
                    'room_id': self.room.id, 'start': '09:30',
                },
            ],
        }, content_type='application/json', **self.headers).json()
        self.assertEqual(result['code'], 1)
        self.assertIn('not available', result['msg'])
