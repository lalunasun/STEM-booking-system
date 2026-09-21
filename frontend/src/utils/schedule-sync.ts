export const SCHEDULE_DATA_CHANGED_EVENT = 'csaa-schedule-data-changed';
const SCHEDULE_DATA_CHANGED_KEY = 'csaa-schedule-data-changed-at';

export const notifyScheduleDataChanged = () => {
  window.dispatchEvent(new Event(SCHEDULE_DATA_CHANGED_EVENT));
  try {
    localStorage.setItem(SCHEDULE_DATA_CHANGED_KEY, String(Date.now()));
  } catch {
    // Storage may be unavailable in a restricted browser context.
  }
};

export const subscribeToScheduleDataChanges = (refresh: () => void) => {
  const handleEvent = () => refresh();
  const handleStorage = (event: StorageEvent) => {
    if (event.key === SCHEDULE_DATA_CHANGED_KEY) {
      refresh();
    }
  };

  window.addEventListener(SCHEDULE_DATA_CHANGED_EVENT, handleEvent);
  window.addEventListener('storage', handleStorage);

  return () => {
    window.removeEventListener(SCHEDULE_DATA_CHANGED_EVENT, handleEvent);
    window.removeEventListener('storage', handleStorage);
  };
};
