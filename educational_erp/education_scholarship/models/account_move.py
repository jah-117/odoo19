from odoo import models, fields

class AccountMove(models.Model):
    _inherit = "account.move"

    invoice_type = fields.Selection(selection_add=[("scholarship", "Scholarship")])