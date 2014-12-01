from openerp.osv import fields, osv
from ..report.account_billing_report import AccountBillingReport, AccountReceivableReport

from datetime import datetime, timedelta

import base64

class aging_report(osv.osv_memory):
    _name = 'account.billing.report'


    def _get_company_id(self, cr, uid, context=None):
        return self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id

    def _get_fiscal_year(self, cr, uid, context=None):
        fyobj = self.pool.get('account.fiscalyear')
        n = datetime.today()
        dst = datetime(n.year, 1, 1)
        dsp = datetime(n.year, 12, 31)
        ids = fyobj.search(cr, uid, [('date_start', '>=', dst.strftime('%Y-%m-%d')), ('date_stop', '<=', dsp.strftime('%Y-%m-%d'))], context=context)
        return ids[0]

    _columns = {
        'company_id': fields.many2one('res.company', string="TGT Entity"),
        'year': fields.many2one('account.fiscalyear', string="Fiscal Year"),
        'type': fields.selection([('billing', 'Billing Report'), ('receivable', 'Account Receivable Report'),], string="Target"),
        'filter': fields.selection([('date_due', 'Due Date'), ('date_invoice', 'Invoice Date'),], string="Filter by"),
    }

    _defaults = {
        'year': _get_fiscal_year,
        'company_id': _get_company_id,
    }

    def print_report(self, cr, uid, ids, context=None):
        #ids = ids and ids[0] or False

        if not ids:
            return False

        data = self.read(cr, uid, ids, ['filter', 'type', 'year'], context=context)
        report = 0
        if data[0]['type'] == 'billing':
            report = AccountBillingReport(data, cr, uid, self.pool, context)
        else:
            report = AccountReceivableReport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Billing Report',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }

