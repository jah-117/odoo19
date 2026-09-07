from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_type = fields.Selection(
        selection_add=[("exam_fee", "Exam Fee")],
    )