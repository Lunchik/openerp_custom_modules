from openerp.osv import fields, osv
from ..report.base_accounting_report import CombinedReport

import base64

class accounting_report_download(osv.osv_memory):
    _name = "accounting.report.xcel.download"

    _columns = {
        'name': fields.char('File Name', size=150),
        'r_file': fields.binary('Download Report'),
    }

    _defaults = {
        'name': 'trial_balance_report.xls',
    }

    def default_get(self, cr, uid, fields, context=None):
        context = context and context or {}
        data = super(accounting_report_download, self).default_get(cr, uid, fields, context=context)
        if context.get('r_file', False):
            data['r_file'] = context.get('r_file')
        return data


class accounting_report(osv.osv_memory):
    _name = "accounting.report.xcel"
    _inherit = "account.common.report"
    _description = "Accounting Profit Report"

    _columns = {
        'name': fields.char('File Name', size=150),
        'r_file': fields.binary('Download Report'),
        'enable_filter': fields.boolean('Enable Comparison'),
        'account_report_id': fields.many2one('account.financial.report', 'Account Reports', required=True),
        'label_filter': fields.char('Column Label', size=32, help="This label will be displayed on report to show the balance computed for the given comparison filter."),
        'fiscalyear_id_cmp': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year'),
        'filter_cmp': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True),
        'period_from_cmp': fields.many2one('account.period', 'Start Period'),
        'period_to_cmp': fields.many2one('account.period', 'End Period'),
        'date_from_cmp': fields.date("Start Date"),
        'date_to_cmp': fields.date("End Date"),
        'debit_credit': fields.boolean('Display Debit/Credit Columns', help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison."),
    }

    _defaults = {
        'name': 'trial_balance_report.xls',
    }

    def default_get(self, cr, uid, fields, context=None):
        context = context and context or {}
        data = super(accounting_report, self).default_get(cr, uid, fields, context=context)

        if context.get('r_file', False):
            data['r_file'] = context.get('r_file')
        return data

    def _get_account_report(self, cr, uid, context=None):
        # TODO deprecate this it doesnt work in web
        menu_obj = self.pool.get('ir.ui.menu')
        report_obj = self.pool.get('account.financial.report')
        report_ids = []
        if context.get('active_id'):
            menu = menu_obj.browse(cr, uid, context.get('active_id')).name
            report_ids = report_obj.search(cr, uid, [('name','ilike',menu)])
        return report_ids and report_ids[0] or False

    _defaults = {
            'filter_cmp': 'filter_no',
            'target_move': 'posted',
            'account_report_id': _get_account_report,
    }
    
    def _build_comparison_context(self, cr, uid, ids, data, context=None):
        if context is None:
            context = {}
        result = {}
        result['fiscalyear'] = 'fiscalyear_id_cmp' in data['form'] and data['form']['fiscalyear_id_cmp'] or False
        result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
        result['chart_account_id'] = 'chart_account_id' in data['form'] and data['form']['chart_account_id'] or False
        result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
        if data['form']['filter_cmp'] == 'filter_date':
            result['date_from'] = data['form']['date_from_cmp']
            result['date_to'] = data['form']['date_to_cmp']
        elif data['form']['filter_cmp'] == 'filter_period':
            if not data['form']['period_from_cmp'] or not data['form']['period_to_cmp']:
                raise osv.except_osv(_('Error!'),_('Select a starting and an ending period'))
            result['period_from'] = data['form']['period_from_cmp']
            result['period_to'] = data['form']['period_to_cmp']
        return result

    def check_report1(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids, ['date_from',  'date_to',  'fiscalyear_id', 'journal_ids', 'period_from', 'period_to',  'filter',  'chart_account_id', 'target_move'], context=context)[0]
        for field in ['fiscalyear_id', 'chart_account_id', 'period_from', 'period_to']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        used_context = self._build_contexts(cr, uid, ids, data, context=context)
        data['form']['periods'] = used_context.get('periods', False) and used_context['periods'] or []
        data['form']['used_context'] = dict(used_context, lang=context.get('lang', 'en_US'))
        return self._print_report(cr, uid, ids, data, context=context)


    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = self.check_report1(cr, uid, ids, context=context)
        data = {}
        data['form'] = self.read(cr, uid, ids, ['account_report_id', 'date_from_cmp',  'date_to_cmp',  'fiscalyear_id_cmp', 'journal_ids', 'period_from_cmp', 'period_to_cmp',  'filter_cmp',  'chart_account_id', 'target_move'], context=context)[0]
        for field in ['fiscalyear_id_cmp', 'chart_account_id', 'period_from_cmp', 'period_to_cmp', 'account_report_id']:
            if isinstance(data['form'][field], tuple):
                data['form'][field] = data['form'][field][0]
        comparison_context = self._build_comparison_context(cr, uid, ids, data, context=context)
        res['datas']['form']['comparison_context'] = comparison_context
        return res

    def _print_report(self, cr, uid, ids, data, context=None):
        data['form'].update(self.read(cr, uid, ids, ['date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter','target_move'], context=context)[0])
        combined = CombinedReport(cr, uid, self.pool, '', context)
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

accounting_report()