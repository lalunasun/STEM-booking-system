# Changelog

## 2026-05-08

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
