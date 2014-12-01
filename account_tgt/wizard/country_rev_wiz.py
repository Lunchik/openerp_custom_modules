from openerp.osv import fields, osv
from ..report.cou_rev import revenue_by_country_mtm,revenue_by_country_ytd

import base64

class co_report(osv.osv_memory):
    _name = 'cou_re'
    
    
    _columns = {
        'mon':fields.selection([('jan', 'Jan'), ('feb', 'Feb'),('mar', 'Mar'), ('apr', 'Apr'), ('may', 'May'),('jun', 'Jun'),('jul', 'Jul'), ('aug', 'Aug'), ('sep', 'Sep'),('oct', 'Oct'), ('nov', 'Nov') ,('des', 'Dec')], 'Month'),
    }
   

    def print_report(self, cr, uid, ids, context=None):
        #ids = ids and ids[0] or False

        if not ids:
            return False

        data = self.read(cr, uid, ids, ['mon'], context=context)
        #company_ids = self.read(cr, uid, ids, ['company_ids'], context=context)

        report = revenue_by_country_mtm(cr, uid, self.pool, context)

        temp = report.generate_by_mtm(data)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Revenue Per Country MTM Vs Target',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }

        #raise ValueError, (data, ids)
class co_y_report(osv.osv_memory):
    _name = 'cou_re_y'
    
    
    _columns = {
        'mon':fields.selection([('jan', 'Jan'), ('feb', 'Feb'),('mar', 'Mar'), ('apr', 'Apr'), ('jun', 'Jun'),('jul', 'Jul'), ('aug', 'Aug'), ('sep', 'Sep'),('oct', 'Oct'), ('nov', 'Nov') ,('des', 'Des')], 'Month'),
    }
   

    def print_report(self, cr, uid, ids, context=None):
        #ids = ids and ids[0] or False

        if not ids:
            return False

        data = self.read(cr, uid, ids, ['mon'], context=context)
        #company_ids = self.read(cr, uid, ids, ['company_ids'], context=context)

        report = revenue_by_country_ytd(cr, uid, self.pool, context)

        temp = report.generate_by_ytd(data)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Revenue Per Country YTD Vs Target',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }
