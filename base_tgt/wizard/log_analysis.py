from openerp.osv import osv, fields

from datetime import datetime

import base64

class log_analysis(osv.osv):
    _name = 'tgt.log.analysis'

    def _get_company_ids(self, cr, uid, context=None):
        return self.pool.get('res.company').search(cr, uid, [], context=context)

    _columns = {
        'company_ids': fields.many2many('res.company', 'log_sale_company_rel', 'log_id', 'company_id', required=True, string='TGT Entities'),
        'date_from': fields.date('From date', required=True),
        'date_to': fields.date('To Date', required=True),
    }

    _defaults = {
        'company_ids': _get_company_ids,
        'date_from': lambda *args: datetime.today().strftime('%Y-01-01'),
        'date_to': lambda *args: datetime.today().strftime('%Y-%m-%d'),
    }

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['company_ids', 'date_to', 'date_from'], context=context)

        from ..report.log_analysis_report import LogAnalysisReport
        report = LogAnalysisReport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Well Logging Analysis',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }