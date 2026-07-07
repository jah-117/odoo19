import json
from odoo import http
from odoo.http import request, content_disposition, Request
from odoo.tools import html_escape

class XLSXReportController(http.Controller):
    @http.route('/xlsx_reports',type='http',auth='user',csrf=False)
    def get_report_xlsx(self, model, options, output_format, report_name,token='ads'):
        uid = request.session.uid
        report_object = request.env[model].with_user(uid)
        options=json.loads(options)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'), (
                        'Content-Disposition',
                        content_disposition(f"{report_name}.xlsx"))
                             ]
                )
                report_object.get_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response
            print(output_format)
            if output_format =='sale':
                print(report_name)
                print(options)
                response = request.make_response(
                    None,
                    headers=[('Content-Type', 'application/vnd.ms-excel'), (
                        'Content-Disposition',
                        content_disposition(f"{report_name}.xlsx"))
                             ]
                )
                report_object.get_xlsx_report_sale(options, response)
                print(report_object)
                response.set_cookie('fileToken', token)
                return response
        except Exception:
            error = {
                'code':200,
                'message':'server adich poyi :)'
            }
            return request.make_response(html_escape(json.dumps(error)))

