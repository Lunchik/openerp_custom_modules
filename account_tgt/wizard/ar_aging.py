from openerp.osv import fields, osv
from ..report.ar_aging_report import ARAgingReport

import base64

class aging_report(osv.osv_memory):
    _name = 'ar.aging.report'
    
    def _get_company_ids(self, cr, uid, context=None):
        return self.pool.get('res.company').search(cr, uid, [], context=context)
        
    _columns = {
        'company_ids': fields.many2many('res.company', 'aging_company_rel', 'aging_id', 'company_id', string="TGT Entities"),
        #'company_id': fields.many2one('res.company', 'Target Entity', help='leave it empty to calculate AR accross entities'),
    }
    _defaults = {
        'company_ids': _get_company_ids,
        }

    def print_report(self, cr, uid, ids, context=None):
        #ids = ids and ids[0] or False

        if not ids:
            return False

        data = self.read(cr, uid, ids, ['company_ids'], context=context)
        #company_ids = self.read(cr, uid, ids, ['company_ids'], context=context)

        report = ARAgingReport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': 'AR Aging Report',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }

        raise ValueError, (data, ids)
