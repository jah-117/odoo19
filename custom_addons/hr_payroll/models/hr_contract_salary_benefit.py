#-*- coding: utf-8 -*-
from odoo import fields, models
import base64, io
import pymupdf4llm,fitz
from odoo.tools.pdf import OdooPdfFileReader

class HrContractSalaryBenefit(models.Model):
    _name = 'hr.contract.salary.benefit'
    _description = 'Salary Benefit'

    name = fields.Char(string="Name")
    sequence = fields.Integer(string="Sequence",default=10)
    employee_id = fields.Many2one('hr.employee',string="Employee")
    country_id = fields.Many2one('res.country',string="Country")
    active = fields.Boolean(default=True,string="Active")
    salary_rule_id = fields.Many2one(comodel_name='hr.salary.rule',string="Salary Rule")
    structure_type_id = fields.Many2one('hr.payroll.structure.type',string="Salary Structure Type")
    description = fields.Char(string="Description")

    def pdfprint(self):
        print(OdooPdfFileReader)

        pdf = self.env['ir.attachment'].browse(2393)
        pdf_bytes = base64.b64decode(pdf.datas)
        with fitz.open(stream=pdf_bytes,filetype="pdf") as doc:
            md = pymupdf4llm.to_markdown(doc)
        print(md)
        open('file.md','w').write(md)