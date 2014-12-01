from openerp.osv import osv, fields

import base64

class tgt_hr_loding_report(osv.osv):
    _name = 'tgt.hr.loding.report'

    _columns = {
        'filter_id': fields.selection([
            ('hr_vacation', 'HR Vacation Report'),
            ('hr_loading', 'HR Loading Report'),
            ], 'Reporting by',required=True ,size=200),
    } 
    _defaults = {
        'filter_id': 'hr_vacation',
        }

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['filter_id'], context=context)

        from ..report.hr_loading import hrlodingReport
        report = hrlodingReport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': ' HR loading XLS',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }
