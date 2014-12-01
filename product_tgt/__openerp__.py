# -*- coding: utf-8 -*-



{
    'name': 'TGT Product Module',
    'version': '0.1',
    'category': 'Customer Relationship Management',
    'sequence': 1,
    'summary': 'Basic',
    'description': """
TGT Product Module
====================================================

Built a new Pricelist System
""",
    'author': 'TGT Oilfield Services',
    'website': 'http://www.tgtoil.com',
    'depends': [
        'product',
        'l10n_tgt',
    ],
    'data': [
        'product_tgt_view.xml',
        #'product_data.xml',
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
