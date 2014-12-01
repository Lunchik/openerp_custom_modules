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
    'name': 'Multiple Analytic Views',
    'version': '1.0',
    'category': 'Accounting',
    'description': """
This module is for modifying account analytic view to show important data to project manager of services companies.
===================================================================================================================

Adds menu to show relevant information to each manager.You can also view the report of account analytic summary user-wise as well as month-wise.
""",
    'author': 'TGT',
    'sequence': 1,
    'depends' :["analytic", 'account', 'base_tgt', 'base'],
    'data': ['multiple_analytic_view.xml', 'cost_centre_data.xml', 'cost_centre_journals.xml',],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
