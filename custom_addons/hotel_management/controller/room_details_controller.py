from odoo import http
from odoo.http import request

# class RoomDetailsController(http.Controller):
#     @http.route('/hotel/room_details', type='http', auth='public', website=True, methods=['POST'])
#     def room_details(self):
#         print('lkdf')
#         return self.env['hotel.room'].search_read([],['id','room_no_id','bed','rent','facility_ids','state'])