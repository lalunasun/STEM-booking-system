from collections import defaultdict
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from CSAA.models import Course, RoomCoursePermission, Tag, Term, Thing


class Command(BaseCommand):
    help = 'Merge existing active room courses into permissions for terms active on a date.'

    def add_arguments(self, parser):
        parser.add_argument('--as-of', default=date.today().isoformat())
        parser.add_argument('--allow', action='append', default=[], metavar='ROOM=COURSE')
        parser.add_argument('--apply', action='store_true', help='Write changes; otherwise preview only.')

    def handle(self, *args, **options):
        try:
            as_of = date.fromisoformat(options['as_of'])
        except ValueError as exc:
            raise CommandError('Use YYYY-MM-DD for --as-of') from exc

        terms = list(Term.objects.filter(
            expect_time__date__lte=as_of, return_time__date__gte=as_of,
        ).order_by('id'))
        if not terms:
            raise CommandError('No terms active on that date')

        rooms = list(Tag.objects.order_by('id'))
        room_by_title = defaultdict(list)
        for room in rooms:
            room_by_title[(room.title or '').strip().casefold()].append(room)

        catalog = {course.title.strip().casefold(): course for course in Course.objects.filter(active=True)}
        extra = defaultdict(set)
        for assignment in options['allow']:
            room_title, separator, course_title = assignment.partition('=')
            matches = room_by_title[room_title.strip().casefold()]
            course = catalog.get(course_title.strip().casefold())
            if not separator or len(matches) != 1 or course is None:
                raise CommandError(f'Invalid --allow: {assignment}')
            extra[matches[0].id].add(course.id)

        current_rules = list(RoomCoursePermission.objects.filter(term__in=terms).prefetch_related('courses'))
        existing = {(rule.room_id, rule.term_id): rule for rule in current_rules}
        room_courses = defaultdict(set)
        for room_id, title in Thing.objects.filter(status='0', tag__isnull=False).values_list('tag_id', 'title').distinct():
            if not title or title.strip().casefold() not in catalog:
                raise CommandError(f'Active class has no active catalog course: room {room_id}, {title}')
            room_courses[room_id].add(catalog[title.strip().casefold()].id)
        for rule in current_rules:
            room_courses[rule.room_id].update(rule.courses.values_list('id', flat=True))
        for room_id, course_ids in extra.items():
            room_courses[room_id].update(course_ids)

        additions = []
        for room in rooms:
            if not room_courses[room.id]:
                continue
            for term in terms:
                rule = existing.get((room.id, term.id))
                current_ids = set(rule.courses.values_list('id', flat=True)) if rule else set()
                missing_ids = room_courses[room.id] - current_ids
                if rule is None or missing_ids:
                    additions.append((room, term, rule, missing_ids))

        self.stdout.write(f'Active terms: {len(terms)}; rooms with courses: {sum(bool(v) for v in room_courses.values())}; rules to create/update: {len(additions)}')
        for room, term, rule, missing_ids in additions:
            names = ', '.join(sorted(Course.objects.filter(id__in=missing_ids).values_list('title', flat=True)))
            self.stdout.write(f'{term.title} | {room.title} | {"create" if rule is None else "extend"} | {names}')

        if not options['apply']:
            self.stdout.write('Preview only. Pass --apply to save.')
            return

        with transaction.atomic():
            for room, term, rule, missing_ids in additions:
                if rule is None:
                    rule = RoomCoursePermission.objects.create(room=room, term=term)
                if missing_ids:
                    rule.courses.add(*Course.objects.filter(id__in=missing_ids))
        self.stdout.write('Permissions updated. Existing classes, orders, and students were not modified.')
