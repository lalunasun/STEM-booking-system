import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from CSAA.models import (
    Child,
    Classification,
    CourseAdjustment,
    Lesson,
    Order,
    StudentAttendance,
    StudentComment,
    StudentLessonNote,
    Tag,
    Term,
    Thing,
    Time,
    User,
)
from CSAA.utils import md5value


class Command(BaseCommand):
    help = "Create an idempotent 10-student dataset for the local AI project branch."

    term_title = "AI Project Test - Fall 2026"
    password = "ai-test-2026"

    students = [
        ("Ava Chen", 8, "F"),
        ("Noah Li", 9, "M"),
        ("Emma Wang", 10, "F"),
        ("Liam Zhang", 11, "M"),
        ("Mia Liu", 9, "F"),
        ("Ethan Zhao", 12, "M"),
        ("Sofia Yang", 10, "F"),
        ("Lucas Wu", 11, "M"),
        ("Chloe Sun", 8, "F"),
        ("Oliver Guo", 12, "M"),
    ]

    comment_sets = [
        [
            "Understands sequencing and follows the build instructions carefully.",
            "Can explain the loop used in today's robotics task.",
            "Next step: practice debugging independently before asking for help.",
        ],
        [
            "Participates actively and collaborates well with a partner.",
            "Understands variables but sometimes changes more than one value at a time.",
            "Next step: test one change at a time and record the result.",
        ],
        [
            "Completed the main challenge and attempted the extension activity.",
            "Shows strong pattern recognition in block-based coding.",
            "Next step: explain the solution using clearer technical vocabulary.",
        ],
        [
            "Needs occasional reminders to read the full problem before coding.",
            "Improved after using a checklist to find syntax errors.",
            "Next step: continue using the debugging checklist each lesson.",
        ],
        [
            "Built a stable robot and tested different motor speeds.",
            "Can compare two test results and identify the better setting.",
            "Next step: write a short prediction before each test.",
        ],
    ]

    @transaction.atomic
    def handle(self, *args, **options):
        self._admin()
        teacher = self._teacher()
        term = self._term()
        courses = self._courses()
        lessons = {key: Lesson.objects.get_or_create(thing=value)[0] for key, value in courses.items()}

        for index, (name, age, gender) in enumerate(self.students, start=1):
            parent, child = self._parent_and_child(index, name, age, gender)
            course_key = "robotics" if index <= 5 else "coding"
            course = courses[course_key]
            lesson = lessons[course_key]
            order = self._order(index, parent, child, course, term)
            lesson.students.add(child)
            self._attendance(index, child, lesson, teacher)
            self._comments(index, child, lesson, teacher)
            self._adjustment(index, parent, child, order, course, term, teacher)

        for lesson in lessons.values():
            lesson.students_num = lesson.students.count()
            lesson.save(update_fields=["students_num"])

        self.stdout.write(self.style.SUCCESS("AI project test data ready: 10 students."))
        self.stdout.write(f"Admin login: ai_admin / {self.password}")
        self.stdout.write(f"Parent login password for all AI test accounts: {self.password}")

    def _admin(self):
        admin, _ = User.objects.update_or_create(
            username="ai_admin",
            defaults={
                "password": md5value(self.password),
                "role": "0",
                "status": "0",
                "nickname": "AI Test Administrator",
                "email": "ai.admin@example.test",
            },
        )
        return admin

    def _teacher(self):
        teacher, _ = User.objects.update_or_create(
            username="ai_test_teacher",
            defaults={
                "password": md5value(self.password),
                "role": "2",
                "status": "0",
                "nickname": "AI Test Teacher",
                "email": "ai.teacher@example.test",
            },
        )
        return teacher

    def _term(self):
        term, _ = Term.objects.update_or_create(
            title=self.term_title,
            defaults={
                "expect_time": datetime.datetime(2026, 9, 1, 0, 0),
                "return_time": datetime.datetime(2026, 11, 30, 23, 59),
                "price": "400",
            },
        )
        return term

    def _courses(self):
        robotics_category, _ = Classification.objects.get_or_create(title="Robotics")
        coding_category, _ = Classification.objects.get_or_create(title="Coding")
        room1, _ = Tag.objects.update_or_create(title="AI Room 1", defaults={"seat": 8})
        room2, _ = Tag.objects.update_or_create(title="AI Room 2", defaults={"seat": 8})
        time1, _ = Time.objects.get_or_create(time="16:00-17:00")
        time2, _ = Time.objects.get_or_create(time="17:00-18:00")

        robotics, _ = Thing.objects.update_or_create(
            title="AI Test Robotics",
            day="Tue",
            time=time1,
            tag=room1,
            defaults={
                "classification": robotics_category,
                "description": "Local AI project test course",
                "price": "40",
                "repertory": "8",
                "status": "0",
            },
        )
        coding, _ = Thing.objects.update_or_create(
            title="AI Test Coding",
            day="Wed",
            time=time2,
            tag=room2,
            defaults={
                "classification": coding_category,
                "description": "Local AI project test course",
                "price": "40",
                "repertory": "8",
                "status": "0",
            },
        )
        return {"robotics": robotics, "coding": coding}

    def _parent_and_child(self, index, name, age, gender):
        username = f"ai_parent_{index:02d}"
        parent, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "password": md5value(self.password),
                "role": "1",
                "status": "0",
                "nickname": f"AI Parent {index:02d}",
                "mobile": f"41655520{index:02d}",
                "email": f"{username}@example.test",
            },
        )
        child, _ = Child.objects.update_or_create(
            parent=parent,
            name=name,
            defaults={
                "age": age,
                "gender": gender,
                "remark": "Synthetic record for local AI project testing only.",
            },
        )
        return parent, child

    def _order(self, index, parent, child, course, term):
        order, _ = Order.objects.update_or_create(
            order_number=f"AI2609{index:07d}",
            defaults={
                "user": parent,
                "thing": course,
                "count": 1,
                "num": 12,
                "child": child,
                "expect_time": term.expect_time,
                "return_time": term.return_time,
                "term": term,
                "amount": "480",
                "status": 6,
                "pay_time": datetime.datetime(2026, 8, 25, 10, index),
                "receiver_name": parent.nickname,
                "receiver_phone": parent.mobile,
                "remark": "AI project synthetic data",
            },
        )
        return order

    def _attendance(self, index, child, lesson, teacher):
        if lesson.thing.day == "Tue":
            dates = [
                datetime.date(2026, 9, 8),
                datetime.date(2026, 9, 15),
                datetime.date(2026, 9, 22),
                datetime.date(2026, 9, 29),
            ]
        else:
            dates = [
                datetime.date(2026, 9, 9),
                datetime.date(2026, 9, 16),
                datetime.date(2026, 9, 23),
                datetime.date(2026, 9, 30),
            ]

        StudentAttendance.objects.filter(student=child, lesson=lesson).delete()
        absent_positions = {2} if index in {2, 5, 8} else ({1, 3} if index == 9 else set())
        for position, lesson_date in enumerate(dates):
            StudentAttendance.objects.create(
                student=child,
                lesson=lesson,
                lesson_date=lesson_date,
                is_absent=position in absent_positions,
                marked_by=teacher,
            )

    def _comments(self, index, child, lesson, teacher):
        StudentComment.objects.filter(student=child, created_by=teacher).delete()
        StudentLessonNote.objects.filter(student=child, lesson=lesson).delete()
        comments = self.comment_sets[(index - 1) % len(self.comment_sets)]
        base_date = datetime.date(2026, 9, 8 if lesson.thing.day == "Tue" else 9)
        for offset, content in enumerate(comments):
            lesson_date = base_date + datetime.timedelta(days=7 * offset)
            StudentComment.objects.create(
                student=child,
                lesson=lesson,
                lesson_date=lesson_date,
                content=content,
                created_by=teacher,
            )
            StudentLessonNote.objects.create(
                student=child,
                lesson=lesson,
                lesson_date=lesson_date,
                note=f"AI test note {offset + 1}: {content}",
                created_by=teacher,
            )

    def _adjustment(self, index, parent, child, order, course, term, teacher):
        CourseAdjustment.objects.filter(
            student=child,
            request_source="admin",
            admin_note="AI project synthetic makeup record",
        ).delete()
        if index not in {2, 5, 8, 9}:
            return

        original_date = datetime.date(2026, 9, 15 if course.day == "Tue" else 16)
        CourseAdjustment.objects.create(
            student=child,
            parent=parent,
            original_order=order,
            original_class=course,
            original_lesson_date=original_date,
            original_day=course.day,
            original_time=course.time.time,
            original_term=term,
            request_type="makeup_class",
            request_reason="Missed lesson requires makeup support.",
            request_source="admin",
            status="completed" if index != 9 else "makeup_available",
            selected_target_class=course if index != 9 else None,
            selected_target_date=original_date + datetime.timedelta(days=7) if index != 9 else None,
            selected_target_day=course.day if index != 9 else None,
            selected_target_time=course.time.time if index != 9 else None,
            selected_target_room=course.tag.title if index != 9 else None,
            admin_note="AI project synthetic makeup record",
            approved_by=teacher,
            approved_time=datetime.datetime(2026, 9, 18, 12, 0),
        )
