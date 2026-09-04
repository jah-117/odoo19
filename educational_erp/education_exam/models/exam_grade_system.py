# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EduExamGradeSystem(models.Model):
    """Configurable grading system for schools/colleges (e.g. 10-Point CGPA, Letter Grade, GPA)."""

    _name = "edu.exam.grade.system"
    _description = "Examination Grading System"
    _order = "is_default desc, name"

    name = fields.Char(
        string="Grading System Name",
        required=True,
        help="e.g. Standard 10-Point Scale, US 4.0 GPA Scale, CBSE 9-Point Scale",
    )
    code = fields.Char(
        string="Code",
        help="Short code or identifier",
    )
    is_default = fields.Boolean(
        string="Default System",
        default=False,
        help="If checked, this grading system is used automatically when none is specified on an exam.",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        help="Company/Campus this grading system belongs to. Leave empty for all companies.",
    )
    description = fields.Text(
        string="Description / Policy",
        help="Institutional rules, passing criteria, or remarks for this grading scale.",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    line_ids = fields.One2many(
        "edu.exam.grade.line",
        "grade_system_id",
        string="Grade Levels",
        copy=True,
    )

    def get_grade_info(self, percentage):
        """Evaluate a score percentage and return matching grade details."""
        self.ensure_one()
        for line in self.line_ids.sorted(key=lambda l: (l.sequence, -l.min_percentage)):
            if line.min_percentage <= percentage <= line.max_percentage:
                return {
                    "grade": line.name,
                    "grade_point": line.grade_point,
                    "pass_fail": line.pass_fail,
                    "description": line.description or "",
                }
        # Fallback if no specific bracket matches
        return {
            "grade": "F" if percentage < 50 else "P",
            "grade_point": 0.0,
            "pass_fail": "fail" if percentage < 50 else "pass",
            "description": "Unclassified",
        }


class EduExamGradeLine(models.Model):
    """Individual grade level within a grading scale."""

    _name = "edu.exam.grade.line"
    _description = "Grading Scale Level"
    _order = "sequence, min_percentage desc"

    grade_system_id = fields.Many2one(
        "edu.exam.grade.system",
        string="Grading System",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    name = fields.Char(
        string="Grade",
        required=True,
        help="e.g. A+, A, Distinction, O, 10",
    )
    min_percentage = fields.Float(
        string="Min %",
        required=True,
        digits=(5, 2),
        help="Minimum percentage score to achieve this grade (inclusive)",
    )
    max_percentage = fields.Float(
        string="Max %",
        required=True,
        digits=(5, 2),
        help="Maximum percentage score for this grade (inclusive)",
    )
    grade_point = fields.Float(
        string="Grade Point",
        default=0.0,
        digits=(4, 2),
        help="Numeric weight or GPA value (e.g. 4.0, 10.0)",
    )
    pass_fail = fields.Selection(
        selection=[
            ("pass", "Pass"),
            ("fail", "Fail"),
        ],
        string="Result Status",
        default="pass",
        required=True,
    )
    description = fields.Char(
        string="Remarks",
        help="e.g. Outstanding, Excellent, Very Good, Average, Fail",
    )

    @api.constrains("min_percentage", "max_percentage")
    def _check_percentages(self):
        for rec in self:
            if rec.min_percentage < 0.0 or rec.max_percentage > 100.0:
                raise ValidationError(_("Percentage limits must be between 0.0% and 100.0%."))
            if rec.min_percentage > rec.max_percentage:
                raise ValidationError(
                    _("Min percentage (%(min).2f%%) cannot exceed Max percentage (%(max).2f%%) for grade '%(grade)s'.",
                      min=rec.min_percentage, max=rec.max_percentage, grade=rec.name)
                )
