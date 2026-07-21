from odoo import http
from odoo.http import request
from datetime import datetime

class WebFormController(http.Controller):

    @http.route('/booking/submit', type='http', auth='public', website=True, methods=['POST'])
    def handle_web_form_submission(self, **post):
        bed_type = post.get('bed_type')
        available_room = self.env['hotel.room'].search([('bed', '=', bed_type),('state','=','available')])
        check_in = datetime.strptime(post.get('check_in'), '%Y-%m-%dT%H:%M')
        other_guest_names = str(post.get('other_guest_names')).split(',')
        accommodation_id = self.env['hotel.accommodation'].sudo().create({
            'guest': request.env.user.partner_id.id,
            'bed_type': bed_type,
            'room_id': available_room[0].id,
            'number_of_guests': len(other_guest_names)+1,
            'expected_days': post.get('expected_days'),
            'check_in': check_in,
        })
        available_room[0].state='not_available'
        if len(other_guest_names) >0:
            accommodation_id.other_guests = [self.env['accommodation.guests.lines'].sudo().create({
                'guest_ids': self.env['res.partner'].create({'name': name.strip()}).id,
            }).id for name in other_guest_names]

        return request.redirect('/thankyou_for_booking')