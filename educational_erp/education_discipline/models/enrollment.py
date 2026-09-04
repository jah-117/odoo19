from odoo import fields, models


class Enrollment(models.Model):
    _inherit = "education.enrollment"

    discipline_case_ids = fields.One2many(
        "education.discipline.case", "student_id", string="Discipline Cases"
    )
    discipline_case_count = fields.Integer(
        string="Discipline Case Count", compute="_compute_discipline_case_count"
    )

    def _compute_discipline_case_count(self):
        for record in self:
            record.discipline_case_count = len(record.discipline_case_ids)

    def action_view_discipline_cases(self):
        self.ensure_one()
        return {
            "name": "Discipline Cases",
            "type": "ir.actions.act_window",
            "res_model": "education.discipline.case",
            "view_mode": "list,form",
            "domain": [("student_id", "=", self.id)],
            "context": {"default_student_id": self.id},
        }
