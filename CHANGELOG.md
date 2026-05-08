# Changelog

## 2026-05-08

- Updated admin Schedule behavior.
  - Changed Week view to a time-grid layout from 9:00 to 20:00.
  - Added explicit `lesson_id` and `thing_id` fields for stable Schedule links.
  - Schedule cards now use order and term dates for student display instead of stale lesson student lists.
  - Course cards remain visible even when there are no active students for the current week.
  - Fixed Schedule-to-Lesson navigation to use the current Vue route instead of opening a direct URL.
- Improved lesson detail loading.
  - Lesson detail now reloads when route query parameters change.
  - Prevented detail API calls when the current route is not a lesson page.
- Improved order and settlement flow.
  - Settlement now calculates lesson count and total even when a term has no fixed price.
  - Parent order tabs now separate `Paid`, `Scheduled`, and `Done`.
  - Admin order action text is clearer: `Mark done`.
- Improved the admin Schedule page.
  - Default view is now Week.
  - Removed the Year view for now because its behavior needs more design work.
  - Kept Month as the secondary view.
  - Changed Schedule controls and labels to English.
- Fixed admin Lesson detail text.
  - Changed `Avaliable` to `Available`.
  - Changed student tabs to full English labels:
    - `Normal Students`
    - `Rescheduled Students`
    - `Trial Students`
    - `Absent Students`
- Restored `frontend/build/` because it contains Vite source configuration required by the frontend build.

Verification:

- `npm run build` passes in `frontend/`.
