import datetime
import csv
import io
import re
from collections import defaultdict
from zoneinfo import ZoneInfo

from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, authentication_classes

from CSAA.auth.authentication import AdminTokenAuthtication
from CSAA.handler import APIResponse
from CSAA.models import CampAttendance, CampEnrollment, CampWaiver, Child, Order, Tag, Term, User

try:
    import openpyxl
except ImportError:
    openpyxl = None


CAMP_START_HOUR = 9
CAMP_END_HOUR = 16
CAMP_LATE_PICKUP_TIME = datetime.time(16, 30)
CAMP_WAIVER_REQUIRED = False
CAMP_WAIVER_VERSION = '2026-summer-v1'
CAMP_LOCAL_TZ = ZoneInfo('America/Toronto')
ROOM_DISPLAY_ORDER = {
    'room1': 0,
    'room3': 1,
    'room4': 2,
    'room5': 3,
    'library': 4,
    'vexiqlab': 5,
    'vexv5lab': 6,
    'v5lab': 6,
    'meetingroom': 90,
    'frclab': 91,
}
LEGACY_STUDENT_NAME_PATTERN = re.compile(r'^(.+)_kid_\d+(?:_age_\d+)?$', re.IGNORECASE)
WEEKDAY_SHEET_OFFSETS = {
    'monday': 0,
    'mon': 0,
    'tuesday': 1,
    'tue': 1,
    'wednesday': 2,
    'wed': 2,
    'thursday': 3,
    'thu': 3,
    'friday': 4,
    'fri': 4,
    'saturday': 5,
    'sat': 5,
    'sunday': 6,
    'sun': 6,
}


def _client_ip(request):
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _camp_local_now():
    return datetime.datetime.now(CAMP_LOCAL_TZ).replace(tzinfo=None)


def _parse_date(value):
    if not value:
        return datetime.date.today()
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return None


def _day_code(target_date):
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][target_date.weekday()]


def _scheduled_orders(target_date):
    orders = Order.objects.filter(
        child__isnull=False,
        thing__isnull=False,
        thing__status='0',
        thing__day=_day_code(target_date),
        term__isnull=False,
        expect_time__date__lte=target_date,
        return_time__date__gte=target_date,
        status=6,
    ).select_related(
        'child',
        'child__parent',
        'term',
        'thing',
        'thing__time',
        'thing__tag',
    ).order_by('thing__tag__title', 'thing__time__time', 'child__name')

    camp_orders = orders.filter(term__title__icontains='camp')
    return camp_orders if camp_orders.exists() else orders


def _camp_enrollments(target_date):
    return CampEnrollment.objects.filter(
        status='active',
        term__expect_time__date__lte=target_date,
        term__return_time__date__gte=target_date,
    ).select_related(
        'student',
        'parent',
        'term',
        'default_room',
        'sign_out_room',
    ).order_by('default_room__title', 'student__name')


def _attendance_map(target_date, child_ids):
    records = CampAttendance.objects.filter(
        attendance_date=target_date,
        student_id__in=child_ids,
    ).select_related('sign_out_room')
    return {record.student_id: record for record in records}


def _serialize_record(record):
    if not record:
        return {
            'status': 'not_arrived',
            'sign_in_time': None,
            'sign_out_time': None,
            'late_pickup': False,
            'late_pickup_minutes': 0,
            'note': '',
        }
    late_pickup = False
    late_pickup_minutes = 0
    if record.sign_out_time and record.sign_out_time.time() > CAMP_LATE_PICKUP_TIME:
        late_pickup = True
        cutoff = datetime.datetime.combine(record.sign_out_time.date(), CAMP_LATE_PICKUP_TIME)
        late_pickup_minutes = max(1, int((record.sign_out_time.replace(tzinfo=None) - cutoff).total_seconds() // 60))
    return {
        'id': record.id,
        'status': record.status,
        'sign_in_time': record.sign_in_time.isoformat() if record.sign_in_time else None,
        'sign_out_time': record.sign_out_time.isoformat() if record.sign_out_time else None,
        'sign_out_room_id': record.sign_out_room_id,
        'sign_out_room_name': record.sign_out_room.title if record.sign_out_room else '',
        'late_pickup': late_pickup,
        'late_pickup_minutes': late_pickup_minutes,
        'note': record.note,
    }


def _empty_attendance_summary():
    return {
        'total_records': 0,
        'signed_in_days': 0,
        'signed_out_days': 0,
        'late_arrivals': 0,
        'late_pickups': 0,
        'absent_days': 0,
        'recent': [],
    }


def _build_attendance_summary(records, limit=5):
    signed_in_statuses = {'signed_in', 'late', 'signed_out', 'early_pickup'}
    signed_out_statuses = {'signed_out', 'early_pickup'}
    ordered_records = sorted(records, key=lambda record: record.attendance_date, reverse=True)[:limit]

    return {
        'total_records': len(records),
        'signed_in_days': sum(1 for record in records if record.sign_in_time or record.status in signed_in_statuses),
        'signed_out_days': sum(1 for record in records if record.sign_out_time or record.status in signed_out_statuses),
        'late_arrivals': sum(1 for record in records if record.status == 'late'),
        'late_pickups': sum(1 for record in records if _serialize_record(record).get('late_pickup')),
        'absent_days': sum(1 for record in records if record.status == 'absent'),
        'recent': [
            {
                'date': record.attendance_date.isoformat(),
                'status': record.status,
                'sign_in_time': record.sign_in_time.isoformat() if record.sign_in_time else None,
                'sign_out_time': record.sign_out_time.isoformat() if record.sign_out_time else None,
                'sign_out_room_id': record.sign_out_room_id,
                'sign_out_room_name': record.sign_out_room.title if record.sign_out_room else '',
                'late_pickup': _serialize_record(record).get('late_pickup'),
                'late_pickup_minutes': _serialize_record(record).get('late_pickup_minutes'),
            }
            for record in ordered_records
        ],
    }


def _attendance_summary_map(student_term_pairs):
    pairs = {(student_id, term_id) for student_id, term_id in student_term_pairs if student_id}
    if not pairs:
        return {}

    student_ids = {student_id for student_id, _term_id in pairs}
    term_ids = {term_id for _student_id, term_id in pairs if term_id}
    records = CampAttendance.objects.filter(student_id__in=student_ids).select_related('sign_out_room')
    if term_ids:
        records = records.filter(term_id__in=term_ids)

    grouped = defaultdict(list)
    for record in records:
        grouped[(record.student_id, record.term_id)].append(record)

    return {
        pair: _build_attendance_summary(grouped.get(pair, []))
        for pair in pairs
    }


def _has_waiver(student_id, term_id):
    if not student_id or not term_id:
        return False
    return CampWaiver.objects.filter(
        student_id=student_id,
        term_id=term_id,
        waiver_version=CAMP_WAIVER_VERSION,
    ).exists()


def _student_display_name(student):
    if not student:
        return '', True

    stored_name = str(student.name or '').strip()
    parent_username = str(
        student.parent.username if student.parent else ''
    ).strip()
    legacy_match = LEGACY_STUDENT_NAME_PATTERN.fullmatch(stored_name)
    is_legacy_placeholder = bool(
        legacy_match
        and parent_username
        and legacy_match.group(1).lower() == parent_username.lower()
    )
    if not stored_name or is_legacy_placeholder:
        return f'Student name missing (ID {student.id})', True
    return stored_name, False


def _waiver_queryset(target_date=None):
    queryset = CampWaiver.objects.all()
    if target_date:
        queryset = queryset.filter(
            term__expect_time__date__lte=target_date,
            term__return_time__date__gte=target_date,
        )
    return queryset.select_related(
        'student',
        'student__parent',
        'parent',
        'term',
    ).order_by('-signed_time', 'student__name')


def _serialize_waiver(waiver):
    student = waiver.student
    parent = waiver.parent or (student.parent if student else None)
    student_name, student_name_missing = _student_display_name(student)
    return {
        'id': waiver.id,
        'student_id': waiver.student_id,
        'student_name': student_name,
        'student_name_missing': student_name_missing,
        'parent_name': (parent.nickname or parent.username) if parent else '',
        'parent_username': parent.username if parent else '',
        'parent_phone': parent.mobile if parent else '',
        'term_id': waiver.term_id,
        'term_title': waiver.term.title if waiver.term else '',
        'signer_name': waiver.signer_name,
        'waiver_version': waiver.waiver_version,
        'signed_time': waiver.signed_time.isoformat() if waiver.signed_time else '',
        'signed_ip': waiver.signed_ip,
    }


def _student_items(target_date):
    enrollments = list(_camp_enrollments(target_date))
    if enrollments:
        child_ids = [enrollment.student_id for enrollment in enrollments]
        records = _attendance_map(target_date, child_ids)
        summaries = _attendance_summary_map(
            (enrollment.student_id, enrollment.term_id)
            for enrollment in enrollments
        )
        items = []
        for enrollment in enrollments:
            student = enrollment.student
            parent = enrollment.parent or student.parent
            attendance_record = records.get(student.id)
            room = (attendance_record.room if attendance_record and attendance_record.room_id else None) or enrollment.default_room
            sign_out_room = (
                attendance_record.sign_out_room
                if attendance_record and attendance_record.sign_out_room_id
                else None
            ) or enrollment.sign_out_room or room
            student_name, student_name_missing = _student_display_name(student)
            items.append({
                'student_id': student.id,
                'student_name': student_name,
                'student_name_missing': student_name_missing,
                'age': student.age,
                'parent_name': (parent.nickname or parent.username) if parent else '',
                'parent_username': parent.username if parent else '',
                'parent_phone': parent.mobile if parent else '',
                'date': target_date.isoformat(),
                'term_id': enrollment.term_id,
                'term_title': enrollment.term.title if enrollment.term else '',
                'waiver_signed': _has_waiver(student.id, enrollment.term_id),
                'room_id': room.id if room else None,
                'room_name': room.title if room else '',
                'sign_out_room_id': sign_out_room.id if sign_out_room else None,
                'sign_out_room_name': sign_out_room.title if sign_out_room else '',
                'attendance': _serialize_record(attendance_record),
                'attendance_summary': summaries.get((student.id, enrollment.term_id), _empty_attendance_summary()),
                'schedule_items': [{
                    'enrollment_id': enrollment.id,
                    'class_id': None,
                    'class_name': enrollment.term.title if enrollment.term else 'Summer Camp',
                    'time': '09:00-16:00',
                    'room_id': room.id if room else None,
                    'room_name': room.title if room else '',
                    'sign_out_room_id': sign_out_room.id if sign_out_room else None,
                    'sign_out_room_name': sign_out_room.title if sign_out_room else '',
                    'term_id': enrollment.term_id,
                    'term_title': enrollment.term.title if enrollment.term else '',
                }],
            })
        return sorted(items, key=lambda value: (value['room_name'], value['student_name']))

    orders = list(_scheduled_orders(target_date))
    child_ids = list({order.child_id for order in orders if order.child_id})
    records = _attendance_map(target_date, child_ids)
    summaries = _attendance_summary_map(
        (order.child_id, order.term_id)
        for order in orders
        if order.child_id
    )

    grouped = {}
    for order in orders:
        if not order.child_id:
            continue
        child = order.child
        parent = child.parent
        student_name, student_name_missing = _student_display_name(child)
        item = grouped.setdefault(child.id, {
            'student_id': child.id,
            'student_name': student_name,
            'student_name_missing': student_name_missing,
            'age': child.age,
            'parent_name': (parent.nickname or parent.username) if parent else '',
            'parent_username': parent.username if parent else '',
            'parent_phone': parent.mobile if parent else '',
            'date': target_date.isoformat(),
            'term_id': order.term_id,
            'term_title': order.term.title if order.term else '',
            'waiver_signed': _has_waiver(child.id, order.term_id),
            'room_id': order.thing.tag_id if order.thing else None,
            'room_name': order.thing.tag.title if order.thing and order.thing.tag else '',
            'sign_out_room_id': order.thing.tag_id if order.thing else None,
            'sign_out_room_name': order.thing.tag.title if order.thing and order.thing.tag else '',
            'attendance': _serialize_record(records.get(child.id)),
            'attendance_summary': summaries.get((child.id, order.term_id), _empty_attendance_summary()),
            'schedule_items': [],
        })
        item['schedule_items'].append({
            'order_id': order.id,
            'class_id': order.thing_id,
            'class_name': order.thing.title if order.thing else '',
            'time': order.thing.time.time if order.thing and order.thing.time else '',
            'room_id': order.thing.tag_id if order.thing else None,
            'room_name': order.thing.tag.title if order.thing and order.thing.tag else '',
            'sign_out_room_id': order.thing.tag_id if order.thing else None,
            'sign_out_room_name': order.thing.tag.title if order.thing and order.thing.tag else '',
            'term_id': order.term_id,
            'term_title': order.term.title if order.term else '',
        })

    return sorted(grouped.values(), key=lambda value: (value['room_name'], value['student_name']))


def _split_student_name(first_name, last_name):
    first = str(first_name or '').strip()
    last = str(last_name or '').strip()
    return ' '.join([part for part in [first, last] if part]).strip()


def _parse_import_date(row, *keys):
    for key in keys:
        raw_value = row.get(key)
        if isinstance(raw_value, datetime.datetime):
            return raw_value.date()
        if isinstance(raw_value, datetime.date):
            return raw_value
        value = str(raw_value or '').strip()
        if value:
            parsed = parse_date(value)
            if parsed:
                return parsed
            if ' ' in value:
                parsed = parse_date(value.split(' ', 1)[0])
                if parsed:
                    return parsed
            for date_format in ['%m/%d/%Y', '%-m/%-d/%Y', '%m/%d/%y']:
                try:
                    return datetime.datetime.strptime(value, date_format).date()
                except ValueError:
                    continue
    return None


def _row_value(row, *keys):
    for key in keys:
        value = str(row.get(key) or '').strip()
        if value:
            return value
    return ''


def _normalize_import_header(value):
    return re.sub(r'[^a-z0-9]+', '_', str(value or '').strip().lower()).strip('_')


def _has_import_content(row):
    ignored_keys = {'source_sheet', 'source_row'}
    return any(str(value or '').strip() for key, value in row.items() if key not in ignored_keys)


def _read_csv_import_rows(upload):
    try:
        raw_text = upload.read().decode('utf-8-sig')
    except UnicodeDecodeError:
        return None, 'CSV file must be saved as UTF-8'

    rows = []
    for index, row in enumerate(csv.DictReader(io.StringIO(raw_text)), start=2):
        normalized = {
            _normalize_import_header(key): value
            for key, value in row.items()
            if key is not None
        }
        normalized['source_row'] = index
        if _has_import_content(normalized):
            rows.append(normalized)
    return rows, ''


def _read_xlsx_import_rows(upload):
    if openpyxl is None:
        return None, 'Excel import requires openpyxl on the server'

    workbook = openpyxl.load_workbook(upload, data_only=True, read_only=True)
    rows = []
    for worksheet in workbook.worksheets:
        row_iter = worksheet.iter_rows(values_only=True)
        headers = next(row_iter, None)
        if not headers:
            continue
        normalized_headers = [_normalize_import_header(header) for header in headers]
        for row_index, values in enumerate(row_iter, start=2):
            row = {
                header: value
                for header, value in zip(normalized_headers, values)
                if header
            }
            row['source_sheet'] = worksheet.title
            row['source_row'] = row_index
            if _has_import_content(row):
                rows.append(row)
    return rows, ''


def _read_import_rows(upload):
    file_name = str(getattr(upload, 'name', '') or '').lower()
    if file_name.endswith('.xlsx') or file_name.endswith('.xlsm'):
        return _read_xlsx_import_rows(upload)
    if file_name.endswith('.csv') or not file_name:
        return _read_csv_import_rows(upload)
    return None, 'Please upload a CSV or XLSX file'


def _sheet_attendance_date(row, start_date):
    explicit_date = _parse_import_date(row, 'attendance_date', 'camp_date', 'date')
    if explicit_date:
        return explicit_date

    sheet_name = str(row.get('source_sheet') or '').strip().lower()
    if not sheet_name or not start_date:
        return None
    for key, offset in WEEKDAY_SHEET_OFFSETS.items():
        if key in sheet_name:
            monday = start_date - datetime.timedelta(days=start_date.weekday())
            return monday + datetime.timedelta(days=offset)
    return None


@api_view(['POST'])
@authentication_classes([AdminTokenAuthtication])
def import_enrollments(request):
    upload = request.FILES.get('file') or request.FILES.get('csv')
    if not upload:
        return APIResponse(code=1, msg='Please upload a CSV or XLSX file')

    rows, read_error = _read_import_rows(upload)
    if read_error:
        return APIResponse(code=1, msg=read_error)
    if not rows:
        return APIResponse(code=1, msg='No rows found in uploaded file')

    created = {
        'parents': 0,
        'students': 0,
        'camp_weeks': 0,
        'rooms': 0,
        'enrollments': 0,
        'updated_enrollments': 0,
        'daily_plans': 0,
        'updated_daily_plans': 0,
    }
    errors = []

    with transaction.atomic():
        for index, row in enumerate(rows, start=2):
            row_label = f"{row.get('source_sheet')} row {row.get('source_row')}" if row.get('source_sheet') else row.get('source_row', index)
            parent_username = _row_value(row, 'parent_username', 'parent')
            first_name = _row_value(row, 'student_first_name', 'first_name')
            last_name = _row_value(row, 'student_last_name', 'last_name')
            student_name = _row_value(row, 'student_name') or _split_student_name(first_name, last_name)
            camp_week_code = _row_value(row, 'camp_week_code', 'term_code')
            camp_week_name = _row_value(row, 'camp_week_name', 'term_title') or camp_week_code
            room_name = _row_value(row, 'default_room', 'room_name', 'room')
            sign_out_room_name = (
                _row_value(
                    row,
                    'sign_out_room',
                    'sign_out',
                    'sign out room',
                    'sign-out room',
                    'pickup_room',
                    'pickup room',
                    'dismissal_room',
                    'dismissal room',
                    'checkout_room',
                    'checkout room',
                )
                or room_name
            )

            if not parent_username or not student_name or not camp_week_code or not room_name:
                errors.append({
                    'row': row_label,
                    'error': 'Required fields: parent_username, student name, camp_week_code, default_room',
                })
                continue

            start_date = _parse_import_date(row, 'start_date', 'camp_start_date')
            end_date = _parse_import_date(row, 'end_date', 'camp_end_date')
            if not start_date or not end_date:
                errors.append({'row': row_label, 'error': 'start_date and end_date must use yyyy-mm-dd'})
                continue
            attendance_date = _sheet_attendance_date(row, start_date)
            if attendance_date and not (start_date <= attendance_date <= end_date):
                errors.append({'row': row_label, 'error': 'attendance date is outside start_date/end_date'})
                continue

            parent, parent_created = User.objects.get_or_create(
                username=parent_username,
                defaults={
                    'password': 'test',
                    'role': '1',
                    'status': '0',
                    'nickname': ' '.join([
                        _row_value(row, 'parent_first_name'),
                        _row_value(row, 'parent_last_name'),
                    ]).strip() or parent_username,
                    'mobile': _row_value(row, 'phone', 'parent_phone'),
                    'email': _row_value(row, 'email', 'parent_email'),
                },
            )
            if parent_created:
                created['parents'] += 1
            else:
                changed = False
                phone = _row_value(row, 'phone', 'parent_phone')
                email = _row_value(row, 'email', 'parent_email')
                nickname = ' '.join([
                    _row_value(row, 'parent_first_name'),
                    _row_value(row, 'parent_last_name'),
                ]).strip()
                if phone and parent.mobile != phone:
                    parent.mobile = phone
                    changed = True
                if email and parent.email != email:
                    parent.email = email
                    changed = True
                if nickname and parent.nickname != nickname:
                    parent.nickname = nickname
                    changed = True
                if changed:
                    parent.save()

            age_text = _row_value(row, 'age')
            student_notes = _row_value(row, 'medical_notes', 'general_notes', 'student_notes')
            if age_text and not age_text.isdigit():
                student_notes = f"{student_notes}; Grade: {age_text}" if student_notes else f"Grade: {age_text}"

            student, student_created = Child.objects.get_or_create(
                parent=parent,
                name=student_name,
                defaults={
                    'age': int(age_text) if age_text.isdigit() else None,
                    'gender': _row_value(row, 'gender'),
                    'remark': student_notes,
                },
            )
            if student_created:
                created['students'] += 1

            term, term_created = Term.objects.get_or_create(
                title=camp_week_name,
                defaults={
                    'expect_time': datetime.datetime.combine(start_date, datetime.time(9, 0)),
                    'return_time': datetime.datetime.combine(end_date, datetime.time(16, 0)),
                    'price': '',
                },
            )
            if term_created:
                created['camp_weeks'] += 1
            else:
                term.expect_time = datetime.datetime.combine(start_date, datetime.time(9, 0))
                term.return_time = datetime.datetime.combine(end_date, datetime.time(16, 0))
                term.save()

            room, room_created = Tag.objects.get_or_create(
                title=room_name,
                defaults={'seat': int(_row_value(row, 'capacity') or 0) or None},
            )
            if room_created:
                created['rooms'] += 1

            sign_out_room, sign_out_room_created = Tag.objects.get_or_create(
                title=sign_out_room_name,
                defaults={'seat': None},
            )
            if sign_out_room_created and sign_out_room.id != room.id:
                created['rooms'] += 1

            enrollment, enrollment_created = CampEnrollment.objects.update_or_create(
                student=student,
                term=term,
                defaults={
                    'parent': parent,
                    'default_room': room,
                    'sign_out_room': sign_out_room,
                    'status': _row_value(row, 'status') or 'active',
                    'payment_status': _row_value(row, 'payment_status') or 'unpaid',
                    'note': _row_value(row, 'notes', 'note'),
                },
            )
            if enrollment_created:
                created['enrollments'] += 1
            else:
                created['updated_enrollments'] += 1

            if attendance_date:
                attendance, attendance_created = CampAttendance.objects.get_or_create(
                    student=student,
                    attendance_date=attendance_date,
                    defaults={
                        'term': term,
                        'room': room,
                        'sign_out_room': sign_out_room,
                        'status': 'not_arrived',
                    },
                )
                changed = False
                if attendance.term_id != term.id:
                    attendance.term = term
                    changed = True
                if attendance.room_id != room.id:
                    attendance.room = room
                    changed = True
                if attendance.sign_out_room_id != sign_out_room.id:
                    attendance.sign_out_room = sign_out_room
                    changed = True
                if changed:
                    attendance.save(update_fields=['term', 'room', 'sign_out_room', 'updated_time'])
                if attendance_created:
                    created['daily_plans'] += 1
                else:
                    created['updated_daily_plans'] += 1

    return APIResponse(code=0, msg='Camp import finished', data={
        **created,
        'error_count': len(errors),
        'errors': errors[:100],
    })


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def export_attendance(request):
    target_date = _parse_date(request.GET.get('date'))
    if target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="camp_signin_{target_date.isoformat()}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'Date',
        'Camp Week',
        'Student Name',
        'Parent Name',
        'Parent Phone',
        'Sign In Room',
        'Sign Out Room',
        'Recorded Sign Out Room',
        'Status',
        'Sign In Time',
        'Sign Out Time',
        'Late Pickup After 4:30 PM',
        'Late Pickup Minutes',
        'Notes',
    ])
    for item in _student_items(target_date):
        attendance = item.get('attendance') or {}
        writer.writerow([
            item.get('date') or target_date.isoformat(),
            item.get('term_title') or '',
            item.get('student_name') or '',
            item.get('parent_name') or '',
            item.get('parent_phone') or '',
            item.get('room_name') or '',
            item.get('sign_out_room_name') or item.get('room_name') or '',
            attendance.get('sign_out_room_name') or '',
            attendance.get('status') or 'not_arrived',
            attendance.get('sign_in_time') or '',
            attendance.get('sign_out_time') or '',
            'Yes' if attendance.get('late_pickup') else 'No',
            attendance.get('late_pickup_minutes') or 0,
            attendance.get('note') or '',
        ])
    return response


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def waiver_list(request):
    target_date = _parse_date(request.GET.get('date'))
    date_filter = str(request.GET.get('date_filter') or '').strip().lower() in ['1', 'true', 'yes']
    if date_filter and target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    waivers = [_serialize_waiver(waiver) for waiver in _waiver_queryset(target_date if date_filter else None)]
    return APIResponse(code=0, msg='OK', data={
        'date': target_date.isoformat() if target_date else '',
        'date_filter': date_filter,
        'waivers': waivers,
    })


@api_view(['GET'])
@authentication_classes([AdminTokenAuthtication])
def export_waivers(request):
    target_date = _parse_date(request.GET.get('date'))
    date_filter = str(request.GET.get('date_filter') or '').strip().lower() in ['1', 'true', 'yes']
    if date_filter and target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    filename_date = target_date.isoformat() if date_filter and target_date else 'all'
    response['Content-Disposition'] = f'attachment; filename="camp_waivers_{filename_date}.csv"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow([
        'Date',
        'Student Name',
        'Parent Name',
        'Parent Username',
        'Parent Phone',
        'Camp Week',
        'Signer Name',
        'Waiver Version',
        'Signed Time',
        'Signed IP',
    ])
    for waiver in _waiver_queryset(target_date if date_filter else None):
        item = _serialize_waiver(waiver)
        writer.writerow([
            filename_date if date_filter else '',
            item.get('student_name') or '',
            item.get('parent_name') or '',
            item.get('parent_username') or '',
            item.get('parent_phone') or '',
            item.get('term_title') or '',
            item.get('signer_name') or '',
            item.get('waiver_version') or '',
            item.get('signed_time') or '',
            item.get('signed_ip') or '',
        ])
    return response


def _matches_name(item, first_name, last_name):
    student_name = (item.get('student_name') or '').lower()
    tokens = [value.lower().strip() for value in [first_name, last_name] if value and value.strip()]
    if not tokens:
        return False
    return all(token in student_name for token in tokens)


def _room_sort_key(value):
    name = str(value or '').strip()
    compact_name = re.sub(r'\s+', '', name).lower()
    return ROOM_DISPLAY_ORDER.get(compact_name, 1000), name.lower()


def _room_names_from_items(items):
    rooms = {}
    for item in items:
        for schedule_item in item.get('schedule_items') or []:
            room_name = schedule_item.get('room_name') or item.get('room_name')
            if room_name:
                rooms[room_name.lower()] = room_name
        room_name = item.get('room_name')
        if room_name:
            rooms[room_name.lower()] = room_name
    return sorted(rooms.values(), key=_room_sort_key)


@api_view(['GET'])
def search(request):
    target_date = _parse_date(request.GET.get('date'))
    if target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    students = _student_items(target_date)
    matches = [
        item for item in students
        if _matches_name(item, first_name, last_name)
    ]
    return APIResponse(code=0, msg='OK', data={
        'date': target_date.isoformat(),
        'camp_time': '9:00 AM - 4:00 PM',
        'room_names': _room_names_from_items(students),
        'students': matches,
    })


@api_view(['GET'])
def summary(request):
    target_date = _parse_date(request.GET.get('date'))
    if target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    students = _student_items(target_date)
    counts = {
        'expected': len(students),
        'not_arrived': 0,
        'signed_in': 0,
        'late': 0,
        'signed_out': 0,
        'early_pickup': 0,
        'absent': 0,
    }
    rooms = {}
    for item in students:
        status = item['attendance']['status']
        counts[status] = counts.get(status, 0) + 1
        room_name = item['room_name'] or 'No room'
        rooms.setdefault(room_name, []).append(item)

    return APIResponse(code=0, msg='OK', data={
        'date': target_date.isoformat(),
        'camp_time': '9:00 AM - 4:00 PM',
        'counts': counts,
        'rooms': [{'room_name': room, 'students': items} for room, items in sorted(rooms.items(), key=lambda pair: _room_sort_key(pair[0]))],
        'students': students,
    })


def _resolve_student_for_action(target_date, student_id):
    try:
        student = Child.objects.select_related('parent').get(pk=student_id)
    except Child.DoesNotExist:
        return None, APIResponse(code=1, msg='Student not found')

    scheduled_ids = {item['student_id'] for item in _student_items(target_date)}
    if student.id not in scheduled_ids:
        return None, APIResponse(code=1, msg='No camp schedule found for this student today')
    return student, None


def _record_waiver_if_needed(request, student, scheduled_item):
    if not CAMP_WAIVER_REQUIRED:
        return None

    term_id = scheduled_item.get('term_id') if scheduled_item else None
    if not term_id or _has_waiver(student.id, term_id):
        return None

    accepted = request.data.get('waiver_accepted')
    signer_name = str(request.data.get('waiver_signer_name') or '').strip()
    accepted_text = str(accepted).strip().lower()
    if accepted_text not in ['1', 'true', 'yes', 'on'] or not signer_name:
        return APIResponse(code=2, msg='Waiver signature is required before sign in', data={
            'waiver_required': True,
            'waiver_version': CAMP_WAIVER_VERSION,
        })

    CampWaiver.objects.create(
        student=student,
        parent=student.parent,
        term_id=term_id,
        signer_name=signer_name,
        waiver_version=CAMP_WAIVER_VERSION,
        signed_ip=_client_ip(request),
    )
    return None


@api_view(['POST'])
@transaction.atomic
def sign_in(request):
    target_date = _parse_date(request.data.get('date'))
    if target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    student, error = _resolve_student_for_action(target_date, request.data.get('student_id'))
    if error:
        return error

    scheduled_item = next((item for item in _student_items(target_date) if item['student_id'] == student.id), None)
    waiver_error = _record_waiver_if_needed(request, student, scheduled_item)
    if waiver_error:
        return waiver_error

    now = _camp_local_now()
    status = 'late' if now.time() > datetime.time(CAMP_START_HOUR, 0) else 'signed_in'
    record, _created = CampAttendance.objects.select_for_update().get_or_create(
        student=student,
        attendance_date=target_date,
        defaults={
            'term_id': scheduled_item.get('term_id') if scheduled_item else None,
            'room_id': scheduled_item.get('room_id') if scheduled_item else None,
        },
    )
    if record.sign_in_time:
        return APIResponse(code=0, msg='Already signed in', data=_serialize_record(record))

    record.sign_in_time = now
    record.status = status
    record.sign_in_ip = _client_ip(request)
    record.term_id = scheduled_item.get('term_id') if scheduled_item else record.term_id
    record.room_id = scheduled_item.get('room_id') if scheduled_item else record.room_id
    record.save()
    return APIResponse(code=0, msg='Signed in', data=_serialize_record(record))


@api_view(['POST'])
@transaction.atomic
def sign_out(request):
    target_date = _parse_date(request.data.get('date'))
    if target_date is None:
        return APIResponse(code=1, msg='Invalid date')

    student, error = _resolve_student_for_action(target_date, request.data.get('student_id'))
    if error:
        return error

    scheduled_item = next((item for item in _student_items(target_date) if item['student_id'] == student.id), None)
    record, _created = CampAttendance.objects.select_for_update().get_or_create(
        student=student,
        attendance_date=target_date,
        defaults={
            'term_id': scheduled_item.get('term_id') if scheduled_item else None,
            'room_id': scheduled_item.get('room_id') if scheduled_item else None,
            'sign_out_room_id': scheduled_item.get('sign_out_room_id') if scheduled_item else None,
        },
    )

    if record.sign_out_time:
        return APIResponse(code=0, msg='Already signed out', data=_serialize_record(record))

    now = _camp_local_now()
    record.sign_out_time = now
    record.status = 'early_pickup' if now.time() < datetime.time(CAMP_END_HOUR, 0) else 'signed_out'
    record.sign_out_room_id = scheduled_item.get('sign_out_room_id') if scheduled_item else record.sign_out_room_id
    record.term_id = scheduled_item.get('term_id') if scheduled_item else record.term_id
    record.room_id = scheduled_item.get('room_id') if scheduled_item else record.room_id
    record.sign_out_ip = _client_ip(request)
    record.save()
    return APIResponse(code=0, msg='Signed out', data=_serialize_record(record))
