# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'TGT Accounting Module',
    'version': '0.1',
    'category': 'Accounting',
    'sequence': 1,
    'summary': 'Basic',
    'description': """
TGT Accounting Module
====================================================

Customization Accounting of:

* Invoices & payments.
* TGT Banks data.
* Legal reports Customization
* and other accounting workflow
* Cost Centre""",
    'author': 'TGT Oilfield Services',
    'website': 'http://www.tgtoil.com',
    'depends': [
        'base',
        'multi_company',
        'account',
        'account_accountant',
        'account_voucher',
    ],
    'data': [
        'account_invoice_view.xml',
        'country_rev.xml',
        'account_voucher_view.xml',
        'account_move_line_view.xml',
        'security/account_tgt_security.xml',
        'security/ir.model.access.csv',
        'wizard/account_profit_loss_report_view.xml',
        'wizard/billing_report.xml',
        'wizard/account_balance_view.xml',
        'wizard/ar_aging_view.xml',
        'wizard/cou_rev_wiz.xml',
        'board_tgt_view.xml',
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
