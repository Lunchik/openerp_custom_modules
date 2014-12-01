from openerp.osv import osv, fields
from openerp.tools.translate import _

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64
import os


class CycleEnum(object):
    def __init__(self, seq):
        self.seq = list(seq)
        self.cursor = 0

    def next(self):
        t = self.seq[self.cursor]
        self.cursor += 1
        if self.cursor == len(self.seq):
            self.cursor = 0
        return t



class tgt_payslip_report(osv.osv_memory):

    _name = 'tgt.payslip.report'

    _columns = {
        'date_from': fields.date('Date From'),
        'date_to': fields.date('Date To'),
        'name': fields.char('File Name', size=200),
        'r_file': fields.binary('Download Report', readonly=True),
    }


    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-01'),
        'date_to': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        'name': 'employee_payslip_report.xls',
    }


    def builder(self, cr, uid, datas, context=None):
        payslip_obj = self.pool.get('hr.payslip')
        struct_obj = self.pool.get('hr.payroll.structure')

        structures = struct_obj.search(cr, uid, [], context=context)

        book = xlwt.Workbook()
        sheet = book.add_sheet('Payslip Report')
        style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour yellow;font: height 250, bold 1;')

        lll = [
            xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;font: height 150, bold 1, color white;'),
            xlwt.Style.easyxf('pattern: pattern solid, fore_colour blue;font: height 150, bold 1, color white;'),
            xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 150, bold 1, color white;')
            ]
        ce = CycleEnum(lll)
        sheet.write(0, 0, 'Employee ID', style)
        sheet.write(0, 1, 'Employee Name', style)
        sheet.write(0, 2, 'Company', style)
        sheet.write(0, 3, 'Currency', style)
        sheet.write(0, 4, 'Total Salary', style)

        k = 5
        aaa = {}
        for ps in struct_obj.browse(cr, uid, structures, context=context):
            for l in ps.rule_ids:
                if l.appears_on_payslip:
                    if l.code == 'NET':
                        continue
                    if l.code in aaa:
                        continue
                    aaa[l.code] = k
                    sheet.write(0, k, l.name, ce.next())
                    sheet.col(k).width = 5000
                    k += 1


        # columns paddings

        sheet.col(0).width = 5000
        sheet.col(1).width = 10000
        sheet.col(2).width = 12000
        sheet.col(3).width = 4000
        sheet.col(4).width = 5000

        temp = tempfile.NamedTemporaryFile()
        #base_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        #url = os.path.join(os.path.dirname(__file__), '../static/report/employee_payslip_report.xls')
        #temp = open(url, 'w')

        #full_url = base_url + '/hr_payroll_tgt/static/report/employee_payslip_report.xls'
        r = 1
        ename_style = xlwt.Style.easyxf('font: bold 1;')
        for ps in payslip_obj.browse(cr, uid, datas['ids'], context=context):
            sheet.write(r, 0, ps.employee_id.employee_id)
            sheet.write(r, 1, ps.employee_id.name, ename_style)
            company = ps.employee_id.company_id
            currency = ps.contract_id.currency_id
            if not currency:
                currency = ps.employee_id.company_id.currency_id

            total = 0.0
            for l in ps.line_ids:
                if l.appears_on_payslip:
                    if l.code == 'NET':
                        total = l.amount
                        continue
                    iddd = aaa.get(l.code, False)
                    if iddd != False:
                        sheet.write(r, iddd, l.amount)

            sheet.write(r, 2, company and company.name or '---')
            sheet.write(r, 3, currency and currency.name or '---')
            sheet.write(r, 4, total)

            r += 1

        book.save(temp)
        #temp.close()

        return temp

    def default_get(self, cr, uid, fields, context=None):
        context = context and context or {}
        data = super(tgt_payslip_report, self).default_get(cr, uid, fields, context=context)
        if context.get('r_file', False):
            data['r_file'] = context.get('r_file')

        #base_url = self.pool.get('ir.config_parameter').get_param(cr, uid, 'web.base.url')
        #data['r_file'] = base_url + '/hr_payroll_tgt/static/reports/employee_payslip_report.xls'
        return data

    def print_report(self, cr, uid, ids, context=None):
        context = context and context or {}
        datas = self.read(cr, uid, ids, context=context)[0]
        payslip_obj = self.pool.get('hr.payslip')
        psids = payslip_obj.search(cr, uid, [('date_from', '>=', datas['date_from']), ('date_to', '<=', datas['date_to'])], context=context)
        datas['ids'] = psids or []
        #datas['ids'] = psids and payslip_obj.browse(cr, uid, psids, context=context) or []

        report = self.builder(cr, uid, datas, context=context)
        report.seek(0)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tgt.payslip.report',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Download Payslips Xcel Report',
            'context': {'r_file': base64.encodestring(report.read()),},
        }

tgt_payslip_report()