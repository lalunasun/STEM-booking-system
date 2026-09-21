const ROOM_ORDER: Record<string, number> = {
  room1: 0,
  room3: 1,
  room4: 2,
  room5: 3,
  library: 4,
  vexiqlab: 5,
  vexv5lab: 6,
  v5lab: 6,
  meetingroom: 90,
  frclab: 91,
};

const compactRoomName = (value: unknown) => String(value || '').trim().toLowerCase().replace(/\s+/g, '');

export const compareRoomNames = (left: unknown, right: unknown) => {
  const leftName = String(left || '');
  const rightName = String(right || '');
  const leftOrder = ROOM_ORDER[compactRoomName(leftName)] ?? 1000;
  const rightOrder = ROOM_ORDER[compactRoomName(rightName)] ?? 1000;
  return leftOrder - rightOrder || leftName.localeCompare(rightName, undefined, { numeric: true });
};
