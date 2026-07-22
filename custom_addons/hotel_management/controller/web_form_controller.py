from odoo import http
from odoo.http import request
from datetime import datetime

class WebFormController(http.Controller):

    @http.route('/booking/submit', type='http', auth='public', website=True, methods=['POST'])
    def handle_web_form_submission(self, **post):
        other_guest_names = request.httprequest.form.getlist('other_guest_name')
        accommodation_id = self.env['hotel.accommodation'].sudo().create({
            'guest': request.env.user.partner_id.id,
            'bed_type': post.get('bed_type'),
            'room_id': int(post.get('room_id')),
            'number_of_guests': len(other_guest_names)+1,
            'expected_days': post.get('expected_days'),
            'check_in': datetime.strptime(post.get('check_in'), '%Y-%m-%dT%H:%M'),
        })
        self.env['hotel.room'].browse(int(post.get('room_id'))).state='not_available'
        other_guest_age = request.httprequest.form.getlist('other_guest_age')
        other_guest_gender = request.httprequest.form.getlist('other_guest_gender')
        if len(other_guest_names):
            accommodation_id.other_guests = [self.env['accommodation.guests.lines'].sudo().create({
                'guest_ids': self.env['res.partner'].create({
                    'name': other_guest_names[index].strip(),
                    'is_hotel_guest' : True,
                }).id,
                'age': other_guest_age[index].strip(),
                'gender': other_guest_gender[index].strip(),
            }).id for index in range(len(other_guest_names))]

        return request.redirect('/thankyou_for_booking')