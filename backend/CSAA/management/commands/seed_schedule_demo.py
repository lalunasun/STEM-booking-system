import datetime

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from CSAA.models import (
    Child,
    CourseAdjustment,
    Lesson,
    Order,
    Tag,
    Term,
    Thing,
    Time,
    TrialRequest,
    User,
)
from CSAA.utils import md5value


class Command(BaseCommand):
    help = "Create an idempotent set of current schedule demo data."

    term_title = "2026 Summer Demo"
    password = "demo123"

    course_specs = {
        "tue_creator": ("Creator", "Tue", "16:00-17:00"),
        "tue_wedo": ("Wedo", "Tue", "17:00-18:00"),
        "wed_creator": ("Creator", "Wed", "16:00-17:00"),
        "thu_scratch": ("Scratch", "Thu", "17:00-18:00"),
        "fri_python": ("Python", "Fri", "18:00-19:00"),
        "sat_creator": ("Creator", "Sat", "9:00-10:00"),
        "sat_wedo": ("Wedo", "Sat", "10:00-11:00"),
        "sun_creator": ("Creator", "Sun", "9:00-10:00"),
        "sun_wedo": ("Wedo", "Sun", "10:00-11:00"),
    }

    students = [
        ("schedule_demo_parent_01", "Alice Demo", 7),
        ("schedule_demo_parent_02", "Ben Demo", 8),
        ("schedule_demo_parent_03", "Chloe Demo", 9),
        ("schedule_demo_parent_04", "Daniel Demo", 10),
        ("schedule_demo_parent_05", "Ethan Demo", 11),
        ("schedule_demo_parent_06", "Fiona Demo", 12),
        ("schedule_demo_parent_07", "Grace Demo", 13),
        ("schedule_demo_parent_08", "Henry Demo", 14),
    ]

    def _course(self, title, day, time):
        course = (
            Thing.objects.filter(
                title=title,
                day=day,
                time__time=time,
                status="0",
            )
            .select_related("time", "tag")
            .first()
        )
        if not course:
            raise CommandError(
                f"Missing active course: {title}, {day}, {time}. "
                "Create the class before seeding schedule data."
            )
        Lesson.objects.get_or_create(thing=course)
        return course

    def _ensure_weekend_courses(self):
        rooms = Tag.objects.all().order_by("title")
        weekend_times = [
            time
            for time in Time.objects.all()
            if self._start_minutes(time.time) is not None
            and 9 * 60 <= self._start_minutes(time.time) < 18 * 60
            and self._start_minutes(time.time) != 12 * 60
        ]
        weekend_times.sort(key=lambda item: self._start_minutes(item.time))

        Thing.objects.filter(
            day__in=["Sat", "Sun"],
            time__time="12:00-13:00",
        ).update(status="1")

        for day in ["Sat", "Sun"]:
            for room in rooms:
                template = (
                    Thing.objects.filter(tag=room, status="0")
                    .exclude(day__in=["Sat", "Sun"])
                    .select_related("classification", "tag")
                    .order_by("id")
                    .first()
                )
                if not template:
                    continue

                for time in weekend_times:
                    course, _ = Thing.objects.update_or_create(
                        title=template.title,
                        day=day,
                        time=time,
                        tag=room,
                        defaults={
                            "classification": template.classification,
                            "cover": template.cover.name if template.cover else None,
                            "description": template.description,
                            "price": template.price,
                            "repertory": template.repertory,
                            "status": "0",
                        },
                    )
                    Lesson.objects.get_or_create(thing=course)

    @staticmethod
    def _start_minutes(value):
        try:
            start = str(value).split("-", 1)[0]
            hour, minute = start.split(":", 1)
            return int(hour) * 60 + int(minute)
        except (TypeError, ValueError):
            return None

    def _parent_and_child(self, username, child_name, age, index):
        parent, _ = User.objects.update_or_create(
            username=username,
            defaults={
                "password": md5value(self.password),
                "role": "1",
                "status": "0",
                "nickname": f"Demo Parent {index:02d}",
                "mobile": f"41655501{index:02d}",
                "email": f"{username}@example.test",
            },
        )
        child, _ = Child.objects.update_or_create(
            parent=parent,
            name=child_name,
            defaults={"age": age},
        )
        return parent, child

    def _scheduled_order(self, number, parent, child, course, term, start, end):
        order, _ = Order.objects.update_or_create(
            order_number=number,
            defaults={
                "user": parent,
                "thing": course,
                "count": 1,
                "num": 10,
                "child": child,
                "expect_time": start,
                "return_time": end,
                "term": term,
                "amount": course.price or "400",
                "status": 6,
                "pay_time": datetime.datetime(2026, 6, 15, 10, 0),
                "receiver_name": parent.nickname,
                "receiver_phone": parent.mobile,
                "remark": "Schedule demo data",
            },
        )
        lesson, _ = Lesson.objects.get_or_create(thing=course)
        lesson.students.add(child)
        lesson.students_num = Order.objects.filter(
            thing=course,
            status=6,
            child__isnull=False,
        ).count()
        lesson.save(update_fields=["students_num"])
        return order

    def _trial_order(self, number, parent, child, term, start, end):
        order, _ = Order.objects.update_or_create(
            order_number=number,
            defaults={
                "user": parent,
                "thing": None,
                "count": 1,
                "num": 3,
                "child": child,
                "expect_time": start,
                "return_time": end,
                "term": term,
                "amount": "98",
                "status": 6,
                "pay_time": datetime.datetime(2026, 6, 15, 10, 0),
                "receiver_name": parent.nickname,
                "receiver_phone": parent.mobile,
                "remark": "Trial Package",
            },
        )
        return order

    def _assert_capacity(self):
        occupied_slots = (
            Thing.objects.filter(
                tag__isnull=False,
                time__isnull=False,
                day__isnull=False,
            )
            .values(
                "tag_id",
                "tag__title",
                "tag__seat",
                "day",
                "time_id",
                "time__time",
            )
            .distinct()
        )

        errors = []
        for slot in occupied_slots:
            same_slot = Thing.objects.filter(
                tag_id=slot["tag_id"],
                day=slot["day"],
                time_id=slot["time_id"],
            )
            order_count = Order.objects.filter(
                thing__in=same_slot,
                child__isnull=False,
                status__in=[2, 6],
            )
            makeup_count = CourseAdjustment.objects.filter(
                selected_target_class__in=same_slot,
                request_type="makeup_class",
                status="completed",
            ).count()
            trial_count = TrialRequest.objects.filter(
                Q(robotics_class__in=same_slot)
                | Q(coding_class__in=same_slot)
                | Q(math_class__in=same_slot),
                package_order__status__in=[2, 6],
                status__in=["approved", "scheduled"],
            ).count()
            occupied = order_count.count() + makeup_count + trial_count
            capacity = int(slot["tag__seat"])
            if occupied > capacity:
                errors.append(
                    f'{slot["tag__title"]} {slot["day"]} '
                    f'{slot["time__time"]}: {occupied}/{capacity}'
                )

        if errors:
            raise CommandError(
                "Schedule demo would exceed room capacity: " + "; ".join(errors)
            )

    @transaction.atomic
    def handle(self, *args, **options):
        start = datetime.datetime(2026, 6, 1, 0, 0)
        end = datetime.datetime(2026, 8, 31, 23, 59)
        Order.objects.filter(
            status__in=[2, 6],
            return_time__lt=start,
        ).update(status=8)

        term, _ = Term.objects.update_or_create(
            title=self.term_title,
            defaults={
                "expect_time": start,
                "return_time": end,
                "price": "400",
            },
        )

        self._ensure_weekend_courses()
        courses = {
            key: self._course(*spec)
            for key, spec in self.course_specs.items()
        }
        people = [
            self._parent_and_child(username, child_name, age, index)
            for index, (username, child_name, age) in enumerate(self.students, 1)
        ]

        assignments = [
            ("SD260621001", 0, "tue_creator"),
            ("SD260621002", 1, "tue_creator"),
            ("SD260621003", 2, "tue_creator"),
            ("SD260621004", 3, "tue_creator"),
            ("SD260621005", 4, "tue_wedo"),
            ("SD260621006", 5, "wed_creator"),
            ("SD260621007", 6, "thu_scratch"),
            ("SD260621009", 0, "sat_creator"),
            ("SD260621010", 1, "sat_wedo"),
            ("SD260621011", 2, "sun_creator"),
            ("SD260621012", 3, "sun_wedo"),
        ]

        orders = {}
        for number, person_index, course_key in assignments:
            parent, child = people[person_index]
            orders[number] = self._scheduled_order(
                number,
                parent,
                child,
                courses[course_key],
                term,
                start,
                end,
            )

        admin = User.objects.filter(username="test", role="0").first()
        chloe_parent, chloe = people[2]
        cancel, _ = CourseAdjustment.objects.update_or_create(
            original_order=orders["SD260621003"],
            request_type="cancel_class",
            original_lesson_date=datetime.date(2026, 6, 23),
            defaults={
                "student": chloe,
                "parent": chloe_parent,
                "original_class": courses["tue_creator"],
                "original_day": "Tue",
                "original_time": "16:00-17:00",
                "original_term": term,
                "request_reason": "Demo absence",
                "request_source": "parent",
                "status": "approved",
                "approved_by": admin,
                "approved_time": datetime.datetime(2026, 6, 20, 12, 0),
            },
        )

        CourseAdjustment.objects.update_or_create(
            source_adjustment=cancel,
            request_type="makeup_class",
            defaults={
                "student": chloe,
                "parent": chloe_parent,
                "original_order": orders["SD260621003"],
                "original_class": courses["tue_creator"],
                "original_lesson_date": datetime.date(2026, 6, 23),
                "original_day": "Tue",
                "original_time": "16:00-17:00",
                "original_term": term,
                "request_reason": "Demo makeup",
                "request_source": "admin",
                "status": "completed",
                "selected_target_class": courses["wed_creator"],
                "selected_target_date": datetime.date(2026, 6, 24),
                "selected_target_day": "Wed",
                "selected_target_time": "16:00-17:00",
                "selected_target_room": courses["wed_creator"].tag.title,
                "approved_by": admin,
                "approved_time": datetime.datetime(2026, 6, 20, 12, 30),
            },
        )

        trial_parent, trial_child = people[7]
        trial_order = self._trial_order(
            "SD260621008",
            trial_parent,
            trial_child,
            term,
            start,
            end,
        )
        TrialRequest.objects.update_or_create(
            parent=trial_parent,
            child=trial_child,
            package_order=trial_order,
            defaults={
                "robotics_class": courses["thu_scratch"],
                "coding_class": courses["fri_python"],
                "math_class": courses["tue_wedo"],
                "status": "scheduled",
                "parent_note": "Schedule demo trial package",
                "admin_note": "Created by seed_schedule_demo",
            },
        )

        for lesson in Lesson.objects.filter(thing__isnull=False):
            lesson.students_num = Order.objects.filter(
                thing=lesson.thing,
                status=6,
                child__isnull=False,
            ).count()
            lesson.save(update_fields=["students_num"])

        self._assert_capacity()

        self.stdout.write(
            self.style.SUCCESS(
                "Schedule demo ready: 1 term, 8 parents, 8 students, "
                "12 orders, weekend classes, 1 absence, 1 makeup, "
                "and 1 trial package."
            )
        )
