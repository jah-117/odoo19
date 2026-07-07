from odoo import  fields, models, api, _
from odoo.exceptions import  MissingError
from odoo.tests import result


class HotelManagementReport(models.Model):
    _name = 'hotel.management.report'


    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    guest_name = fields.Many2one('res.partner', string='Guest')

    def generate_report(self):
        sql = """
        SELECT 
            id
        FROM hotel_accommodation WHERE 
        """
        sql += _(""" guest = %(guest)s  """, guest=self.guest_name.id) if self.guest_name else ""
        sql += """ AND """if self.guest_name and self.date_from else ""
        sql += _(""" check_in >= '%(date_from)s' """, date_from=self.date_from) if self.date_from else ""
        sql += """ AND """ if self.date_from and self.date_to else ""
        sql += _(""" check_in <= '%(date_to)s' """, date_to=self.date_to) if self.date_to else ""
        if not self.guest_name and not self.date_from and not self.date_to:
            sql += _("""
            1 = 1 
            """)
        self.env.cr.execute(sql)
        result = self.env.cr.fetchall()
        print(result)
        records = self.env['hotel.accommodation'].search([('id', 'in', result)])
        print(records)
        return self.env.ref(
            'hotel_management.action_report_hotel_mangement'
        ).with_context(
            guest_name=self.guest_name,
            date_from=self.date_from,
            date_to=self.date_to
        ).report_action(records)

