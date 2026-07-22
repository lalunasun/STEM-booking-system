import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from CSAA.models import Child


class Command(BaseCommand):
    help = "Export the 10-student local AI project dataset as readable JSON."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            default="../outputs/ai_project/ai_student_learning_profile_10.json",
            help="Output path, relative to the backend directory unless absolute.",
        )

    def handle(self, *args, **options):
        output_path = Path(options["output"])
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        students = (
            Child.objects.filter(parent__username__startswith="ai_parent_")
            .select_related("parent")
            .prefetch_related(
                "child_order__thing__classification",
                "child_order__thing__tag",
                "child_order__thing__time",
                "child_order__term",
                "attendance_records__lesson__thing",
                "admin_comments__lesson__thing",
                "course_adjustments__original_class",
                "course_adjustments__selected_target_class",
            )
            .annotate(
                attendance_total=Count("attendance_records", distinct=True),
                absent_total=Count(
                    "attendance_records",
                    filter=Q(attendance_records__is_absent=True),
                    distinct=True,
                ),
            )
            .order_by("parent__username")
        )

        records = [self._student_record(position, student) for position, student in enumerate(students, 1)]
        payload = {
            "dataset": {
                "name": "CSAA AI Student Learning Profile - 10 Student Test",
                "version": "1.0",
                "privacy": "Synthetic demo data only. No real student information.",
                "purpose": "Small local test for Python analysis, AI comment summary, and support recommendations.",
                "student_count": len(records),
            },
            "students": records,
        }

        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Exported {len(records)} students to {output_path}"))

    def _student_record(self, position, student):
        order = student.child_order.filter(status=6).select_related(
            "thing__classification", "thing__tag", "thing__time", "term"
        ).first()
        attendance = list(student.attendance_records.select_related("lesson__thing").order_by("lesson_date"))
        comments = list(student.admin_comments.select_related("lesson__thing").order_by("lesson_date", "id"))
        adjustments = list(
            student.course_adjustments.select_related("original_class", "selected_target_class").order_by(
                "original_lesson_date", "id"
            )
        )

        attended_total = student.attendance_total - student.absent_total
        attendance_rate = round(attended_total / student.attendance_total, 3) if student.attendance_total else None
        completed_makeups = sum(item.status == "completed" for item in adjustments)
        pending_makeups = sum(item.status in {"pending", "approved", "makeup_available"} for item in adjustments)

        return {
            "student_id": f"AI-{position:03d}",
            "student": {
                "name": student.name,
                "age": student.age,
                "gender": student.gender,
                "parent_reference": student.parent.username if student.parent else None,
            },
            "current_course": {
                "name": order.thing.title if order and order.thing else None,
                "category": order.thing.classification.title if order and order.thing and order.thing.classification else None,
                "term": order.term.title if order and order.term else None,
                "day": order.thing.day if order and order.thing else None,
                "time": order.thing.time.time if order and order.thing and order.thing.time else None,
                "room": order.thing.tag.title if order and order.thing and order.thing.tag else None,
            },
            "attendance_summary": {
                "recorded_lessons": student.attendance_total,
                "attended": attended_total,
                "absent": student.absent_total,
                "attendance_rate": attendance_rate,
                "completed_makeups": completed_makeups,
                "pending_makeups": pending_makeups,
            },
            "attendance_records": [
                {
                    "date": item.lesson_date.isoformat(),
                    "course": item.lesson.thing.title if item.lesson and item.lesson.thing else None,
                    "status": "absent" if item.is_absent else "present",
                }
                for item in attendance
            ],
            "makeup_records": [
                {
                    "original_date": item.original_lesson_date.isoformat() if item.original_lesson_date else None,
                    "original_course": item.original_class.title if item.original_class else None,
                    "status": item.status,
                    "target_date": item.selected_target_date.isoformat() if item.selected_target_date else None,
                    "target_course": item.selected_target_class.title if item.selected_target_class else None,
                }
                for item in adjustments
            ],
            "teacher_comments": [
                {
                    "date": item.lesson_date.isoformat() if item.lesson_date else None,
                    "course": item.lesson.thing.title if item.lesson and item.lesson.thing else None,
                    "comment": item.content,
                }
                for item in comments
            ],
            "ai_input": {
                "comment_text": "\n".join(item.content for item in comments),
                "review_required": True,
                "suggested_tasks": [
                    "summarize_learning_progress",
                    "extract_strengths_and_needs_review_tags",
                    "identify_support_signal",
                    "recommend_next_teacher_action",
                ],
            },
        }
