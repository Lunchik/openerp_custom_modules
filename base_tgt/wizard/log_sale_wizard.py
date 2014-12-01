from openerp.osv import osv, fields

import base64

class tgt_sales_Revenue_report(osv.osv):
    _name = 'tgt.sales.revenue.report'

    _columns = {
        'filter_id': fields.selection([
            ('opreator', 'Operator/Country'),
            ('serviceop', 'Service/Operator'),
            ('countryc', 'Country/Client'),
            ('avg_cou', 'Avg Job/Country'),
            ('avg_po', 'Avg Job/Client'),
            ('avg_opr', 'Avg Job/Operator'),
            ('avg_de', 'Avg Job/Category'),
            ('service2', 'Service (Detailed)'),
            ('service3', 'Service (Category)'),
            ('servisec', 'Service/Country'),
            ('servise_client', 'Service/Client'),
            ('cost', 'Cost Centre/Country'),
            ('cost_client',' Cost Centre/Client'),

            ], 'Revenue by',required=True ,size=200),
    } 
    _defaults = {
        'filter_id': 'filter_no',
        }

    def print_report(self, cr, uid, ids, context=None):
        ''' Adding Data Here ! '''
        data = self.read(cr, uid, ids[0], ['filter_id'], context=context)

        from ..report.log_sales_report import salesRevenueReport
        report = salesRevenueReport(data, cr, uid, self.pool, context)

        temp = report.generate()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'accounting.report.xcel.download',
            'view_mode': 'form',
            'target': 'new',
            'name': ' Sales Revenue Report XLS',
            'datas': data,
            'context': {'r_file': base64.encodestring(temp.read()),},
        }
