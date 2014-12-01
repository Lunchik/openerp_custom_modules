from openerp.osv import fields, osv

from ..report.account_balance_report import TrialBalanceReport

import base64

class account_balance_report(osv.osv_memory):
    _inherit = "account.balance.report"
    _name = 'account.balance.report.xcel'
    _description = 'Trial Balance Report XCEL'

    def _get_company_ids(self, cr, uid, context=None):
        return self.pool.get('res.company').search(cr, uid, [], context=context)

    _columns = {
        'company_ids': fields.many2many('res.company', 'trial_company_rel', 'trial_id', 'company_id', string="TGT Entities"),
    }
    
    _defaults = {
        'company_ids': _get_company_ids,
    }

    def _print_report(self, cr, uid, ids, data, context=None):
        company_ids = self.read(cr, uid, ids, ['company_ids'], context=context)
        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form']['company_ids'] = company_ids[0]['company_ids']
        combined = TrialBalanceReport(cr, uid, self.pool, '', context)
        combined.set_context([], data, [])
        report = combined.generate()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Trial Balance Report',
            'datas': data,
            'context': {'r_file': base64.encodestring(report.read()),},
        }
        return {'type': 'ir.actions.report.xml', 'report_name': 'account.account.balance', 'datas': data}

account_balance_report()
