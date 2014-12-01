from openerp.report import report_sxw


class rotator_daysoff(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(payslip_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'get_total': self.get_total,
        })

    def get_total(self, obj):
        payslip_line = self.pool.get('hr.payslip.line')
        res = []
        ids = []
        for id in range(len(obj)):
            if obj[id].appears_on_payslip == True:
                ids.append(obj[id].id)
        if ids:
            for l in payslip_line.browse(self.cr, self.uid, ids):
                if l.code == 'NET':
                    res = l.amount
        return res and res or 0.0

report_sxw.report_sxw('report.rotator.daysoff.report', 'hr.employee', 'addons/hr_payroll_tgt/report/rotator_daysoff.rml', parser=rotator_daysoff, header='internal')
