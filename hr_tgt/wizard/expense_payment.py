from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import SUPERUSER_ID

import datetime


class hr_expense_line(osv.osv_memory):

    _name = 'hr.expense.payment'
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'journal_id': fields.many2one('account.journal', 'Payment Method'),
        'period_id': fields.many2one('account.period', 'Force Period'),
        'amount': fields.float('Amount'),
        'company_id': fields.many2one('res.company'),
        'currency_id': fields.many2one('res.currency', 'Currency'),
    }

    def _get_company_id(self, cr, uid, context=None):
        context = context and context or {}
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        return expense.employee_id.company_id.id

    def _get_employee_id(self, cr, uid, context=None):
        context = context and context or {}
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        return expense.employee_id.id

    def _get_period_id(self, cr, uid, context=None):
        context = context and context or {}
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        #return 1
        return expense.period_id.id

    def _get_journal_id(self, cr, uid, context=None):
        context = context and context or {}
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        company_id = expense.employee_id.company_id
        company_id = company_id and company_id or False
        if not company_id:
            raise osv.except_osv("Warning", 'Employee must belong to company')
        journals = self.pool.get('account.journal').search(cr, uid, [('company_id','=',company_id.id),('type','=','bank')], context=context)
        return journals and journals[0] or False

    def _get_amount(self, cr, uid, context=None):
        context = context and context or {}
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        currency_id = expense.currency_id.id
        amount = 0.0
        for line in expense.account_move_id.line_id:
            if line.account_id.type == 'payable':
                amount = line.credit
                if currency_id != expense.company_id.currency_id.id:
                    amount = line.amount_currency
                amount = amount < 0 and amount * -1 or amount
                break
        return amount

    def _get_currency_id(self, cr, uid, context=None):
        pass
        context = context and context or {}
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        return expense.currency_id.id

    _defaults = {
        'employee_id': _get_employee_id,
        'journal_id': _get_journal_id,
        'period_id': _get_period_id,
        'amount': _get_amount,
        'company_id': _get_company_id,
        'currency_id': _get_currency_id,
    }


    def register_payment(self, cr, uid, ids, context=None):
        if not ids:
            return False

        ids = ids[0]
        period_pool = self.pool.get('account.period')
        expense_id = context.get('expense_id', False)
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        record = self.browse(cr, uid, ids, context=context)
        ctx = dict(context or {}, account_period_prefer_normal=True, company_id=expense.company_id.id)
        search_periods = period_pool.find(cr, uid, expense.date, context=ctx)
        period_id = search_periods[0]
        period_id = record.period_id.id
        debit_line = False
        for line in expense.account_move_id.line_id:
            if line.account_id.type == 'payable':
                debit_line = line
                break
        timenow = datetime.datetime.today()
        move = {
            'narration': '%s Payment' % expense.name,
            'company_id': expense.company_id.id,
            'date': timenow,
            'ref': '%s Payment' % expense.name,
            'journal_id': record.journal_id.id,
            'period_id': period_id,
        }

        line_ids = []
        amt_curr = 0.0
        if expense.currency_id.id != expense.company_id.currency_id.id:
            amt_curr = line.amount_currency
        amt_curr = amt_curr < 0.0 and -1 * amt_curr or amt_curr
        cur_id = False
        if expense.currency_id.id != expense.company_id.currency_id.id:
            cur_id = expense.currency_id.id
        debit_line_ids = (0, 0, {
            'company_id': expense.company_id.id,
            'name': '/',
            'date': timenow,
            'account_id': debit_line.account_id.id,
            'journal_id': record.journal_id.id,
            'period_id': period_id,
            'debit': line.credit,
            'credit': 0.0,
            'currency_id': cur_id,
            'amount_currency': amt_curr,
            #'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
            'analytic_account_id': False,
            'tax_code_id': False,
            'tax_amount': 0.0,
        })

        line_ids.append(debit_line_ids)
        credit_account_id = record.journal_id.default_credit_account_id.id
        credit_line_ids = (0, 0, {
            'company_id': expense.company_id.id,
            'name': '/',
            'date': timenow,
            'account_id': credit_account_id,
            'journal_id': record.journal_id.id,
            'period_id': period_id,
            'credit': line.credit,
            'debit': 0.0,
            'currency_id': cur_id,
            'amount_currency': -amt_curr,
            #'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
            'analytic_account_id': False,
            'tax_code_id': False,
            'tax_amount': 0.0,
        })

        line_ids.append(credit_line_ids)

        move['line_id'] = line_ids

        self.pool.get('account.move').create(cr, uid, move, context=context)
        self.pool.get('hr.expense.expense').write(cr, uid, expense.id, {'state': 'paid'}, context=context)
        return {'type': 'ir.actions.act_window_close'}


