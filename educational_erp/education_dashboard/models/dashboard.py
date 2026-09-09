# -*- coding: utf-8 -*-
"""
education_dashboard — Dashboard data provider
=============================================
AbstractModel exposing @api.model methods consumed by the Admin and Faculty
OWL dashboard components. Returns plain dicts (KPIs + small chart series) so
the front-end stays dependency-free.
"""
from odoo import api, fields, models


class EduDashboard(models.AbstractModel):
    _name = "edu.dashboard"
    _description = "Education Dashboard Data Provider"

    # ── helpers ───────────────────────────────────────────────────────────

    @api.model
    def _has_field(self, model, fname):
        return model in self.env and fname in self.env[model]._fields

    @api.model
    def _attendance_breakdown(self, domain):
        """Return present/absent/late/excused counts + present-rate % for a
        given attendance domain."""
        Att = self.env["education.attendance"]
        total = Att.search_count(domain)
        out = {"total": total, "rate": 0.0}
        for key in ("present", "absent", "late", "excused"):
            out[key] = Att.search_count(domain + [("state", "=", key)])
        if total:
            out["rate"] = round((out["present"] + out["late"]) * 100.0 / total, 1)
        return out

    # ── ADMIN DASHBOARD ───────────────────────────────────────────────────

    @api.model
    def get_admin_dashboard(self):
        Enrollment = self.env["education.enrollment"]
        Application = self.env["education.application"]
        Exam = self.env["edu.exam"]
        Department = self.env["education.department"]
        currency = self.env.company.root_id.currency_id.symbol

        total_students = Enrollment.search_count([("state", "=", "active")])
        total_faculty = self.env["education.faculty"].search_count([])
        total_programs = self.env["education.program"].search_count([])
        total_classes = self.env["education.class"].search_count([])
        total_departments = Department.search_count([])
        pending_applications = Application.search_count([("state", "=", "submitted")])

        scholarships = "education.scholarship" in self.env
        total_active_scholarships = total_scholarship_budget = total_applications = total_approved_amount = total_approved_scholarship = total_applications_to_review = active_ids = 0
        if scholarships:
            ScholarShip = self.env["education.scholarship"]
            SApplication = self.env["education.scholarship.application"]
            active_scholarships = ScholarShip.search([('state', 'in', ['active'])])
            active_ids = active_scholarships.ids
            active_applications = SApplication.search([('scholarship_id', 'in', active_scholarships.ids)])
            total_active_scholarships = len(active_scholarships)
            total_scholarship_budget = f'{sum([s.amount * s.available_scholarships for s in active_scholarships])}{currency}'
            total_applications = len(active_applications)
            approved_scholarships = active_applications.filtered(lambda app: app.state == "approved")
            total_approved_amount = f'{sum([app.scholarship_id.amount for app in approved_scholarships])}{currency}'
            total_approved_scholarship = len(approved_scholarships)
            total_applications_to_review = len(active_applications.filtered(lambda app: app.state == "submitted"))
        hostel = "edu.hostel.property" in self.env
        total_properties = total_rooms = total_beds = total_beds_occupied = total_rooms_with_unoccupied_bed = total_amount_invoiced = 0
        if hostel:
            total_properties = self.env["edu.hostel.property"].search_count([])
            rooms = self.env["edu.hostel.room"].search([])
            total_rooms = len(rooms)
            total_beds = sum([room.capacity for room in rooms])
            total_beds_occupied = sum([room.occupied_beds for room in rooms])
            total_rooms_with_unoccupied_bed = len(rooms.filtered(lambda r: r.available_beds))
            total_amount_invoiced = f'{sum(
                [sum([invoice.amount_residual for invoice in room.invoice_ids]) for room in rooms])}{currency}'

        upcoming_exams = Exam.search_count([
            ("state", "in", ["scheduled"])
        ])
        ongoing_exams = Exam.search_count([
            ("state", "in", ["ongoing"])
        ])
        under_valuation = Exam.search_count([
            ("state", "in", ["valuation"])
        ])
        result_published = Exam.search_count([("state", "in", ["result_published"])])

        # Fees outstanding (field is contributed by financial mgmt module)
        fees_outstanding = 0
        if self._has_field("education.enrollment", "fee_state"):
            fees_outstanding = Enrollment.search_count([
                ("state", "=", "active"),
                ("fee_state", "in", ["overdue", "invoiced", "partial"]),
            ])

        attendance = self._attendance_breakdown([])

        # Students by program (top 8)
        by_program = []
        groups = Enrollment._read_group(
            [("state", "=", "active")],
            groupby=["program_id"],
            aggregates=["__count"],
        )
        for program, count in groups:
            by_program.append({"label": program.name if program else "Unassigned",
                               "value": count})
        by_program.sort(key=lambda r: r["value"], reverse=True)
        by_program = by_program[:8]

        # Applications funnel
        funnel = []
        for state, label in [("draft", "Draft"), ("submitted", "Submitted"),
                             ("approved", "Approved"), ("rejected", "Rejected")]:
            funnel.append({"label": label,
                           "value": Application.search_count([("state", "=", state)])})

        # Recent applications awaiting review
        recent = []
        for app in Application.search([("state", "=", "submitted")],
                                      limit=6, order="id desc"):
            recent.append({
                "id": app.id,
                "name": app.display_name,
                "program": app.program_id.name if app.program_id else "",
            })

        return {
            "kpis": {
                "total_students": total_students,
                "total_faculty": total_faculty,
                "total_programs": total_programs,
                "total_classes": total_classes,
                "total_departments": total_departments,
                "pending_applications": pending_applications,
                "upcoming_exams": upcoming_exams,
                "ongoing_exams": ongoing_exams,
                "under_valuation": under_valuation,
                "result_published": result_published,
                "fees_outstanding": fees_outstanding,
                "attendance_rate": attendance["rate"],
                "total_active_scholarships": total_active_scholarships,
                "total_scholarship_budget": total_scholarship_budget,
                "total_applications": total_applications,
                "total_approved_scholarship": total_approved_scholarship,
                "total_approved_amount": total_approved_amount,
                "total_applications_to_review": total_applications_to_review,
                "total_properties": total_properties,
                "total_rooms": total_rooms,
                "total_beds": total_beds,
                "total_beds_occupied": total_beds_occupied,
                "total_rooms_with_unoccupied_bed": total_rooms_with_unoccupied_bed,
                "total_amount_invoiced": total_amount_invoiced,
            },
            "active_ids": active_ids,
            "scholarships": scholarships,
            "hostel":hostel,
            "attendance": attendance,
            "by_program": by_program,
            "funnel": funnel,
            "recent_applications": recent,
        }

    # ── FACULTY DASHBOARD ─────────────────────────────────────────────────

    @api.model
    def get_faculty_dashboard(self, faculty_id=None):
        """Return a workload summary for every faculty member.

        This is intentionally not scoped to the current user: the board is
        meant to show all faculty regardless of who is looking at it.
        ``faculty_id`` is accepted for backward compatibility but is no
        longer used to filter the result.
        """
        Faculty = self.env["education.faculty"]
        faculties = Faculty.search([], order="name")
        rows = [self._faculty_summary(fac) for fac in faculties]

        return {
            "faculties": rows,
            "kpis": {
                "total_faculty": len(rows),
                "total_classes": sum(r["kpis"]["my_classes"] for r in rows),
                "total_students": sum(r["kpis"]["my_students"] for r in rows),
                "total_upcoming_exams": sum(
                    r["kpis"]["upcoming_exams"] for r in rows),
                "total_ongoing_exams": sum(
                    r["kpis"]["ongoing_exams"] for r in rows),
                "total_under_valuation": sum(
                    r["kpis"]["under_valuation_exams"] for r in rows),
                "attendance_pending": sum(
                    r["kpis"]["attendance_pending"] for r in rows),
            },
        }

    @api.model
    def _faculty_summary(self, faculty):
        """Workload summary (classes, students, subjects, attendance,
        exams) for a single faculty record."""
        Class = self.env["education.class"]
        Enrollment = self.env["education.enrollment"]
        Slot = self.env["education.timetable.slot"]
        Exam = self.env["edu.exam"]
        today = fields.Date.today()

        my_classes = Class.search([("class_teacher_id", "=", faculty.id)])
        my_slots = Slot.search([("teacher_id", "=", faculty.id)])
        # Subjects taught (from timetable slots, distinct names)
        subjects = sorted({f'{s.subject_id.name} / {s.subject_id.code}' for s in my_slots if s.subject_id})

        my_students = Enrollment.search_count([
            ("class_id", "in", my_classes.ids), ("state", "=", "active"),
        ]) if my_classes else 0

        # Attendance pending: my classes with no attendance marked today
        attendance_pending = 0
        for cls in my_classes:
            if not self.env["education.attendance"].search_count([
                ("class_id", "=", cls.id), ("date", "=", today)]):
                attendance_pending += 1

        # Upcoming exams touching my classes
        upcoming = Exam.search([
            ("state", "in", ["scheduled"]),
            ("class_ids", "in", my_classes.ids),
        ], order="date_from") if my_classes else Exam.browse()
        # Ongoing exams touching my classes
        ongoing = Exam.search([
            ("state", "in", ["ongoing"]),
            ("class_ids", "in", my_classes.ids),
        ], order="date_from") if my_classes else Exam.browse()

        under_valuation = Exam.search([
            ("state", "in", ["valuation"]),
            ("class_ids", "in", my_classes.ids),
        ], order="date_from") if my_classes else Exam.browse()

        upcoming_exams = [{
            "id": e.id,
            "name": e.name,
            "date": e.date_from and e.date_from.strftime("%d %b %Y") or "",
            "state": e.state,
        } for e in upcoming[:6]]
        ongoing_exams = [{
            "id": e.id,
            "name": e.name,
            "date": e.date_from and e.date_from.strftime("%d %b %Y") or "",
            "state": e.state,
        } for e in ongoing[:6]]
        under_valuation_exams = [{
            "id": e.id,
            "name": e.name,
            "date": e.date_from and e.date_from.strftime("%d %b %Y") or "",
            "state": e.state,
        } for e in under_valuation[:6]]

        # Per-class roster sizes
        class_rows = [{
            "id": cls.id,
            "name": cls.display_name,
            "students": Enrollment.search_count([
                ("class_id", "=", cls.id), ("state", "=", "active")]),
        } for cls in my_classes]

        attendance = self._attendance_breakdown(
            [("class_id", "in", my_classes.ids)] if my_classes else [("id", "=", 0)])

        return {
            "faculty": {
                "id": faculty.id,
                "name": faculty.name,
                "designation": faculty.designation or "",
                "department": faculty.department_id.name if faculty.department_id else "",
            },
            "kpis": {
                "my_classes": len(my_classes),
                "my_students": my_students,
                "my_subjects": len(subjects),
                "attendance_pending": attendance_pending,
                "upcoming_exams": len(upcoming),
                "ongoing_exams": len(ongoing),
                "under_valuation_exams": len(under_valuation),
                "weekly_slots": len(my_slots),
            },
            "subjects": subjects[:12],
            "upcoming_exams": upcoming_exams,
            "ongoing_exams": ongoing_exams,
            "under_valuation_exams": under_valuation_exams,
            "classes": class_rows,
            "attendance": attendance,
        }

# # -*- coding: utf-8 -*-
# """
# education_dashboard — Dashboard data provider
# =============================================
# AbstractModel exposing @api.model methods consumed by the Admin and Faculty
# OWL dashboard components. Returns plain dicts (KPIs + small chart series) so
# the front-end stays dependency-free.
# """
# from odoo import api, fields, models
#
#
# class EduDashboard(models.AbstractModel):
#     _name = "edu.dashboard"
#     _description = "Education Dashboard Data Provider"
#
#     # ── helpers ───────────────────────────────────────────────────────────
#
#     @api.model
#     def _has_field(self, model, fname):
#         return model in self.env and fname in self.env[model]._fields
#
#     @api.model
#     def _attendance_breakdown(self, domain):
#         """Return present/absent/late/excused counts + present-rate % for a
#         given attendance domain."""
#         Att = self.env["education.attendance"]
#         total = Att.search_count(domain)
#         out = {"total": total, "rate": 0.0}
#         for key in ("present", "absent", "late", "excused"):
#             out[key] = Att.search_count(domain + [("state", "=", key)])
#         if total:
#             out["rate"] = round((out["present"] + out["late"]) * 100.0 / total, 1)
#         return out
#
#     # ── ADMIN DASHBOARD ───────────────────────────────────────────────────
#
#     @api.model
#     def get_admin_dashboard(self):
#         Enrollment = self.env["education.enrollment"]
#         Application = self.env["education.application"]
#         Exam = self.env["edu.exam"]
#         today = fields.Date.today()
#
#         total_students = Enrollment.search_count([("state", "=", "active")])
#         total_faculty = self.env["education.faculty"].search_count([])
#         total_programs = self.env["education.program"].search_count([])
#         total_classes = self.env["education.class"].search_count([])
#         pending_applications = Application.search_count([("state", "=", "submitted")])
#         upcoming_exams = Exam.search_count([
#             ("state", "in", ["scheduled", "ongoing"]),
#             ("date_from", ">=", today),
#         ])
#
#         # Fees outstanding (field is contributed by financial mgmt module)
#         fees_outstanding = 0
#         if self._has_field("education.enrollment", "fee_state"):
#             fees_outstanding = Enrollment.search_count([
#                 ("state", "=", "active"),
#                 ("fee_state", "in", ["overdue", "invoiced", "partial"]),
#             ])
#
#         attendance = self._attendance_breakdown([])
#
#         # Students by program (top 8)
#         by_program = []
#         groups = Enrollment._read_group(
#             [("state", "=", "active")],
#             groupby=["program_id"],
#             aggregates=["__count"],
#         )
#         for program, count in groups:
#             by_program.append({"label": program.name if program else "Unassigned",
#                                "value": count})
#         by_program.sort(key=lambda r: r["value"], reverse=True)
#         by_program = by_program[:8]
#
#         # Applications funnel
#         funnel = []
#         for state, label in [("draft", "Draft"), ("submitted", "Submitted"),
#                              ("approved", "Approved"), ("rejected", "Rejected")]:
#             funnel.append({"label": label,
#                           "value": Application.search_count([("state", "=", state)])})
#
#         # Recent applications awaiting review
#         recent = []
#         for app in Application.search([("state", "=", "submitted")],
#                                      limit=6, order="id desc"):
#             recent.append({
#                 "id": app.id,
#                 "name": app.display_name,
#                 "program": app.program_id.name if app.program_id else "",
#             })
#
#         return {
#             "kpis": {
#                 "total_students": total_students,
#                 "total_faculty": total_faculty,
#                 "total_programs": total_programs,
#                 "total_classes": total_classes,
#                 "pending_applications": pending_applications,
#                 "upcoming_exams": upcoming_exams,
#                 "fees_outstanding": fees_outstanding,
#                 "attendance_rate": attendance["rate"],
#             },
#             "attendance": attendance,
#             "by_program": by_program,
#             "funnel": funnel,
#             "recent_applications": recent,
#         }
#
#     # ── FACULTY DASHBOARD ─────────────────────────────────────────────────
#
#     @api.model
#     def _resolve_faculty(self, faculty_id=None):
#         Faculty = self.env["education.faculty"]
#         if faculty_id:
#             return Faculty.browse(faculty_id)
#         user = self.env.user
#         # 1) via linked HR employee
#         fac = Faculty.search([("employee_id.user_id", "=", user.id)], limit=1)
#         # 2) via matching work email / login
#         if not fac and (user.email or user.login):
#             fac = Faculty.search(
#                 ["|", ("email", "=ilike", user.email or ""),
#                  ("email", "=ilike", user.login or "")], limit=1)
#         # 3) demo fallback: prefer a faculty who actually teaches a class so
#         #    admins previewing the board see populated data
#         if not fac:
#             teacher = self.env["education.class"].search(
#                 [("class_teacher_id", "!=", False)], limit=1).class_teacher_id
#             fac = teacher or Faculty.search([], limit=1)
#         return fac
#
#     @api.model
#     def get_faculty_dashboard(self, faculty_id=None):
#         faculty = self._resolve_faculty(faculty_id)
#         if not faculty:
#             return {"faculty": False}
#
#         Class = self.env["education.class"]
#         Enrollment = self.env["education.enrollment"]
#         Slot = self.env["education.timetable.slot"]
#         Exam = self.env["edu.exam"]
#         today = fields.Date.today()
#
#         my_classes = Class.search([("class_teacher_id", "=", faculty.id)])
#         my_slots = Slot.search([("teacher_id", "=", faculty.id)])
#         # Subjects taught (from timetable slots, distinct names)
#         subjects = sorted({f'{s.subject_id.name} / {s.subject_id.code}' for s in my_slots if s.subject_id})
#
#         my_students = Enrollment.search_count([
#             ("class_id", "in", my_classes.ids), ("state", "=", "active"),
#         ]) if my_classes else 0
#
#         # Attendance pending: my classes with no attendance marked today
#         attendance_pending = 0
#         for cls in my_classes:
#             if not self.env["education.attendance"].search_count([
#                     ("class_id", "=", cls.id), ("date", "=", today)]):
#                 attendance_pending += 1
#
#         # Upcoming exams touching my classes
#         upcoming = Exam.search([
#             ("state", "in", ["scheduled", "ongoing"]),
#             ("date_from", ">=", today),
#             ("class_ids", "in", my_classes.ids),
#         ], order="date_from") if my_classes else Exam.browse()
#
#         upcoming_exams = [{
#             "id": e.id,
#             "name": e.name,
#             "date": e.date_from and e.date_from.strftime("%d %b %Y") or "",
#             "state": e.state,
#         } for e in upcoming[:6]]
#
#         # Per-class roster sizes
#         class_rows = [{
#             "id": cls.id,
#             "name": cls.display_name,
#             "students": Enrollment.search_count([
#                 ("class_id", "=", cls.id), ("state", "=", "active")]),
#         } for cls in my_classes]
#
#         attendance = self._attendance_breakdown(
#             [("class_id", "in", my_classes.ids)] if my_classes else [("id", "=", 0)])
#
#         return {
#             "faculty": {
#                 "id": faculty.id,
#                 "name": faculty.name,
#                 "designation": faculty.designation or "",
#                 "department": faculty.department_id.name if faculty.department_id else "",
#             },
#             "kpis": {
#                 "my_classes": len(my_classes),
#                 "my_students": my_students,
#                 "my_subjects": len(subjects),
#                 "attendance_pending": attendance_pending,
#                 "upcoming_exams": len(upcoming),
#                 "weekly_slots": len(my_slots),
#             },
#             "subjects": subjects[:12],
#             "upcoming_exams": upcoming_exams,
#             "classes": class_rows,
#             "attendance": attendance,
#         }
