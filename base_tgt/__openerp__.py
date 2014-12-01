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
    'name': 'TGT Base Module',
    'version': '0.1',
    'category': 'Customer Relationship Management',
    'sequence': 1,
    'summary': 'Basic',
    'description': """
TGT Basic Module
====================================================

the basic infrastructure for TGT.
""",
    'author': 'TGT Oilfield Services',
    'website': 'http://www.tgtoil.com',
    'depends': [
        'base',
        'multi_company',
        'crm',
        'sale',
        'sale_crm',
        'account_accountant',
        'account_asset',
        'hr_attendance',
        'hr_payroll',
        'account_analytic_analysis',
        'product_tgt',
        'purchase',
    ],
    'data': [
        'base_tgt_view.xml',
        'purchase_view.xml',
        'res_company_view.xml',
        'data.xml',
        'companies_data.xml',
        'companies_logo_data.xml',
        'mail_server_data.xml',
        'wizard/log_analysis_view.xml',
        'wizard/log_analysis_view_asset.xml',
        'wizard/log_sale_view.xml',
        'security/tgt_sales_security.xml',
        'security/ir.model.access.csv',
        'main_board.xml',
        'sales_reports_board.xml',
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
