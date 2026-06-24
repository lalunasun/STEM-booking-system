# CSAA Test Audit - 2026-06-22

## Summary

- Django system check: PASS
- Existing backend tests: 8 PASS
- Frontend production build: PASS
- Frontend automated test runner: NOT CONFIGURED
- Isolated order/security probes: 18 FAIL
- Existing demo database was not modified. Probe tests used a temporary test database.

This audit tests current executable behavior. Rules that have not been implemented, such as automatic cancellation, are listed separately instead of being marked as failed runtime tests.

## Existing Tests That Pass

1. A student is hidden from a lesson before the enrollment start date.
2. A student appears on the enrollment start date.
3. A schedule-change request rejects a date on which the class does not meet.
4. Multiple absence weeks are retained and sorted.
5. Parent adjustment results can be filtered by child ID.
6. Makeup recommendations avoid the student's existing time conflict.
7. Makeup recommendations stay inside the current term without future enrollment.
8. Future-term makeup is offered only after a future enrollment exists.

## Confirmed Failures

### P0 - Authorization and data isolation

1. Parent order list can be read without authentication by changing `userId`.
2. Parent child list can be read without authentication by changing `parent`.
3. Parent schedule-change list can be read without authentication by changing `parent_id`.
4. Admin order list can be read without an admin token.
5. An authenticated parent can cancel another parent's order by changing the order ID.
6. An authenticated parent can mark another parent's order as paid by changing the order ID.
7. A parent can create an order using a child belonging to another parent.

Impact: multi-child and multi-family data are not safely isolated even though records have separate IDs.

### P0 - Order state integrity

8. A canceled order can be changed back to Paid.
9. A Scheduled order can be canceled through the parent order-cancel endpoint.
10. An administrator can schedule an unpaid order.
11. Manual payment changes the status but does not populate `pay_time`.

Required state flow:

`Pending payment -> Paid -> Scheduled -> Done`

`Pending payment -> Canceled`

Other backwards or cross-state transitions should be rejected unless a dedicated administrator correction/refund workflow exists.

### P0 - Enrollment uniqueness and capacity

12. The database does not enforce a unique enrollment for `child + class + term`.
13. Two pending orders for the same child, class, and term can be created.
14. Pending orders are counted as occupied seats during order creation.
15. Pending orders are not counted as occupied seats by the class-list serializer.
16. When existing enrollment is already over capacity, the create-order check only tests `remaining == 0`; a negative remaining count allows another order.

The capacity rule is therefore inconsistent between display and order creation.

### P0 - Lesson roster integrity

17. A Pending payment order immediately adds the child to `Lesson.students` and increments `students_num`.
18. Canceling an order does not remove the child from the lesson roster or decrement `students_num`.

Impact: dashboard totals and lesson details can disagree with actual paid/scheduled enrollment.

### P1 - Reporting and search

19. Admin order list ignores a supplied child filter and returns orders for all children.
20. Combined reporting by child, class, time, and term is not implemented as a supported API contract.
21. Same-name children have separate database IDs, but current unprotected list/mutation endpoints make reliable family isolation impossible.

### P1 - Windows/runtime robustness

22. Authentication classes print Chinese diagnostic text directly to stdout. Under a non-UTF-8 Windows test process this raises `UnicodeEncodeError` and turns valid authenticated requests into server errors.

## Not Implemented / Pending Decisions

1. Automatic cancellation of unpaid orders after 48 hours: NOT IMPLEMENTED.
2. The 48-hour duration is still a business decision and should be configurable.
3. Warning notification before automatic cancellation: NOT IMPLEMENTED.
4. Automatic-cancel system message: NOT IMPLEMENTED.
5. Idempotent scheduled job for automatic cancellation: NOT IMPLEMENTED.
6. Payment gateway integration: intentionally out of scope; payment is currently manual.
7. Read/unread persistent system notifications: NOT IMPLEMENTED. Mobile messages are currently derived from adjustment records.
8. Concurrent last-seat booking: not safely testable with the current SQLite setup and no transaction/locking implementation.
9. Concurrent makeup confirmation for the last seat: requires transaction and locking coverage.
10. Full frontend interaction tests: no Vitest, Cypress, or Playwright test configuration exists.

## Recommended Fix Order

1. Lock down all parent/admin list and mutation endpoints using the authenticated identity, never a caller-supplied owner ID.
2. Define and enforce the order state machine.
3. Add an enrollment identity/constraint for active `child + class + term` records.
4. Make capacity use one shared definition: only Paid and Scheduled reserve seats.
5. Add/remove lesson roster membership only when the order enters/leaves Scheduled.
6. Add child/class/time/term filters and aggregate reporting.
7. Implement configurable unpaid-order expiry after the 48-hour rule is confirmed.
8. Add transaction-based concurrency tests using the production database engine.

## Commands Run

```text
python manage.py check
python manage.py test CSAA -v 2
npm run build
python manage.py test CSAA.tests_audit_probe -v 1
```

