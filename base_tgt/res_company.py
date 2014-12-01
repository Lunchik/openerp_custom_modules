'''Customzied Partners'''

from openerp.osv import osv, orm, fields
from openerp import netsvc

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import datetime

from openerp import SUPERUSER_ID

class res_company(osv.osv):
    _inherit = 'res.company'

    _columns = {
        'code': fields.char('Code', size=10, required=True),
    }

    def rename_accounts(self, cr, uid, ids, context=None):
        objs = [
            'account.period',
            'account.journal',
            'account.fiscalyear',
            'account.account',
        ]

        for obj in objs:
            acc = self.pool.get(obj)
            obj_ids = acc.search(cr, uid, [], context=context)
            for rec in acc.browse(cr, uid, obj_ids, context):
                name = '%s (%s)' % (rec.name, rec.company_id.code)
                val = {'name': name}
                try:
                    acc.write(cr, uid, [rec.id], val, context=context)
                except:
                    continue

        return True

    def fix_analytic(self, cr, uid, ids, context=None):
        ml_obj = self.pool.get('account.move.line')
        cr.execute("""
            SELECT id FROM account_move_line WHERE company_id!=(SELECT company_id FROM account_analytic_account WHERE id=analytic_account_id)
            """)
        res = cr.fetchall()
        ml_ids = [id[0] for id in res]
        for line in ml_obj.browse(cr, uid, ml_ids, context=context):
            data = {
                'analytic_account_id': False,
            }
            new_acc = self.pool.get('account.analytic.account').search(cr, uid, [('parent_id', '=', line.analytic_account_id.parent_id.id),('company_id','=',line.company_id.id)], context=context)
            if new_acc:
                data['analytic_account_id'] = new_acc[0]
            ml_obj.write(cr, uid, [line.id], data, context=context)

    def link_analytic_journals(self, cr, uid, ids, context=None):
        ajo = self.pool.get('account.analytic.journal')
        jo = self.pool.get('account.journal')
        for jor in jo.browse(cr, uid, jo.search(cr, uid, [], context=context), context=context):
            typ = ''
            if jor.type in ('sale', 'sale_refund'):
                typ = 'sale'
            if jor.type in ('purchase', 'purchase_refund'):
                typ = 'purchase'
            if jor.type in ('bank', 'cash'):
                typ = 'cash'
            if jor.type in ('general',):
                typ = 'expense'
            if jor.type in ('situation',):
                typ = 'situation'

            idd = ajo.search(cr, uid, [('company_id', '=', jor.company_id.id), ('type', '=', typ)], context=context)
            data = {
                'analytic_journal_id': idd and idd[0] or False,
            }
            jo.write(cr, uid, [jor.id], data, context=context)

    def set_hadvance(self, cr, uid, ids, context=None):
        co = self.pool.get('hr.contract')
        log_obj = self.pool.get('hr_tgt.payslip.housingadvance')
        cids = co.search(cr, uid, [], context=context)
        for con in co.browse(cr, uid, cids, context=context):
            emp_id = con.employee_id.id
            log_ids = log_obj.search(cr, uid, [('employee_id', '=', emp_id)], context=context)
            #raise ValueError, (con.has_hadvance, vals.get('has_hadvance', True))
            if not log_ids:
                # he enabled housing advanvce
                period = (con.period and con.period not in ['1','0']) and con.period or '3'
                last_payment = datetime.datetime.now() - datetime.timedelta(days=int(period))
                hadvance = con.has_hadvance
                v = {'period': period, 'last_payment': last_payment.strftime('%Y-%m-%d'), 'employee_id': emp_id}
                #if vals.get('hadvance_amount', False) != False:
                v['hadvance_amount'] = con.hadvance_amount * int(con.period)
                log_obj.create(cr, uid, v, context=context)

        return True

class res_partner_bank(osv.osv):
    '''Bank Accounts'''
    _inherit = "res.partner.bank"
    _columns = {
        'bank_bic': fields.char('iBan Code', size=32),
    }

class Bank(osv.osv):
    _description='Bank'
    _inherit = 'res.bank'
    _columns = {
        'bic': fields.char('Swift Code', size=64,
            help="Sometimes called BIC or Swift."),
    }
