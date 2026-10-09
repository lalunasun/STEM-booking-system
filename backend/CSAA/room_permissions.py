from datetime import date

from django.db.models import Q

from CSAA.models import AdminTrialSession, Course, Order, RoomCoursePermission, Tag, Term, Thing, Time
from CSAA.time_slots import equivalent_time_ids, time_slot_key

DAY_CODES = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')


def blocked_day_codes(rule):
    if not rule or not rule.blocked_days:
        return set()
    return {item for item in rule.blocked_days.split(',') if item in DAY_CODES}


def room_day_allowed(room_id, term, day):
    rule = RoomCoursePermission.objects.filter(room_id=room_id, term=term).first()
    return rule is None or day not in blocked_day_codes(rule)


def room_day_allowed_for_date(room_id, class_date):
    day = DAY_CODES[class_date.weekday()]
    rules = list(RoomCoursePermission.objects.filter(
        room_id=room_id,
        term__expect_time__date__lte=class_date,
        term__return_time__date__gte=class_date,
    ))
    return not rules or any(day not in blocked_day_codes(rule) for rule in rules)


def rooms_blocked_for_date(class_date):
    day = DAY_CODES[class_date.weekday()]
    rules = RoomCoursePermission.objects.filter(
        term__expect_time__date__lte=class_date,
        term__return_time__date__gte=class_date,
    )
    rules_by_room = {}
    for rule in rules:
        rules_by_room.setdefault(rule.room_id, []).append(rule)
    blocked = {
        room_id for room_id, room_rules in rules_by_room.items()
        if room_rules and all(day in blocked_day_codes(rule) for rule in room_rules)
    }
    if not blocked:
        return blocked
    occupied_room_ids = set(Order.objects.filter(
        thing__tag_id__in=blocked,
        thing__day=day,
        child__isnull=False,
        status__in=[2, 6],
        expect_time__date__lte=class_date,
        return_time__date__gte=class_date,
    ).values_list('thing__tag_id', flat=True))
    trial_rooms = AdminTrialSession.objects.filter(
        Q(room_id__in=blocked) | Q(room__isnull=True, lesson__thing__tag_id__in=blocked),
        session_date=class_date,
        status='active',
    ).values_list('room_id', 'lesson__thing__tag_id')
    occupied_room_ids.update(
        room_id or lesson_room_id for room_id, lesson_room_id in trial_rooms
    )
    return blocked - occupied_room_ids


def course_allowed(room_id, term, title, day=''):
    catalog = Course.objects.filter(title__iexact=title).first()
    if catalog and not catalog.active:
        return False
    rule = RoomCoursePermission.objects.filter(room_id=room_id, term=term).first()
    if rule is None:
        return True
    if day and day in blocked_day_codes(rule):
        return False
    return rule.courses.filter(title__iexact=title, active=True).exists()


def candidate_classes(term, title, day='', time_id=None):
    catalog = Course.objects.filter(title__iexact=title).first()
    if catalog and not catalog.active:
        return []
    title = catalog.title if catalog else title
    existing = Thing.objects.filter(status='0').select_related('tag', 'time')
    if day:
        existing = existing.filter(day=day)
    if time_id:
        selected_time = Time.objects.filter(pk=time_id).first()
        if not selected_time:
            return []
        existing = existing.filter(time_id__in=equivalent_time_ids(selected_time))
    rules = {
        rule.room_id: (
            {course.title.casefold() for course in rule.courses.all() if course.active},
            blocked_day_codes(rule),
        )
        for rule in RoomCoursePermission.objects.filter(term=term).prefetch_related('courses')
    }
    slots = {}
    closed = {
        (thing.tag_id, thing.day, time_slot_key(thing.time))
        for thing in Thing.objects.filter(title__iexact=title, status='1').select_related('time')
    }
    for thing in existing.order_by('id'):
        if not thing.tag_id or not thing.time_id or not thing.day:
            continue
        rule_data = rules.get(thing.tag_id)
        if rule_data is not None and thing.day in rule_data[1]:
            continue
        allowed = rule_data[0] if rule_data is not None else None
        if allowed is not None and title.casefold() not in allowed:
            continue
        key = (thing.tag_id, thing.day, time_slot_key(thing.time))
        if (thing.title or '').casefold() == title.casefold():
            if key not in slots or slots[key].pk is None:
                slots[key] = thing
        elif allowed is not None and key not in slots and key not in closed:
            slots[key] = Thing(title=title, tag=thing.tag, day=thing.day, time=thing.time, status='0')

    # A configured room/course permission applies to every selectable school time.
    # This also makes a newly added time usable before any class exists at that time.
    if day and time_id and selected_time:
        key_time = time_slot_key(selected_time)
        permitted_room_ids = [
            room_id for room_id, (allowed, blocked_days) in rules.items()
            if title.casefold() in allowed and day not in blocked_days
        ]
        rooms = {
            room.id: room
            for room in Tag.objects.filter(id__in=permitted_room_ids)
        }
        for room_id in permitted_room_ids:
            key = (room_id, day, key_time)
            if room_id in rooms and key not in slots and key not in closed:
                slots[key] = Thing(
                    title=title, tag=rooms[room_id], day=day,
                    time=selected_time, status='0',
                )
    return sorted(slots.values(), key=lambda item: (item.day, time_slot_key(item.time), item.tag.title))


def protected_class_instances(things, as_of=None):
    """Return current class instances that are still backed by room permissions."""
    things = list(things)
    room_ids = {thing.tag_id for thing in things if thing.tag_id}
    if not room_ids:
        return []

    as_of = as_of or date.today()
    active_terms = Term.objects.filter(
        expect_time__date__lte=as_of,
        return_time__date__gte=as_of,
    )
    allowed_by_room = {}
    rules = RoomCoursePermission.objects.filter(
        room_id__in=room_ids,
        term__in=active_terms,
    ).prefetch_related('courses')
    for rule in rules:
        allowed_by_room.setdefault(rule.room_id, set()).update(
            course.title.strip().casefold()
            for course in rule.courses.all()
            if course.active and course.title
        )

    return [
        thing for thing in things
        if thing.title
        and thing.title.strip().casefold() in allowed_by_room.get(thing.tag_id, set())
    ]
