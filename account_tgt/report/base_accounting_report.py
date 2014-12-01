from openerp.addons.account.report.common_report_header import common_report_header
from openerp.addons.account.report.account_financial_report import report_account_common

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from .xcel_styles import FitSheetWrapper

class CombinedReport(common_report_header):
    def __init__(self, cr, uid, pool, name, context={}):
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.name = name
        self.context = context
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Accounting Report')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids
        if (data['model'] == 'ir.ui.menu'):
            new_ids = 'chart_account_id' in data['form'] and [data['form']['chart_account_id']] or []
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        self.objects = objects
        self.data = data


    def generate(self):
        self.sheet.write(0, 0, 'Company', self.style)
        self.sheet.write(0, 1, 'Account Name', self.style)
        self.sheet.write(0, 2, 'Cost Centre', self.style)
        self.sheet.write(0, 3, 'Description', self.style)
        self.sheet.write(0, 4, 'Opening Balance', self.style)
        self.sheet.write(0, 5, 'Debit', self.style)
        self.sheet.write(0, 6, 'Credit', self.style)
        self.sheet.write(0, 7, 'Ending Balance', self.style)

        # Account Type Bolding

        styles = {
            0: xlwt.Style.easyxf('font: height 230, bold 1;'),
            1: xlwt.Style.easyxf('font: height 200, bold 1;'),
            2: xlwt.Style.easyxf('font: height 190, bold 1;'),
            3: xlwt.Style.easyxf('font: height 180, bold 1;'),
            4: xlwt.Style.easyxf('font: height 170, bold 1;'),
            5: xlwt.Style.easyxf('font: height 160, bold 1;'),
            6: xlwt.Style.easyxf('font: height 150, bold 0;'),
        }

        i = 1
        for line in self.get_lines(self.data):
            bolder = styles[line['level']]
            ident = line['level']
            self.sheet.write(i, ident + 0, line['name'], bolder)
            self.sheet.write(i, 7, line['balance'], bolder)
            i += 1
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp

    def get_lines(self, data):
        lines = []
        account_obj = self.pool.get('account.account')
        currency_obj = self.pool.get('res.currency')
        ids2 = self.pool.get('account.financial.report')._get_children_by_order(self.cr, self.uid, [data['form']['account_report_id'][0]], context=data['form']['used_context'])
        for report in self.pool.get('account.financial.report').browse(self.cr, self.uid, ids2, context=data['form']['used_context']):
            vals = {
                'name': report.name,
                'balance': report.balance * report.sign or 0.0,
                'type': 'report',
                'level': bool(report.style_overwrite) and report.style_overwrite or report.level,
                'account_type': report.type =='sum' and 'view' or False, #used to underline the financial report balances
            }
            if data['form']['debit_credit']:
                vals['debit'] = report.debit
                vals['credit'] = report.credit
            if data['form']['enable_filter']:
                vals['balance_cmp'] = self.pool.get('account.financial.report').browse(self.cr, self.uid, report.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
            lines.append(vals)
            account_ids = []
            if report.display_detail == 'no_detail':
                #the rest of the loop is used to display the details of the financial report, so it's not needed here.
                continue
            if report.type == 'accounts' and report.account_ids:
                account_ids = account_obj._get_children_and_consol(self.cr, self.uid, [x.id for x in report.account_ids])
            elif report.type == 'account_type' and report.account_type_ids:
                account_ids = account_obj.search(self.cr, self.uid, [('user_type','in', [x.id for x in report.account_type_ids])])
            if account_ids:
                for account in account_obj.browse(self.cr, self.uid, account_ids, context=data['form']['used_context']):
                    #if there are accounts to display, we add them to the lines with a level equals to their level in
                    #the COA + 1 (to avoid having them with a too low level that would conflicts with the level of data
                    #financial reports for Assets, liabilities...)
                    if report.display_detail == 'detail_flat' and account.type == 'view':
                        continue
                    flag = False
                    vals = {
                        'name': account.code + ' ' + account.name,
                        'balance':  account.balance != 0 and account.balance * report.sign or account.balance,
                        'type': 'account',
                        'level': report.display_detail == 'detail_with_hierarchy' and min(account.level + 1,6) or 6, #account.level + 1
                        'account_type': account.type,
                    }

                    if data['form']['debit_credit']:
                        vals['debit'] = account.debit
                        vals['credit'] = account.credit
                    if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance']):
                        flag = True
                    if data['form']['enable_filter']:
                        vals['balance_cmp'] = account_obj.browse(self.cr, self.uid, account.id, context=data['form']['comparison_context']).balance * report.sign or 0.0
                        if not currency_obj.is_zero(self.cr, self.uid, account.company_id.currency_id, vals['balance_cmp']):
                            flag = True
                    if flag:
                        lines.append(vals)
        return lines