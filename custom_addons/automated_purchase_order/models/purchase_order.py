from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    automated = fields.Boolean(string="Automated", default=False)

    @api.model
    def _automate_confirm(self, record):
        po = self.env['purchase.order'].search([('id', '=', record.id)])
        if po.automated and po.state == 'sent':
            po.button_confirm()
