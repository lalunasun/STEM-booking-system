# Course Registration System

Student course registration system for managing courses, rooms, schedules, terms, parents, children, and enrollment orders.

## Project Structure

```text
csaa-course-system/
  backend/    Django + Django REST Framework API
  frontend/   Vue 3 + Vite admin and parent-facing web app
```

## Local Development

Current local workflow uses one public browser entrypoint: Django serves the built frontend and the API on `http://127.0.0.1:8000`.

### 1. Build Frontend

Run this after frontend code changes, or after cloning the project on a new computer.

```powershell
cd frontend
npm install
npm run build
```

### 2. Start Backend and Frontend Together

```powershell
cd backend
python -m pip install -r requirements-local.txt
python manage.py runserver 127.0.0.1:8000
```

Open the app at:

```text
http://127.0.0.1:8000/admin/schedule
```

The old `http://127.0.0.1:8080` frontend dev server is not the default local workflow anymore.

### Local Entry Points

```text
Admin dashboard:       http://127.0.0.1:8000/admin/schedule
Parent web portal:     http://127.0.0.1:8000/index/portal
Parent mobile web app: http://127.0.0.1:8000/index/mobile
Mobile shortcut:       http://127.0.0.1:8000/mobile
```

The parent mobile web app is a separate parent-facing entry. It does not replace the existing web portal.

### Operating Modes

The long-term product direction uses one shared backend with role-based permissions, but separates the main working screens by real-world device and role.

- Admin desktop view: administrators use a computer for full operations, including setup, orders, payment confirmation, scheduling, manual adjustments, permanent course changes, user/student management, and data maintenance.
- Teacher iPad classroom view: teachers use a tablet-friendly classroom workspace for daily teaching tasks, including viewing today's classes, checking student lists, reading notes, marking attendance/absence, and writing comments.
- Teacher accounts should not have setup, order, payment, drag-to-move, permanent adjustment, or data maintenance permissions.
- The iPad teacher view should not force teachers to use the full admin schedule grid. It should prioritize today's date, assigned rooms/time slots, class rosters, student markers, notes, and comment entry.
- The current admin Schedule remains desktop-first. The future teacher iPad view should reuse the same backend data and permissions rather than becoming a separate system.

### Current AWS Demo
Demo access available upon request.

## Set Up on Another Computer

```powershell
git clone https://github.com/lalunasun/csaa-booking-system.git
cd csaa-booking-system
```

Then build the frontend:

```powershell
cd frontend
npm install
npm run build
```

Then start the backend from a second terminal:

```powershell
cd backend
python -m pip install -r requirements-local.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Open `http://127.0.0.1:8000/admin/schedule`.

If you want to keep the same local test data on another computer, copy `backend/db.sqlite3` manually from this computer because it is ignored by Git.

### Local Admin Login

```text
Username: test
Password: test
```

## Schedule Operation Tips

Manual adjustment on the admin Schedule page supports both drag-and-drop and click-to-move.

- Short move: drag the handle beside a student name and drop the student onto the target class.
- Off-screen target: drag near the schedule panel edge to auto-scroll horizontally or vertically.
- Long move: click the handle beside a student name to select the student, scroll to the target class, then click the target class heading.
- Cancel selection: press `Esc` to clear the currently selected student.
- Moved students can be moved again on the same date. The system updates the existing daily move record so the final move remains one clear adjustment.
- Room capacity is checked by room/time slot, not by each class name inside the same room/time cell.

## Core Booking Flow

Parent-side course purchase follows this flow:

1. Browse classes from the parent link page.
2. Select a course type first.
3. Select a specific day/time slot.
4. Choose the child who will take the class.
5. Confirm the term, class count, and total amount.
6. Submit the order as `Pending payment`.
7. After payment is confirmed, the order becomes `Paid`.
8. Admin confirms the student on the class schedule, then the order becomes `Scheduled`.
9. `Paid` and `Scheduled` orders count toward class capacity.
10. When capacity reaches the room limit, the class/time slot displays `Full`.

Current test/admin behavior:

- Payment is simulated by admin status changes.
- Scheduling is simulated by marking the order as scheduled/checked in.
- `Canceled` and `Done` orders should remain as history but should not count toward current capacity.

## Parent Mobile Web App

The mobile parent entry is designed around the registered parent workflow. After login, the first screen focuses on the selected child's current learning status instead of showing a course catalog first.

Current mobile v1 behavior:

- Login from `/index/mobile` returns to `/index/mobile` after success.
- The home page shows a child selector.
- `Next class` shows the next scheduled class for the selected child.
- `Current classes` shows the selected child's active scheduled classes with class time and term start/end dates.
- `Action needed` highlights pending payment and paid-but-not-yet-scheduled orders.
- The lower part of the same page keeps a mobile-friendly class browsing area.
- The bottom mobile navigation stays inside the mobile page for `Home`, `Book`, `Reschedule`, `Orders`, and `Kids`.

Current mobile v1 limitations:

- Mobile booking, trial request, order payment, and reschedule submission are displayed as mobile sections/placeholders first.
- The full production actions still exist in the original parent web portal while mobile-specific second-level pages are being designed.

## Project Documents

- Requirements: `docs/REQUIREMENTS.md`
- Requirements Chinese: `docs/REQUIREMENTS.zh-CN.md`
- Test cases: `docs/TEST_CASES.md`
- Test cases Chinese: `docs/TEST_CASES.zh-CN.md`

## Notes

- `backend/db.sqlite3` is local development data and is ignored by Git.
- The frontend defaults to `http://127.0.0.1:8000` for API calls.
- For another API host, set `VITE_API_BASE_URL` before starting the frontend.
