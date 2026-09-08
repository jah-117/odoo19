from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_type = fields.Selection(
        selection_add=[("exam_fee", "Exam Fee")],
    )
    exam_id = fields.Many2one(comodel_name="edu.exam", string="Exam")