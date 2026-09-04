# -*- coding: utf-8 -*-
"""
education_hostel — Unit Tests
================================
Covers:
  - Initial room availability
  - Allocation confirm: state + room occupancy
  - Allocation vacate: state + room freed
  - Duplicate active allocation raises UserError
  - date_to < date_from raises ValidationError
  - Property room_count / occupied_count computed fields
  - Portal students can only read their own hostel allocations
"""
from datetime import date, timedelta

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from odoo import fields


@tagged("post_install", "-at_install")
class TestHostel(TransactionCase):
    """Unit tests for the education_hostel module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Hostel property ───────────────────────────────────────────────
        cls.property = cls.env["edu.hostel.property"].create({
            "name": "Test Hostel Block A",
            "total_capacity": 10,
        })
        cls.room_type = cls.env["edu.hostel.room.type"].create({
            "name": "Single",
            "fee": 100.0,
        })

        # ── Room ──────────────────────────────────────────────────────────
        cls.room = cls.env["edu.hostel.room"].create({
            "property_id": cls.property.id,
            "room_no": "101",
            "room_type_id": cls.room_type.id,
            "capacity": 1,
        })

        # ── Enrollment (via application workflow) ─────────────────────────
        cls.academic_year = cls.env["education.academic.year"].create({
            "name": "Hostel Test Year",
            "code": "HSTYR26",
            "date_start": date(2025, 7, 1),
            "date_end": date(2026, 6, 30),
            "is_current": False,
        })
        cls.department = cls.env["education.department"].create({
            "name": "Hostel Test Dept",
            "code": "HSTDEPT",
        })
        cls.program = cls.env["education.program"].create({
            "name": "Hostel Test Program",
            "code": "HSTPROG",
            "department_id": cls.department.id,
            "degree_type": "bachelor",
            "duration_years": 3,
        })
        app = cls.env["education.application"].create({
            "first_name": "Charlie",
            "last_name": "HostelStudent",
            "date_of_birth": date.today() - timedelta(days=365 * 19),
            "gender": "male",
            "email": "charlie.hostel@example.com",
            "phone": "3333333333",
            "program_id": cls.program.id,
            "academic_year_id": cls.academic_year.id,
        })
        app.action_submit()
        app.action_approve()
        cls.enrollment = app.enrollment_id

    def _create_enrollment(self, number):
        app = self.env["education.application"].create({
            "first_name": "Hostel",
            "last_name": "Student%s" % number,
            "date_of_birth": date.today() - timedelta(days=365 * 19),
            "gender": "male",
            "email": "hostel.student%s@example.com" % number,
            "phone": "33333333%s" % number,
            "program_id": self.program.id,
            "academic_year_id": self.academic_year.id,
        })
        app.action_submit()
        app.action_approve()
        return app.enrollment_id

    # ── Initial state ─────────────────────────────────────────────────────

    def test_room_initially_available(self):
        """A newly created room should have state='available'."""
        self.assertEqual(self.room.state, "available")

    # ── Confirm allocation ────────────────────────────────────────────────

    def test_confirm_allocation(self):
        """action_confirm() should set allocation state=confirmed and room.state=occupied."""
        alloc = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc.action_confirm()
        self.assertEqual(alloc.state, "confirmed")
        self.assertEqual(self.room.state, "occupied")
        # Clean up for other tests
        alloc.action_vacate()

    # ── Vacate allocation ─────────────────────────────────────────────────

    def test_vacate_allocation(self):
        """action_vacate() should set allocation state=vacated and room.state=available."""
        alloc = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc.action_confirm()
        self.assertEqual(alloc.state, "confirmed")
        alloc.action_vacate()
        self.assertEqual(alloc.state, "vacated")
        self.assertEqual(self.room.state, "available")

    def test_room_capacity_updates_occupancy_and_blocks_overbooking(self):
        room = self.env["edu.hostel.room"].create({
            "property_id": self.property.id,
            "room_no": "201",
            "room_type_id": self.room_type.id,
            "capacity": 2,
        })
        first = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": room.id,
            "date_from": fields.Date.today(),
        })
        first.action_confirm()
        self.assertEqual(room.occupied_beds, 1)
        self.assertEqual(room.available_beds, 1)
        self.assertEqual(room.state, "partially_occupied")

        second = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self._create_enrollment(2).id,
            "room_id": room.id,
            "date_from": fields.Date.today(),
        })
        second.action_confirm()
        self.assertEqual(room.occupied_beds, 2)
        self.assertEqual(room.available_beds, 0)
        self.assertEqual(room.state, "occupied")

        third = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self._create_enrollment(3).id,
            "room_id": room.id,
            "date_from": fields.Date.today(),
        })
        with self.assertRaises(UserError):
            third.action_confirm()

    # ── Duplicate allocation raises UserError ─────────────────────────────

    def test_duplicate_allocation_raises(self):
        """Confirming a second allocation for the same student should raise UserError."""
        alloc1 = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc1.action_confirm()

        # Create a second room so the room-availability is not the blocker
        room2 = self.env["edu.hostel.room"].create({
            "property_id": self.property.id,
            "room_no": "102",
            "room_type_id": self.room_type.id,
            "capacity": 1,
        })
        alloc2 = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": room2.id,
            "date_from": fields.Date.today(),
        })
        with self.assertRaises(UserError):
            alloc2.action_confirm()

        # Clean up
        alloc1.action_vacate()

    # ── Date constraint ───────────────────────────────────────────────────

    def test_date_constraint(self):
        """date_to earlier than date_from should raise ValidationError."""
        with self.assertRaises(ValidationError):
            self.env["edu.hostel.allocation"].create({
                "enrollment_id": self.enrollment.id,
                "room_id": self.room.id,
                "date_from": fields.Date.today(),
                "date_to": fields.Date.today() - timedelta(days=1),
            })

    # ── Property computed counts ──────────────────────────────────────────

    def test_room_counts(self):
        """property.room_count should be 1; occupied_count should be 1 after confirming an allocation."""
        self.property._compute_room_counts()
        # room_count counts ALL rooms linked to this property (at least 1)
        self.assertGreaterEqual(self.property.room_count, 1)

        alloc = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": self.room.id,
            "date_from": fields.Date.today(),
        })
        alloc.action_confirm()
        self.property._compute_room_counts()
        self.assertGreaterEqual(self.property.occupied_count, 1)

        # Clean up
        alloc.action_vacate()

    def test_portal_student_only_sees_own_confirmed_allocation(self):
        """The portal record rule must never reveal another student's room."""
        room = self.env["edu.hostel.room"].create({
            "property_id": self.property.id,
            "room_no": "301",
            "room_type_id": self.room_type.id,
            "capacity": 2,
        })
        own_allocation = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self.enrollment.id,
            "room_id": room.id,
            "date_from": fields.Date.today(),
        })
        other_allocation = self.env["edu.hostel.allocation"].create({
            "enrollment_id": self._create_enrollment(4).id,
            "room_id": room.id,
            "date_from": fields.Date.today(),
        })
        own_allocation.action_confirm()
        other_allocation.action_confirm()

        portal_group = self.env.ref("base.group_portal")
        portal_user = self.env["res.users"].create({
            "name": "Hostel Portal Student",
            "login": "hostel.portal.student@example.com",
            "partner_id": self.enrollment.student_partner_id.id,
            "groups_id": [(6, 0, [portal_group.id])],
        })

        visible_allocations = self.env["edu.hostel.allocation"].with_user(portal_user).search([])
        self.assertEqual(visible_allocations, own_allocation)
