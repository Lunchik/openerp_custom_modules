from openerp.osv import osv, fields

import base64

class tgt_account_asset_utilazation_report(osv.osv):
    _name = 'tgt.account.asset.utilazation.report' 

    _columns = {
        'filter_id': fields.selection([
            ('draft', 'Please select the report '),
            ('all_countries','Assets Utilazation By Revenue All Countries'),
            ('all_countriesj','Assets Utilazation By Job All Countries'),

            ], ' Report of :',required=True ,size=200),
    } 
    _defaults = {
        'filter_id': 'draft',
        }

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['filter_id'], context=context)

        from ..report.asset_utilazation_report import assetutilazationreport
        report = assetutilazationreport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new', 
            'name': ' Assets utilazation report',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }
