# -*- coding: utf-8 -*-



{
    'name': 'TGT HR Payroll',
    'version': '0.1',
    'category': 'Human Resource',
    'sequence': 1,
    'summary': 'TGT Payroll calculation',
    'description': """
TGT HR Payroll Module
====================================================

calculate unusual earning & deductions for employee.
""",
    'author': 'TGT Oilfield Services',
    'website': 'http://www.tgtoil.com',
    'depends': [
        'hr_tgt',
        'hr_payroll',
        'hr_payroll_account',
        'hr_contract',
        'hr_timesheet',
        'hr_holidays',
    ],
    'data': [
        'hr_payroll_tgt_view.xml',
        'wizard/hr_rotator_timesheet_view.xml',
        'wizard/tgt_payslip_report_view.xml',
        'wizard/rotator_daysoff_view.xml',
        'wizard/hr_loading_view.xml',
        'hr_payroll_data.xml',
        'board_hr_loading.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': [],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
