from odoo import fields,models

class HospitalPrescriptionLine(models.Model):
    _name = 'hospital.prescription.line'

    appointment_id = fields.Many2one('hospital.appointment')
    product_id = fields.Many2one('product.product')
    dosage = fields.Char(string="Dosage")
    days = fields.Integer(string="Days")
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Price")
    