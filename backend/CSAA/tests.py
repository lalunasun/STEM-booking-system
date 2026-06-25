import datetime

from django.test import TestCase

from CSAA.models import Child, CourseAdjustment, Lesson, Order, StudentLessonNote, Tag, Term, Thing, Time, User
from CSAA.serializers import AdminStudentSerializer, LessonDetailSerializer, LessonSerializer
from CSAA.views.admin.course_adjustment import _recommend_makeup_options


class LessonDetailDateFilterTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create(
            username='date_filter_parent',
            password='unused',
            role='1',
        )
        self.current_child = Child.objects.create(
            parent=self.parent,
            name='Current Student',
        )
        self.future_child = Child.objects.create(
            parent=self.parent,
            name='Future Student',
        )
        room = Tag.objects.create(title='Date Filter Room', seat=4)
        time = Time.objects.create(time='16:00-17:00')
        self.thing = Thing.objects.create(
            title='Date Filter Class',
            tag=room,
            time=time,
            day='Sun',
            status='0',
        )
        self.lesson = Lesson.objects.create(thing=self.thing)
        term = Term.objects.create(
            title='2026 Summer',
            expect_time=datetime.datetime(2026, 6, 1),
            return_time=datetime.datetime(2026, 8, 31),
        )
        Order.objects.create(
            order_number='DATEFILTER001',
            user=self.parent,
            child=self.current_child,
            thing=self.thing,
            term=term,
            expect_time=datetime.datetime(2026, 6, 1),
            return_time=datetime.datetime(2026, 8, 31),
            status=6,
        )
        Order.objects.create(
            order_number='DATEFILTER002',
            user=self.parent,
            child=self.future_child,
            thing=self.thing,
            term=term,
            expect_time=datetime.datetime(2026, 6, 28),
            return_time=datetime.datetime(2026, 8, 31),
            status=6,
        )

    def _student_names(self, class_date):
        data = LessonDetailSerializer(
            self.lesson,
            context={'class_date': class_date},
        ).data
        return data, [student['name'] for student in data['students']]

    def test_future_student_is_hidden_before_start_date(self):
        data, names = self._student_names(datetime.date(2026, 6, 24))

        self.assertEqual(names, ['Current Student'])
        self.assertEqual(data['students_num'], 1)

    def test_future_student_appears_on_start_date(self):
        data, names = self._student_names(datetime.date(2026, 6, 28))

        self.assertEqual(names, ['Current Student', 'Future Student'])
        self.assertEqual(data['students_num'], 2)

    def test_lesson_list_includes_room_identity_for_daily_grid(self):
        data = LessonSerializer(self.lesson).data

        self.assertEqual(data['room_id'], self.thing.tag_id)
        self.assertEqual(data['room_name'], 'Date Filter Room')

    def test_lesson_list_filters_to_requested_date(self):
        other_thing = Thing.objects.create(
            title='Other Day Class',
            tag=self.thing.tag,
            time=self.thing.time,
            day='Tue',
            status='0',
        )
        Lesson.objects.create(thing=other_thing)

        response = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-06-28'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {lesson['day'] for lesson in response.json()['data']},
            {'Sun'},
        )

    def test_student_lesson_note_is_saved_and_updated_for_one_date(self):
        admin = User.objects.create(
            username='note_admin',
            password='unused',
            role='0',
            admin_token='note-admin-token',
        )
        payload = {
            'student_id': self.current_child.id,
            'lesson_id': self.lesson.id,
            'lesson_date': '2026-06-28',
            'note': 'Needs extra setup time',
            'admin_user_id': admin.id,
        }

        response = self.client.post(
            '/CSAA/admin/studentLessonNote',
            payload,
            HTTP_ADMINTOKEN='note-admin-token',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)

        payload['note'] = 'Bring the project kit'
        update_response = self.client.post(
            '/CSAA/admin/studentLessonNote',
            payload,
            HTTP_ADMINTOKEN='note-admin-token',
        )
        self.assertEqual(update_response.json()['code'], 0)
        self.assertEqual(StudentLessonNote.objects.count(), 1)
        self.assertEqual(StudentLessonNote.objects.get().note, 'Bring the project kit')

        list_response = self.client.get(
            '/CSAA/admin/studentLessonNote',
            {'date': '2026-06-28'},
            HTTP_ADMINTOKEN='note-admin-token',
        )
        self.assertEqual(list_response.json()['data'][0]['student'], self.current_child.id)
        self.assertEqual(list_response.json()['data'][0]['lesson'], self.lesson.id)

    def test_lesson_detail_separates_absent_student_for_selected_date(self):
        current_order = Order.objects.get(order_number='DATEFILTER001')
        future_order = Order.objects.get(order_number='DATEFILTER002')
        CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=current_order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 6, 28),
            original_day='Sun',
            original_time='16:00-17:00',
            original_term=current_order.term,
            request_type='cancel_class',
            status='approved',
        )
        CourseAdjustment.objects.create(
            student=self.future_child,
            parent=self.parent,
            original_order=future_order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 7, 5),
            original_day='Sun',
            original_time='16:00-17:00',
            original_term=future_order.term,
            request_type='cancel_class',
            status='approved',
        )

        data, normal_names = self._student_names(datetime.date(2026, 6, 28))
        absent_names = [student['name'] for student in data['leave_students']]

        self.assertEqual(normal_names, ['Future Student'])
        self.assertEqual(absent_names, ['Current Student'])
        self.assertEqual(data['students_num'], 1)

    def test_lesson_detail_filters_makeup_students_by_selected_date(self):
        order = Order.objects.get(order_number='DATEFILTER001')
        candidate = self._candidate_class('Wed', '18:00-19:00', 'Makeup Room')
        target_lesson = Lesson.objects.create(thing=candidate)
        CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 6, 28),
            original_term=order.term,
            request_type='makeup_class',
            status='completed',
            selected_target_class=candidate,
            selected_target_date=datetime.date(2026, 7, 1),
        )
        CourseAdjustment.objects.create(
            student=self.future_child,
            parent=self.parent,
            original_order=Order.objects.get(order_number='DATEFILTER002'),
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 7, 5),
            original_term=order.term,
            request_type='makeup_class',
            status='completed',
            selected_target_class=candidate,
            selected_target_date=datetime.date(2026, 7, 8),
        )

        data = LessonDetailSerializer(
            target_lesson,
            context={'class_date': datetime.date(2026, 7, 1)},
        ).data

        self.assertEqual(
            [student['name'] for student in data['reschedule_students']],
            ['Current Student'],
        )

    def test_cancel_request_rejects_date_without_class(self):
        order = Order.objects.get(order_number='DATEFILTER001')

        response = self.client.post(
            '/CSAA/index/courseAdjustment/createCancel',
            {
                'order_id': order.id,
                'user_id': self.parent.id,
                'lesson_date': '2026-07-06',
                'parent_note': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 1)
        self.assertIn('No class is scheduled', response.json()['msg'])

    def test_duplicate_cancel_request_is_idempotent(self):
        order = Order.objects.get(order_number='DATEFILTER001')
        existing = CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 7, 5),
            original_day='Sun',
            original_time='16:00-17:00',
            original_term=order.term,
            request_type='cancel_class',
            status='pending',
        )

        response = self.client.post(
            '/CSAA/index/courseAdjustment/createCancel',
            {
                'order_id': order.id,
                'user_id': self.parent.id,
                'lesson_date': '2026-07-05',
                'parent_note': 'Repeated tap',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['data']['id'], existing.id)
        self.assertEqual(
            CourseAdjustment.objects.filter(
                original_order=order,
                original_lesson_date=datetime.date(2026, 7, 5),
                request_type='cancel_class',
            ).count(),
            1,
        )

    def test_student_detail_includes_multiple_absence_weeks(self):
        order = Order.objects.get(order_number='DATEFILTER001')
        term = order.term
        CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 7, 5),
            original_day='Sun',
            original_time='16:00-17:00',
            original_term=term,
            request_type='cancel_class',
            request_reason='Family trip week 1',
            status='pending',
        )
        CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 7, 12),
            original_day='Sun',
            original_time='16:00-17:00',
            original_term=term,
            request_type='cancel_class',
            request_reason='Family trip week 2',
            status='approved',
        )

        data = AdminStudentSerializer(self.current_child).data

        self.assertEqual(len(data['absence_records']), 2)
        self.assertEqual(
            [record['lesson_date'] for record in data['absence_records']],
            ['2026-07-12', '2026-07-05'],
        )
        self.assertEqual(
            [record['status'] for record in data['absence_records']],
            ['approved', 'pending'],
        )

    def test_parent_adjustment_list_is_filtered_by_child(self):
        order = Order.objects.get(order_number='DATEFILTER001')
        CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=order,
            original_class=self.thing,
            original_lesson_date=datetime.date(2026, 7, 5),
            original_day='Sun',
            original_time='16:00-17:00',
            original_term=order.term,
            request_type='cancel_class',
            status='pending',
            admin_note='Private admin note',
        )

        response = self.client.get(
            '/CSAA/index/courseAdjustment/list',
            {'parent_id': self.parent.id, 'child_id': self.current_child.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(len(response.json()['data']), 1)
        self.assertEqual(response.json()['data'][0]['student_name'], 'Current Student')
        self.assertNotIn('admin_note', response.json()['data'][0])

    def test_admin_user_search_accepts_nickname_username_phone_and_id(self):
        self.parent.nickname = 'Demo Parent Search'
        self.parent.mobile = '4165550999'
        self.parent.save()

        for keyword in ['Demo Parent Search', 'date_filter_parent', str(self.parent.id), '4165550999']:
            response = self.client.get('/CSAA/admin/user/list', {'keyword': keyword})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['code'], 0)
            self.assertEqual(
                [user['id'] for user in response.json()['data']],
                [self.parent.id],
            )

    def _makeup_adjustment(self, lesson_date=datetime.date(2026, 7, 5)):
        order = Order.objects.get(order_number='DATEFILTER001')
        return CourseAdjustment.objects.create(
            student=self.current_child,
            parent=self.parent,
            original_order=order,
            original_class=self.thing,
            original_lesson_date=lesson_date,
            original_day=self.thing.day,
            original_time=self.thing.time.time,
            original_term=order.term,
            request_type='makeup_class',
            status='makeup_available',
        )

    def _candidate_class(self, day, time_label, room_name):
        time = Time.objects.create(time=time_label)
        room = Tag.objects.create(title=room_name, seat=4)
        return Thing.objects.create(
            title=self.thing.title,
            tag=room,
            time=time,
            day=day,
            status='0',
        )

    def test_makeup_options_skip_student_schedule_conflicts(self):
        conflicting_class = self._candidate_class('Tue', '17:00-18:00', 'Conflict Room')
        available_class = self._candidate_class('Wed', '18:00-19:00', 'Available Room')
        Order.objects.create(
            order_number='DATEFILTER003',
            user=self.parent,
            child=self.current_child,
            thing=conflicting_class,
            term=Order.objects.get(order_number='DATEFILTER001').term,
            expect_time=datetime.datetime(2026, 6, 1),
            return_time=datetime.datetime(2026, 8, 31),
            status=6,
        )

        options = _recommend_makeup_options(self._makeup_adjustment(), limit=0)

        self.assertNotIn(conflicting_class.id, [option['class_id'] for option in options])
        self.assertIn(available_class.id, [option['class_id'] for option in options])

    def test_makeup_options_stay_in_original_term_without_future_enrollment(self):
        self._candidate_class('Wed', '18:00-19:00', 'Current Term Room')
        adjustment = self._makeup_adjustment()

        options = _recommend_makeup_options(adjustment, limit=0)

        self.assertTrue(options)
        self.assertTrue(all(option['date'] <= '2026-08-31' for option in options))
        self.assertEqual({option['term_title'] for option in options}, {'2026 Summer'})

    def test_makeup_options_include_future_term_only_after_enrollment(self):
        future_candidate = self._candidate_class('Wed', '18:00-19:00', 'Future Term Room')
        future_term = Term.objects.create(
            title='2026 Fall',
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2026, 10, 31),
        )
        Order.objects.create(
            order_number='DATEFILTER004',
            user=self.parent,
            child=self.current_child,
            thing=self.thing,
            term=future_term,
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2026, 10, 31),
            status=6,
        )

        options = _recommend_makeup_options(self._makeup_adjustment(), limit=0)
        future_options = [
            option
            for option in options
            if option['class_id'] == future_candidate.id and option['term_title'] == '2026 Fall'
        ]

        self.assertTrue(future_options)
        self.assertTrue(all('2026-09-01' <= option['date'] <= '2026-10-31' for option in future_options))
