from osv import osv, fields
from openerp import SUPERUSER_ID

GRADES = [('%s'%i, '%s- Grade %s' % (i, i)) for i in range(1, 31)]

class hr_employee_applicant(osv.osv):

    _inherit = 'hr.applicant'
    _columns = {
        'cv_ref': fields.binary(string="CV Reference"),
    }
    
class hr_employee_classification(osv.osv):

    _name = 'hr.employee.class'
    _columns = {
        'name': fields.char('Classification Name'),
        'description': fields.text('Description'),
    }


class hr_employee_tgt(osv.osv):
    
    _inherit = 'hr.employee'

    def _get_default_expense_account(self, cr, uid, context=None):
        ids = self.pool.get('hr.expense.config').search(cr, uid, [], context=context)
        if not ids:
            return False
        account = self.pool.get('hr.expense.config').browse(cr, uid, ids[0], context=context).expense_account_id
        return account.id

    _columns = {
        'grade':fields.selection(GRADES, 'Grade'),
        'visa_code':fields.selection([('dmcc', 'DMCC'),('fze', 'FZE'),('sponsor', 'Sponsor'),], 'Visa Code'),
        'account_payable_id':fields.many2one('account.account', 'Expenses Account Payable', domain=[('type', '=', 'payable')]),
        'classification_id':fields.many2one('hr.employee.class', 'Classification'),
        'bank_account_num':fields.char('Bank Account', size=100),
        'is_rotator':fields.boolean('Is Rotator'),
        'is_loc_engineer': fields.boolean('Is Local Engineer'),
        'labor_id':fields.char('Labor ID',size=20),
        'iban_id':fields.char('IBAN',size=30), 
        'contact_home':fields.char('Contact at Home Country',size=64),
        'bank_name':fields.char('Name of The Bank',size=64),
        'resident_country':fields.many2one('res.country', 'Resident Country'),
        'resident_city':fields.char('Resident City',size=64),
        'resident_address':fields.char('Resident Address',size=64),
        'home_address':fields.char('Home Address',size=164),
        'resident_contact':fields.char('Resident Contact',size=64),
        'social_security':fields.char('Social Security',size=64),
        'emirates_id':fields.char('Emirates ID',size=30),
        'passport_expiry_date':fields.date('Passport Expiry Date'),
        'residence_visa_expiry':fields.date('Visa Expiry Date'),
        'residence_visa':fields.char('Residence visa',size=40),
        'employee_id':fields.char('Employee Number',size=40),
        'bank_no':fields.char('Bank account number',size=40),
        'joining_date':fields.date('Joining Date'),
        'anual_leaves':fields.integer('Annual Leaves'),
        'emp_other_docs':fields.binary('Others'),
        'emp_contarct_doc':fields.binary('Employee Contract'),
        'emp_others':fields.binary('Other Documents'),
        'emp_pass_doc':fields.binary('Passport/Visa/Photos'),
        'emp_cv_doc':fields.binary('CV/Certificates'),
        'emp_exit_doc':fields.binary('Exit Document'),
    }
    _defaults = {
        'anual_leaves':30,
        #'account_payable_id': _get_default_expense_account,
    }

    def onchange_company(self, cr, uid, ids, company, context=None):
        result = super(hr_employee_tgt, self).onchange_company(cr, uid, ids, company, context=context)
        ids = self.pool.get('hr.expense.config').search(cr, SUPERUSER_ID, [], context=context)
        if not ids:
            return False

        account = self.pool.get('hr.expense.config').browse(cr, SUPERUSER_ID, ids[0], context=context).expense_account_id
        account_id = account.id
        if account.company_id.id != company:
            ids = self.pool.get('account.account').search(cr, uid, [('code','=',account.code),('company_id','=',company)], context=context)
            if ids:
                account_id = ids[0]
            else:
                account_id = False
        result['value']['account_payable_id'] = account_id
        return result

