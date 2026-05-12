# CSAA Booking System Requirements

Version: 0.1
Last updated: 2026-05-11

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

Future improvements:

- Full logic should use room/time shared capacity.
- Add filters by room, category, term, and student.
- Show room grouping more clearly.
- Support student-specific schedule view.

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

Recommended admin query output:

| Student | Parent | Course | Day/Time | Term | Total Lessons | Used | Remaining |
| --- | --- | --- | --- | --- | --- | --- | --- |

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

## 18. Known Risks

- Full logic currently needs to be upgraded to shared room/time capacity.
- Class needs a clearer term relationship.
- Test data should be rebuilt around real room compatibility rules.
- Uploaded images are local files and are not stored in GitHub.
- Parent mobile flow has not started.
- Reschedule rules need to be finalized before implementation.

## 19. Suggested Next Steps

Web admin:

1. Upgrade Full logic to shared Room + Day + Time capacity.
2. Rebuild test course data based on real room compatibility.
3. Add student-centered query module.
4. Clarify Class-Term relationship.
5. Continue updating this requirements document.

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
