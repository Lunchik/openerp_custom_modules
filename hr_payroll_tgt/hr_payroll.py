from openerp.osv import osv, fields
import datetime, time
from openerp.tools.translate import _

from dateutil import relativedelta
from openerp import SUPERUSER_ID
import logging

logger = logging.getLogger(__name__)

MONTHS = [
    #('1', 'Monthly'),
    #('2', 'Every 2 Months'),
    ('3', 'Quarterly (every 3 months)'),
    ('4', 'Triple (every 4 months)'),
    #('5', 'Every 5 Months'),
    ('6', 'Twice a year (every 6 months)'),
    #('7', 'Every 7 Months'),
    #('8', 'Every 8 Months'),
    #('9', 'Every 9 Months'),
    #('10', 'Every 10 Months'),
    #('11', 'Every 11 Months'),
    #('12', 'Yearly (every 12 months)'),
]


MONTHS_NAMES = [
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('4', 'Apr'),
    ('5', 'May'),
    ('6', 'Jun'),
    ('7', 'Jul'),
    ('8', 'Aug'),
    ('9', 'Sep'),
    ('10', 'Oct'),
    ('11', 'Nov'),
    ('12', 'Dec'),
]





class hr_rotation_method(osv.osv):
    ''' HR Rotation Method'''

    _name = 'hr_tgt.rotation.method'

    _columns = {
        'days_work': fields.integer('Work Days', help='Number of Days he/she must work before getting daysoff'),
        'days_off': fields.integer('Off Days', help='Daysoff'),
        'name': fields.char('Name'),
    }

    _defaults = {
        'days_work': 30,
        'days_off': 30,
    }

    def create(self, cr, uid, vals, context=None):
        dw, do = int(vals.get('days_work', '0')), int(vals.get('days_off', '0'))
        setit = True 
        if dw >= 7 and dw % 7 == 0:
            dw = dw / 7
        else:
            setit = False
        if do >= 7 and do % 7 == 0:
            do = do / 7
        else:
            setit = False

        if setit:
            vals['name'] = u'%sx%s' % (dw, do)
        else:
            vals['name'] = u'%sx%s' % (vals.get('days_work', '0'), vals.get('days_off', '0'))
        return super(hr_rotation_method, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        dw, do = int(vals.get('days_work', '0')), int(vals.get('days_off', '0'))
        setit = True 
        if dw >= 7 and dw % 7 == 0:
            dw = dw / 7
        else:
            setit = False
        if do >= 7 and do % 7 == 0:
            do = do / 7
        else:
            setit = False

        if setit:
            vals['name'] = u'%sx%s' % (dw, do)
        return super(hr_rotation_method, self).write(cr, uid, ids, vals, context=context)


class hr_rotation_history(osv.osv):
    '''HR Rotation Method History'''

    _name = "hr_tgt.rotation.history"

    _columns = {
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
        'rotation_id': fields.many2one('hr_tgt.rotation.method', 'Rotation Method'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
    }



class hr_contract(osv.osv):
    """
    Employee contract based on the visa, work permits
    allows to configure different Salary structure
    """

    _inherit = 'hr.contract'
    _description = 'Employee Contract'


    def get_default_currency(self, cr, uid, ids, context=None):
        return self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id 
        #return self.pool.get('res.company').

    _columns = {
        'currency_id':fields.many2one('res.currency', 'Salary Payment Currency'),
        'analytic_account_id':fields.many2one('account.analytic.account', 'Cost Centre Account'),
        'analytic_journal_id': fields.many2one('account.analytic.journal', 'Cost Centre'),
        'account_debit': fields.many2one('account.account', 'Debit Account'),
        'account_credit': fields.many2one('account.account', 'Credit Account'),
        'has_hadvance': fields.boolean('Enable Housing Advance'),
        'hadvance_amount': fields.float('Housing Allowance Amount'),
        'period': fields.selection(MONTHS, 'Housing Advance Period', help="set housing advance (HADVANCE) monthly period for employee"),
        'trans_allowance': fields.float('Transportation Allowance Amount'),
        'social_security_gosi': fields.float('Social Security Employee'),
        'social_security': fields.float('Social Security Employer'),
        'salary_tax': fields.float('Salary Tax'),
        'p_income_tax': fields.float('Personal Icome Tax'),
        'pension_fund': fields.float('Pension Fund'),
        'compulsary_health': fields.float('Compulsory Health'),
        'sponser_deduction': fields.float('Sponsor Deduction Amount'),
        'onpaid_vacation': fields.float('UnPaid Vacation Amount'),
        'wage': fields.float('Basic Salary', digits=(16,2), required=True, help="Basic Salary of the employee"),
        'ref_doc': fields.binary('Upload Contract Doc'),
    }

    _defaults = {
        'period': '3',
        'has_hadvance': False,
        'currency_id': get_default_currency,
    }

    def check_hadvance(self, cr, uid, ids, context=None):
        ids = self.search(cr, uid, [], context=context)
        had_obj = self.pool.get('hr_tgt.payslip.housingadvance')
        for con in self.browse(cr, uid, ids, context=context):
            had_ids = had_obj.search(cr, uid, [('employee_id', '=', con.employee_id.id)], context=context)
            if had_ids:
                continue
            period = '3'
            last_payment = datetime.datetime.now() - datetime.timedelta(days=int(period))
            hadvance = False
            v = {'period': period, 'last_payment': last_payment.strftime('%Y-%m-%d'), 'employee_id': con.employee_id.id}
            v['hadvance_amount'] = 0 * int(period)
            had_obj.create(cr, uid, v, context=context)

        return False


    def create(self, cr, uid, vals, context=None):
        log_obj = self.pool.get('hr_tgt.payslip.housingadvance')
        emp_id = vals['employee_id']
        log_ids = log_obj.search(cr, uid, [('employee_id', '=', emp_id)], context=context)
        if log_ids:
            # get log obj
            period = vals.get('period', '3')
            hadvance = vals.get('has_hadvance', False)

            v = {'period': period}

            last_payment = datetime.datetime.now() - datetime.timedelta(days=int(period))
            log_obj.write(cr, uid, log_ids, v, context=context)
        else:
            period = vals.get('period', '3')
            last_payment = datetime.datetime.now() - datetime.timedelta(days=int(period))
            hadvance = vals.get('has_hadvance', False)
            v = {'period': period, 'last_payment': last_payment.strftime('%Y-%m-%d'), 'employee_id': emp_id}
            #if hadvance != False:
            v['hadvance_amount'] = vals.get('hadvance_amount') * int(vals.get('period', '3'))
            log_obj.create(cr, uid, v, context=context)

        return super(hr_contract, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):

        if not 'period' in vals and not 'hadvance_amount' in vals and not 'has_hadvance' in vals:
            return super(hr_contract, self).write(cr, uid, ids, vals, context=context)

        log_obj = self.pool.get('hr_tgt.payslip.housingadvance')
        for con in self.browse(cr, uid, ids, context=context):
            emp_id = con.employee_id.id
            log_ids = log_obj.search(cr, uid, [('employee_id', '=', emp_id)], context=context)
            #raise ValueError, (con.has_hadvance, vals.get('has_hadvance', True))
            if log_ids:
                # get log obj
                period = vals.get('period', '3')
                hadvance_amount = vals.get('hadvance_amount', False)
                v = {'period': period}
                if hadvance_amount != False:
                    v['hadvance_amount'] = hadvance_amount * int(con.period)

                log_obj.write(cr, uid, log_ids, v, context=context)
            elif vals.get('has_hadvance', True):
                # he enabled housing advanvce
                period = vals.get('period', '3')
                last_payment = datetime.datetime.now() - datetime.timedelta(days=int(period))
                hadvance = vals.get('has_hadvance', False)
                v = {'period': period, 'last_payment': last_payment.strftime('%Y-%m-%d'), 'employee_id': emp_id}
                #if vals.get('hadvance_amount', False) != False:
                v['hadvance_amount'] = vals.get('hadvance_amount', 0) * int(con.period)
                log_obj.create(cr, uid, v, context=context)


        return super(hr_contract, self).write(cr, uid, ids, vals, context=context)


class hr_payslip(osv.osv):
    '''
    Pay Slip, Advance Housing allowance,
    and Site Allowance
    '''

    _inherit = 'hr.payslip'


    def _get_site_allowance(self, cr, uid, ids, field_name, arg, context=None):
        cur_obj = self.pool.get('res.currency')
        conf_obj = self.pool.get('site.allowance.config')
        res = {}
        c_ids = conf_obj.search(cr, uid, [], context=context, limit=1)
        c_ids = c_ids and c_ids[0] or False
        cobj = c_ids and conf_obj.read(cr, uid, c_ids, ['onshore', 'offshore', 'travel'], context=context) or False
        if not cobj:

            cobj = {
                'onshore': 30,
                'offshore': 50,
                'travel': 30,
            }
        for payslip in self.browse(cr, uid, ids, context=context):

            currency_id = payslip.contract_id.currency_id.id
            ir_mdata = self.pool.get('ir.model.data')
            usd_id = ir_mdata.get_object(cr, uid, 'base', 'USD').id

            onshore = cur_obj.compute(cr, uid, usd_id, currency_id, cobj.get('onshore'), round=True, context=context)
            offshore = cur_obj.compute(cr, uid, usd_id, currency_id, cobj.get('offshore'), round=True, context=context)
            travel = cur_obj.compute(cr, uid, usd_id, currency_id, cobj.get('travel'), round=True, context=context)

            res[payslip.id] = {
                'onshore': onshore,
                'offshore': offshore,
                'travel': travel,
            }

        return res


    _columns = {
        'onshore': fields.function(_get_site_allowance, method=True, string='Onshore', type='float', multi=True),
        'offshore': fields.function(_get_site_allowance, method=True, string='Offshore Amount', type='float', multi=True),
        'travel': fields.function(_get_site_allowance, method=True, string='Travel Amount', type='float', multi=True),
    }

    def create(self, cr, uid, vals, context=None):
        return super(hr_payslip, self).create(cr, SUPERUSER_ID, vals, context=context)

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        return super(hr_payslip, self).onchange_employee_id(cr, uid, ids, date_from, date_to, employee_id=employee_id, contract_id=contract_id, context=context)
        if not employee_id:
            return res
        if not contract_id and not res.get('contract_id', False):
            return res


    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context=None):
        ''' Re-create BrowsableObject, because its local variable
        in super class
        '''

        # get the ids of the structures on the contracts and their parent id as well
        payslip = self.browse(cr, uid, payslip_id, context=context)
        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        # get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        result = super(hr_payslip, self).get_payslip_lines(cr, uid, contract_ids, payslip_id, context=context)
        # if result not contained HADVANCE, return
        contract_obj = self.pool.get('hr.contract')
        has_hadvance = False
        #raise ValueError, result
        for r in result:
            conn = contract_obj.browse(cr, uid, r['contract_id'], context=context)
            if not conn.has_hadvance:
                continue
            if r['code'] == 'HADVANCE':
                has_hadvance = True
                break
        if not has_hadvance:
            return result

        today = datetime.datetime.now()


        illegable = False
        payslip = self.browse(cr, uid, payslip_id, context=context)

        #raise ValueError, payslip.onshore
        
        hadvance_obj = self.pool.get('hr_tgt.payslip.housingadvance')
        hadvance_id = hadvance_obj.search(cr, uid, [('employee_id', '=', payslip.employee_id.id)], context=context)

        if hadvance_id:
            hadvance_id = hadvance_id[0]

        hadvance = hadvance_obj.browse(cr, uid, hadvance_id, context=context)
        #rounds = {
        #    '3': [ 3, 6, 9, 12],
        #    '6': [ 6, 12],
        #}

        #current_month = datetime.datetime.strptime(payslip.date_from, '%Y-%m-%d').month
        period = hadvance.period
        #if current_month not in rounds.get(period, []):
        #    return result


        last_payment = datetime.datetime.strptime(hadvance.last_payment, '%Y-%m-%d')

        delta = datetime.timedelta(days=int(period) * 30)
        today = datetime.datetime.now()
        expected = last_payment + delta

        if today > expected:
            illegable = True

        if hadvance.hadvance_amount < hadvance.accumulated_ded:
            # accumulated_ded >= hadvance_amount
            illegable = True
            hadvance_obj.write(cr, uid, [hadvance.id], {'accumulated_ded': 0.0, 'last_deduction': datetime.datetime(1970, 01, 01)}, context=context)


        #if illegable:

        #    # check if Housing allowance (HALLOW)
        #    # and toggle illegable to False if there
        #    # because you cannot add HALLOW and HADVANCE
        #    # for the same salary structure

        #    for r in result:
        #        if r['code'] == 'HALLOW':
        #            raise osv.except_osv(_('Salary Structure Configuration!'), _('You Cannot add "%s" (%s) and "Housing Advance" (HADVACE) in same salary structure\n please remove one of them.')% (r['name'], r['code']))             

        if not illegable:
            # remove all HADVANCE codes from result
            reresult = []
            for r in result:
                if r['code'] != 'HADVANCE':
                    reresult.append(r)
                else:
                    #raise ValueError, (hadvance.accumulated_ded, hadvance.hadvance_amount)
                    if hadvance.accumulated_ded < hadvance.hadvance_amount and hadvance.accumulated_ded > 0:
                        r['amount'] = 0
                    if hadvance.accumulated_ded == hadvance.hadvance_amount:
                        hadvance_obj.write(cr, uid, [hadvance.id], {'accumulated_ded': 0.0, 'last_deduction': datetime.datetime(1970, 01, 01)}, context=context)
                    reresult.append(r)
            result = reresult
        return result

    def hr_verify_sheet(self, cr, uid, ids, context=None):
        result = super(hr_payslip, self).hr_verify_sheet(cr, uid, ids, context=context)
        ir_mdata = self.pool.get('ir.model.data')
        mail_obj = self.pool.get('mail.mail')
        hr_managers_group_id = ir_mdata.get_object(cr, uid, 'base', 'group_hr_manager').id
        #raise ValueError, hr_managers_group_id
        hr_managers_group = self.pool.get('res.groups').browse(cr, uid, hr_managers_group_id, context=context)
        #raise ValueError, [u.email for u in hr_managers_group.users if u.email]
        email_address = [u.email for u in hr_managers_group.users if u.email]
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        log_obj = self.pool.get('hr_tgt.payslip.housingadvance')

        for ps in self.browse(cr, uid, ids, context=context):
            payslip_date = datetime.datetime.strptime(ps.date_from, '%Y-%m-%d')
            try:
                employee_id = ps.employee_id
                email = employee_id.work_email
                if not email and employee_id.user_id:
                    email = employee_id.user_id.email
                if email:
                    subject = u'Payslip of %s' % payslip_date.strftime('%B %Y')
                    body = u'Your Email - This email For test porposes, just ignore it \:0)'
                    mfrom = 'tgterp@tgtoil.com'
                    values = {}
                    values['subject'] = subject
                    values['email_from'] = email
                    values['email_to'] = email
                    values['body_html'] = body
                    values['body'] = body

                    msg_id = mail_obj.create(cr, uid, values, context=context)


            except Exception, e:
                pass

            setit = False
            if ps.contract_id.has_hadvance:
                setit = True
            #for line in ps.line_ids:
            #    if line.code == 'HADVANCE':
            #        setit = True
            #        break

            if not setit:
                continue

            emp_id = ps.employee_id.id
            log_ids = log_obj.search(cr, uid, [('employee_id', '=', emp_id)], context=context)
            if log_ids:
                if isinstance(log_ids, list):
                    log_ids = log_ids[0]
                log_obj.write(cr, uid, log_ids, {'last_payment': today,}, context=context)

            for line in ps.line_ids:
                log = log_obj.browse(cr, uid, log_ids, context=context)
                if line.code == 'HADVANCE_DED':
                    dat = {
                        'accumulated_ded': log.accumulated_ded,
                        'last_deduction': today,
                    }
                    dat['accumulated_ded'] += line.amount * -1

                    if dat['accumulated_ded'] >= log.hadvance_amount:
                        dat['last_payment'] = datetime.datetime.now() - datetime.timedelta(days=int(ps.contract_id.period))
                        dat['last_deduction'] = datetime.datetime.now() - datetime.timedelta(days=int(ps.contract_id.period))
                    if log_ids:
                        log_obj.write(cr, uid, log_ids, dat, context=context)
                    break


        #raise ValueError, result
        return result


    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
        contract_obj = self.pool.get('hr.contract')
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):

            # get the ids of the structures on the contracts and their parent id as well
            rotator = False
            structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, [contract.id], context=context)
            #get the rules of the structure and thier children
            rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
            #run the rules by sequence
            sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]
            # read rules code
            rules = self.pool.get('hr.salary.rule').read(cr, uid, sorted_rule_ids, ['code'], context=context)


            rotator = [r for r in rules if r['code'] == 'SALLOW']
            if contract.employee_id.is_rotator:
                #raise ValueError, 'VEE'
                wsheet_obj = self.pool.get('hr.payslip.working_sheet')
                dstart = datetime.datetime.strptime(date_from, '%Y-%m-%d')
                dend = datetime.datetime.strptime(date_to, '%Y-%m-%d')

                dstart2 = dstart + relativedelta.relativedelta(months=-1, day=1)
                dstart2 = dstart + relativedelta.relativedelta(days=-1, day=1)
                
                dend = dend + relativedelta.relativedelta(months=0, day=1, days=-1)

                dend, dstart = datetime.datetime.strftime(dstart2, '%Y-%m-%d'), datetime.datetime.strftime(dstart2, '%Y-%m-01')

                os_ids = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'O')], context=context, count=True)
                or_ids  = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'S'), ('with_allow', '=', False)], context=context, count=True)
                or_ids2  = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'S'), ('with_allow', '=', True)], context=context, count=True)
                lo_ids  = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'L'), ('with_allow', '=', False)], context=context, count=True)
                lo_ids2  = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'L'), ('with_allow', '=', True)], context=context, count=True)
                ba_ids  = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'B'), ('with_allow', '=', True)], context=context, count=True)
                t_ids  = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'T+')], context=context, count=True)
                pl_ids = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'PL'), ('with_allow', '=', False)], context=context, count=True)
                pl_ids2 = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'PL'), ('with_allow', '=', True)], context=context, count=True)
                ps_ids = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'PS'), ('with_allow', '=', False)], context=context, count=True)
                ps_ids2 = wsheet_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id), ('date', '>=', dstart), ('date', '<=', dend), ('state', '=', 'PS'), ('with_allow', '=', True)], context=context, count=True)

                res.append({
                    'name': 'Site Allowance - Daysoff',
                    'code': 'SA_OVERSTAY',
                    'amount': os_ids,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Base + Meal',
                    'code': 'SA_BASE_P',
                    'amount': ba_ids,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Onshore',
                    'code': 'SA_ONSHORE',
                    'amount': lo_ids,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Onshore + Meal',
                    'code': 'SA_ONSHORE_P',
                    'amount': lo_ids2,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Offshore',
                    'code': 'SA_OFFSHORE',
                    'amount': or_ids,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Offshore + Meal',
                    'code': 'SA_OFFSHORE_P',
                    'amount': or_ids2,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Meal Allowance',
                    'code': 'SA_MALLOW',
                    'amount': t_ids,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Public Holiday Onshore',
                    'code': 'SA_PHONSHORE',
                    'amount': pl_ids,
                    'contract_id': contract.id,
                    })
                res.append({
                    'name': 'Site Allowance - Public Holiday Onshore + Meal',
                    'code': 'SA_PHONSHORE_P',
                    'amount': pl_ids2,
                    'contract_id': contract.id,
                    })                
                res.append({
                    'name': 'Site Allowance - Public Holiday Offshore',
                    'code': 'SA_PHOFFSHORE',
                    'amount': ps_ids,
                    'contract_id': contract.id,
                    }) 
                res.append({
                    'name': 'Site Allowance - Public Holiday Offshore + Meal',
                    'code': 'SA_PHOFFSHORE_P',
                    'amount': ps_ids2,
                    'contract_id': contract.id,
                    })     
                # HADVANCE_DED Housing Advance Deduction


            inputt3 = {
                    'name': 'Example Input',
                    'code': 'O2EXAMPLE',
                    'contract_id': contract.id,
                    'amount': 0.0,
                }
            res += [inputt3]


            if not contract.has_hadvance:
                inputt = {
                        'name': 'Housing Advance Deduction',
                        'code': 'HADVANCE_DED',
                        'contract_id': contract.id,
                        'amount': 0.0,
                    }
                inputt2 = {
                    'name': 'Housing Advance',
                    'code': 'HADVANCE',
                    'contract_id': contract.id,
                    'amount': 0.0,
                }
                res += [inputt, inputt2]
            
            else:
            

                # also check if the selected contract has
                # salary structure that has rule called
                # "SALLOW"
                # if so, add 4 inputs values, else dont add

                log_obj = self.pool.get('hr_tgt.payslip.housingadvance')


                hadv = [r for r in rules if r['code'] == 'HADVANCE']
                hadvded = [r for r in rules if r['code'] == 'HADVANCE_DED']

                settit = True
                if hadvded:
                    log_ids = log_obj.search(cr, uid, [('employee_id', '=', contract.employee_id.id)], context=context)
                    if isinstance(log_ids, (list,)):
                        log_ids = log_ids[0]
                    log = log_obj.browse(cr, uid, log_ids, context=context)

                    ded_amount = 0.0

                    if contract.has_hadvance:
                        last_payment = datetime.datetime.strptime(log.last_payment or '1970-01-01', '%Y-%m-%d')
                        last_deduction = datetime.datetime.strptime(log.last_deduction or '1970-01-01', '%Y-%m-%d')

                        period = int(log.period)

                        melapsed = last_payment + datetime.timedelta(days=period * 30)
                        today = datetime.datetime.now()

                        period_payments = log.hadvance_amount * (period * 1.0)

                        elapsed = log.hadvance_amount - log.accumulated_ded

                        if elapsed > 0 and log.accumulated_ded:
                            settit = False

                        elapsed_after_ded = elapsed - period_payments

                        ded_amount = contract.hadvance_amount

                        if elapsed_after_ded < 1 and elapsed_after_ded > 0:
                            ded_amount = period_payments + elapsed_after_ded

                        inputt = {
                            'name': 'Housing Advance Deduction',
                            'code': 'HADVANCE_DED',
                            'contract_id': contract.id,
                            'amount': ded_amount,
                        }
                        res += [inputt]

                    else:
                        inputt = {
                            'name': 'Housing Advance Deduction',
                            'code': 'HADVANCE_DED',
                            'contract_id': contract.id,
                            'amount': 0.0,
                        }
                        res += [inputt]
                if hadv:
                    inputt = {
                        'name': 'Housing Advance (%s)' % dict(MONTHS).get(contract.period, ''),
                        'code': 'HADVANCE',
                        'contract_id': contract.id,
                        'amount': settit and contract.hadvance_amount * int(contract.period) or 0.0,
                    }
                    res += [inputt]
        return res

    def compute_sheet(self, cr, uid, ids, context=None):
        slip_line_pool = self.pool.get('hr.payslip.line')
        sequence_obj = self.pool.get('ir.sequence')

        for payslip in self.browse(cr, uid, ids, context=context):
            date_from, date_to = payslip.date_from, payslip.date_to
            dstart = datetime.datetime.strptime(date_from, '%Y-%m-%d')
            dend = datetime.datetime.strptime(date_to, '%Y-%m-%d')

            dstart2 = dstart + relativedelta.relativedelta(months=-1, day=1)
            dstart2 = dstart + relativedelta.relativedelta(days=-1, day=1)
            
            dend = dend + relativedelta.relativedelta(months=0, day=1, days=-1)

            dend, dstart = datetime.datetime.strftime(dstart2, '%Y-%m-%d'), datetime.datetime.strftime(dstart2, '%Y-%m-01')
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            #delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)

#            old_slipline_ids
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            if payslip.contract_id:
                #set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]
            else:
                #if we don't give the contract, then the rules to apply should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
            abc = sorted(range(len(lines)), key=lambda a: lines[a][2]['category_id'])
            lines = [lines[l] for l in abc]
            for a in abc:
                if lines[a][2]['code'] == 'SALLOW':
                    details = u''
                    for il in payslip.input_line_ids:
                        if il.code in ['SA_OVERSTAY','SA_ONSHORE', 'SA_ONSHORE_P','SA_OFFSHORE', 'SA_OFFSHORE_P','SA_MALLOW', 'SA_BASE_P', 'SA_PHONSHORE', 'SA_PHONSHORE_P', 'SA_PHOFFSHORE', 'SA_PHOFFSHORE_P']:
                            details = u'%s\n%s = %s days' % (details, il.name[17:], il.amount)
                    lines[a][2]['name'] = u'%s for %s\n%s\n%s' % (lines[a][2]['name'], dstart2.strftime('%B %Y'), '-' * 45, details)
                    break
            abc = sorted(range(len(lines)), key=lambda a: lines[a][2]['category_id'])
            lines = [lines[l] for l in abc]
            self.write(cr, uid, [payslip.id], {'line_ids': lines, 'number': number,}, context=context)
        return True


hr_payslip()


class payroll_housing_advance(osv.osv):
    ''' housing Advance log and setting'''

    _name = 'hr_tgt.payslip.housingadvance'
    _rec_name = 'last_payment'

    # we need another boolean flag that check if this employee
    # illegable for housing advance
    # 'illegable': fields.function(type='boolean', _check_if_illegable)
    # not illegable if he has housing allowance

    _columns = {
        'hadvance_amount': fields.float('Housing Advance Amount'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'last_payment': fields.date('Last Payment'),
        'last_deduction': fields.date('Last Deduction'),
        'accumulated_ded': fields.float('Accumulated Deduction'),
        'period': fields.selection(MONTHS, 'Housing Advance Period', help="set housing advance (HADVANCE) monthly period for employee"),
    }

payroll_housing_advance()

DAYS = [(str(i), 'Day %s' % i) for i in range(1, 32)]


class hr_employee(osv.osv):
    _inherit = "hr.employee"
    _columns = {
        'journal_id': fields.many2one('account.analytic.journal', 'Cost Centre', invisible=True),
        'rotation_ids': fields.one2many('hr_tgt.rotation.history', 'employee_id', 'Rotation History'),
        'rotation_id': fields.many2one('hr_tgt.rotation.method', 'Current Rotation Method'),
    }


    def check_visa_status(self, cr, uid, context=None):
        #logger.debug('%s Checking Visa Status ', '=+=' * 10)
        hr_manager_emails = []

        now = datetime.datetime.now()
        d15 = now + datetime.timedelta(days=15)
        emp_obj = self.pool.get('hr.employee')
        
        employee_ids = emp_obj.search(cr, uid, [('residence_visa_expiry', '<=', d15), ('residence_visa_expiry', '>=', now)], context=context)
        if not employee_ids:
            return False
        ir_mdata = self.pool.get('ir.model.data')
        mail_obj = self.pool.get('mail.mail')
        hr_managers_group_id = ir_mdata.get_object(cr, uid, 'base', 'group_hr_manager').id
        #raise ValueError, hr_managers_group_id
        hr_managers_group = self.pool.get('res.groups').browse(cr, uid, hr_managers_group_id, context=context)
        #raise ValueError, [u.email for u in hr_managers_group.users if u.email]
        email_address = [u.email for u in hr_managers_group.users if u.email]

        employees = emp_obj.browse(cr, uid, employee_ids, context=context)
        subject = u'Visa Expiration Warning!'
        body = u'''
            Dear HR Manager,
            Below are list of employees who thier Visa will
            expire in less than 15 days:
            <table border="1">
                <tr><td>Employee</td><td>Expire Date</td></tr>
        '''
        for emp in employees:
            a = u'<tr><td>%s</td><td>%s</td></tr>' % (emp.name, emp.residence_visa_expiry)
            body = body + a
        body += '</table>'
        values = {}
        values['email_from'] = u'tgterp@tgtoil.com'
        values['subject'] = subject
        values['email_to'] = ','.join(email_address)
        values['body'] = body
        values['body_html'] = body

        msg_id = mail_obj.create(cr, uid, values, context=context)
        if msg_id:
            mail_obj.send(cr, uid, [msg_id], context=context)

        return True





class working_sheet(osv.osv):
    ''' Working Sheet for rotator based employees'''

    _name = 'hr.payslip.working_sheet'

    def _get_eq_date(self, cr, uid, ids, field_names, arg=None, context=None):
        ''' Get Equivelance date'''
        result = {}
        if not ids:
            return {}
        cr.execute('''SELECT id, day, month, year FROM hr_payslip_working_sheet WHERE id in %s''', (tuple(ids),))
        res = cr.fetchall()
        for r in res:
            id, day, month, year = tuple(r)
            result[id] = datetime.datetime(int(year), int(month), int(day))
        return result

    _columns = {
        'name': fields.char('Name', size=250),
        'date': fields.function(_get_eq_date, method=True, string='Date', args=None, type='date', store=True),
        'year': fields.integer('Year'),
        'with_allow': fields.boolean('With Allowance'),
        'month': fields.selection([
            ('1', 'Jan'),
            ('2', 'Feb'),
            ('3', 'Mar'),
            ('4', 'Apr'),
            ('5', 'May'),
            ('6', 'Jun'),
            ('7', 'Jul'),
            ('8', 'Aug'),
            ('9', 'Sep'),
            ('10', 'Oct'),
            ('11', 'Nov'),
            ('12', 'Dec'),
        ], 'Month'),
        'day': fields.selection(DAYS, 'Day', help="Day of the month"),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'state': fields.selection([
            ('L', 'Land (Onshore)'),
            ('S', 'Sea (off shore)'),
            ('B', 'Base'),
            ('O', 'Days Off'),
            ('SL', 'Sick leave'),
            ('T', 'Travel'),
            ('T+', 'Travel with Allowance'),
            ('W', 'Week end / Holiday'),
            ('PL', 'Public Holiday (Onshore)'),
            ('PS', 'Public Holiday (Offshore)'),
            ('V', 'Vacation'),
        ], 'State'),
    }

    _defaults = {
        'state': 'O',
        'year': datetime.datetime.now().year,
        'month': str(datetime.datetime.now().month),
        'day': str(datetime.datetime.now().day),
    }

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for w in self.browse(cr, uid, ids, context=context):
            res.append((w.id, u'%s %s %s [%s] %s' % (w.day,
                w.month,
                w.year,
                w.state,
                w.employee_id.name)))

        return res

working_sheet()

class site_allowance(osv.osv):
    _name = 'site.allowance.config'

    _columns = {
       'offshore': fields.float('Offshore Amount (USD)'), 
       'onshore': fields.float('Land Amount (USD)'),
       'travel': fields.float('Travel Allowance Amount (USD)'),
    }

    _defaults = {
        'offshore': 50,
        'onshore': 30,
        'travel': 30,
    }

class hr_payslip_worksheet_adjustment(osv.osv):
    _name = 'hr.payslip.worksheet_adjustment'
    _description = 'Rotators Worksheet Adjustment'

    def _get_eq_date(self, cr, uid, ids, field_names, arg=None, context=None):
        ''' Get Equivelance date'''
        result = {}
        if not ids:
            return {}
        cr.execute('''SELECT id, month, year FROM hr_payslip_worksheet_adjustment WHERE id in %s''', (tuple(ids),))
        res = cr.fetchall()
        for r in res:
            id, month, year = tuple(r)
            result[id] = datetime.datetime(int(year), int(month), int(1))
        return result

    def _get_real_adjust(self, cr, uid, ids, f, k, context=None):        
        ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = obj.adjust_value*float(obj.adjust_sign)
            res[obj.id] = su
        return res  

    _columns = {
        'name': fields.char('Record Name', size=250),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'month': fields.selection(MONTHS_NAMES, 'Adjustment Month',
            help="select the month, that needs adjustment"),
        'year': fields.integer('Year'),
        'date': fields.function(_get_eq_date, method=True, string='Date', args=None, type='date', store=True),
        'adjust_value': fields.float('Adjusment Value', help="enter the adjustment of days off balance"),
        'adjust_sign': fields.selection([(1, 'Add'), (-1, 'Remove'),], 
            'Choose Adjustment Option', 
            help="choose if you want to increase or decrease days off"),
        'adjust_fin': fields.function(_get_real_adjust, string="Adjustment", type="float", method=True, store=False),
        'description': fields.text('Reason for Adjustment'),
    }

    _defaults = {
        'adjust_sign': 1,
        'year': datetime.datetime.now().year,
        'month': str(datetime.datetime.now().month),
    }    


    def power(self, *args):
        i = 1.0
        for k in args:
            i *= k
        return i 

hr_payslip_worksheet_adjustment()        