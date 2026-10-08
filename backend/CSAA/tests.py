import datetime
import json

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from CSAA.models import AdminTrialSession, Child, Classification, Course, CourseAdjustment, DailyStudentAdjustment, Lesson, OpLog, Order, PermanentCourseChange, RoomCoursePermission, StudentAttendance, StudentComment, StudentLessonNote, Tag, Term, Thing, Time, TrialRequest, User
from CSAA.serializers import AdminStudentSerializer, LessonDetailSerializer, LessonSerializer
from CSAA.course_conflicts import selected_slot_conflict, student_slot_conflict_on_date
from CSAA.student_creation_audit import STUDENT_CREATED_EVENT
from CSAA.utils import md5value
from CSAA.views.admin.course_adjustment import _recommend_makeup_options
from CSAA.views.camp_checkin import _student_display_name


class StudentScheduleConflictTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create(username='conflict_parent', role='1')
        self.student = Child.objects.create(parent=self.parent, name='Conflict Student')
        self.term = Term.objects.create(
            title='Conflict Term',
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2026, 12, 31),
        )
        self.room_one = Tag.objects.create(title='Conflict Room 1', seat=4)
        self.room_two = Tag.objects.create(title='Conflict Room 2', seat=4)
        self.first_time = Time.objects.create(time='16:00-17:00')
        self.overlap_time = Time.objects.create(time='16:30-17:30')
        self.first = Thing.objects.create(
            title='Creator', day='Tue', time=self.first_time, tag=self.room_one, status='0',
        )
        self.overlap = Thing.objects.create(
            title='Scratch', day='Tue', time=self.overlap_time, tag=self.room_two, status='0',
        )

    def test_selected_courses_reject_different_time_records_that_overlap(self):
        conflict = selected_slot_conflict([self.first, self.overlap])
        self.assertIn('overlap', conflict)

    def test_student_cannot_hold_two_overlapping_courses_on_same_date(self):
        Order.objects.create(
            order_number='CONFLICT001', user=self.parent, child=self.student,
            thing=self.first, term=self.term, status=6,
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2026, 12, 31),
        )
        conflict = student_slot_conflict_on_date(
            self.student, self.overlap, datetime.date(2026, 9, 22),
        )
        self.assertIn('already has Creator', conflict)

    def test_admin_trial_blocks_overlapping_course_on_its_date_only(self):
        lesson = Lesson.objects.create(thing=self.first)
        AdminTrialSession.objects.create(
            student=self.student, lesson=lesson, session_index=1,
            session_date=datetime.date(2026, 9, 22),
            starts_at=datetime.time(16, 0), ends_at=datetime.time(17, 30),
        )
        self.assertIn(
            'administrator-booked trial',
            student_slot_conflict_on_date(
                self.student, self.overlap, datetime.date(2026, 9, 22),
            ),
        )
        self.assertIsNone(student_slot_conflict_on_date(
            self.student, self.overlap, datetime.date(2026, 9, 29),
        ))


class CampStudentDisplayNameTests(TestCase):
    def test_legacy_parent_based_child_name_is_marked_missing(self):
        parent = User.objects.create(
            username='parent_02',
            nickname='Parent 02',
            role='1',
        )
        child = Child.objects.create(
            parent=parent,
            name='parent_02_kid_2_age_7',
        )

        display_name, is_missing = _student_display_name(child)

        self.assertEqual(display_name, f'Student name missing (ID {child.id})')
        self.assertTrue(is_missing)

    def test_real_student_name_is_preserved(self):
        parent = User.objects.create(username='parent_07', role='1')
        child = Child.objects.create(parent=parent, name='Grace Demo')

        display_name, is_missing = _student_display_name(child)

        self.assertEqual(display_name, 'Grace Demo')
        self.assertFalse(is_missing)


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
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual([item['thing'] for item in response.json()['data']], [self.thing.id])
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

    def test_teacher_can_login_and_write_student_lesson_note(self):
        teacher = User.objects.create(
            username='teacher_login',
            password=md5value('teacherpass'),
            role='2',
        )

        login_response = self.client.post(
            '/CSAA/admin/adminLogin',
            {'username': 'teacher_login', 'password': 'teacherpass'},
        )
        self.assertEqual(login_response.json()['code'], 0)
        self.assertEqual(login_response.json()['data']['role'], '2')

        token = login_response.json()['data']['admin_token']
        note_response = self.client.post(
            '/CSAA/admin/studentLessonNote',
            {
                'student_id': self.current_child.id,
                'lesson_id': self.lesson.id,
                'lesson_date': '2026-06-28',
                'note': 'Teacher note from class.',
                'admin_user_id': teacher.id,
            },
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(note_response.json()['code'], 0)
        self.assertEqual(StudentLessonNote.objects.get().created_by, teacher)

        comment_response = self.client.post(
            '/CSAA/admin/student/comment/create',
            {
                'student_id': self.current_child.id,
                'lesson_id': self.lesson.id,
                'lesson_date': '2026-06-28',
                'content': 'Teacher comment from lesson page.',
            },
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(comment_response.json()['code'], 0)
        comment = StudentComment.objects.get()
        self.assertEqual(comment.created_by, teacher)
        self.assertEqual(comment.lesson, self.lesson)
        self.assertEqual(comment.lesson_date, datetime.date(2026, 6, 28))

        schedule_response = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-06-28'},
        )
        students = schedule_response.json()['data'][0]['scheduled_students']
        comment_flags = {student['name']: student['comment_done'] for student in students}
        self.assertTrue(comment_flags['Current Student'])
        self.assertFalse(comment_flags['Future Student'])

        done_absent_response = self.client.post(
            '/CSAA/admin/studentAttendance/markAbsent',
            {
                'student_id': self.current_child.id,
                'lesson_id': self.lesson.id,
                'lesson_date': '2026-06-28',
                'is_absent': 'true',
            },
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(done_absent_response.json()['code'], 1)

        absent_response = self.client.post(
            '/CSAA/admin/studentAttendance/markAbsent',
            {
                'student_id': self.future_child.id,
                'lesson_id': self.lesson.id,
                'lesson_date': '2026-06-28',
                'is_absent': 'true',
            },
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(absent_response.json()['code'], 0)
        self.assertTrue(StudentAttendance.objects.filter(
            student=self.future_child,
            lesson=self.lesson,
            lesson_date=datetime.date(2026, 6, 28),
            is_absent=True,
        ).exists())

        schedule_response = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-06-28'},
        )
        students = schedule_response.json()['data'][0]['scheduled_students']
        absent_flags = {student['name']: student['absent_marked'] for student in students}
        self.assertFalse(absent_flags['Current Student'])
        self.assertTrue(absent_flags['Future Student'])

        clear_absent_response = self.client.post(
            '/CSAA/admin/studentAttendance/markAbsent',
            {
                'student_id': self.future_child.id,
                'lesson_id': self.lesson.id,
                'lesson_date': '2026-06-28',
                'is_absent': 'false',
            },
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(clear_absent_response.json()['code'], 0)
        self.assertFalse(StudentAttendance.objects.filter(
            student=self.future_child,
            lesson=self.lesson,
            lesson_date=datetime.date(2026, 6, 28),
        ).exists())

        list_response = self.client.get(
            '/CSAA/admin/student/list',
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(list_response.json()['code'], 0)
        self.assertIn('Current Student', [item['name'] for item in list_response.json()['data']])

        detail_response = self.client.get(
            '/CSAA/admin/student/detail',
            {'id': self.current_child.id},
            HTTP_ADMINTOKEN=token,
        )
        self.assertEqual(detail_response.json()['code'], 0)
        self.assertEqual(detail_response.json()['data']['name'], 'Current Student')

    def test_teacher_token_cannot_call_admin_only_daily_adjustment(self):
        teacher = User.objects.create(
            username='teacher_limited',
            password='unused',
            role='2',
            admin_token='teacher-limited-token',
        )

        response = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {'lesson_date': '2026-06-28', 'actions': json.dumps([])},
            HTTP_ADMINTOKEN=teacher.admin_token,
        )

        self.assertEqual(response.status_code, 403)

        create_response = self.client.post(
            '/CSAA/admin/student/create',
            {'name': 'Blocked Student', 'parent': self.parent.id},
            HTTP_ADMINTOKEN=teacher.admin_token,
        )
        self.assertEqual(create_response.status_code, 403)

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

    def test_daily_move_can_use_a_different_lesson_date(self):
        admin = User.objects.create(
            username='cross_date_move_admin',
            password='unused',
            role='0',
            admin_token='cross-date-move-admin-token',
        )
        target_room = Tag.objects.create(title='Cross Date Target Room', seat=4)
        target_time = Time.objects.create(time='17:00-18:00')
        target_thing = Thing.objects.create(
            title='Cross Date Target Class',
            tag=target_room,
            time=target_time,
            day='Sun',
            status='0',
        )
        target_lesson = Lesson.objects.create(thing=target_thing)

        response = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {
                'lesson_date': '2026-06-28',
                'actions': json.dumps([{
                    'type': 'move',
                    'student_id': self.current_child.id,
                    'source_lesson_id': self.lesson.id,
                    'source_lesson_date': '2026-06-28',
                    'target_lesson_id': target_lesson.id,
                    'target_lesson_date': '2026-07-05',
                }]),
            },
            HTTP_ADMINTOKEN='cross-date-move-admin-token',
        )

        self.assertEqual(response.json()['code'], 0)
        record = DailyStudentAdjustment.objects.get(student=self.current_child)
        self.assertEqual(record.lesson_date.isoformat(), '2026-06-28')
        self.assertEqual(record.target_lesson_date.isoformat(), '2026-07-05')

        target_schedule = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-07-05'},
            HTTP_ADMINTOKEN='cross-date-move-admin-token',
        ).json()
        target_item = next(item for item in target_schedule['data'] if item['id'] == target_lesson.id)
        self.assertEqual(target_item['moved_students'][0]['student_id'], self.current_child.id)

        source_schedule = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-06-28'},
            HTTP_ADMINTOKEN='cross-date-move-admin-token',
        ).json()
        source_item = next(item for item in source_schedule['data'] if item['id'] == self.lesson.id)
        self.assertFalse(any(
            student['student_id'] == self.current_child.id
            for student in source_item['scheduled_students']
        ))

        revert_response = self.client.post(
            '/CSAA/admin/dailyAdjustment/revert',
            {'id': record.id},
            HTTP_ADMINTOKEN='cross-date-move-admin-token',
        )
        self.assertEqual(revert_response.json()['code'], 0)

    def test_cross_date_move_rejects_second_course_at_same_time(self):
        admin = User.objects.create(
            username='conflicting_move_admin', role='0', admin_token='conflicting-move-token',
        )
        target_room = Tag.objects.create(title='Conflicting Move Room', seat=4)
        target_thing = Thing.objects.create(
            title='Conflicting Move Class', tag=target_room, time=self.thing.time,
            day='Sun', status='0',
        )
        target_lesson = Lesson.objects.create(thing=target_thing)
        response = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {
                'lesson_date': '2026-06-28',
                'actions': json.dumps([{
                    'type': 'move', 'student_id': self.current_child.id,
                    'source_lesson_id': self.lesson.id,
                    'source_lesson_date': '2026-06-28',
                    'target_lesson_id': target_lesson.id,
                    'target_lesson_date': '2026-07-05',
                }]),
            },
            HTTP_ADMINTOKEN=admin.admin_token,
        ).json()
        self.assertNotEqual(response['code'], 0)
        self.assertIn('already has', response['msg'])
        self.assertFalse(DailyStudentAdjustment.objects.exists())

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

        schedule = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-06-28'},
            HTTP_ADMINTOKEN='leave-admin-token',
        ).json()
        lesson_data = next(item for item in schedule['data'] if item['id'] == self.lesson.id)
        self.assertNotIn(self.current_child.id, [
            student['student_id'] for student in lesson_data['scheduled_students']
        ])
        self.assertEqual(lesson_data['sick_leave_students'][0]['student_id'], self.current_child.id)

        revert_response = self.client.post(
            '/CSAA/admin/dailyAdjustment/revert',
            {'id': record_id},
            HTTP_ADMINTOKEN='leave-admin-token',
        )
        self.assertEqual(revert_response.json()['code'], 0)
        order.refresh_from_db()
        self.assertEqual(order.num, 10)

        restored_schedule = self.client.get(
            '/CSAA/admin/lesson/list',
            {'date': '2026-06-28'},
            HTTP_ADMINTOKEN='leave-admin-token',
        ).json()
        restored_lesson = next(item for item in restored_schedule['data'] if item['id'] == self.lesson.id)
        self.assertIn(self.current_child.id, [
            student['student_id'] for student in restored_lesson['scheduled_students']
        ])
        self.assertEqual(restored_lesson['sick_leave_students'], [])

    def test_revert_targets_one_saved_adjustment(self):
        User.objects.create(
            username='targeted_revert_admin',
            password='unused',
            role='0',
            admin_token='targeted-revert-token',
        )
        first = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {
                'lesson_date': '2026-06-28',
                'actions': json.dumps([{
                    'type': 'sick_leave',
                    'student_id': self.current_child.id,
                    'source_lesson_id': self.lesson.id,
                }]),
            },
            HTTP_ADMINTOKEN='targeted-revert-token',
        ).json()['data'][0]['id']
        second = self.client.post(
            '/CSAA/admin/dailyAdjustment/saveBatch',
            {
                'lesson_date': '2026-06-28',
                'actions': json.dumps([{
                    'type': 'sick_leave',
                    'student_id': self.future_child.id,
                    'source_lesson_id': self.lesson.id,
                }]),
            },
            HTTP_ADMINTOKEN='targeted-revert-token',
        ).json()['data'][0]['id']

        demo_student = Child.objects.create(parent=self.parent, name='Parent Demo Student')
        DailyStudentAdjustment.objects.create(
            student=demo_student,
            lesson_date=datetime.date(2026, 6, 28),
            adjustment_type='sick_leave',
            source_lesson=self.lesson,
        )

        listed = self.client.get(
            '/CSAA/admin/dailyAdjustment/list',
            {'date': '2026-06-28'},
            HTTP_ADMINTOKEN='targeted-revert-token',
        ).json()['data']
        self.assertEqual({item['id'] for item in listed}, {first, second})
        self.assertEqual(listed[0]['source_room'], 'Date Filter Room')
        self.assertEqual(listed[0]['source_time'], '16:00-17:00')

        response = self.client.post(
            '/CSAA/admin/dailyAdjustment/revert',
            {'id': first},
            HTTP_ADMINTOKEN='targeted-revert-token',
        )
        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(DailyStudentAdjustment.objects.get(id=first).status, 'reverted')
        self.assertEqual(DailyStudentAdjustment.objects.get(id=second).status, 'active')

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

        catalog = self.client.get(
            '/CSAA/admin/permanentCourseChange/options',
            {'student_id': self.current_child.id, 'source_lesson_id': self.lesson.id,
             'effective_date': '2026-07-01'},
            HTTP_ADMINTOKEN='permanent-admin-token',
        ).json()
        self.assertEqual(catalog['code'], 0)
        self.assertTrue(any(item['class_name'] == 'Permanent Target Class' for item in catalog['data']))
        choices = self.client.get(
            '/CSAA/admin/permanentCourseChange/options',
            {'student_id': self.current_child.id, 'source_lesson_id': self.lesson.id,
             'effective_date': '2026-07-01', 'course': 'Permanent Target Class'},
            HTTP_ADMINTOKEN='permanent-admin-token',
        ).json()
        self.assertEqual(choices['code'], 0)
        self.assertEqual([item['lesson_id'] for item in choices['data']], [target_lesson.id])
        self.assertEqual(choices['data'][0]['remaining'], 4)

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
        self.assertEqual(source_order.return_time.date(), datetime.date(2026, 6, 28))
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

    def test_permanent_change_can_create_allowed_course_in_an_existing_room_slot(self):
        admin = User.objects.create(
            username='permanent_virtual_slot_admin',
            password='unused',
            role='0',
            admin_token='permanent-virtual-slot-token',
        )
        source_order = Order.objects.get(order_number='DATEFILTER001')
        course = Course.objects.create(title=self.thing.title)
        target_room = Tag.objects.create(title='Allowed Target Room', seat=4)
        target_time = Time.objects.create(time='17:00-18:00')
        Thing.objects.create(
            title='Different Existing Course',
            tag=target_room,
            time=target_time,
            day='Thu',
            status='0',
        )
        permission = RoomCoursePermission.objects.create(
            room=target_room,
            term=source_order.term,
            updated_by=admin,
        )
        permission.courses.add(course)

        catalog = self.client.get(
            '/CSAA/admin/permanentCourseChange/options',
            {
                'student_id': self.current_child.id,
                'source_lesson_id': self.lesson.id,
                'effective_date': '2026-07-01',
            },
            HTTP_ADMINTOKEN=admin.admin_token,
        ).json()
        self.assertTrue(any(
            item['class_name'] == self.thing.title and item['day'] == 'Thu'
            for item in catalog['data']
        ))

        choices = self.client.get(
            '/CSAA/admin/permanentCourseChange/options',
            {
                'student_id': self.current_child.id,
                'source_lesson_id': self.lesson.id,
                'effective_date': '2026-07-02',
                'course': self.thing.title,
            },
            HTTP_ADMINTOKEN=admin.admin_token,
        ).json()
        target = next(item for item in choices['data'] if item['room_id'] == target_room.id)
        self.assertIsNone(target['lesson_id'])
        self.assertEqual(target['time'], '17:00-18:00')

        response = self.client.post(
            '/CSAA/admin/permanentCourseChange/create',
            {
                'student_id': self.current_child.id,
                'source_lesson_id': self.lesson.id,
                'target_room_id': target['room_id'],
                'target_time_id': target['time_id'],
                'course': self.thing.title,
                'effective_date': '2026-07-02',
                'reason': 'Move to an allowed empty course slot',
            },
            HTTP_ADMINTOKEN=admin.admin_token,
        )

        self.assertEqual(response.json()['code'], 0)
        record = PermanentCourseChange.objects.get()
        self.assertEqual(record.target_lesson.thing.title, self.thing.title)
        self.assertEqual(record.target_lesson.thing.tag, target_room)
        self.assertEqual(record.target_lesson.thing.time, target_time)
        self.assertEqual(record.target_lesson.thing.day, 'Thu')

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

    def test_lesson_detail_lists_daily_move_as_rescheduled_not_normal(self):
        order = Order.objects.get(order_number='DATEFILTER001')
        candidate = self._candidate_class('Sun', '16:00-17:00', 'Daily Move Room')
        target_lesson = Lesson.objects.create(thing=candidate)
        DailyStudentAdjustment.objects.create(
            student=self.current_child,
            lesson_date=datetime.date(2026, 6, 28),
            adjustment_type='move',
            source_lesson=self.lesson,
            target_lesson=target_lesson,
            source_order=order,
            status='active',
        )

        source_data = LessonDetailSerializer(
            self.lesson,
            context={'class_date': datetime.date(2026, 6, 28)},
        ).data
        target_data = LessonDetailSerializer(
            target_lesson,
            context={'class_date': datetime.date(2026, 6, 28)},
        ).data

        self.assertNotIn(
            'Current Student',
            [student['name'] for student in source_data['students']],
        )
        self.assertNotIn(
            'Current Student',
            [student['name'] for student in target_data['students']],
        )
        self.assertEqual(
            [student['name'] for student in target_data['reschedule_students']],
            ['Current Student'],
        )
        self.assertEqual(
            target_data['reschedule_students'][0]['adjustment_status'],
            'moved',
        )

    def test_lesson_detail_lists_cross_date_daily_move_on_target_date(self):
        order = Order.objects.get(order_number='DATEFILTER001')
        candidate = self._candidate_class('Sun', '16:00-17:00', 'Cross Date Move Room')
        target_lesson = Lesson.objects.create(thing=candidate)
        target_date = datetime.date(2026, 7, 5)
        DailyStudentAdjustment.objects.create(
            student=self.current_child,
            lesson_date=datetime.date(2026, 6, 28),
            target_lesson_date=target_date,
            adjustment_type='move',
            source_lesson=self.lesson,
            target_lesson=target_lesson,
            source_order=order,
            status='active',
        )

        target_data = LessonDetailSerializer(
            target_lesson,
            context={'class_date': target_date},
        ).data

        self.assertEqual(
            [student['name'] for student in target_data['reschedule_students']],
            ['Current Student'],
        )
        self.assertEqual(
            target_data['reschedule_students'][0]['adjustment_status'],
            'moved',
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

    def test_student_detail_lists_trial_package_robotics_and_coding(self):
        coding_time = Time.objects.create(time='17:00-18:00')
        coding = Thing.objects.create(
            title='Trial Coding', tag=self.thing.tag, time=coding_time, day='Tue', status='0'
        )
        package_order = Order.objects.create(
            order_number='TRIALPACKAGE001', user=self.parent, child=self.current_child,
            thing=self.thing, num=2, amount='98', status=6, remark='Trial Package',
        )
        TrialRequest.objects.create(
            parent=self.parent, child=self.current_child, package_order=package_order,
            robotics_class=self.thing, coding_class=coding, status='scheduled',
        )

        data = AdminStudentSerializer(self.current_child).data

        self.assertEqual(len(data['trial_packages']), 1)
        self.assertEqual(data['trial_packages'][0]['status'], 'scheduled')
        self.assertEqual(
            [course['category'] for course in data['trial_packages'][0]['courses']],
            ['Robotics', 'Coding'],
        )
        self.assertTrue(all(course['configured'] for course in data['trial_packages'][0]['courses']))

    def test_trial_request_requires_robotics_and_coding_only(self):
        self.parent.token = 'trial-parent-token'
        self.parent.save(update_fields=['token'])
        trial_child = Child.objects.create(
            parent=self.parent,
            name='Trial Student',
        )
        robotics_category = Classification.objects.create(title='Robotics')
        coding_category = Classification.objects.create(title='Coding')
        coding_time = Time.objects.create(time='17:00-18:30')
        self.thing.classification = robotics_category
        self.thing.save(update_fields=['classification'])
        coding = Thing.objects.create(
            title='Trial Coding',
            classification=coding_category,
            tag=self.thing.tag,
            time=coding_time,
            day='Tue',
            status='0',
        )

        response = self.client.post(
            '/CSAA/index/trial/create',
            {
                'parent': self.parent.id,
                'child': trial_child.id,
                'robotics_class': self.thing.id,
                'coding_class': coding.id,
            },
            HTTP_TOKEN='trial-parent-token',
        )

        self.assertEqual(response.json()['code'], 0)
        trial_request = TrialRequest.objects.get(child=trial_child)
        self.assertEqual(trial_request.robotics_class, self.thing)
        self.assertEqual(trial_request.coding_class, coding)
        self.assertIsNone(trial_request.math_class)
        self.assertEqual(trial_request.package_order.num, 2)

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


class QuickStudentEnrollmentTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='quick_student_admin',
            password='unused',
            role='0',
            admin_token='quick-student-admin-token',
        )
        self.parent = User.objects.create(
            username='quick_student_parent',
            password='unused',
            role='1',
        )
        self.room = Tag.objects.create(title='Quick Room', seat=4)
        self.time = Time.objects.create(time='16:00-17:00')
        self.term = Term.objects.create(
            title='Quick Term',
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2027, 6, 30),
        )
        self.thing = Thing.objects.create(
            title='Quick Course',
            tag=self.room,
            time=self.time,
            day='Tue',
            status='0',
        )

    def test_available_slots_returns_matching_class_and_capacity(self):
        response = self.client.get(
            '/CSAA/admin/student/availableSlots',
            {
                'term': self.term.id,
                'course': 'Quick Course',
                'day': 'Tue',
                'time': self.time.id,
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(response.json()['data'][0]['id'], self.thing.id)
        self.assertEqual(response.json()['data'][0]['available_seats'], 4)

    def test_quick_create_creates_student_and_active_enrollment(self):
        response = self.client.post(
            '/CSAA/admin/student/quickCreate',
            {
                'name': 'Quick Student',
                'parent': self.parent.id,
                'term': self.term.id,
                'thing': self.thing.id,
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(response.json()['code'], 0)
        student = Child.objects.get(name='Quick Student')
        order = Order.objects.get(child=student)
        self.assertEqual(order.thing, self.thing)
        self.assertEqual(order.term, self.term)
        self.assertEqual(order.status, 6)

    def test_quick_add_can_materialize_a_room_permitted_course(self):
        permitted_course = Course.objects.create(title='Permitted Quick Course')
        permission = RoomCoursePermission.objects.create(room=self.room, term=self.term)
        permission.courses.add(permitted_course)

        slots_response = self.client.get(
            '/CSAA/admin/student/availableSlots',
            {
                'term': self.term.id,
                'course': permitted_course.title,
                'day': self.thing.day,
                'time': self.time.id,
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(slots_response.json()['code'], 0)
        slots = slots_response.json()['data']
        self.assertEqual(len(slots), 1)
        self.assertIsNone(slots[0]['id'])
        self.assertTrue(slots[0]['new_class'])
        self.assertEqual(slots[0]['room_id'], self.room.id)

        create_response = self.client.post(
            '/CSAA/admin/student/quickCreate',
            {
                'name': 'Permitted Slot Student',
                'term': self.term.id,
                'course': permitted_course.title,
                'room': self.room.id,
                'day': self.thing.day,
                'time': self.time.id,
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(create_response.json()['code'], 0)
        created_class = Thing.objects.get(
            title=permitted_course.title,
            tag=self.room,
            day=self.thing.day,
            time=self.time,
        )
        student = Child.objects.get(name='Permitted Slot Student')
        self.assertTrue(Order.objects.filter(child=student, thing=created_class, status=6).exists())
        self.assertTrue(Lesson.objects.filter(thing=created_class).exists())

    def test_admin_can_add_course_to_existing_student(self):
        student = Child.objects.create(parent=self.parent, name='Existing Student')

        response = self.client.post(
            '/CSAA/admin/student/addCourse',
            {
                'student': student.id,
                'term': self.term.id,
                'thing': self.thing.id,
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(response.json()['code'], 0)
        self.assertEqual(Child.objects.filter(name='Existing Student').count(), 1)
        order = Order.objects.get(child=student)
        self.assertEqual(order.thing, self.thing)
        self.assertEqual(order.term, self.term)
        self.assertEqual(order.status, 6)
        self.assertEqual(order.expect_time.date(), datetime.date(2026, 9, 8))
        self.assertEqual(order.return_time.date(), datetime.date(2027, 2, 2))
        self.assertTrue(Lesson.objects.get(thing=self.thing).students.filter(pk=student.id).exists())

    def test_admin_add_course_rejects_duplicate_and_time_conflict(self):
        student = Child.objects.create(parent=self.parent, name='Busy Student')
        Order.objects.create(
            child=student,
            user=self.parent,
            thing=self.thing,
            term=self.term,
            status=6,
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2027, 6, 30),
        )
        duplicate = self.client.post(
            '/CSAA/admin/student/addCourse',
            {
                'student': student.id,
                'term': self.term.id,
                'thing': self.thing.id,
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )
        conflicting_thing = Thing.objects.create(
            title='Another Course', tag=self.room, time=self.time, day='Tue', status='0',
        )
        slot_response = self.client.get(
            '/CSAA/admin/student/availableSlots',
            {
                'student': student.id,
                'term': self.term.id,
                'course': 'Another Course',
                'day': 'Tue',
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )
        conflict = self.client.post(
            '/CSAA/admin/student/addCourse',
            {
                'student': student.id,
                'term': self.term.id,
                'thing': conflicting_thing.id,
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(duplicate.json()['code'], 1)
        self.assertIn('already enrolled', duplicate.json()['msg'])
        slot = next(item for item in slot_response.json()['data'] if item['id'] == conflicting_thing.id)
        self.assertIn('Schedule conflict', slot['conflict'])
        self.assertEqual(conflict.json()['code'], 1)
        self.assertIn('Schedule conflict', conflict.json()['msg'])
        self.assertEqual(Order.objects.filter(child=student).count(), 1)

    def test_creation_log_distinguishes_confirmed_additions_from_old_requests(self):
        OpLog.objects.create(
            re_url='/CSAA/admin/student/create',
            re_method='POST',
            re_content='{"name":"Legacy Student","mobile":"private phone","email":"private email"}',
        )
        self.client.post(
            '/CSAA/admin/student/quickCreate',
            {
                'name': 'Logged Student',
                'parent': self.parent.id,
                'term': self.term.id,
                'thing': self.thing.id,
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )
        response = self.client.get(
            '/CSAA/admin/student/creationLog',
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )
        self.assertEqual(response.json()['code'], 0)
        rows = response.json()['data']
        created = next(row for row in rows if row['confirmed'])
        self.assertEqual(created['student_name'], 'Logged Student')
        self.assertEqual(created['source'], 'admin_quick')
        self.assertEqual(created['actor'], self.admin.username)
        legacy = next(row for row in rows if not row['confirmed'])
        self.assertEqual(legacy['student_name'], 'Legacy Student')
        self.assertNotIn('private phone', str(rows))
        self.assertNotIn('private email', str(rows))
        self.assertIsNone(OpLog.objects.filter(
            re_url='/CSAA/admin/student/quickCreate',
        ).latest('id').re_content)

    def test_creation_log_displays_toronto_time(self):
        student = Child.objects.create(name='Timezone Student')
        event = OpLog.objects.create(
            re_url=STUDENT_CREATED_EVENT,
            re_method='EVENT',
            re_content=json.dumps({
                'student_id': student.id,
                'source': 'admin_quick',
                'actor_id': self.admin.id,
            }),
        )
        OpLog.objects.filter(pk=event.pk).update(
            re_time=datetime.datetime(2026, 9, 22, 2, 41),
        )

        response = self.client.get(
            '/CSAA/admin/student/creationLog',
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.json()['data'] if item['student_id'] == student.id)
        self.assertEqual(row['created_time'], '2026-09-21 14:41')

    def test_creation_log_is_admin_only_and_records_other_create_paths(self):
        self.assertEqual(self.client.get('/CSAA/admin/student/creationLog').status_code, 403)
        self.client.post(
            '/CSAA/admin/student/create',
            {'name': 'Admin Added'},
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )
        self.parent.token = 'creation-log-parent-token'
        self.parent.save(update_fields=['token'])
        self.client.post(
            '/CSAA/index/child/create',
            {'name': 'Parent Added', 'parent': self.parent.id},
            HTTP_TOKEN=self.parent.token,
        )
        rows = self.client.get(
            '/CSAA/admin/student/creationLog',
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()['data']
        self.assertEqual({row['source'] for row in rows if row['confirmed']}, {'admin', 'parent'})

    def test_quick_create_uses_student_class_dates_in_schedule(self):
        response = self.client.post(
            '/CSAA/admin/student/quickCreate',
            {
                'name': 'Partial Term Student',
                'term': self.term.id,
                'thing': self.thing.id,
                'start_date': '2026-09-08',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(response.json()['code'], 0)
        order = Order.objects.get(child__name='Partial Term Student')
        self.assertEqual(order.expect_time.date(), datetime.date(2026, 9, 8))
        self.assertEqual(order.return_time.date(), datetime.date(2027, 2, 2))
        self.assertEqual(Order.objects.filter(
            thing=self.thing, status=6,
            expect_time__date__lte=datetime.date(2027, 2, 2),
            return_time__date__gte=datetime.date(2027, 2, 2),
        ).count(), 1)
        Lesson.objects.create(thing=self.thing)
        last_day = self.client.get('/CSAA/admin/lesson/list', {'date': '2027-02-02'}).json()
        after_end = self.client.get('/CSAA/admin/lesson/list', {'date': '2027-02-09'}).json()
        self.assertEqual(
            [student['name'] for lesson in last_day['data'] for student in lesson['scheduled_students']],
            ['Partial Term Student'],
        )
        self.assertEqual(
            [student['name'] for lesson in after_end['data'] for student in lesson['scheduled_students']],
            [],
        )

    def test_quick_create_rejects_dates_outside_term(self):
        response = self.client.post(
            '/CSAA/admin/student/quickCreate',
            {
                'name': 'Invalid Dates',
                'term': self.term.id,
                'thing': self.thing.id,
                'start_date': '2026-08-31',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )

        self.assertEqual(response.json()['code'], 1)
        self.assertFalse(Child.objects.filter(name='Invalid Dates').exists())

    def test_available_capacity_uses_requested_class_dates(self):
        self.room.seat = 1
        self.room.save(update_fields=['seat'])
        earlier_student = Child.objects.create(name='Earlier Student')
        Order.objects.create(
            child=earlier_student,
            thing=self.thing,
            term=self.term,
            status=6,
            expect_time=datetime.datetime(2026, 9, 1),
            return_time=datetime.datetime(2026, 10, 31, 23, 59, 59),
        )

        full_term = self.client.get(
            '/CSAA/admin/student/availableSlots',
            {'term': self.term.id, 'course': 'Quick Course'},
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()['data'][0]
        later_window = self.client.get(
            '/CSAA/admin/student/availableSlots',
            {
                'term': self.term.id,
                'course': 'Quick Course',
                'start_date': '2027-01-01',
                'end_date': '2027-02-02',
            },
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()['data'][0]

        self.assertEqual(full_term['available_seats'], 0)
        self.assertEqual(later_window['available_seats'], 1)


class AdminTrialBookingTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(username='trial_admin', role='0', admin_token='trial-admin-token')
        self.parent = User.objects.create(username='trial_parent', role='1', token='trial-parent-token')
        self.student = Child.objects.create(parent=self.parent, name='Trial Booking Student')
        self.other_student = Child.objects.create(parent=self.parent, name='Other Trial Student')
        self.regular_student = Child.objects.create(parent=self.parent, name='Regular Student')
        self.room = Tag.objects.create(title='Trial Room', seat=2)
        self.other_room = Tag.objects.create(title='Coding Room', seat=2)
        afternoon = Time.objects.create(time='16:00-17:00')
        following = Time.objects.create(time='17:00-18:00')
        self.robotics = Lesson.objects.create(thing=Thing.objects.create(
            title='Creator', tag=self.room, time=afternoon, day='Tue', status='0'))
        self.following = Lesson.objects.create(thing=Thing.objects.create(
            title='Scratch', tag=self.room, time=following, day='Tue', status='0'))
        self.coding = Lesson.objects.create(thing=Thing.objects.create(
            title='Scratch', tag=self.other_room, time=afternoon, day='Wed', status='0'))
        self.term = Term.objects.create(title='Trial Test Term',
            expect_time=datetime.datetime(2026, 9, 1), return_time=datetime.datetime(2026, 10, 31))
        Order.objects.create(
            child=self.regular_student, user=self.parent, thing=self.following.thing,
            term=self.term, status=6,
            expect_time=datetime.datetime(2026, 9, 1), return_time=datetime.datetime(2026, 10, 31),
        )

    def _book(self, name):
        return self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': name,
            'sessions': [
                {'lesson_id': self.robotics.id, 'date': '2026-09-22'},
                {'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()

    def test_trial_occupies_both_room_slots_and_can_be_canceled(self):
        created = self._book('New Trial Student')
        self.assertEqual(created['code'], 0, created)
        new_student = Child.objects.get(id=created['data']['student_id'])
        self.assertEqual(new_student.name, 'New Trial Student')
        self.assertTrue(OpLog.objects.filter(re_url='student_created', re_content__contains='admin_trial').exists())
        self.assertEqual(AdminTrialSession.objects.filter(status='active').count(), 2)

        schedule = self.client.get('/CSAA/admin/lesson/list', {'date': '2026-09-22'}).json()['data']
        first = next(item for item in schedule if item['id'] == self.robotics.id)
        second = next(item for item in schedule if item['id'] == self.following.id)
        self.assertEqual(first['scheduled_trial_students'][0]['name'], new_student.name)
        self.assertEqual(second['continuing_trial_students'], [])
        self.assertEqual(self.client.get('/CSAA/admin/lesson/detail', {
            'lesson_id': self.robotics.id, 'date': '2026-09-22',
        }).json()['data']['try_students'][0]['name'], new_student.name)
        detail = self.client.get('/CSAA/admin/student/detail', {'id': new_student.id},
                                 HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']
        self.assertEqual(detail['trial_packages'][0]['source'], 'admin')
        self.assertEqual(detail['trial_packages'][0]['status'], 'active')

        options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': '2026-09-22',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']
        self.assertEqual(options[0]['remaining'], 0)
        student_options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': '2026-09-22', 'student_id': self.regular_student.id,
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']
        self.assertTrue(student_options[0]['student_conflict'])
        self.assertNotEqual(self._book('No Capacity Student')['code'], 0)
        self.assertFalse(Child.objects.filter(name='No Capacity Student').exists())
        self.assertEqual(AdminTrialSession.objects.filter(status='active').count(), 2)

        canceled = self.client.post('/CSAA/admin/trialBooking/cancel', {
            'package_key': created['data']['package_key'],
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(canceled['code'], 0)
        self.assertEqual(AdminTrialSession.objects.filter(status='active').count(), 0)
        detail = self.client.get('/CSAA/admin/student/detail', {'id': new_student.id},
                                 HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']
        self.assertEqual(detail['trial_packages'][0]['status'], 'canceled')
        self.assertEqual(self._book('Second New Trial Student')['code'], 0)

    def test_trial_continuation_is_never_attached_to_other_courses(self):
        Lesson.objects.create(thing=Thing.objects.create(
            title='Spike', tag=self.room, time=self.following.thing.time,
            day='Tue', status='0',
        ))
        Lesson.objects.create(thing=Thing.objects.create(
            title='Python', tag=self.room, time=self.following.thing.time,
            day='Tue', status='0',
        ))

        created = self._book('Single Continue Trial')
        self.assertEqual(created['code'], 0, created)
        schedule = self.client.get(
            '/CSAA/admin/lesson/list', {'date': '2026-09-22'},
        ).json()['data']

        continuations = [
            student
            for lesson in schedule
            for student in lesson.get('continuing_trial_students', [])
            if student['name'] == 'Single Continue Trial'
        ]
        self.assertEqual(continuations, [])
        following = next(item for item in schedule if item['id'] == self.following.id)
        self.assertEqual(following['continuing_trial_students'], [])

    def test_roblox_trial_continues_only_on_one_matching_next_slot_card(self):
        source_time = Time.objects.create(time='17:00-18:00')
        overlapping_time = Time.objects.create(time='17:00-18:30')
        next_time = Time.objects.create(time='18:00-19:00')
        source = Lesson.objects.create(thing=Thing.objects.create(
            title='Roblox', tag=self.room, time=source_time, day='Thu', status='0',
        ))
        Lesson.objects.create(thing=Thing.objects.create(
            title='Scratch', tag=self.room, time=overlapping_time, day='Thu', status='0',
        ))
        Lesson.objects.create(thing=Thing.objects.create(
            title='Spike', tag=self.room, time=overlapping_time, day='Thu', status='0',
        ))
        next_roblox = Lesson.objects.create(thing=Thing.objects.create(
            title='Roblox', tag=self.room, time=next_time, day='Thu', status='0',
        ))
        Lesson.objects.create(thing=Thing.objects.create(
            title='Python', tag=self.room, time=next_time, day='Thu', status='0',
        ))
        Lesson.objects.create(thing=Thing.objects.create(
            title='Spike', tag=self.room, time=next_time, day='Thu', status='0',
        ))

        created = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Austin Regression',
            'sessions': [
                {'mode': 'existing', 'lesson_id': source.id, 'date': '2026-10-08'},
                {'mode': 'existing', 'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(created['code'], 0, created)

        schedule = self.client.get(
            '/CSAA/admin/lesson/list', {'date': '2026-10-08'},
        ).json()['data']
        continuation_cards = [
            lesson for lesson in schedule
            if any(
                student['name'] == 'Austin Regression'
                for student in lesson.get('continuing_trial_students', [])
            )
        ]
        self.assertEqual([item['id'] for item in continuation_cards], [next_roblox.id])
        self.assertEqual(continuation_cards[0]['time'], '18:00-19:00')

    def test_trial_rejects_overlapping_sessions_and_parent_identity_mismatch(self):
        bad = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Overlapping Trial Student',
            'sessions': [
                {'lesson_id': self.robotics.id, 'date': '2026-09-22'},
                {'lesson_id': self.robotics.id, 'date': '2026-09-22'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertNotEqual(bad['code'], 0)
        self.assertEqual(AdminTrialSession.objects.count(), 0)
        self.assertFalse(Child.objects.filter(name='Overlapping Trial Student').exists())

        existing = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_id': self.student.id,
            'student_name': 'Existing Trial Student',
            'sessions': [
                {'lesson_id': self.robotics.id, 'date': '2026-09-22'},
                {'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertNotEqual(existing['code'], 0)
        self.assertFalse(Child.objects.filter(name='Existing Trial Student').exists())

        another_parent = User.objects.create(username='another_parent', role='1', token='another-parent-token')
        unauthorized = self.client.post('/CSAA/index/trial/create', {
            'parent': self.parent.id,
            'child': self.student.id,
            'robotics_class': self.robotics.thing.id,
            'coding_class': self.coding.thing.id,
        }, HTTP_TOKEN=another_parent.token).json()
        self.assertNotEqual(unauthorized['code'], 0)
        self.assertEqual(TrialRequest.objects.count(), 0)

    def test_flexible_trial_uses_room_permissions_and_appears_as_dated_schedule_card(self):
        ai_room = Tag.objects.create(title='AI Flexible Room', seat=1)
        ai_course = Course.objects.create(title='AI')
        permission = RoomCoursePermission.objects.create(room=ai_room, term=self.term, updated_by=self.admin)
        permission.courses.add(ai_course)

        options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'AI', 'date': '2026-09-22', 'mode': 'flexible',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(options['code'], 0)
        flexible = next(item for item in options['data'] if item['room_id'] == ai_room.id and item['start'] == '16:00')
        self.assertTrue(flexible['teacher_confirmation_required'])
        self.assertEqual(flexible['remaining'], 1)

        created = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Flexible Trial Student',
            'sessions': [
                {
                    'mode': 'flexible', 'subject': 'AI', 'date': '2026-09-22',
                    'course': 'AI', 'room_id': ai_room.id, 'start': '16:00',
                },
                {'mode': 'existing', 'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(created['code'], 0)
        flexible_session = AdminTrialSession.objects.get(
            student_id=created['data']['student_id'], booking_mode='flexible',
        )
        self.assertIsNone(flexible_session.lesson_id)
        self.assertEqual(flexible_session.room_id, ai_room.id)
        self.assertEqual(flexible_session.course_name, 'AI')

        schedule = self.client.get('/CSAA/admin/lesson/list', {'date': '2026-09-22'}).json()['data']
        card = next(item for item in schedule if item.get('virtual_trial'))
        self.assertEqual(card['class_name'], 'AI')
        self.assertEqual(card['room_name'], ai_room.title)
        self.assertEqual(card['scheduled_trial_students'][0]['name'], 'Flexible Trial Student')

        full_options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'AI', 'date': '2026-09-22', 'mode': 'flexible',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']
        full = next(item for item in full_options if item['room_id'] == ai_room.id and item['start'] == '16:00')
        self.assertEqual(full['remaining'], 0)

    def test_robotics_flexible_trial_can_start_on_the_half_hour(self):
        creator, _ = Course.objects.get_or_create(title='Creator')
        permission = RoomCoursePermission.objects.create(
            room=self.room, term=self.term, updated_by=self.admin,
        )
        permission.courses.add(creator)

        options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': '2026-09-22', 'mode': 'flexible',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertEqual(options['code'], 0)
        half_hour = next(
            item for item in options['data']
            if item['room_id'] == self.room.id and item['start'] == '16:30'
        )
        self.assertEqual(half_hour['end'], '18:00')
        self.assertEqual(half_hour['remaining'], 1)

        created = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Half Hour Trial Student',
            'sessions': [
                {
                    'mode': 'flexible', 'subject': 'Robotics', 'date': '2026-09-22',
                    'course': 'Creator', 'room_id': self.room.id, 'start': '16:30',
                },
                {'mode': 'existing', 'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertEqual(created['code'], 0)
        session = AdminTrialSession.objects.get(
            student_id=created['data']['student_id'], booking_mode='flexible',
        )
        self.assertEqual(session.starts_at, datetime.time(16, 30))
        self.assertEqual(session.ends_at, datetime.time(18, 0))

    def test_existing_trial_can_start_on_the_half_hour(self):
        late_lesson = Lesson.objects.create(thing=Thing.objects.create(
            title='Spike', tag=self.room, time=self.following.thing.time,
            day='Tue', status='0',
        ))
        options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': '2026-09-22', 'mode': 'existing',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertEqual(options['code'], 0)
        half_hour = next(
            item for item in options['data']
            if item['lesson_id'] == self.robotics.id and item['start'] == '16:30'
        )
        self.assertEqual(half_hour['end'], '18:00')
        self.assertEqual(
            half_hour['option_key'],
            f'existing:{self.robotics.id}:16:30',
        )
        late_half_hour = next(
            item for item in options['data']
            if item['lesson_id'] == late_lesson.id and item['start'] == '17:30'
        )
        self.assertEqual(late_half_hour['end'], '19:00')

        invalid = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Invalid Quarter Hour',
            'sessions': [
                {
                    'mode': 'existing', 'lesson_id': self.robotics.id,
                    'date': '2026-09-22', 'start': '16:15',
                },
                {'mode': 'existing', 'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertNotEqual(invalid['code'], 0)
        self.assertFalse(Child.objects.filter(name='Invalid Quarter Hour').exists())

        created = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Existing Half Hour Trial',
            'sessions': [
                {
                    'mode': 'existing', 'lesson_id': self.robotics.id,
                    'date': '2026-09-22', 'start': '16:30',
                },
                {'mode': 'existing', 'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertEqual(created['code'], 0, created)
        session = AdminTrialSession.objects.get(
            student_id=created['data']['student_id'], session_index=1,
        )
        self.assertEqual(session.booking_mode, 'existing')
        self.assertEqual(session.starts_at, datetime.time(16, 30))
        self.assertEqual(session.ends_at, datetime.time(18, 0))

    def test_trial_course_permissions_are_applied_per_course_and_room(self):
        room_five = Tag.objects.create(title='Room 5', seat=4)
        creator, _ = Course.objects.get_or_create(title='Creator')
        wedo, _ = Course.objects.get_or_create(title='WeDo')
        creator_rule = RoomCoursePermission.objects.create(
            room=self.room, term=self.term, updated_by=self.admin,
        )
        creator_rule.courses.add(creator)
        wedo_rule = RoomCoursePermission.objects.create(
            room=room_five, term=self.term, updated_by=self.admin,
        )
        wedo_rule.courses.add(wedo)

        flexible = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': '2026-09-22', 'mode': 'flexible',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']

        pairs = {(item['course'], item['room']) for item in flexible}
        self.assertIn(('Creator', self.room.title), pairs)
        self.assertIn(('WeDo', room_five.title), pairs)
        self.assertNotIn(('WeDo', self.room.title), pairs)
        self.assertNotIn(('Creator', room_five.title), pairs)

        existing = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'date': '2026-09-22', 'mode': 'existing',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()['data']
        self.assertEqual(
            [(item['course'], item['start']) for item in existing],
            [('Creator', '16:00'), ('Creator', '16:30')],
        )

        rejected = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Wrong Room Trial Student',
            'sessions': [
                {
                    'mode': 'flexible', 'subject': 'Robotics', 'course': 'WeDo',
                    'date': '2026-09-22', 'room_id': self.room.id, 'start': '16:00',
                },
                {'mode': 'existing', 'lesson_id': self.coding.id, 'date': '2026-09-23'},
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertNotEqual(rejected['code'], 0)
        self.assertFalse(Child.objects.filter(name='Wrong Room Trial Student').exists())

    def test_trial_package_templates_and_creator_packages(self):
        templates = self.client.get(
            '/CSAA/admin/trialBooking/templates',
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()

        self.assertEqual(templates['code'], 0)
        by_key = {item['key']: item for item in templates['data']}
        self.assertEqual(set(by_key), {'standard', 'creator', 'creator_2x90', 'vex_v5'})
        self.assertEqual(
            [item['duration'] for item in by_key['creator']['sessions']],
            [60, 60, 60],
        )
        self.assertEqual(
            [item['start_interval'] for item in by_key['creator']['sessions']],
            [60, 60, 60],
        )
        self.assertEqual(
            [item['duration'] for item in by_key['creator_2x90']['sessions']],
            [90, 90],
        )

        options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'course': 'Creator', 'duration': 60,
            'start_interval': 60, 'date': '2026-09-22', 'mode': 'existing',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(options['code'], 0)
        self.assertEqual({item['course'] for item in options['data']}, {'Creator'})
        self.assertEqual(
            [(item['start'], item['end']) for item in options['data']],
            [('16:00', '17:00')],
        )

        rejected_half_hour = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Invalid Half Hour Creator Package',
            'package_type': 'creator',
            'sessions': [
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-22', 'start': '16:30',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-29', 'start': '16:00',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-10-06', 'start': '16:00',
                },
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertNotEqual(rejected_half_hour['code'], 0)
        self.assertFalse(Child.objects.filter(name='Invalid Half Hour Creator Package').exists())

        created = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Creator Package Student',
            'package_type': 'creator',
            'sessions': [
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-22', 'start': '16:00',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-29', 'start': '16:00',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-10-06', 'start': '16:00',
                },
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertEqual(created['code'], 0, created)
        sessions = list(AdminTrialSession.objects.filter(
            student_id=created['data']['student_id'],
        ).order_by('session_index'))
        self.assertEqual(len(sessions), 3)
        self.assertTrue(all(item.course_name == 'Creator' for item in sessions))
        self.assertTrue(all(
            datetime.datetime.combine(item.session_date, item.ends_at)
            - datetime.datetime.combine(item.session_date, item.starts_at)
            == datetime.timedelta(minutes=60)
            for item in sessions
        ))

        detail = self.client.get(
            '/CSAA/admin/student/detail', {'id': created['data']['student_id']},
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()['data']
        self.assertEqual(detail['trial_packages'][0]['package_type'], 'creator')

        ninety_minute_options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'Robotics', 'course': 'Creator', 'duration': 90,
            'start_interval': 30, 'date': '2026-09-22', 'mode': 'existing',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(ninety_minute_options['code'], 0)
        self.assertIn(
            ('16:30', '18:00'),
            [(item['start'], item['end']) for item in ninety_minute_options['data']],
        )

        creator_90 = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Creator Ninety Minute Package',
            'package_type': 'creator_2x90',
            'sessions': [
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-22', 'start': '16:30',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-29', 'start': '16:30',
                },
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(creator_90['code'], 0, creator_90)
        creator_90_sessions = AdminTrialSession.objects.filter(
            student_id=creator_90['data']['student_id'],
        ).order_by('session_index')
        self.assertEqual(creator_90_sessions.count(), 2)
        self.assertTrue(all(
            datetime.datetime.combine(item.session_date, item.ends_at)
            - datetime.datetime.combine(item.session_date, item.starts_at)
            == datetime.timedelta(minutes=90)
            for item in creator_90_sessions
        ))
        creator_90_detail = self.client.get(
            '/CSAA/admin/student/detail', {'id': creator_90['data']['student_id']},
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()['data']
        self.assertEqual(
            creator_90_detail['trial_packages'][0]['package_type'],
            'creator_2x90',
        )

    def test_vex_v5_package_uses_two_hour_v5_and_one_hour_coding(self):
        vex_room = Tag.objects.create(title='VEX V5 Room', seat=3)
        vex_time = Time.objects.create(time='17:00-19:00')
        vex_lesson = Lesson.objects.create(thing=Thing.objects.create(
            title='VEX V5', tag=vex_room, time=vex_time, day='Tue', status='0',
        ))

        vex_options = self.client.get('/CSAA/admin/trialBooking/options', {
            'subject': 'VEX V5', 'course': 'VEX V5', 'duration': 120,
            'date': '2026-09-22', 'mode': 'existing',
        }, HTTP_ADMINTOKEN=self.admin.admin_token).json()
        self.assertEqual(vex_options['code'], 0)
        self.assertEqual(
            [(item['start'], item['end']) for item in vex_options['data']],
            [('17:00', '19:00')],
        )

        created = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'VEX V5 Package Student',
            'package_type': 'vex_v5',
            'sessions': [
                {
                    'mode': 'existing', 'subject': 'VEX V5',
                    'lesson_id': vex_lesson.id, 'date': '2026-09-22', 'start': '17:00',
                },
                {
                    'mode': 'existing', 'subject': 'Coding',
                    'lesson_id': self.coding.id, 'date': '2026-09-23', 'start': '16:30',
                },
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertEqual(created['code'], 0, created)
        sessions = list(AdminTrialSession.objects.filter(
            student_id=created['data']['student_id'],
        ).order_by('session_index'))
        durations = [
            int((
                datetime.datetime.combine(item.session_date, item.ends_at)
                - datetime.datetime.combine(item.session_date, item.starts_at)
            ).total_seconds() // 60)
            for item in sessions
        ]
        self.assertEqual([item.course_name for item in sessions], ['VEX V5', 'Scratch'])
        self.assertEqual(durations, [120, 60])

        detail = self.client.get(
            '/CSAA/admin/student/detail', {'id': created['data']['student_id']},
            HTTP_ADMINTOKEN=self.admin.admin_token,
        ).json()['data']
        self.assertEqual(detail['trial_packages'][0]['package_type'], 'vex_v5')

    def test_creator_package_rejects_non_creator_course(self):
        rejected = self.client.post('/CSAA/admin/trialBooking/create', json.dumps({
            'student_name': 'Invalid Creator Package',
            'package_type': 'creator',
            'sessions': [
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.following.id, 'date': '2026-09-22', 'start': '17:00',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-09-29', 'start': '16:00',
                },
                {
                    'mode': 'existing', 'subject': 'Robotics',
                    'lesson_id': self.robotics.id, 'date': '2026-10-06', 'start': '16:00',
                },
            ],
        }), content_type='application/json', HTTP_ADMINTOKEN=self.admin.admin_token).json()

        self.assertNotEqual(rejected['code'], 0)
        self.assertFalse(Child.objects.filter(name='Invalid Creator Package').exists())


class InternalAssistantQueryTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create(
            username='assistant_admin', role='0', status='0', admin_token='assistant-token',
        )
        self.parent = User.objects.create(username='assistant_parent', role='1', status='0')
        self.student = Child.objects.create(parent=self.parent, name='Query Student-Z2020')
        today = datetime.date.today()
        self.term = Term.objects.create(
            title='Assistant Current Term',
            expect_time=datetime.datetime.combine(today - datetime.timedelta(days=30), datetime.time.min),
            return_time=datetime.datetime.combine(today + datetime.timedelta(days=90), datetime.time.max),
        )
        self.room = Tag.objects.create(title='Assistant Room 3', seat=3)
        self.time = Time.objects.create(time='16:00-17:00')
        self.thing = Thing.objects.create(
            title='Scratch Assistant', day='Sat', time=self.time, tag=self.room, status='0',
        )
        Order.objects.create(
            order_number='ASSIST001', user=self.parent, child=self.student,
            thing=self.thing, term=self.term, status=6, num=7,
            expect_time=self.term.expect_time, return_time=self.term.return_time,
        )

    def _ask(self, question):
        response = self.client.post(
            '/CSAA/admin/assistant/query',
            json.dumps({'question': question}),
            content_type='application/json',
            HTTP_ADMINTOKEN=self.admin.admin_token,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['code'], 0)
        return payload['data']

    def test_availability_uses_shared_room_capacity(self):
        other_course = Thing.objects.create(
            title='Spike Assistant', day='Sat', time=self.time, tag=self.room, status='0',
        )
        second_student = Child.objects.create(parent=self.parent, name='Second Query Student')
        Order.objects.create(
            order_number='ASSIST002', user=self.parent, child=second_student,
            thing=other_course, term=self.term, status=6, num=4,
            expect_time=self.term.expect_time, return_time=self.term.return_time,
        )

        result = self._ask('Which Scratch Assistant classes have seats on Saturday?')

        self.assertEqual(result['intent'], 'availability')
        self.assertEqual(len(result['items']), 1)
        self.assertEqual(result['items'][0]['enrolled_count'], 2)
        self.assertEqual(result['items'][0]['available_seats'], 1)

    def test_remaining_lessons_come_from_active_enrollment(self):
        result = self._ask('How many lessons does Query Student-Z2020 have left?')

        self.assertEqual(result['intent'], 'student_remaining')
        self.assertIn('7 remaining lessons', result['answer'])
        self.assertEqual(result['items'][0]['remaining_lessons'], 7)
        self.assertEqual(result['items'][0]['course'], 'Scratch Assistant')

    def test_legacy_zero_balance_is_labeled_as_calendar_estimate(self):
        Order.objects.filter(child=self.student).update(num=0)

        result = self._ask('How many lessons does Query Student-Z2020 have left?')

        self.assertIn('no tracked remaining-lesson balance', result['answer'])
        self.assertGreater(result['items'][0]['calendar_estimate'], 0)
        self.assertEqual(result['items'][0]['balance_source'], 'calendar_estimate')
