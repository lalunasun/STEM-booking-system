import datetime
import re

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from CSAA.models import Child, Course, Lesson, Order, Tag, Term, Thing, Time


COURSE_NAMES = {
    'Wedo': 'WeDo',
    'WeDo': 'WeDo',
    'Scratch Junior': 'Scratch JR',
    'Maths': 'Spark Maths',
    'Scartch': 'Scratch',
    'Dr.Joel': "Dr. Joel's Writing Skills & Public Speaking",
}

ROOM_NAMES = {
    'room1': 'Room 1',
    'room3': 'Room 3',
    'room4': 'Room 4',
    'room5': 'Room 5',
    'library': 'Library',
    'vexiqlab': 'VEX IQ Lab',
    'vexv5lab': 'VEX V5 Lab',
    'v5lab': 'VEX V5 Lab',
}

ROOM_CAPACITIES = {
    'Room 1': 4,
    'Room 3': 8,
    'Room 4': 4,
    'Room 5': 4,
    'Library': 6,
    'VEX IQ Lab': 6,
    'VEX V5 Lab': 6,
    'Meeting Room': 8,
}

# These dates follow the school term rules already discussed. They remain editable
# in the admin Terms page after import.
TERM_DEFAULTS = {
    '2025-26 Full Year': (datetime.date(2025, 9, 8), datetime.date(2026, 12, 20)),
    '2026 Full Year': (datetime.date(2026, 9, 8), datetime.date(2027, 6, 27)),
    '2026-27 Full Year': (datetime.date(2026, 9, 8), datetime.date(2027, 6, 27)),
    '2026 Fall': (datetime.date(2026, 9, 8), datetime.date(2026, 12, 20)),
}


def _text(value):
    return str(value or '').strip()


def _date_time(value, end=False):
    date_value = value
    if isinstance(value, datetime.datetime):
        date_value = value.date()
    if not isinstance(date_value, datetime.date):
        raise ValueError(f'Invalid date: {value}')
    return datetime.datetime.combine(
        date_value,
        datetime.time.max if end else datetime.time.min,
    )


def _normalize_course(value):
    title = _text(value)
    return COURSE_NAMES.get(title, title)


def _normalize_room(value):
    title = _text(value)
    return ROOM_NAMES.get(re.sub(r'\s+', '', title).lower(), title)


def _normalize_time(value):
    raw = _text(value).replace('：', ':').replace('–', '-').replace('—', '-')
    raw = re.sub(r'\s+', '', raw).replace('4:300', '4:30')
    parts = raw.split('-', 1)
    if len(parts) != 2:
        raise ValueError(f'Invalid time: {value}')

    normalized = []
    for part in parts:
        match = re.fullmatch(r'(\d{1,2}):(\d{2})', part)
        if not match:
            raise ValueError(f'Invalid time: {value}')
        hour = int(match.group(1))
        minute = int(match.group(2))
        if hour < 8:
            hour += 12
        if hour > 23 or minute > 59:
            raise ValueError(f'Invalid time: {value}')
        normalized.append(f'{hour:02d}:{minute:02d}')
    return '-'.join(normalized)


class Command(BaseCommand):
    help = 'Import confirmed regular student schedule rows from the school workbook.'

    def add_arguments(self, parser):
        parser.add_argument('--file', required=True, help='Path to the .xlsx workbook')
        parser.add_argument('--apply', action='store_true', help='Write imported data; otherwise run a dry-run')

    def _term(self, title, cache, missing):
        if title in cache:
            return cache[title]
        term = Term.objects.filter(title=title).first()
        if not term:
            dates = TERM_DEFAULTS.get(title)
            if not dates:
                missing.append(title)
                return None
            if not self.apply:
                missing.append(title)
                return None
            start, end = dates
            term = Term.objects.create(
                title=title,
                expect_time=_date_time(start),
                return_time=_date_time(end, end=True),
            )
        cache[title] = term
        return term

    def _room(self, title):
        room = Tag.objects.filter(title__iexact=title).first()
        if not room:
            compact_title = re.sub(r'\s+', '', title).lower()
            room = next(
                (
                    candidate for candidate in Tag.objects.all()
                    if re.sub(r'\s+', '', _text(candidate.title)).lower() == compact_title
                ),
                None,
            )
        if not room:
            room = Tag.objects.create(title=title, seat=ROOM_CAPACITIES.get(title))
        elif room.title != title:
            room.title = title
            room.save(update_fields=['title'])
        capacity = ROOM_CAPACITIES.get(title)
        if capacity is not None and room.seat != capacity:
            room.seat = capacity
            room.save(update_fields=['seat'])
        return room

    def _thing(self, course, day, time_text, room):
        time, _ = Time.objects.get_or_create(time=time_text)
        thing, _ = Thing.objects.get_or_create(
            title=course,
            day=day,
            time=time,
            tag=room,
            defaults={'price': '', 'status': '0'},
        )
        Course.objects.get_or_create(title=course)
        if thing.status != '0':
            thing.status = '0'
            thing.save(update_fields=['status'])
        Lesson.objects.get_or_create(thing=thing)
        return thing

    def _order_number(self, review_no, excel_row):
        if review_no not in (None, ''):
            try:
                return f'SCHIMP{int(float(review_no)):04d}'
            except (TypeError, ValueError):
                pass
        # Some confirmed rows have no review number. The worksheet row keeps
        # their import idempotent without inventing a review number.
        return f'SCHX{excel_row:08d}'

    def _child(self, name):
        child = Child.objects.filter(name=name, parent__isnull=True).first()
        if child:
            return child, False
        child = Child.objects.filter(name=name).first()
        if child:
            return child, False
        return Child.objects.create(name=name), True

    def _import_row(self, row, headers, term_cache, missing_terms, stats, excel_row, seen_keys):
        value = lambda key: row[headers[key]] if headers[key] < len(row) else None
        review_no = value('Review no.')
        course_raw = _text(value('课程名称'))
        room_raw = _text(value('Room'))
        term_title = _text(value('Term名称'))
        enrollment = _text(value('Enrollment status')).lower()

        if course_raw == 'Dr.Joel':
            room_raw = 'Meeting Room'
        elif room_raw == 'Other':
            stats['deferred_special'] += 1
            return
        if term_title in {'Trial', 'Trial Class'}:
            stats['deferred_trial'] += 1
            return
        if ',' in course_raw:
            stats['deferred_composite'] += 1
            stats['warnings'].append(
                f'row {excel_row}: composite course needs confirmation: {course_raw}'
            )
            return
        if not term_title:
            stats['skipped_missing_term'] += 1
            return

        try:
            course = _normalize_course(course_raw)
            room_title = _normalize_room(room_raw)
            time_text = _normalize_time(value('time'))
            term = self._term(term_title, term_cache, missing_terms)
        except ValueError as error:
            stats['skipped_invalid'] += 1
            stats['warnings'].append(f'row {review_no}: {error}')
            return
        if not term:
            stats['skipped_missing_term'] += 1
            return

        enrollment_key = (
            _text(value('Tentative student name')).casefold(),
            term_title.casefold(),
            course.casefold(),
            _text(value('Day')).casefold(),
            time_text,
            room_title.casefold(),
        )
        if enrollment_key in seen_keys:
            stats['duplicate_rows'] += 1
            stats['warnings'].append(
                f'row {excel_row}: duplicate enrollment skipped for {enrollment_key[0]}'
            )
            return
        seen_keys.add(enrollment_key)

        if not self.apply:
            stats['preview'] += 1
            if time_text != re.sub(r'\s+', '', _text(value('time'))):
                stats['normalized_times'] += 1
            return

        room = self._room(room_title)
        thing = self._thing(course, _text(value('Day'))[:3].title(), time_text, room)
        child, created = self._child(_text(value('Tentative student name')))
        if created:
            stats['created_children'] += 1
        else:
            stats['matched_children'] += 1

        order_number = self._order_number(review_no, excel_row)
        order, _ = Order.objects.update_or_create(
            order_number=order_number,
            defaults={
                'user': child.parent,
                'thing': thing,
                'count': 1,
                'num': 0,
                'child': child,
                'expect_time': term.expect_time,
                'return_time': term.return_time,
                'term': term,
                'amount': '',
                'status': 6 if enrollment == 'active' else 1,
                'receiver_name': '',
                'receiver_phone': '',
                'remark': f'School import row {review_no or excel_row}',
            },
        )
        lesson = Lesson.objects.get_or_create(thing=thing)[0]
        if order.status == 6:
            lesson.students.add(child)
            stats['scheduled_orders'] += 1
        else:
            lesson.students.remove(child)
            stats['pending_orders'] += 1
        stats['imported_orders'] += 1

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            from openpyxl import load_workbook
        except ImportError as error:
            raise CommandError('openpyxl is required to import .xlsx files') from error

        try:
            workbook = load_workbook(options['file'], data_only=True, read_only=True)
            sheet = workbook['Student Schedule Review']
        except Exception as error:
            raise CommandError(f'Cannot read workbook: {error}') from error

        rows = [tuple(list(row) + [None] * 30) for row in sheet.iter_rows(values_only=True)]
        if not rows:
            raise CommandError('The worksheet is empty')
        raw_headers = rows[0]
        headers = {_text(value): index for index, value in enumerate(raw_headers)}
        required = {
            'Review no.', 'Review status', 'Tentative student name', 'Term名称',
            '课程名称', 'Day', 'time', 'Room', 'Enrollment status',
        }
        missing_headers = sorted(required - set(headers))
        if missing_headers:
            raise CommandError(f'Missing headers: {", ".join(missing_headers)}')

        self.apply = options['apply']
        term_cache = {}
        missing_terms = []
        seen_keys = set()
        stats = {
            'confirmed': 0,
            'preview': 0,
            'imported_orders': 0,
            'scheduled_orders': 0,
            'pending_orders': 0,
            'created_children': 0,
            'matched_children': 0,
            'deferred_special': 0,
            'deferred_trial': 0,
            'deferred_composite': 0,
            'duplicate_rows': 0,
            'skipped_missing_term': 0,
            'skipped_invalid': 0,
            'normalized_times': 0,
            'warnings': [],
        }

        for excel_row, row in enumerate(rows[1:], start=2):
            review_status = _text(row[headers['Review status']] if headers['Review status'] < len(row) else '').lower()
            if review_status != 'confirmed':
                continue
            stats['confirmed'] += 1
            self._import_row(
                row, headers, term_cache, missing_terms, stats,
                excel_row, seen_keys,
            )

        if missing_terms:
            stats['warnings'].append(
                'Missing term configuration: ' + ', '.join(sorted(set(missing_terms)))
            )

        mode = 'APPLIED' if self.apply else 'DRY-RUN'
        self.stdout.write(self.style.SUCCESS(f'{mode}: {stats["confirmed"]} confirmed rows scanned'))
        for key in (
            'preview', 'imported_orders', 'scheduled_orders', 'pending_orders',
            'created_children', 'matched_children', 'deferred_special',
            'deferred_trial', 'deferred_composite', 'duplicate_rows',
            'skipped_missing_term', 'skipped_invalid',
        ):
            self.stdout.write(f'{key}: {stats[key]}')
        if stats['normalized_times']:
            self.stdout.write(f'normalized_times: {stats["normalized_times"]}')
        for warning in stats['warnings']:
            self.stdout.write(self.style.WARNING(warning))
        if not self.apply:
            self.stdout.write('Use --apply to write the eligible rows to the local database.')
