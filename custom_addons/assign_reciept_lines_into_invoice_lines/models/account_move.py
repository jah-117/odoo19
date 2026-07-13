from odoo import fields,models,api,_
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    receipt = fields.Many2one(comodel_name='stock.picking',  string="Receipt")

    def action_assign(self):
        if self.receipt and self.receipt.move_ids:
            self.update({'invoice_line_ids': [fields.Command.create({
                'product_id': move_line.product_id.id,
                'name': self.receipt.name,
                'quantity': move_line.quantity,
                'price_unit': move_line.product_id.list_price,
                'price_subtotal': move_line.quantity * move_line.product_id.list_price,
            }) for move_line in self.receipt.move_ids]})

            
    def action_post(self):
        if not self.invoice_line_ids:
            raise ValidationError('Cannot Confirm without lines')
        return super().action_post()

    def action_register_payment(self):
        if self.receipt:
            self.payment_reference = f'{self.name}, {self.receipt.name}'
        return super().action_register_payment()