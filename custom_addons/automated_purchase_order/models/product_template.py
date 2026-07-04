from odoo import models

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_create_po(self):
        # ir_model_data = self.env['ir.model.data']
        # template_id = ir_model_data._xmlid_lookup('purchase.email_template_edi_purchase')[1]
        # mail_template = self.env['mail.template'].search([('id','=',template_id)])
        # mail_template.send_mail(self.id)
        # self.state = 'sent'
        # return super().button_confirm()
        return {
            'type':'ir.actions.act_window',
            'res_model': 'automate.po.wizard',
            'name':self.name,
            'view_mode':'form',
            'target':'new',
            'context':{
                'default_product_id':self.id,
                'default_unit_cost':self.standard_price,
            }
        }