import re

from CSAA.models import Time


def normalized_time_range(value):
    match = re.fullmatch(r'\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*', value or '')
    if not match:
        return None
    h1, m1, h2, m2 = map(int, match.groups())
    if not (0 <= h1 < 24 and 0 <= h2 < 24 and 0 <= m1 < 60 and 0 <= m2 < 60):
        return None
    if h1 * 60 + m1 >= h2 * 60 + m2:
        return None
    return f'{h1:02d}:{m1:02d}-{h2:02d}:{m2:02d}'


def time_slot_key(time):
    if time is None:
        return None
    return normalized_time_range(time.time) or f'id:{time.pk}'


def equivalent_time_ids(time):
    key = time_slot_key(time)
    return [item.pk for item in Time.objects.all() if time_slot_key(item) == key]
