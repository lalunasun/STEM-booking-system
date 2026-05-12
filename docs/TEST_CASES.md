# CSAA Booking System Test Cases

Last updated: 2026-05-12

This document records manual test cases for the CSAA course booking system.

## Test Data Notes

- Local database: `backend/db.sqlite3`
- Local database is ignored by Git.
- Admin login for local testing:
  - Username: `test`
  - Password: `test`
- Current room default capacity: `4`
- Active capacity-counting order statuses:
  - `Paid`
  - `Scheduled`
- Non-capacity-counting statuses:
  - `Pending payment`
  - `Canceled`
  - `Done`

## Status Legend

- `Pending`: test case is planned but not yet tested.
- `Passed`: tested and working.
- `Failed`: tested and currently broken.
- `Blocked`: cannot test because setup/data is missing.

## TC-001 Admin Login

Status: `Passed`

Purpose:

Verify admin can log in locally.

Steps:

1. Open `http://127.0.0.1:8080/adminLogin`.
2. Enter username `test`.
3. Enter password `test`.
4. Click login.

Expected result:

- Admin enters the dashboard.
- Admin name appears in the top bar.

Notes:

- Local admin account was reset to `test/test` on 2026-05-12.

## TC-002 Start Local Backend and Frontend

Status: `Passed`

Purpose:

Verify local services can start.

Steps:

1. Start Django backend on `127.0.0.1:8000`.
2. Start Vite frontend on `127.0.0.1:8080`.
3. Open the admin page.
4. Open the parent portal page.

Expected result:

- Backend listens on port `8000`.
- Frontend listens on port `8080`.
- Admin and parent pages load.

Notes:

- Frontend should be started with `NODE_OPTIONS=--max-old-space-size=8192` to reduce Vite memory crashes.

## TC-003 Admin Schedule Week Grid

Status: `Passed`

Purpose:

Verify the admin schedule page displays weekly classes correctly.

Steps:

1. Log in as admin.
2. Open `Schedule`.
3. Confirm the default view is Week.
4. Scroll down the schedule.
5. Hover over a class with students.
6. Click a class.

Expected result:

- Week grid is shown by default.
- Time axis appears on the left.
- Weekday header remains visible while scrolling.
- Lunch row is compact and visually separated.
- Class colors are distinct.
- Hover expands student names.
- Clicking class opens lesson detail.

## TC-004 Lesson Detail Student Display

Status: `Passed`

Purpose:

Verify lesson detail shows paid/scheduled students.

Steps:

1. Open admin Schedule.
2. Click a class with active students.
3. View the lesson detail page.

Expected result:

- Normal Students tab shows active students.
- Student name, parent, phone, and term are shown when available.
- Student count matches active paid/scheduled orders.

## TC-005 Term Name Editing

Status: `Passed`

Purpose:

Verify admin can edit a term name and dates.

Steps:

1. Log in as admin.
2. Open `Term`.
3. Click `Edit` on an existing term.
4. Change the term name.
5. Save.

Expected result:

- Term saves successfully.
- Term list shows the updated name.
- Date fields remain valid.

Notes:

- Fixed on 2026-05-11 by normalizing date values during update.

## TC-006 Student Admin Module

Status: `Passed`

Purpose:

Verify admin can manage students separately from parent users.

Steps:

1. Log in as admin.
2. Open `Student`.
3. Search by student or parent.
4. Add a student under a parent.
5. Edit student name or age.
6. Delete a test student if needed.

Expected result:

- Student list loads.
- Parent name and phone are shown.
- Active classes and active terms are shown when available.
- Add/edit/delete works.

## TC-007 Parent Portal Course Selection

Status: `Passed`

Purpose:

Verify parent-facing course browsing is organized by course type first, then day/time.

Steps:

1. Open `http://127.0.0.1:8080/index/portal`.
2. Select a course card, such as `Creator`.
3. Review available weekday/time slots.
4. Click `Choose for Child` on a time slot.

Expected result:

- Course cards are grouped by course title.
- Duplicate capitalization such as `scratch` and `Scratch` is merged.
- Time slots are grouped by weekday.
- Each time slot shows room, price, status, and remaining seats.
- Clicking a time slot opens class detail.

## TC-008 Parent Portal Full / Open Display

Status: `Passed`

Purpose:

Verify parent portal displays `Full` when room capacity is reached.

Planned setup:

- Class: `Creator`
- Day/time: `Tue 16:00-17:00`
- Room: `Room1`
- Capacity: `4`
- Term: `2026 spring`

Test data created on 2026-05-12:

| Order ID | Order Number | Parent | Parent Phone | Child | Age | Status | Term | Amount |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 24 | 1778597103741 | donut |  | donut_kid1 | 10 | Paid | 2026 spring | 400 |
| 25 | 1778597103750 | donut |  | donut_kid2 | 7 | Paid | 2026 spring | 400 |
| 26 | 1778597103765 | parent_01 | 555-01001 | parent_01_kid_1_age_5 | 5 | Paid | 2026 spring | 400 |
| 27 | 1778597103774 | parent_01 | 555-01001 | parent_01_kid_2_age_6 | 6 | Paid | 2026 spring | 400 |

Steps:

1. Create 4 paid orders for the same class, day/time, and room.
2. Open parent portal.
3. Select `Creator`.
4. Find `Tuesday 16:00-17:00`.

Expected result:

- Available seats display `0`.
- Status displays `Full`.
- Admin schedule also shows `FULL`.

Actual result:

- API returns `available_seats: 0`.
- API returns `display_status: Full`.
- Class remains manually open with `status: 0`; full is now calculated dynamically.

Notes:

- Fixed an old parent list API behavior that incorrectly saved full classes as `status: 1`.
- Full should be display logic, not a permanent manual class status change.

## TC-009 Booking to Payment to Scheduling Flow

Status: `Pending`

Purpose:

Verify the main business flow from parent booking to admin scheduling.

Steps:

1. Parent selects a course type.
2. Parent selects a day/time.
3. Parent logs in or registers.
4. Parent selects a child.
5. Parent confirms term and order amount.
6. System creates `Pending payment` order.
7. Admin marks order as `Paid`.
8. Admin marks order as `Scheduled`.
9. Open admin Schedule.
10. Open parent order history.

Expected result:

- Pending order is created first.
- Paid order counts toward active class capacity.
- Scheduled order appears on the admin weekly schedule.
- Parent can still see the historical purchase.

## TC-010 Admin Link Button

Status: `Passed`

Purpose:

Verify admin top bar `Link` opens the parent portal.

Steps:

1. Log in as admin.
2. Click `Link` in the top bar.

Expected result:

- Browser opens `/index/portal`.
- Parent portal loads.

Notes:

- The link is now a native anchor to `/index/portal`.

## TC-011 Hidden Unimplemented Admin Modules

Status: `Passed`

Purpose:

Verify unfinished admin menu entries do not break the dashboard.

Steps:

1. Log in as admin.
2. Review the left navigation.
3. Click each visible module.

Expected result:

- Visible modules have corresponding pages.
- Hidden/unimplemented modules do not appear.

Currently hidden:

- Comment(St2)
- Log(St2/3)
- Analysis(St2/3)

## TC-012 Default Course Cover Images

Status: `Passed`

Purpose:

Verify default course images display for all main course types.

Course covers:

- Creator
- Wedo
- Spike
- Scratch JR
- Scratch
- Roblox
- Python
- Java

Steps:

1. Open parent portal.
2. Review course cards.
3. Open a course detail page.

Expected result:

- Course card image displays.
- Detail image displays.
- Scratch and Python use the newer default images.
