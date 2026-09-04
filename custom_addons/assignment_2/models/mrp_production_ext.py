from odoo import models, fields, _, api
from odoo.exceptions import UserError


class MrpProductionExt(models.Model):
    _name = 'mrp.production.ext'

    name = fields.Char(string="Name", required=True, copy=False,
                       readonly=True, default=lambda self: _('New'))
    product_id = fields.Many2one(
        'product.product',
        string='Product',
    )
    bom_id = fields.Many2one(
        'mrp.bom', 'Bill of Material')
    # available
    #
    quantity = fields.Integer(string='Quantity', default=1 )
    planned_date = fields.Date(string='Planned Date', )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status')
    material_line_ids = fields.One2many(comodel_name='mrp.production.material.line', inverse_name='production_id')
    is_material_available = fields.Boolean(default=True)
    material_count = fields.Integer(string='Number of Materials', compute='_compute_material_count')

    @api.onchange('material_line_ids')
    def _compute_material_count(self):
        if self.material_line_ids:
            self.material_count = len(self.material_line_ids)
        else:
            self.material_count = 0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            bom = self.bom_id.search([('product_tmpl_id', '=', self.product_id.product_tmpl_id)],limit=1)
            if bom:
                self.bom_id = bom
                self.is_material_available = True
            else:
                self.is_material_available = False
                # raise UserError(_("The Bom for selected product is not available"))

            if self.material_line_ids:
                self.material_line_ids = False
               # a=  [material.unlink() for material in self.material_line_ids]
            if self.bom_id:
                self.material_line_ids = [fields.Command.create({
                    'product_id': material.product_id.id,
                    'required_qty': material.product_qty * (self.quantity if self.quantity else 1),
                }) for material in self.bom_id.bom_line_ids]

    @api.onchange('quantity')
    def _onchange_quantity(self):
        if self.quantity:
            if self.bom_id:
                for material in self.material_line_ids:
                    bom_materail = self.bom_id.bom_line_ids.filtered(
                        lambda rec: rec.product_id == material.product_id)
                    material.required_qty = bom_materail.product_qty * self.quantity
    def action_confirm(self):
        if self.bom_id and self.quantity >0:
            self.state = 'confirmed'
        else:
            raise UserError(_('Please select a bom line or update quantity.'))
    def action_start_production(self):
        if not self.material_line_ids.filtered(lambda rec: rec.required_qty > rec.available_qty):
            self.state = 'in_progress'
        else:
            raise UserError(_('Materials are not available in stock.'))
    def action_consume_quantity(self):
        for material in self.material_line_ids:
            material.consumed_qty = material.required_qty
    def action_open_orders(self):
        return {
            'name': _('Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.material.line',
            'domain': [('production_id', '=', self.id)],
            'view_mode': 'list',
        }
    def action_mark_as_done(self):
        for material in self.material_line_ids:
            ...

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if val.get('name', _("New")) == _("New"):
                val['name'] = (self.env['ir.sequence']
                               .next_by_code('man.seq') or _("New"))
        return super().create(vals)
    #
    # @api.onchange('bom_id')
    # def _onchange_bom_id(self):
    #     if self.material_line_ids:
    #         [material.unlink() for material in self.material_line_ids]
    #     if self.bom_id:
    #         self.material_line_ids = [fields.Command.create({
    #             'product_id': material.product_id.id,
    #             'required_qty': material.product_qty * (self.quantity if self.quantity else 1),
    #         }) for material in self.bom_id.bom_line_ids]

