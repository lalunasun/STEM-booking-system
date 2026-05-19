# Changelog

## 2026-05-15

- Added a separate parent mobile web app entry:
  - `/index/mobile`
  - `/mobile` redirects to `/index/mobile`
- Changed parent login redirect behavior:
  - login from mobile returns to `/index/mobile`
  - default web login still returns to the parent web portal
- Built mobile Home v1 around the registered parent workflow:
  - selected child appears first
  - `Next class` shows the selected child's next scheduled class
  - `Current classes` shows active classes with schedule and term start/end dates
  - `Action needed` highlights pending payment and paid orders waiting for admin scheduling
- Kept mobile navigation inside the mobile page for now:
  - Home
  - Book
  - Reschedule
  - Orders
  - Kids
- Added mobile in-page placeholder sections for class detail, trial package, orders, and reschedule.
- Refined mobile visual style with a lighter parent-facing palette.
- Improved local backend startup script to set the backend working directory and local dependency path.
- Updated local backend startup to prefer the bundled compatible Python runtime before falling back to system Python.
- Documented the current AWS Lightsail demo IP: `35.183.120.34`.

Verification:

- `npm run build` passes in `frontend/`.
- `/index/mobile` returns HTTP 200 locally.

## 2026-05-12

- Changed local startup to a single `8000` workflow:
  - Django now serves the built Vue frontend and API together.
  - Local app entry is `http://127.0.0.1:8000/admin/schedule`.
  - `8080` is no longer the default local workflow.
- Improved parent and admin order/class logic:
  - Parent order cards now show class day, time, and room.
  - Paid orders reserve capacity.
  - Only scheduled orders appear on the admin schedule and admin lesson student list.
  - Admin lesson detail no longer shows the parent-side `Order Now` button.
- Improved admin student list:
  - Main table focuses on student name, age, and active class schedule.
  - Detailed parent/phone/term information is available from `View Detail`.
- Documented the parent booking flow:
  - browse course
  - choose child
  - create pending order
  - mark paid
  - schedule student
  - reflect capacity/full status

## 2026-05-08

- Refined the admin Schedule grid.
  - Course rows now use compact fixed-height formatting for busy time slots.
  - Course colors are assigned consistently by course.
  - Student summaries truncate in the grid, with a hover dropdown showing one student per line.
  - Added a sticky weekday header while scrolling.
  - Highlighted the 12:00-13:00 lunch slot as a compact separator row.
  - Added a `FULL` badge when the scheduled student count reaches room capacity.
- Improved Schedule and Lesson student consistency.
  - Lesson detail now reads normal students from paid/scheduled orders, matching the Schedule grid.
  - Lesson detail student count now reflects paid/scheduled orders.
- Improved Time management.
  - Time periods are returned in start-time order.
  - Local test data was filled out from 9:00-10:00 through 19:00-20:00.
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
