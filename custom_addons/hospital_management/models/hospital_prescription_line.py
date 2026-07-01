from odoo import fields,models, api

class HospitalPrescriptionLine(models.Model):
    _name = 'hospital.prescription.line'

    appointment_id = fields.Many2one('hospital.appointment')
    product_id = fields.Many2one('product.product')
    dosage = fields.Char(string="Dosage")
    days = fields.Integer(string="Days")
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Price")

    @api.onchange('product_id')
    def unit_price_change(self):
        self.unit_price = self.product_id.list_price

