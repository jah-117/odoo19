# -*- coding: utf-8 -*-
"""
edu.exam.mark.entry.wizard — Bulk mark entry & revaluation mark update
=====================================================================
Select Exam + Class → every enrolled student × every subject scheduled
for that exam loads automatically. Teacher / Admin enters marks and saves in bulk.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.orm.decorators import readonly


class EduExamMarkEntryWizard(models.TransientModel):
    _name = "edu.exam.mark.entry.wizard"
    _description = "Bulk Mark Entry Wizard"
    _rec_name = "exam_id"

    exam_id = fields.Many2one(
        "edu.exam",
        string="Exam",
        required=True,
        domain="[('state', 'in', ['scheduled', 'ongoing', 'valuation', 'result_published', 'closed'])]",
    )
    class_id = fields.Many2one(
        "education.class",
        string="Class",
        required=True,
    )
    line_ids = fields.One2many(
        "edu.exam.mark.entry.line",
        "wizard_id",
        string="Student Marks",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        exam_id = res.get("exam_id") or self.env.context.get("default_exam_id")
        class_id = res.get("class_id") or self.env.context.get("default_class_id")
        if exam_id and class_id:
            exam = self.env["edu.exam"].browse(exam_id)
            enrollments = self.env["education.enrollment"].search([
                ("class_id", "=", class_id),
                ("state", "=", "active"),
            ], order="student_name")
            subject_lines = exam.subject_line_ids
            if enrollments and subject_lines:
                lines = []
                for enr in enrollments:
                    for subj_line in subject_lines:
                        existing = self.env["edu.exam.result"].search([
                            ("exam_id", "=", exam.id),
                            ("enrollment_id", "=", enr.id),
                            ("subject_id", "=", subj_line.subject_id.id),
                        ], limit=1)
                        lines.append((0, 0, {
                            "enrollment_id": enr.id,
                            "subject_id": subj_line.subject_id.id,
                            "max_marks": subj_line.max_marks,
                            "pass_marks": subj_line.pass_marks,
                            "marks_obtained": existing.marks_obtained if existing else 0.0,
                            "absent": existing.absent if existing else False,
                        }))
                res["line_ids"] = lines
        return res

    @api.onchange("exam_id", "class_id")
    def _onchange_load(self):
        """Load all students × all exam subjects when both fields are set."""
        self.line_ids = [(5, 0, 0)]
        if not (self.exam_id and self.class_id):
            return

        enrollments = self.env["education.enrollment"].search([
            ("class_id", "=", self.class_id.id),
            ("state", "=", "active"),
        ], order="student_name")

        subject_lines = self.exam_id.subject_line_ids
        if not enrollments or not subject_lines:
            return

        lines = []
        for enr in enrollments:
            for subj_line in subject_lines:
                existing = self.env["edu.exam.result"].search([
                    ("exam_id", "=", self.exam_id.id),
                    ("enrollment_id", "=", enr.id),
                    ("subject_id", "=", subj_line.subject_id.id),
                ], limit=1)
                lines.append((0, 0, {
                    "enrollment_id": enr.id,
                    "subject_id": subj_line.subject_id.id,
                    "max_marks": subj_line.max_marks,
                    "pass_marks": subj_line.pass_marks,
                    "marks_obtained": existing.marks_obtained if existing else 0.0,
                    "absent": existing.absent if existing else False,
                }))
                print("loaded max mark",subj_line.max_marks)
        self.line_ids = lines

    def action_save_marks(self):
        """Create or update edu.exam.result for each line."""
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("No student lines to save."))

        Result = self.env["edu.exam.result"]
        saved = 0
        for line in self.line_ids:
            existing = Result.search([
                ("exam_id", "=", self.exam_id.id),
                ("enrollment_id", "=", line.enrollment_id.id),
                ("subject_id", "=", line.subject_id.id),
            ], limit=1)
            vals = {
                "marks_obtained": line.marks_obtained,
                "absent": line.absent,
                "max_marks": line.max_marks,
                "pass_marks": line.pass_marks,
            }
            print(vals)
            # If the exam is already published or closed, keep/set results as published
            if self.exam_id.state in ("result_published", "closed"):
                vals["state"] = "published"

            if existing:
                existing.write(vals)
            else:
                Result.create({
                    "exam_id": self.exam_id.id,
                    "enrollment_id": line.enrollment_id.id,
                    "subject_id": line.subject_id.id,
                    **vals,
                })
            saved += 1

        self.exam_id.sudo().message_post(
            body=_("Marks saved for %d entries — %s.") % (saved, self.class_id.name),
            author_id=self.env.user.partner_id.id,
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Results — %s") % self.class_id.name,
            "res_model": "edu.exam.result",
            "view_mode": "list,form",
            "domain": [
                ("exam_id", "=", self.exam_id.id),
                ("class_id", "=", self.class_id.id),
            ],
        }

class EduExamMarkEntryLine(models.TransientModel):
    _name = "edu.exam.mark.entry.line"
    _description = "Mark Entry Line"
    _order = "student_name, subject_id"

    wizard_id = fields.Many2one(
        "edu.exam.mark.entry.wizard",
        ondelete="cascade",
        required=True,
    )

    enrollment_id = fields.Many2one(
        "education.enrollment",
        string="Student",
        required=True,
        readonly=True,
    )

    student_name = fields.Char(
        related="enrollment_id.student_name",
        store=True,
        readonly=True,
    )

    subject_id = fields.Many2one(
        "education.subject",
        string="Subject",
        required=True,
        readonly=True,
    )

    max_marks = fields.Float(
        string="Max",
        compute="_compute_exam_marks",
        readonly=True,
    )

    pass_marks = fields.Float(
        string="Pass",
        compute="_compute_exam_marks",
        readonly=True,
    )

    marks_obtained = fields.Float(
        string="Marks",
        default=0.0,
    )

    absent = fields.Boolean(
        string="Absent",
        default=False,
    )

    @api.depends("wizard_id.exam_id", "subject_id")
    def _compute_exam_marks(self):
        ExamSubject = self.env["edu.exam.subject"]

        for line in self:
            line.max_marks = 0.0
            line.pass_marks = 0.0

            exam = line.wizard_id.exam_id

            if not exam or not line.subject_id:
                continue

            exam_subject = ExamSubject.search([
                ("exam_id", "=", exam.id),
                ("subject_id", "=", line.subject_id.id),
            ], limit=1)

            if exam_subject:
                line.max_marks = exam_subject.max_marks
                line.pass_marks = exam_subject.pass_marks

    @api.constrains("marks_obtained", "absent")
    def _check_marks_obtained(self):
        for line in self:
            if line.marks_obtained < 0:
                raise UserError(
                    _("Marks obtained cannot be less than 0.")
                )

            if line.marks_obtained > line.max_marks:
                raise UserError(
                    _(
                        "Marks obtained (%s) cannot be greater than "
                        "the maximum mark (%s) for %s."
                    )
                    % (
                        line.marks_obtained,
                        line.max_marks,
                        line.subject_id.name,
                    )
                )
