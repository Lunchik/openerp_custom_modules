from openerp.osv import osv, fields
from openerp.tools.translate import _

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64


class CycleEnum(object):
    def __init__(self, seq):
        self.seq = list(seq)
        self.cursor = 0

    def next(self):
        t = self.seq[self.cursor]
        self.cursor += 1
        if self.cursor == len(self.seq):
            self.cursor = 0
        return t


STATUS = [
    ('L', '[L] Land (Onshore)'),
    ('S', '[S] Sea (off shore)'),
    ('B', '[B] Base'),
    ('O', '[O] Days Off'),
    ('SL', '[SL] Sick leave'),
    ('T', '[T] Travel'),
    ('T+', '[T+] Travel with Allowance'),
    ('W', '[W] Week end / Holiday'),
    ('V', '[V] Vacation'),
]

class rotator_daysoff(osv.osv_memory):

    _name = 'tgt.rotator.daysoff'
    _columns = {
        'date_from': fields.date('Date From'),
        'date_to': fields.date('Date To'),
        'name': fields.char('File Name', size=150),
        'r_file': fields.binary('Download Report'),
    }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'name': 'tgt_leaves_report.xls',
    }

    def leaves_builder(self, cr, uid, book, datas, context=None):
        sheet = book.add_sheet('Employees Leaves')
        holiday_obj = self.pool.get('hr.holidays')
        hstatus_obj = self.pool.get('hr.holidays.status')
        emp_obj = self.pool.get('hr.employee')

        status_ids = hstatus_obj.search(cr, uid, [('active', '=', True)], context=context)
        emp_ids = emp_obj.search(cr, uid, [('is_rotator', '=', False)], context=context)

        style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        lll = [
            xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 150, bold 1, color white;')
            ]
        ce = CycleEnum(lll)
        sheet.write(0, 0, 'Employee ID', style)
        sheet.write(0, 1, 'Employee Name', style)
        sheet.write(0, 2, 'Remaining Leaves', style)
        sheet.write(0, 3, 'Total Requested Leaves', style)
        k = 4
        aaa = {}
        for status in hstatus_obj.browse(cr, uid, status_ids, context=context):
            sheet.write(0, k, status.name, ce.next())
            aaa[status.id] = k
            k += 1
        # columns paddings
        for i in range(k + 1):
            sheet.col(i).width = 5000
        sheet.col(1).width = 10000
        sheet.col(2).width = 8000
        sheet.col(3).width = 8000

        sheet.write(1, 0, 'From Date', xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;font: height 200, bold 1, color white;'))
        sheet.write(1, 1, datas['date_from'], xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;font: height 150, bold 1, color white;'))
        sheet.write(1, k-2, 'To Date', xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;font: height 200, bold 1, color white;'))
        sheet.write(1, k-1, datas['date_to'], xlwt.Style.easyxf('pattern: pattern solid, fore_colour red;font: height 150, bold 1, color white;'))

        hold = aaa.copy()
        r = 2
        for emp in emp_obj.browse(cr, uid, emp_ids, context=context):
            sheet.write(r, 0, emp.employee_id)
            sheet.write(r, 1, emp.name)
            for a in hold:
                hold[a] = 0
            hol_ids = holiday_obj.search(cr, uid, [('date_from', '>=', datas['date_from']), ('date_to', '<=', datas['date_to']), ('type', '=', 'remove'), ('employee_id', '=', emp.id)], context=context)
            if hol_ids:
                for h in holiday_obj.browse(cr, uid, hol_ids, context=context):
                    hold[h.holiday_status_id.id] += h.number_of_days
            total = 0
            for num in hold:
                total += hold[num]
                sheet.write(r, aaa[num], hold[num])
            sheet.write(r, 2, emp.remaining_leaves)
            sheet.write(r, 3, total)
            r += 1


        return book
        

    def builder(self, cr, uid, datas, context=None):
        wsheet_obj = self.pool.get('hr.payslip.working_sheet')
        emp_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        emp_ids = emp_obj.search(cr, uid, [('is_rotator', '=', True)], context=context)

        #raise ValueError, emp_ids

        book = xlwt.Workbook()
        sheet = book.add_sheet('Rotator Daysoff')
        style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        lll = [
            xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 150, bold 1, color white;')
            ]
        ce = CycleEnum(lll)
        sheet.write(0, 0, 'Employee ID', style)
        sheet.write(0, 1, 'Employee Name', style)
        sheet.write(0, 2, 'Rotation Method', style)
        sheet.write(0, 3, 'Last State', style)
        sheet.write(0, 4, 'Remaining Daysoff', style)
        sheet.write(0, 5, 'Next Daysoff Date', style)
        o = 6
        for i in STATUS:
            sheet.write(0, o, i[1], ce.next())
            o += 1


        # columns paddings
        for i in range(o + 1):
            sheet.col(i).width = 8000

        sheet.col(1).width = 10000

        temp = tempfile.NamedTemporaryFile()
        r = 1
        ename_style = xlwt.Style.easyxf('font: bold 1;')
        for emp in emp_obj.browse(cr, uid, emp_ids, context=context):
            sids = wsheet_obj.search(cr, uid, [('employee_id', '=', emp.id), ('date', '>=', datas['date_from']), ('date', '<=', datas['date_to'])], order='date desc', context=context)
            #cont_ids = contract_obj.search(cr, uid, [('employee_id', '=', emp.id)], limit=1, context=context)
            #if not cont_ids:
            #    continue
            #cont_ids = cont_ids[0]
            #contract = contract_obj.browse(cr, uid, cont_ids, context=context)
            summ = dict(STATUS)
            for k in summ:
                summ[k] = 0
            status_rec = wsheet_obj.browse(cr, uid, sids, context=context)
            lrec, ldoff, lbdoff, all_dayson, all_daysoff = None, None, None, 0.0, 0.0
            for i in STATUS:
                sc = i[0]
                for s in status_rec:
                    if s.state == 'O':
                        ldoff = not ldoff and s or ldoff
                    else:
                        all_dayson += 1
                    lrec = status_rec[0]
                    if s.state == sc:
                        summ[sc] += 1
                    if ldoff and s.state != 'O' and not lbdoff:
                        # last work day before dayoff
                        lbdoff = s


            rm = emp.rotation_id
            rm_days_off, rm_days_work = (rm and int(rm.days_off) or 0, rm and int(rm.days_work) or 0)

            lrec_date = lrec and datetime.strptime(lrec.date, '%Y-%m-%d') or None
            ldoff_date = ldoff and datetime.strptime(ldoff.date, '%Y-%m-%d') or None
            lbdoff_date = lbdoff and datetime.strptime(lbdoff.date, '%Y-%m-%d') or None

            ldoff_days = ldoff_date and lbdoff_date and ldoff_date - lbdoff_date or None
            ldoff_days = ldoff_days and ldoff_days.days or 0
            lrec_days = 0
            if lrec and lrec.state != 'O' and ldoff_date:
                lrec_days = lrec_date - ldoff_date
                lrec_days = lrec_days.days

            remaining_days_off = 0
            next_expect_doff = 0
            if ldoff_date and rm:
                if ldoff_days < rm_days_off:
                    remaining_days_off = rm_days_off - ldoff_days
                if lrec.state != 'O':
                    next_expect_doff = rm_days_work - lrec_days

                if lrec.state == 'O':
                    next_expect_doff = rm_days_work + remaining_days_off

            all_daysoff, all_dayson = 0.0, 0.0
            for k in status_rec:
                if k.state != 'O':
                    all_dayson += 1
                else:
                    all_daysoff += 1

            if all_dayson:
                abc = 0.0
                if rm_days_work:
                    abc = (1.0 /rm_days_work)
                remaining_days_off = all_dayson * (rm_days_off * abc) - all_daysoff

            #raise ValueError, ((1.0 /rm_days_work), rm_days_off * (1.0 /rm_days_work),emp.name, all_dayson, all_daysoff, rm_days_off, rm_days_work, len(sids), len(status_rec), remaining_days_off)


            next_expect_doff_date = lrec_date and lrec_date + timedelta(days=next_expect_doff) or 'UnKnown'


            sheet.write(r, 0, emp.employee_id)
            sheet.write(r, 1, emp.name, ename_style)
            sheet.write(r, 2, emp.rotation_id.name, ename_style)
            company = emp.company_id

            #sheet.write(r, 3, company and company.name or '---')
            sheet.write(r, 3, lrec and ('%s %s' % (lrec.date, lrec.state)))
            sheet.write(r, 4, remaining_days_off)
            if type(next_expect_doff_date) == type(''):
                sheet.write(r, 5, next_expect_doff_date)
            else:
                sheet.write(r, 5, next_expect_doff_date, xlwt.Style.easyxf(num_format_str='YYYY-MM-DD'))
            o = 6
            for w in STATUS:
                sheet.write(r, o, summ[w[0]])
                o += 1
            r += 1

        book = self.leaves_builder(cr, uid, book, datas, context=context)

        book.save(temp)

        return temp

    def default_get(self, cr, uid, fields, context=None):
        context = context and context or {}
        data = super(rotator_daysoff, self).default_get(cr, uid, fields, context=context)
        if context.get('r_file', False):
            data['r_file'] = context.get('r_file')
        return data

    def print_report(self, cr, uid, ids, context=None):
        context = context and context or {}
        datas = self.read(cr, uid, ids, context=context)[0]
        wsheet_obj = self.pool.get('hr.payslip.working_sheet')
        psids = wsheet_obj.search(cr, uid, [('date', '>=', datas['date_from']), ('date', '<=', datas['date_to'])], context=context)
        datas['ids'] = psids or []
        #datas['ids'] = psids and payslip_obj.browse(cr, uid, psids, context=context) or []

        report = self.builder(cr, uid, datas, context=context)
        report.seek(0)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tgt.rotator.daysoff',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Download Rotators Daysoff Report',
            'context': {'r_file': base64.encodestring(report.read()),},
        }
        

