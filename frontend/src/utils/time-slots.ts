export const normalizedTimeRange = (value: string) => {
  const match = /^\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$/.exec(value || '');
  if (!match) return value;
  return `${match[1].padStart(2, '0')}:${match[2]}-${match[3].padStart(2, '0')}:${match[4]}`;
};

export const uniqueTimeSlots = <T extends { time: string }>(slots: T[]): T[] => {
  const unique = new Map<string, T>();
  for (const slot of slots) {
    const time = normalizedTimeRange(slot.time);
    if (!unique.has(time)) unique.set(time, { ...slot, time });
  }
  return [...unique.values()].sort((a, b) => a.time.localeCompare(b.time));
};

export const groupCourseSlots = <T extends { class_name?: string; time?: string; virtual_trial?: boolean }>(lessons: T[]) => {
  const groups = new Map<string, { head: T; members: T[] }>();
  for (const lesson of lessons) {
    const key = `${(lesson.class_name || '').trim().toLowerCase()}:${normalizedTimeRange(lesson.time || '')}:${!!lesson.virtual_trial}`;
    const group = groups.get(key);
    if (group) group.members.push(lesson);
    else groups.set(key, { head: lesson, members: [lesson] });
  }
  return [...groups.values()];
};
