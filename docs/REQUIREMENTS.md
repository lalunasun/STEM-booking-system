# CSAA Booking System Requirements

Version: 0.3
Last updated: 2026-06-25

## 1. Project Goal

The system manages student course registration, scheduling, orders, room capacity, and future rescheduling/makeup workflows.

The product has three user-facing areas:

- Admin Dashboard: used by administrators to create rooms, time slots, terms, courses, users/students, orders, and schedules.
- Parent Mobile/Web Link: used by parents to register, create children, buy courses, select times, check course records, and later request leave/reschedule.
- Guest View: guests can browse courses, but must register/login before booking.

Current priority:

- Phase 1: finish and stabilize the web admin dashboard with test data.
- Phase 1.5: build the parent mobile web flow.
- Phase 2: leave/reschedule, reminders, makeup class recommendations, and advanced room matching.

## 2. Roles

### Admin

Admins can:

- Manage rooms.
- Manage time slots.
- Manage categories.
- Manage terms.
- Manage classes.
- Manage users and students.
- View the weekly schedule.
- View class details and enrolled students.
- View and update orders.
- See available/full/unavailable class status.
- Later approve or reject leave/reschedule requests.

### Parent

Parents can:

- Register and login.
- Create one or more children.
- Browse courses.
- Buy classes for a selected child.
- View orders and course records.
- Later submit leave/reschedule requests.
- Later receive reminders.

### Guest

Guests can:

- Browse course lists and course detail pages.

Guests cannot:

- Book classes.
- Create orders.
- Submit leave/reschedule requests.
- View personal course records.

## 3. Core Business Object: Student

The current login account is parent-based, but the main business object should be the student.

Current model:

```text
User(parent) -> Child
Order -> User + Child + Class + Term
```

Future product logic should treat `Child` as `Student`.

Recommended conceptual model:

```text
Parent/User
  -> Student/Child
      -> Orders
      -> Enrollments
      -> Attendance
      -> Reschedule Requests
      -> Lesson Records
```

Important rules:

- Parent is the account owner/contact.
- Student is the object being enrolled, scheduled, searched, rescheduled, and tracked.
- One parent can have multiple students.
- One student can have multiple classes and terms.
- Admin search and reports should be student-centered, not parent-centered.

Required admin improvement:

- Add a Student page in the admin dashboard.
- The page can use the existing `Child` model for now.
- Display student name, age, parent, phone, current classes, term, remaining lessons, and notes.

Required parent-side behavior:

- After login, parent should select which child they are booking for.
- All booking, order, leave, and reschedule actions must include `child_id`.

## 3.1 Parent Mobile Web App

The parent mobile web app is a separate entry from the existing parent web portal.

Entry points:

```text
/index/mobile
/mobile
```

Mobile home priority:

1. Show the selected child's current course status first.
2. Show the next upcoming scheduled class.
3. Show active/current classes with term start and end dates.
4. Show action items such as pending payment or paid orders waiting for admin scheduling.
5. Keep booking and rescheduling available, but not as the first screen priority.

Mobile v1 rules:

- The mobile app should stay inside the mobile experience when users tap bottom navigation.
- The existing parent web portal remains available at `/index/portal`.
- The mobile app should not automatically fall back to old desktop-style pages for common parent actions.
- Login from mobile should return to `/index/mobile`.

Current v1 limitation:

- Booking, trial request, order payment, and reschedule submission have mobile sections/placeholders first.
- Full forms can remain in the existing web portal until dedicated mobile second-level pages are built.

## 4. Room Module

Admins create rooms.

Room fields:

- Room name
- Seat capacity

Current rule:

- Each room defaults to 4 seats.
- Future rooms may have different capacities.

Important capacity rule:

- Full capacity should be calculated by shared room occupancy:

```text
Room + Day + Time
```

not only by individual class.

Example:

- If Creator and Scratch happen in Room1 at the same time, they share the same 4 seats.
- If Room1 Tuesday 16:00-17:00 already has 4 active students total, all compatible classes in that room/time should be Full.

## 5. Time Module

Admins create standard time slots.

Rules:

- Monday is closed.
- Tuesday to Friday:
  - 16:00-17:00
  - 17:00-18:00
  - 18:00-19:00
  - 19:00-20:00
- Saturday and Sunday:
  - 09:00-10:00
  - 10:00-11:00
  - 11:00-12:00
  - 12:00-13:00 lunch break
  - 13:00-14:00
  - 14:00-15:00
  - 15:00-16:00
  - 16:00-17:00
  - 17:00-18:00

Schedule UI:

- Use a weekly time-grid.
- Keep weekday header sticky while scrolling.
- Show 12:00-13:00 as a compact lunch separator.

## 6. Category Module

Classes belong to a category.

Planned categories:

- Coding
- Robotics
- Trial
- StemDay
- Math
- Language
- Competition

Current system may still contain older category names such as Lego. These should later be normalized.

## 7. Term Module

Term represents a course cycle.

Term fields:

- Term name
- Start date
- End date
- Price, optional
- Total weeks/lessons, future field
- Holiday exclusions, future field

Rules:

- Term is used to calculate total lessons and remaining lessons.
- Term week count should be calculated from dates.
- Admin must be able to adjust week count because spring break and irregular holidays may change actual lesson count.
- Booking should happen for a selected term.

Future improvement:

- Class should explicitly support term relationship.

## 8. Class Module

Class fields:

- Class name
- Category
- Term, future required field
- Room
- Day
- Time
- Price
- Status
- Cover image
- Description

Current status concepts:

- Available: manually open and not full.
- Unavailable: manually closed by admin.
- Full: dynamically calculated when active student count reaches capacity.

Important future correction:

- Full should be based on shared room capacity:

```text
Room + Day + Time active student count >= room.seat
```

Active statuses should generally include:

- Paid
- Scheduled

Inactive statuses should generally exclude:

- Canceled
- Done

Pending payment capacity behavior still needs confirmation.

## 9. Room and Course Compatibility

This is a key system rule for future rescheduling.

Business understanding:

- Robotics/building courses usually need fixed rooms and equipment.
- Coding courses are more flexible.
- Rooms are more like age/level groups than course-only rooms.
- One room can contain a building course and compatible coding courses at the same time.

Current compatibility draft:

| Level | Building Course | Compatible Coding |
| --- | --- | --- |
| Junior | Creator | Scratch JR / Scratch |
| Middle | Wedo | Scratch / Roblox |
| Senior | Spike | Roblox / Python / Java |

Open questions:

- Which room belongs to which level?
- Which ages map to each level?
- Can a coding student move across levels?
- Does Trial occupy regular seats?
- How do StemDay, Math, Language, and Competition share rooms?

## 10. Order Module

Order represents a parent buying a class/term for a student.

Current statuses:

- Pending payment
- Paid
- Scheduled
- Canceled
- Done

Rules:

- Paid and Scheduled should count toward active enrollment.
- Canceled should not count.
- Done is historical and should not count toward current capacity.
- Pending payment capacity behavior needs confirmation.

Order should keep historical purchase records for parents and students.

### 10.1 Booking, Payment, and Scheduling Flow

The parent-facing booking flow should be:

1. Guest or parent browses available courses.
2. Parent selects a course type.
3. Parent selects a specific day/time slot.
4. Parent logs in or registers if needed.
5. Parent selects the child who will take the class.
6. Parent selects/confirm the term.
7. System creates an order with status `Pending payment`.
8. Parent completes payment, or admin manually marks payment complete during local testing.
9. Order status changes to `Paid`.
10. Admin reviews the paid order and confirms the student on the schedule.
11. Order status changes to `Scheduled`.
12. The class appears on the admin weekly schedule with the student name.

Capacity behavior:

- `Paid` and `Scheduled` orders count toward active occupancy.
- `Pending payment` does not count toward capacity for now unless the business later decides to temporarily hold seats.
- `Canceled` and `Done` do not count toward current capacity.
- A class should display `Full` when active occupancy reaches the room capacity for the same `Room + Day + Time`.

Admin test workflow:

1. Create or pick a parent.
2. Create or pick a child under that parent.
3. Create an order for the selected class/term/child.
4. Mark the order as `Paid`.
5. Mark the order as `Scheduled`.
6. Verify the schedule and parent order history.

### 10.2 Trial Package Flow

Trial should not be booked as a normal Class. It should behave as a separate trial package / experience product that is visible on the parent side, with booking and scheduling logic separated from regular course registration.

The Trial package includes 3 trial lessons by default, currently priced at CAD $98:

1. One Robotics lesson.
2. One Coding lesson.
3. One Math lesson.

Current business rules:

- Parents can see a Trial entry on the parent portal.
- Selecting Trial should not enter the normal Class registration flow directly.
- Parent must select a child.
- The system recommends trial slots in three groups:
  - Available Robotics slots.
  - Available Coding slots.
  - Available Math slots.
- Parents must choose one Robotics slot, one Coding slot, and one Math slot. A Trial package cannot be submitted until all three selections are available and complete.
- Trial slot choices must show the exact date, weekday, time, and room.
- A Trial package creates one package order only after the required choices are complete, not multiple normal class orders.
- Trial package total price is fixed at CAD $98, and the order quantity displays as 3 lessons.
- Trial package starts as `Pending payment`.
- Parent side keeps a `Pay` button; after payment, the order enters the admin scheduling flow.
- Admin scheduling must place the student into each selected concrete class slot from the Trial package.
- Recommended slots must have available capacity and should be within allowed booking windows.
- The Trial package itself does not occupy a seat; capacity is occupied by the specific selected class slots.
- Admin schedule and class detail should show Trial students under `Trial Students`.
- Trial students count toward the target `Room + Day + Time` capacity.
- If no Math trial slot exists yet, the parent side must explain that a Math time is required and disable Trial submission.
- `Pending payment` Trial orders should not occupy the schedule or room capacity. Trial students appear only after payment and admin scheduling.
- Trial students should have a recognizable marker on the main schedule, and the class detail `Trial Students` tab should show the specific trial date.

Draft recommendation rules:

- Robotics trial should prefer available classes in the Robotics category.
- Coding trial should prefer available classes in the Coding category.
- Math trial should later prefer available classes in the Math category.
- Do not recommend Full slots.
- Do not recommend slots that conflict with the student's existing active classes, paid unscheduled Trial choices, scheduled Trial lessons, or confirmed makeup classes.
- Selected Trial slots cannot conflict with each other. If a conflict is selected, the system should warn the parent and allow a different choice in the other column.
- Later, recommendation can be improved by student age/level.

Current implementation guidance:

1. Use Trial request records to store concrete choices inside the package.
2. Parent Trial page shows Robotics, Coding, and Math columns; all three require one selected slot.
3. Each column shows the nearest available options first to keep the page manageable.
4. Submission creates one Trial package order.
5. Parent pays the order.
6. Admin schedules each selected slot from the order page.
7. After scheduling, the student is added to each target class's `Trial Students`.
8. Main schedule shows Trial students and counts them toward capacity.

## 11. Schedule Module

Admin schedule is the main operational view.

Current features:

- Week view by default.
- Left time axis.
- Weekday columns.
- Sticky weekday header.
- Compact course rows.
- Course colors.
- Student summary in row.
- Hover dropdown with one student per line.
- Lunch separator.
- FULL badge.
- Click class row to open class detail.
- Search by student name, case-insensitive.
- Keep the top search/view controls sticky while scrolling.
- Keep weekday headers sticky during vertical scroll.
- When opening class detail from the schedule, pass the concrete date so the detail page can filter normal, rescheduled, trial, and absent/canceled records for that date.
- If the selected date has Rescheduled / Trial / Absent students, the corresponding class detail tab shows a count badge.
- The left Order menu shows a red dot when paid but unscheduled orders exist.
- Hover student dropdowns must not block clicking the class card.

Future improvements:

- Add filters by room, category, term, and student.
- Show room grouping more clearly.
- Support student-specific schedule view.
- Add admin note markers that can be shown on schedule cards and detail views.

## 12. Query Module

The system needs student-centered query features.

Required query fields:

- Course name
- Class time
- Student name
- Parent name
- Parent phone
- Term
- Lesson start date
- Lesson end date
- Total lesson count
- Used lesson count
- Remaining lesson count
- Order status
- Leave/reschedule records
- Course status: active / finished / canceled / pending payment / scheduled
- Trial / Rescheduled / Absent markers
- Concrete lesson date, weekday, time, and room

Recommended admin query output:

| Student | Parent | Course | Day/Time | Term | Total Lessons | Used | Remaining |
| --- | --- | --- | --- | --- | --- | --- | --- |

Student module display rules:

- List page should show core information only: student name, age, and active class summary.
- Active class summary should include class name, date/weekday, time, and room.
- Detail page should show all course records, including active classes, finished classes, trial classes, rescheduled classes, and canceled/absent records.
- Finished classes must remain as historical records and should not be removed from the student profile.
- Student name search should be case-insensitive.

## 13. Leave, Makeup, and Reschedule

Phase 2 feature.

Rules:

- Parent must request leave at least 48 hours before class.
- Student has 2 reschedule chances before the course/term ends.
- Approved leave should create a makeup/reschedule opportunity.

Reschedule recommendation should consider:

- Student age/level.
- Original course type.
- Target room compatibility.
- Target time capacity.
- Building course fixed-room rules.
- Coding course flexible-room rules.
- Shared room occupancy.

Required reschedule record fields:

- Student
- Parent
- Original class
- Original date/time
- Original term
- Request type
- Reason
- Requested target date/time
- Assigned target class
- Status: pending / approved / rejected / completed / canceled
- Admin note
- Created time
- Updated time

Schedule display:

- Normal students show normally.
- Rescheduled students should be marked, for example with a green star.
- Absent and trial students should be shown in separate tabs/details.

## 14. Parent Mobile Web

The first mobile version should be a mobile web app, not native app.

Phase 1.5 mobile features:

- Login/register.
- Select child.
- Create child.
- Browse courses.
- View course details.
- Book class for selected child.
- Select term.
- View orders.
- View child's current courses.

Phase 2 mobile features:

- Request leave.
- Request reschedule.
- Choose makeup options.
- Receive reminders.

## 15. Reminders

Advanced feature.

Reminder types:

- Upcoming class reminder.
- Term ending reminder.
- Remaining lesson reminder.
- Makeup class reminder.
- Reschedule decision reminder.
- Course recommendation reminder.

Possible channels:

- In-app message.
- Email.
- SMS/WhatsApp/WeChat, future decision.

## 16. Course Recommendation

Advanced feature.

Recommendation can use:

- Student age.
- Current level.
- Completed courses.
- Available time.
- Room capacity.
- Remaining lessons.
- Parent purchase history.

## 16.5 Reschedule, Cancel Class, and Makeup Workflow

This module should first be completed on the parent web side. After the business workflow is stable, it can be migrated to the mobile web experience. The first implementation should focus on a small testable workflow instead of trying to finish every edge case at once.

### 16.5.1 Core Rules

- Parents must submit a cancel/reschedule request at least 48 hours before the class.
- If the request is within 48 hours, the system should tell the parent to contact admin by phone or email for special handling.
- Each student's reschedule count must be tracked within a term. The current draft rule is 2 reschedule opportunities before the term ends.
- An approved canceled class creates one makeup eligibility.
- Makeup classes must be scheduled within the original order/term date range unless admin manually approves an exception.
- Makeup students occupy capacity in the target room/time.
- After admin confirms scheduling, the makeup student appears under Rescheduled Students for the target class and should be marked specially on the main schedule.
- Original course and purchase history must be preserved; records should not be deleted.

### 16.5.2 Parent Flow

The parent should start from a purchased and active course.

Recommended entry points:

- My Orders / My Courses shows the student's active classes.
- Parent selects a child.
- Parent opens a purchased, paid, and active class.
- The page shows a class calendar with the student's lesson dates within the term.

Parent cancel class flow:

1. Parent selects a child.
2. Parent opens the child's active class.
3. Parent selects one class date from the class calendar.
4. System checks whether the class is at least 48 hours away.
5. If not, system tells the parent to contact admin by phone/email and blocks normal submission.
6. If yes, parent clicks Cancel Class.
7. System shows a confirmation modal explaining that admin approval is required.
8. Parent confirms and the system creates a cancel class request.
9. System sends a cancel class request email to admin.
10. Request status becomes Pending admin review.

After admin approves cancellation:

1. Original lesson is marked absent/canceled by request for that student.
2. System creates one makeup eligibility.
3. Parent can choose a makeup class.
4. System recommends 2 available makeup time slots by default.

Parent makeup request flow:

1. Parent sees 2 recommended makeup time slots.
2. Recommended slots must be within the term range.
3. Recommended slots must have room capacity.
4. Recommended slots should match course type, age/level, and room compatibility.
5. Parent selects one makeup slot.
6. Parent confirms and submits a makeup request.
7. System sends the course adjustment request to admin.
8. Request status becomes Pending admin review.

### 16.5.3 Admin Flow

Admin needs a new course adjustment module, suggested name: Reschedule Requests or Course Adjustments.

The admin module should show:

- Request ID
- Student
- Parent
- Parent phone/email
- Original class
- Original class date/time
- Original term
- Request type: cancel class / makeup class / admin manual reschedule
- Request reason
- Request status
- Recommended makeup options
- Selected makeup option
- Admin decision
- Admin note
- Created time
- Updated time

Admin cancel approval flow:

1. Admin reviews the parent cancel request.
2. Admin checks the 48-hour rule.
3. Admin approves or rejects.
4. If approved, system records the original lesson as canceled/absent.
5. System creates makeup eligibility.
6. System opens makeup selection for the parent.
7. System may notify the parent of the result.

Admin makeup approval flow:

1. Admin reviews the parent's selected makeup slot.
2. Admin checks whether the target class is within the term range.
3. Admin checks target room capacity.
4. Admin checks course type, age/level, and room compatibility.
5. After approval, system adds the student to target class Rescheduled Students.
6. Target room/time occupancy increases.
7. Main schedule shows the student as rescheduled/makeup.
8. System notifies the parent that the request is confirmed.

### 16.5.4 Makeup Recommendation Rules

The system should recommend 2 available makeup time slots by default.

Draft recommendation rules:

- Must be within the original order term start/end date.
- Must be after the current date.
- Must have available capacity.
- Must not conflict with the student's existing active classes.
- Prefer the same class name and same course type.
- If no exact same class is available, consider compatible course/room options.
- Robotics/building courses prefer fixed rooms and equipment.
- Coding courses can be more flexible by age/level and capacity.
- Recommendation result should show class name, date, weekday, time, room, and remaining seats.

Confirmed rules:

- Makeup cannot be assigned to a different class name just because it has the same level; makeup should stay with the same class name whenever possible.
- Cross-term makeup is not allowed by default.
- If the student is already enrolled in the next term, admin may allow the makeup to be deferred into the next term.
- If the parent does not accept the 2 recommended slots, they can leave a request note or call admin directly.
- Special arrangements from notes or phone calls are handled manually by admin.
- Admin must be able to manually add a third recommended makeup option.
- The admin-added third option should still check capacity, term range, and schedule conflicts. If admin force schedules it, admin note is required.

### 16.5.5 Admin Manual Reschedule

Admin needs manual reschedule capability for phone/email special cases or requests inside 48 hours.

Draft admin manual flow:

1. Admin searches for a student.
2. Admin views the student's active classes and class calendar.
3. Admin selects the original class date.
4. Admin selects a target makeup date/class.
5. System shows capacity, term range, compatibility, and conflict check results.
6. Admin can force confirm but must enter an admin note.
7. System creates an admin manual reschedule record.
8. Student is added to target class Rescheduled Students.
9. Target class occupancy increases.
10. Parent can see the updated makeup record.

### 16.5.6 Admin Note and Schedule Marker

Admin needs to add notes during course adjustment for phone conversations, special reasons, manual arrangements, and exception approvals.

Note display requirements:

- Course Adjustments list shows an admin note summary.
- Adjustment detail page shows full admin note and parent note.
- Main schedule should show a note marker for courses/students manually marked by admin.
- Hover or class detail should allow admin to read the note content.
- Notes do not replace formal status; status still uses pending / approved / rejected / completed / canceled.

### 16.5.7 Data Model Draft

A future RescheduleRequest / CourseAdjustment model may be needed.

Suggested fields:

- id
- student/child
- parent/user
- original_order
- original_class
- original_lesson_date
- original_day
- original_time
- original_term
- request_type
- request_reason
- request_source: parent / admin
- status: pending / approved / rejected / completed / canceled
- recommended_options
- admin_extra_recommendation
- selected_target_class
- selected_target_date
- selected_target_day
- selected_target_time
- selected_target_room
- admin_note
- parent_note
- approved_by
- approved_time
- created_time
- updated_time

### 16.5.8 Suggested Implementation Phases

1. Confirm requirements and data model.
2. Parent web shows class calendar and Cancel Class button inside purchased active classes.
3. Create cancel class request without changing schedule directly.
4. Admin Course Adjustments list can approve/reject cancel requests.
5. Approved cancellation creates makeup eligibility and recommends 2 time slots.
6. Parent selects one makeup slot and submits makeup request.
7. Admin approves makeup request and schedules the student.
8. Main schedule and class detail show Rescheduled Students and count them toward capacity.

## 17. Current Completed Work

Completed or partially completed:

- Local frontend/backend running.
- GitHub repository.
- Admin login.
- Basic Room / Time / Category / Term / Class / User / Order pages.
- Weekly schedule grid.
- Lesson detail student list.
- Paid / Scheduled / Done status separation.
- Schedule FULL badge.
- Class list dynamic status.
- Student admin page using the existing Child model.
- Time sorting.
- Local test data creation.
- Local image file recovery.
- Parent course portal grouped by class name, with duplicate names normalized to the newer generated course images.
- Parent Trial package selection page.
- Trial package order, payment, and admin scheduling flow.
- Trial students on the main schedule and `Trial Students` tab.
- Student name search on the main schedule.
- Sticky schedule toolbar and weekday headers.
- Count badges on class detail Rescheduled / Trial / Absent tabs.
- Red dot on the Order menu for paid but unscheduled orders.
- Basic course adjustment loop: parent cancel request, admin approval, makeup eligibility, makeup recommendations, and admin makeup scheduling.
- Makeup recommendation avoids recommending a time when the student already has a class.

## 18. Known Risks

- Full logic now uses capacity checks in key flows, but shared Room + Day + Time edge cases still need more real-data validation.
- Class needs a clearer term relationship.
- Historical test data may still contain legacy states, duplicate trial choices, or unreasonable schedules and should continue to be cleaned.
- Uploaded images are local files and are not stored in GitHub.
- Parent mobile flow has not formally started; the web flow is being used to validate business rules first.
- Trial package requires a configured Math class before it can be submitted. Historical incomplete packages remain visible to administrators for follow-up.
- AWS/public demo deployment is still early and needs process persistence, static asset handling, database backups, and access control before production use.
- Permanent course change now has a basic workflow, but the candidate list and revert action are still closer to demo/operations validation and should become a full history UI with clearer validation messages.

## 19. Suggested Next Steps

Web admin:

1. Continue validating Full, Trial, Rescheduled, and Absent capacity behavior and detail-page display.
2. Improve Student detail to show full active/finished/trial/rescheduled/canceled course history.
3. Clarify Class-Term relationship and reduce temporary legacy term data.
4. Add admin note markers for special rescheduling, phone conversations, and manual exceptions.
5. Continue cleaning and adding test course data based on real room compatibility.
6. Continue updating this requirements document and the test case document.

Mobile:

1. Build parent login/register.
2. Build child selection and child management.
3. Build course list and course detail.
4. Build booking flow.
5. Build order/course record view.

Phase 2:

1. Leave request.
2. Reschedule request.
3. Makeup recommendation.
4. Reminder system.
5. Course recommendation.

## 20. Recent Confirmed Requirements (2026-05-14)

This section captures recently confirmed requirements that may still be refined during testing.

### 20.1 Main Schedule Reminders and Markers

- Main schedule needs student name search, case-insensitive.
- Schedule toolbar and weekday headers should remain visible while scrolling.
- Course cards show a student summary; hover expansion shows student names only, one per line.
- If the selected date/time has makeup students, the `Rescheduled Students` tab shows a count badge.
- If the selected date/time has Trial students, the `Trial Students` tab shows a count badge.
- If the selected date/time has canceled/absent records, the `Absent Students` tab shows a count badge.
- The left Order menu shows a red dot when any `Paid` order is waiting for scheduling.

### 20.2 Order and Scheduling Boundaries

- `Pending payment` orders do not appear on the main schedule and do not occupy capacity.
- `Paid` means the parent has paid, but admin still needs to schedule the student.
- A student appears on the main schedule and class detail only after admin scheduling.
- A Trial package contains multiple concrete selected slots but appears as one package order to the parent.
- Admin scheduling must schedule each selected Trial package slot into its corresponding class.

### 20.3 Student Profile

- Student is the center object for future search and operations.
- Student list should show only a compact summary.
- Student detail should show:
  - Parent and contact information.
  - Current active classes.
  - Finished classes.
  - Trial records.
  - Rescheduled records.
  - Absent / canceled records.
  - Term, date, weekday, time, room, and status for every course record.

### 20.4 Trial Package

- Trial is currently sold as a package: CAD $98 / 3 lessons.
- First version requires Robotics and Coding choices; Math shows Coming soon.
- Every selectable slot must show a concrete date, not only weekday.
- Trial choices cannot have internal time conflicts.
- Trial students enter the main schedule after admin scheduling and show in the `Trial Students` tab.

## 21. Recent Confirmed Requirements (2026-06-25)

This section captures the design rules added around the new Schedule view, student profile, one-day adjustments, and permanent course changes. A separate user manual should later turn these rules into admin and parent-facing operating steps.

### 21.1 Daily Schedule Operations View

The Schedule page now focuses on one operating day instead of a traditional full-week grid.

Current rules:

- The default view shows one selected day's course operations.
- The left date rail shows the current week's available dates for quick switching.
- The top-right Week control remains available for fast week/date navigation.
- Monday is closed and should not appear as a regular teaching day.
- Tuesday to Friday show 16:00-20:00 teaching slots.
- Saturday and Sunday show 09:00-18:00 teaching slots.
- 12:00-13:00 is lunch/break time and should not be used for classes.
- A date may appear in the date rail even when there are no classes, but the body should clearly show no classes.
- Each column represents one room.
- Each row represents one time slot.
- Each cell shows the classes, teacher, and students for that date, room, and time.
- Empty time slots can be hidden to reduce page height.

Display rules:

- Announcement is shown in one compact row visible to all teachers.
- Room headers show room, teacher, and seat information in one line, for example `Room1 · TeacherA · 4 seats`.
- Each room uses one stable color so teachers can quickly identify their room.
- Class title and teacher name should be compact, for example `Creator · TeacherA`.
- Student names show one per line for scanning.
- Student markers can include Trial, Rescheduled, Absent, and Note; colors/icons can be refined later.
- Hovering a student should show term information and admin notes.
- A full class should use an operations-friendly capacity label such as `At capacity` or `4/4 seats`, instead of only `Full`.

Performance rules:

- First load should not become slow because of full student detail, historical orders, or comments.
- Schedule should load only the data needed for the selected operating day.
- Full student profile, internal comments, and course history should load on demand after clicking a student.

### 21.2 Teacher and Room Assignment

Teacher data is currently preset for demo and operations discussions.

Rules:

- A teacher is assigned to a specific date, room, and time slot.
- Teacher names may change later, so they should not be hard-coded into student or order history.
- Teacher information first supports Schedule display and daily operations.
- If teacher login is added later, teachers should only see, or at least prioritize, their assigned room/time.

Open questions:

- Whether teachers need independent accounts.
- Whether teachers can write student performance records directly.
- Whether teachers can see parent contact information.

### 21.2.1 Operating Surfaces and Role Permissions

The expected real-world operating pattern is admin-on-desktop and teacher-on-iPad.

Product direction:

- The system should use one shared backend, one shared data model, and role-based permissions.
- Admin users should continue to use the desktop admin dashboard for full operations.
- Teacher users should have a tablet-friendly classroom workspace optimized for iPad use.
- The teacher iPad workspace is a separate front-end surface or role-specific view, not a separate system.

Admin desktop view:

- Full setup access: rooms, time slots, terms, classes, users, students, and system settings.
- Order operations: review new orders, confirm payment, edit pending orders, schedule paid orders, cancel/done orders.
- Schedule operations: daily schedule review, drag/click manual adjustment, same-day moves, sick leave, permanent course changes, revert actions, and capacity management.
- Student operations: full student profile, parent information, order/class history, internal comments, and future performance records.

Teacher iPad classroom view:

- Focuses on today's teaching operations rather than full administration.
- Shows assigned rooms/time slots first, with class rosters grouped by class name inside each room/time slot.
- Allows teachers to view student details needed for class, read schedule notes, see Trial/Makeup/Moved/Absent markers, mark attendance/absence, and write lesson comments.
- Should use touch-friendly controls, larger tap targets, and a layout suitable for iPad landscape.
- Should not require teachers to use the full desktop schedule grid for routine classroom work.

Teacher permission limits:

- Teachers must not access setup modules.
- Teachers must not access order/payment confirmation.
- Teachers must not move students, create permanent course changes, or change capacity/setup data.
- Teachers may view schedule/student information and write comments/attendance records only.

Design note:

- The current admin Schedule remains desktop-first.
- The future teacher iPad classroom view should reuse the same schedule, student, note, attendance, and comment APIs with teacher-safe permissions.

### 21.3 Student Note, Internal Comment, and Performance

The system separates three kinds of records:

- Schedule note: visible on the day schedule for temporary reminders or special handling.
- Student internal comment: admin comment stored on the student profile long-term.
- Performance record: future per-class performance record attached to the student and a concrete lesson date.

Confirmed rules:

- Note only appears on Dashboard/Schedule and is not the same as formal performance.
- Comment belongs in Student detail as long-term internal information.
- Performance will later appear in Student detail and be queryable by student and lesson date.
- Clicking a student name on Schedule should open the student detail, not only show the day's data.
- Closing student detail should return to the original Schedule date and view state.
- Student search should support the real display name, such as `Ivy Demo`, without failing because of internal username or casing.

Performance requirements:

- Student list loads summary data only.
- Course history, leave/makeup records, and internal comments load when opening student detail.
- Future performance records may grow quickly and must support paging/filtering by student, class, term, and date.

### 21.4 Manual Adjustment: One-Day Change

Admins can enter Manual Adjustment mode on the Schedule page for one selected date.

Rules:

- A one-day adjustment affects only the selected concrete date.
- It does not modify the original order or the student's long-term class.
- Moving a student must be saved before it becomes effective.
- Unsaved changes should support undo/revert.
- Saved changes record source class, target class, date, admin, and note.
- Temporary sick leave/absence can be marked separately.
- Admin chooses whether sick leave deducts one lesson; if it does, remaining lessons must be updated.
- A canceled/absent student must not appear in both Normal Students and Absent Students.
- Students who do not belong to the selected date must not appear in that day's class detail.

Capacity and conflict rules:

- Target room/time must pass capacity checks.
- A moved student cannot conflict with their own existing class on that day.
- Trial, Rescheduled, and Absent states should continue to classify correctly in class detail.
- Schedule and class detail must remain consistent after a one-day adjustment.

### 21.5 Manual Adjustment: Permanent Course Change

When a student needs to move to a different recurring class in the middle of a term, admin uses `All future classes`.

Business rules:

- A permanent change starts from an effective date.
- It affects only classes on or after the effective date.
- History before the effective date remains on the original order and class.
- The original order is not overwritten; the system splits history into an old order segment and a new order segment.
- The source order end date is shortened to the day before the effective date.
- The target order inherits the same student, parent, term, payment information, and remaining lessons.
- The target order joins the new class and becomes the student's future recurring class.
- The system records a Permanent Course Change for query and revert.
- Admin can revert the latest permanent change; revert restores the source order/class and cancels the target order.

Validation rules:

- Target class cannot be the same as the source class.
- Target class must still have at least one class date on or after the effective date.
- Target class must have capacity.
- Target time cannot conflict with the student's other active classes.
- If the student does not have a new term, changes default to the current term range only.
- Cross-term exceptions require admin confirmation and an admin note.

Current implementation limits:

- Candidate classes may be listed first, with strict capacity/conflict validation on save.
- Revert is currently suitable for demo/operations validation; later it should become a full permanent-change history view.

### 21.6 Class Detail and Student Classification Consistency

Class detail must be filtered by concrete date, not only by the class's long-term roster.

Rules:

- Normal Students shows only students who should attend normally on that date.
- Rescheduled Students shows only makeup/rescheduled students for that date.
- Trial Students shows only trial students for that date.
- Absent Students shows only canceled, leave, or sick students for that date.
- One student can belong to only one main classification for the same class/date.
- The status shown on Schedule must match the status shown after opening class detail.
- Tab count badges must match the actual list content.

### 21.7 Parent-Side Synchronization

Parent-facing pages need to progressively sync student course and reschedule information.

Rules:

- Parent order cards must show child information, especially for multi-child families.
- Parent side should have a dedicated Choose Classes entry.
- Purchased class records should show child, current class, next/recent class, and whether leave/reschedule information exists.
- Reschedule, leave, and makeup results should sync to the parent side.
- The mobile home should not show too many unrelated classes; course selection should open from the bottom navigation.
- Multi-child families need child switching, and orders/classes/reschedules should filter by selected child.

### 21.8 Demo Data and Testing

Demo data should remain rich enough for reporting and validation.

Rules:

- Demo data should include multiple parents, students, multi-child families, courses, rooms, and terms.
- It should include normal, trial, absent/canceled, makeup/rescheduled, full-room, and empty-room examples.
- The current Schedule date should contain enough students to test room color, capacity, note, student detail, one-day adjustment, and permanent change.
- Demo login information should remain stable before presentations.
- Test data must preserve the core traceable relationship: student + class + time + term.

### 21.9 Future User Manual Plan

A separate user manual should be created instead of continuing to expand this design document.

Suggested manual structure:

1. Admin login and base settings.
2. Create Room, Time, Term, and Class.
3. Manage parents, students, and orders.
4. Daily Schedule viewing.
5. One-day manual adjustment.
6. Permanent course change.
7. Leave, cancellation, and makeup handling.
8. Student detail, comment, and future performance records.
9. Parent-side common operations.
10. Demo accounts and presentation checklist.
