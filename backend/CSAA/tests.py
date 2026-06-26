import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from CSAA.models import Child, CourseAdjustment, DailyStudentAdjustment, Lesson, Order, PermanentCourseChange, StudentComment, StudentLessonNote, Tag, Term, Thing, Time, TrialRequest, User
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

    def test_student_comment_is_saved_and_returned_in_student_detail(self):
        admin = User.objects.create(
            username='comment_admin',
            nickname='Comment Admin',
            password='unused',
            role='0',
            admin_token='comment-admin-token',
        )

        create_response = self.client.post(
            '/CSAA/admin/student/comment/create',
            {
                'student_id': self.current_child.id,
                'content': 'Participates well and needs more keyboard practice.',
            },
            HTTP_ADMINTOKEN='comment-admin-token',
        )

        self.assertEqual(create_response.json()['code'], 0)
        self.assertEqual(StudentComment.objects.count(), 1)

        detail_response = self.client.get(
            '/CSAA/admin/student/detail',
            {'id': self.current_child.id},
            HTTP_ADMINTOKEN='comment-admin-token',
        )
        self.assertEqual(detail_response.json()['code'], 0)
        self.assertEqual(detail_response.json()['data']['parent_username'], 'date_filter_parent')
        self.assertEqual(
            detail_response.json()['data']['comments'][0]['content'],
            'Participates well and needs more keyboard practice.',
        )
        self.assertEqual(
            detail_response.json()['data']['comments'][0]['created_by'],
            admin.nickname,
        )

    def test_student_comments_can_be_imported_from_csv_text(self):
        User.objects.create(
            username='bulk_comment_admin',
            nickname='Bulk Comment Admin',
            password='unused',
            role='0',
            admin_token='bulk-comment-admin-token',
        )
        csv_text = (
            'student_name,parent_username,comment,created_time\n'
            'Current Student,date_filter_parent,"Focused well in the old robotics class",2026-05-18 16:30\n'
            'Missing Student,date_filter_parent,"Should not import",2026-05-19 16:30\n'
        )

        response = self.client.post(
            '/CSAA/admin/student/comment/import',
            {'text': csv_text},
            HTTP_ADMINTOKEN='bulk-comment-admin-token',
        )

        payload = response.json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(payload['data']['created_count'], 1)
        self.assertEqual(payload['data']['error_count'], 1)
        self.assertEqual(StudentComment.objects.count(), 1)

        comment = StudentComment.objects.get()
        self.assertEqual(comment.student, self.current_child)
        self.assertEqual(comment.content, 'Focused well in the old robotics class')
        self.assertEqual(comment.created_time.strftime('%Y-%m-%d %H:%M'), '2026-05-18 16:30')

    def test_student_comments_can_be_imported_from_csv_file(self):
        User.objects.create(
            username='file_comment_admin',
            nickname='File Comment Admin',
            password='unused',
            role='0',
            admin_token='file-comment-admin-token',
        )
        csv_file = SimpleUploadedFile(
            'comments.csv',
            (
                'student_id,comment,created_time\n'
                f'{self.current_child.id},"Uploaded CSV comment",2026-05-20 17:45\n'
            ).encode('utf-8-sig'),
            content_type='text/csv',
        )

        response = self.client.post(
            '/CSAA/admin/student/comment/import',
            {'file': csv_file},
            HTTP_ADMINTOKEN='file-comment-admin-token',
        )

        payload = response.json()
        self.assertEqual(payload['code'], 0)
        self.assertEqual(payload['data']['created_count'], 1)
        self.assertEqual(StudentComment.objects.count(), 1)
        comment = StudentComment.objects.get()
        self.assertEqual(comment.student, self.current_child)
        self.assertEqual(comment.content, 'Uploaded CSV comment')

    def test_daily_move_does_not_change_order_class(self):
        admin = User.objects.create(
            username='move_admin',
            password='unused',
            role='0',
            admin_token='move-admin-token',
        )
        target_room = Tag.objects.create(title='Move Target Room', seat=4)
        target_thing = Thing.objects.create(
            title='Move Target Class',
            tag=target_room,
            time=self.thing.time,
            day='Sun',
            status='0',
        )
        target_lesson = Lesson.objects.create(thing=target_thing)
        order = Order.objects.get(order_number='DATEFILTER001')

        response = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {
                'lesson_date': '2026-06-28',
                'actions': json.dumps([{
                    'type': 'move',
                    'student_id': self.current_child.id,
                    'source_lesson_id': self.lesson.id,
                    'target_lesson_id': target_lesson.id,
                }]),
            },
            HTTP_ADMINTOKEN='move-admin-token',
        )

        self.assertEqual(response.json()['code'], 0)
        order.refresh_from_db()
        self.assertEqual(order.thing_id, self.thing.id)
        self.assertTrue(DailyStudentAdjustment.objects.filter(
            student=self.current_child,
            target_lesson=target_lesson,
            status='active',
        ).exists())

    def test_sick_leave_lesson_count_is_restored_on_revert(self):
        admin = User.objects.create(
            username='leave_admin',
            password='unused',
            role='0',
            admin_token='leave-admin-token',
        )
        order = Order.objects.get(order_number='DATEFILTER001')
        order.num = 10
        order.save(update_fields=['num'])

        response = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {
                'lesson_date': '2026-06-28',
                'actions': json.dumps([{
                    'type': 'sick_leave',
                    'student_id': self.current_child.id,
                    'source_lesson_id': self.lesson.id,
                    'deduct_lesson': True,
                    'reason': 'Flu',
                }]),
            },
            HTTP_ADMINTOKEN='leave-admin-token',
        )
        self.assertEqual(response.json()['code'], 0)
        record_id = response.json()['data'][0]['id']
        order.refresh_from_db()
        self.assertEqual(order.num, 9)

        revert_response = self.client.post(
            '/CSAA/admin/dailyAdjustment/revert',
            {'id': record_id},
            HTTP_ADMINTOKEN='leave-admin-token',
        )
        self.assertEqual(revert_response.json()['code'], 0)
        order.refresh_from_db()
        self.assertEqual(order.num, 10)

    def test_permanent_course_change_splits_enrollment_and_can_revert(self):
        admin = User.objects.create(
            username='permanent_admin',
            password='unused',
            role='0',
            admin_token='permanent-admin-token',
        )
        target_room = Tag.objects.create(title='Permanent Target Room', seat=4)
        target_time = Time.objects.create(time='18:00-19:00')
        target_thing = Thing.objects.create(
            title='Permanent Target Class',
            tag=target_room,
            time=target_time,
            day='Wed',
            status='0',
        )
        target_lesson = Lesson.objects.create(thing=target_thing)
        source_order = Order.objects.get(order_number='DATEFILTER001')
        source_order.num = 7
        source_order.save(update_fields=['num'])

        response = self.client.post(
            '/CSAA/admin/permanentCourseChange/create',
            {
                'student_id': self.current_child.id,
                'source_lesson_id': self.lesson.id,
                'target_lesson_id': target_lesson.id,
                'effective_date': '2026-07-01',
                'reason': 'Permanent schedule change',
            },
            HTTP_ADMINTOKEN='permanent-admin-token',
        )

        self.assertEqual(response.json()['code'], 0)
        source_order.refresh_from_db()
        record = PermanentCourseChange.objects.get()
        self.assertEqual(source_order.return_time.date(), datetime.date(2026, 6, 30))
        self.assertEqual(source_order.num, 0)
        self.assertEqual(record.target_order.thing_id, target_thing.id)
        self.assertEqual(record.target_order.num, 7)
        self.assertEqual(record.target_order.expect_time.date(), datetime.date(2026, 7, 1))

        revert_response = self.client.post(
            '/CSAA/admin/permanentCourseChange/revert',
            {'id': record.id},
            HTTP_ADMINTOKEN='permanent-admin-token',
        )
        self.assertEqual(revert_response.json()['code'], 0)
        source_order.refresh_from_db()
        record.target_order.refresh_from_db()
        self.assertEqual(source_order.return_time.date(), datetime.date(2026, 8, 31))
        self.assertEqual(source_order.num, 7)
        self.assertEqual(record.target_order.status, 7)

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

    def test_student_detail_lists_all_trial_package_categories(self):
        coding_time = Time.objects.create(time='17:00-18:00')
        math_time = Time.objects.create(time='18:00-19:00')
        coding = Thing.objects.create(
            title='Trial Coding', tag=self.thing.tag, time=coding_time, day='Tue', status='0'
        )
        math = Thing.objects.create(
            title='Trial Math', tag=self.thing.tag, time=math_time, day='Wed', status='0'
        )
        package_order = Order.objects.create(
            order_number='TRIALPACKAGE001', user=self.parent, child=self.current_child,
            thing=self.thing, num=3, amount='98', status=6, remark='Trial Package',
        )
        TrialRequest.objects.create(
            parent=self.parent, child=self.current_child, package_order=package_order,
            robotics_class=self.thing, coding_class=coding, math_class=math, status='scheduled',
        )

        data = AdminStudentSerializer(self.current_child).data

        self.assertEqual(len(data['trial_packages']), 1)
        self.assertEqual(data['trial_packages'][0]['status'], 'scheduled')
        self.assertEqual(
            [course['category'] for course in data['trial_packages'][0]['courses']],
            ['Robotics', 'Coding', 'Math'],
        )
        self.assertTrue(all(course['configured'] for course in data['trial_packages'][0]['courses']))

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
