import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from openerp import SUPERUSER_ID
from openerp import pooler, tools
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round

import openerp.addons.decimal_precision as dp


class wizard_multi_charts_accounts(osv.osv_memory):
    """
    Create a new account chart for a company.
    Wizards ask for:
        * a company
        * an account chart template
        * a number of digits for formatting code of non-view accounts
        * a list of bank accounts owned by the company
    Then, the wizard:
        * generates all accounts from the template and assigns them to the right company
        * generates all taxes and tax codes, changing account assignations
        * generates all accounting properties and assigns them correctly
    """
    _name = _inherit ='wizard.multi.charts.accounts'

    def _prepare_all_journals(self, cr, uid, chart_template_id, acc_template_ref, company_id, context=None):
        '''Override default creation by add aproper link to analytic journal'''
        def _get_analytic_journal(journal_type):
            # Get the analytic journal
            data = False
            if journal_type in ('sale', 'sale_refund'):
                data = obj_data.get_object_reference(cr, uid, 'account', 'analytic_journal_sale')
            elif journal_type in ('purchase', 'purchase_refund'):
                pass
            elif journal_type == 'general':
                pass
            return data and data[1] or False

        def _get_default_account(journal_type, type='debit'):
            # Get the default accounts
            default_account = False
            if journal_type in ('sale', 'sale_refund'):
                default_account = acc_template_ref.get(template.property_account_income_categ.id)
            elif journal_type in ('purchase', 'purchase_refund'):
                default_account = acc_template_ref.get(template.property_account_expense_categ.id)
            elif journal_type == 'situation':
                if type == 'debit':
                    default_account = acc_template_ref.get(template.property_account_expense_opening.id)
                else:
                    default_account = acc_template_ref.get(template.property_account_income_opening.id)
            return default_account

        journal_names = {
            'sale': _('Sales Journal'),
            'purchase': _('Purchase Journal'),
            'sale_refund': _('Sales Refund Journal'),
            'purchase_refund': _('Purchase Refund Journal'),
            'general': _('Miscellaneous Journal'),
            'situation': _('Opening Entries Journal'),
        }
        journal_codes = {
            'sale': _('SAJ'),
            'purchase': _('EXJ'),
            'sale_refund': _('SCNJ'),
            'purchase_refund': _('ECNJ'),
            'general': _('MISC'),
            'situation': _('OPEJ'),
        }

        obj_data = self.pool.get('ir.model.data')
        analytic_journal_obj = self.pool.get('account.analytic.journal')
        template = self.pool.get('account.chart.template').browse(cr, uid, chart_template_id, context=context)

        journal_data = []
        for journal_type in ['sale', 'purchase', 'sale_refund', 'purchase_refund', 'general', 'situation']:
            vals = {
                'type': journal_type,
                'name': journal_names[journal_type],
                'code': journal_codes[journal_type],
                'company_id': company_id,
                'centralisation': journal_type == 'situation',
                'analytic_journal_id': _get_analytic_journal(journal_type),
                'default_credit_account_id': _get_default_account(journal_type, 'credit'),
                'default_debit_account_id': _get_default_account(journal_type, 'debit'),
            }
            journal_data.append(vals)
        return journal_data