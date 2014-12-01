from openerp.osv import osv, fields

import base64

class tgt_account_asset_location_summary_report(osv.osv):
    _name = 'tgt.account.asset.summary.report' 

    _columns = {
        'filter_id': fields.selection([
            ('draft', 'draft'),
            ('summary', 'Summary Report'),


            ], ' Assets Tool Fleet :',required=True ,size=200),
    } 
    _defaults = {
        'filter_id': 'summary',
        }

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['filter_id'], context=context)

        from ..report.asset_location_summary_report import assetlocationsumaryreport
        report = assetlocationsumaryreport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new', 
            'name': ' Assets Tool fleet (location) report',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }