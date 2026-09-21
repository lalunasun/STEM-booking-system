from CSAA.models import Course, RoomCoursePermission, Thing


def course_allowed(room_id, term, title):
    catalog = Course.objects.filter(title__iexact=title).first()
    if catalog and not catalog.active:
        return False
    rule = RoomCoursePermission.objects.filter(room_id=room_id, term=term).first()
    if rule is None:
        return True
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
        existing = existing.filter(time_id=time_id)
    rules = {
        rule.room_id: {course.title.casefold() for course in rule.courses.all() if course.active}
        for rule in RoomCoursePermission.objects.filter(term=term).prefetch_related('courses')
    }
    slots = {}
    closed = set(Thing.objects.filter(title__iexact=title, status='1').values_list('tag_id', 'day', 'time_id'))
    for thing in existing.order_by('id'):
        if not thing.tag_id or not thing.time_id or not thing.day:
            continue
        allowed = rules.get(thing.tag_id)
        if allowed is not None and title.casefold() not in allowed:
            continue
        key = (thing.tag_id, thing.day, thing.time_id)
        if (thing.title or '').casefold() == title.casefold():
            if key not in slots or slots[key].pk is None:
                slots[key] = thing
        elif allowed is not None and key not in slots and key not in closed:
            slots[key] = Thing(title=title, tag=thing.tag, day=thing.day, time=thing.time, status='0')
    return sorted(slots.values(), key=lambda item: (item.day, item.time.time, item.tag.title))
