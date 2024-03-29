{
    'name':'TGT  HR  Extended ',
    'description':'Extensive Features of Employee',
    'author':'TGT Oilfield Services',
    'website':'http://tgtoil.com',
    'version':'1.0',
    'sequence': 1,
    'category':'Human Resources',
    'depends':[
        'hr',
        'hr_attendance',
        'hr_expense',
        'hr_timesheet',
        'hr_holidays',
        'hr_recruitment',
        'account',
    ],
    'update_xml': [
        'hr_tgt.xml',
        'data.xml',
        'job_data.xml',
        'hr_expense_view.xml', 
        'wizard/leave_reset_view.xml',
        'wizard/expense_payment_view.xml',
        'res_config_view.xml',
    ],
    'data': [
        'security/tgt_payroll_security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
}