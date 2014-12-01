from openerp.osv import fields, osv

class hr_config_settings(osv.osv_memory):
    _name = 'hr.expense.config'

    _columns = {
        'expense_account_id': fields.many2one('account.account'),
    }


class hr_config_settings(osv.osv_memory):
    _inherit = 'hr.config.settings'

    _columns = {
        'expense_account_id': fields.many2one('account.account', 'Default Expense Account Payable', help='This is the default employees account payable for expenses'),
    }

    def get_default_expense_account_id(self, cr, uid, fields, context=None):
        ids = self.pool.get('hr.expense.config').search(cr, uid, [], context=context)
        if ids:
            ids = self.pool.get('hr.expense.config').browse(cr, uid, ids[0], context=context).expense_account_id.id
        return {'expense_account_id': ids and ids or False}

    def set_default_expense_account_id(self, cr, uid, ids, context=None):
        rec = self.browse(cr, uid, ids[0], context=context)
        expense_account_id = rec.expense_account_id.id
        ids = self.pool.get('hr.expense.config').search(cr, uid, [], context=context)
        if ids:
            self.pool.get('hr.expense.config').write(cr, uid, ids, {'expense_account_id': expense_account_id}, context=context)
        else:
            self.pool.get('hr.expense.config').create(cr, uid, {'expense_account_id': expense_account_id}, context=context)

