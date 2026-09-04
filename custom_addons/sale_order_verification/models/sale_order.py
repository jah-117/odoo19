from odoo import models,_
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_quotation_send(self):
        if not self.order_line:
            raise UserError(_("No order  lines Found"))
        return super().action_quotation_send();

    def action_confirm(self):
        for line in self.order_line:
            other_line = self.order_line.filtered(lambda l: l.product_id.id != line.product_id.id)
            for product in line.product_id.restricted_product_ids:
                if product.id in other_line.mapped("product_id.id"):
                    raise UserError(_("Restricted product found"))
        else:
            return super().action_confirm()