from odoo import  fields, models, api, _
import xlsxwriter
import io
import json
from odoo.tools import json_default

class HotelManagementReport(models.Model):
    _name = 'hotel.management.report'


    date_from = fields.Date('Date from')
    date_to = fields.Date('Date to')
    guest_name = fields.Many2one('res.partner', string='Guest')

    def _get_query(self):
        sql = """
              SELECT a.id, 
                     g.name, 
                     a.check_in,
                     a.check_out, 
                     a.state
              FROM hotel_accommodation as a 
                       JOIN
                   res_partner as g ON a.guest = g.id
              WHERE 
              """
        sql += _(""" a.guest = %(guest)s  """, guest=self.guest_name.id) if self.guest_name else ""
        sql += """ AND """ if self.guest_name and self.date_from else ""
        sql += _(""" a.check_in >= '%(date_from)s' """, date_from=self.date_from) if self.date_from else ""
        sql += """ AND """ if self.date_from and self.date_to else ""
        sql += _(""" a.check_in <= '%(date_to)s' """, date_to=self.date_to) if self.date_to else ""
        if not self.guest_name and not self.date_from and not self.date_to:
            sql += _("""
                    1 = 1 
                    """)
        self.env.cr.execute(sql)
        return self.env.cr.fetchall()

    def generate_report(self):
        result = self._get_query()
        vals = []
        for record in result:
            data={
                'id':record[0],
                'name': record[1],
                'check_in':record[2].strftime('%Y-%m-%d %H:%M:%S') if record[2] is not None else "",
                'check_out':record[3].strftime('%Y-%m-%d %H:%M:%S') if record[3] is not None else "",
                'state':record[4],
            }
            vals.append(data)
        return self.env.ref(
            'hotel_management.action_report_hotel_mangement'
        ).with_context(
            guest_name=self.guest_name.name if self.guest_name else False,
            date_from=self.date_from.strftime('%Y-%m-%d') if self.date_from else False,
            date_to=self.date_to.strftime('%Y-%m-%d') if self.date_to else False,
        ).report_action(self,data={'datas':vals})

    def generate_xlsx(self):
        data = self._get_query()
        return {
            'type':'ir.actions.report',
            'data': {
                  'model': 'hotel.management.report',
                'options': json.dumps(data, default=json_default),
                'output_format': 'xlsx',
                'report_name': 'Hotel Management Report'
            },
            'rep':'acc',
            'report_type':'xlsx',
        }

    def generate_sale_order(self):
        sql = """
        SELECT
        s.name,
        c.name,
        p.name, ol.product_uom_qty, ol.price_unit,
        i.name, i.state, i.amount_total
        FROM
            sale_order AS s
            LEFT JOIN res_partner AS c ON s.partner_id = c.id
            LEFT JOIN sale_order_line AS ol ON ol.order_id = s.id
            LEFT JOIN product_template AS p ON ol.product_id = p.id
            LEFT JOIN account_move AS i ON i.id = ol.order_id
        """

        self.env.cr.execute(sql)
        raw = self.env.cr.fetchall()
        data=[]
        for rec in raw:
            data.append(list(rec))
        print(data)
        for rec in data:
            rec[2] = rec[2]['en_US'] if rec[2] is not None else 'Product'
        return {
            'type': 'ir.actions.report',
            'data': {
                'model': 'hotel.management.report',
                'options': json.dumps(data, default=json_default),
                'output_format': 'sale',
                'report_name': 'Sales Report'
            },
            'rep':'sale',
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self,data,response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range(2,0,0,4,'Hotel Management Report',head)
        sheet.write_row(4,0,['Id','Guest','Check In','Check Out','State'],cell_format)
        row=5
        for record in data:
            sheet.write_row(row,0,record,txt)
            row+=1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def get_xlsx_report_sale(self,data,response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '12px', 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px'})
        txt = workbook.add_format({'font_size': '10px', 'align': 'center'})
        sheet.merge_range(2,0,0,4,'Sales Report',head)
        sheet.write_row(4,0,['Sale Order','Customer','Product','Quantity','Price','Invoice','State'],cell_format)
        row=5
        for record in data:
            sheet.write_row(row,0,record,txt)
            row+=1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()









