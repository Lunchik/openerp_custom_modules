from openerp.osv import osv, fields

import base64

class tgt_account_asset_report(osv.osv):
    _name = 'tgt.account.asset.report' 
    _description = 'asset tool fileds '

    def _get_company_ids(self, cr, uid, context=None):
        return self.pool.get('res.company').search(cr, uid, [], context=context)

    _columns = {
        'company_ids': fields.many2many('res.company', 'trial_asset_company_rel', 'trial_id', 'company_id', string="Companys"),
    }

    _defaults = {
        'company_ids': _get_company_ids,
    }

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['company_ids'], context=context)

        from ..report.asset_report import assetreport
        report = assetreport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': ' Assets report',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }