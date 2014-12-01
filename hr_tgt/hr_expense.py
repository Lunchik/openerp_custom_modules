from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID


class hr_expense_line(osv.osv):
    _inherit = "hr.expense.line"
    _description = "Expense Line"

    _columns = {
        'expense_account_id': fields.many2one('account.account', 'Expense Account'),
    }


class expense_category(osv.osv):
    _name = 'hr.expense.category'
    _description = 'Employee Expenses Categories'

    _columns = {
        'name': fields.char('Name', required=True),
        'company_id': fields.many2one('res.company', 'TGT Entity', required=True),
        'expense_account_id': fields.many2one('account.account', 'Expense Account', required=True, help='e.g. Travel Category will be "521040 Travel expenses"'),
    }

class hr_expense(osv.osv):

    _inherit = 'hr.expense.expense'
    _columns = {
        'period_id': fields.many2one('account.period', 'Force Period'),
        'state': fields.selection([
            ('draft', 'New'),
            ('cancelled', 'Refused'),
            ('confirm', 'Waiting Approval'),
            ('accepted', 'Approved'),
            ('done', 'Waiting Payment'),
            ('paid', 'Paid'),
            ],
            'Status', readonly=True, track_visibility='onchange',
            help='When the expense request is created the status is \'Draft\'.\n It is confirmed by the user and request is sent to admin, the status is \'Waiting Confirmation\'.\
            \nIf the admin accepts it, the status is \'Accepted\'.\n If the accounting entries are made for the expense request, the status is \'Waiting Payment\'.'),
    }

    def action_register_payment(self, cr, uid, ids, context=None):
        expense_id = ids and ids[0] or False
        return {
            'name': _('Expense Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.expense.payment',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': {
                'expense_id': expense_id,
            },
        }

    def action_receipt_create(self, cr, uid, ids, context=None):
        '''
        main function that is called when trying to create the accounting entries related to an expense
        '''
        move_obj = self.pool.get('account.move')
        for exp in self.browse(cr, uid, ids, context=context):
            if not exp.employee_id.account_payable_id.id:
                raise osv.except_osv(_('Error!'), _('The employee must have a payable account set on his profile.'))
            company_currency = exp.company_id.currency_id.id
            diff_currency_p = exp.currency_id.id <> company_currency
            
            #create the move that will contain the accounting entries
            cooked_data = self.account_move_get(cr, uid, exp.id, context=context)

            cooked_data['period_id'] = exp.period_id.id
            move_id = move_obj.create(cr, uid, cooked_data, context=context)
        
            #one account.move.line per expense line (+taxes..)
            eml = self.move_line_get(cr, uid, exp.id, context=context)
            
            #create one more move line, a counterline for the total on payable account
            total, total_currency, eml = self.compute_expense_totals(cr, uid, exp, company_currency, exp.name, eml, context=context)
            acc = exp.employee_id.account_payable_id.id
            eml.append({
                    'type': 'dest',
                    'name': '/',
                    'price': total, 
                    'account_id': acc, 
                    'date_maturity': exp.date_confirm, 
                    'amount_currency': diff_currency_p and total_currency or False, 
                    'currency_id': diff_currency_p and exp.currency_id.id or False, 
                    'ref': exp.name
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, exp.employee_id.address_home_id, exp.date_confirm, context=context)), eml)
            move_obj.write(cr, uid, [move_id], {'line_id': lines}, context=context)
            self.write(cr, uid, ids, {'account_move_id': move_id, 'state': 'done'}, context=context)
        return True

    def move_line_get_item(self, cr, uid, line, context=None):
        company = line.expense_id.company_id
        property_obj = self.pool.get('ir.property')
        acc = line.expense_account_id
        employee_id = line.expense_id.employee_id
        return {
            'type':'src',
            'name': line.name.split('\n')[0][:64],
            'price_unit':line.unit_amount,
            'quantity':line.unit_quantity,
            'price':line.total_amount,
            'account_id':acc.id,
            'product_id':line.product_id.id,
            'uos_id':line.uom_id.id,
            'account_analytic_id':line.analytic_account.id,
        }
