from openerp.osv import osv, fields

import base64

class tgt_account_asset_location_report(osv.osv):
    _name = 'tgt.account.asset.location.report' 

    _columns = {
        'location_id':fields.many2one('tgt.location','Location', required=True),

    }

   

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['location_id'], context=context)

        from ..report.asset_location_report import assetlocationreport
        report = assetlocationreport(data, cr, uid, self.pool, context)

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