from odoo import models, fields
from odoo.exceptions import ValidationError


class AutomatePoWizard(models.TransientModel):
    _name = 'automate.po.wizard'

    product_id = fields.Many2one('product.template',string='Product')
    quantity = fields.Float(string='Quantity')
    unit_cost = fields.Float(string='Unit Price')

    def action_create_po(self):

        vendor = self.product_id.seller_ids[0].partner_id if self.product_id.seller_ids else False
        if not vendor:
            raise ValidationError('Please add a vendor to purchase')
        draft_po = self.env['purchase.order'].search([('partner_id','=',vendor.id),('state','not in',['purchase','to approve','cancel'])])
        draft_po = draft_po[0] if draft_po else False
        if not draft_po:
            draft_po = self.env['purchase.order'].create({'partner_id':vendor.id})
        draft_po.write({'state':'draft'})
        draft_po.update({'order_line': [fields.Command.create({
            'product_id': self.product_id.id,
            'product_qty': self.quantity,
            'price_unit': self.unit_cost,
        })]})


        self._action_rfq_send(draft_po)


        draft_po.button_confirm()

    def _action_rfq_send(self, po):
        return po.action_rfq_send

    # def action_discard(self):
    #     print('discarded')
