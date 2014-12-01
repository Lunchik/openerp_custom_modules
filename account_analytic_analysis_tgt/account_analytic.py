
from openerp.osv import fields, osv

class account_analytic_journal(osv.osv):
    _inherit = 'account.analytic.journal'

    _columns = {
        'type': fields.selection([('sale','Sale'), ('purchase','Purchase'), ('cash','Cash'), ('general','General'), ('expense','Expense'), ('situation','Situation')], 'Type', size=32, required=True, help="Gives the type of the analytic journal. When it needs for a document (eg: an invoice) to create analytic entries, OpenERP will look for a matching journal of the same type."),
    }

    _defaults = {
        'type': 'general',
    }


class account_move_line(osv.osv):
    _inherit = 'account.move.line'

    _columns = {
        'company_id': fields.related('account_id', 'company_id', type='many2one', relation='res.company', 
                            string='Company', select=True, store=True),
    }

    def _prepare_analytic_line(self, cr, uid, obj_line, context=None):
        result = super(account_move_line, self)._prepare_analytic_line(cr, uid, obj_line, context=context)
        if 'salary' in context:
            company_id = context.get('company_id', False)
            company_id = company_id and company_id or self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            obj = self.pool.get('account.analytic.journal')
            jids = obj.search(cr, uid, [('company_id', '=', company_id), ('type', '=', 'expense')], context=context)

            if jids:
                result['journal_id'] = jids[0]
        return result