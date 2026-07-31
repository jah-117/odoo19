from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    hotel_image_ids = fields.Many2many('hotel.image', string="Hotel Images")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        if self.hotel_image_ids:
            self.env['ir.config_parameter'].sudo().set_param(
                'res.config.settings.hotel_image_ids',
                ','.join([str(image_id) for image_id in self.hotel_image_ids.ids]))
        else:
            self.env['ir.config_parameter'].sudo().set_param(
                'res.config.settings.hotel_image_ids',
                '')
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings,self).get_values()
        image_ids =self.env['ir.config_parameter'].sudo().get_param('res.config.settings.hotel_image_ids')
        res.update(hotel_image_ids=self.env['hotel.image'].browse([int(image_id) for image_id in image_ids.split(',')])) if image_ids else res
        return res

    @api.model
    def get_hotel_images(self):
        image_ids = self.env['ir.config_parameter'].sudo().get_param('res.config.settings.hotel_image_ids')
        images=False
        if image_ids:
            images=[]
            hotel_image_ids = self.env['hotel.image'].browse([int(image_id) for image_id in image_ids.split(',')])
            for hotel_image_id in hotel_image_ids:
                images.append(f'data:image/jpeg;charset=utf-8;base64,{hotel_image_id.image_1920.decode("utf-8")}')
        return {'images':images,'number_of_images':len(images)if images else 0}
