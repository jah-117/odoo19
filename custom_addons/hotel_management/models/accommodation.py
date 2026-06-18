from odoo import fields,models,api


class Accommodation(models.Model):
    _name = 'hotel.accommodation'

    # number = fields.Char(string="Accommodation Number", required=True, copy=False, readonly=True, defaul='New')
    #
    #
    # @api.model
    # def create(self,vals):
    #     if vals.get('number','New')== 'New':
    #         vals['number']=self.env['ir.sequence'].next_by_code('acc.seq') or 'New'
    #     return super(Accommodation,self).create(vals)
    name = fields.Selection(default = 'single',selection=[('single',"Single"),('double',"Double"),('dormitory',"Dormitory")],string="Bed Type", required = True)