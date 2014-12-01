
import time
from lxml import etree

from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _
from openerp.tools import float_compare
from openerp.report import report_sxw


class account_voucher(osv.osv):
    _inherit = 'account.voucher'

    def recompute_voucher_linesBACKUP(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        result = super(account_voucher, self).recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
        account_id = False
        if result.get('value', {}).get('line_cr_ids', []):
            account_id = result.get('value', {}).get('line_cr_ids', [])[0].get('account_id', False)
        if result.get('value', {}).get('line_dr_ids', []):
            account_id = result.get('value', {}).get('line_dr_ids', [])[0].get('account_id', False)

        if not account_id:
            return result

        company_id = self.pool.get('account.account').browse(cr, uid, account_id, context=context).company_id

        ctx = dict(context or {}, company_id=company_id.id, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        period_id = periods and periods[0] or False
        if period_id:
            result['value']['period_id'] = period_id

        #raise ValueError, 'ValueError...'

        return result


    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=None):
        result = super(account_voucher, self).onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, ttype, company_id, context=context)

        journal_pool = self.pool.get('account.journal')
        period_pool = self.pool.get('account.period')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        if not journal_id:
            return result
        ctx = dict(context or {}, company_id=journal.company_id.id, account_period_prefer_normal=True)
        periods = period_pool.find(cr, uid, context=ctx)
        period_id = periods and periods[0] or False
        if period_id:
            result['value']['period_id'] = period_id
            result['value']['company_id'] = journal.company_id.id
        if journal.currency:
            currency_id = journal.currency.id
        else:
            currency_id = journal.company_id.currency_id.id
        if context.get('payment_expected_currency') and currency_id != context.get('payment_expected_currency'):
            amt = self.pool.get('res.currency').compute(cr, uid, context.get('payment_expected_currency'), currency_id, amount, context=context)
            result['value']['amount'] = amt
            amount = amt

        #raise ValueError, periods
        return result



