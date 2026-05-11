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
