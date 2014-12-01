from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

class LogAnalysisReport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        
        self.book = xlwt.Workbook()
        self.sheet = self.book.add_sheet('Logging Analysis')
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour blue;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def filter(self):
        emp_obj = self.pool.get('hr.employee')
        sale_obj = self.pool.get('sale.order')
        company_ids = self.data['company_ids']
        date_from = self.data['date_from']
        date_to = self.data['date_to']


        sql = """
             select to_char(
                (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=k.id) limit 1)
                ,'mm(Month) yyyy') as mon
             from sale_order k where 
                (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=k.id) limit 1)
             <=%s and 

                (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=k.id) limit 1)
             >=%s 
             and k.company_id in %s
             and k.state in ('done','progress')
             group by 1
             order by 1
        """
        self.cr.execute(sql, (date_to, date_from, tuple(company_ids)))
        rgroups = { i[0]: [0, 0.0] for i in self.cr.fetchall() }
        rotator_ids = emp_obj.search(self.cr, self.uid, [('is_rotator', '=', True), ('company_id', 'in', company_ids)], context=self.context)

        res = {}
        for rid in rotator_ids:
            groups = rgroups.copy()
            emp = emp_obj.browse(self.cr, self.uid, rid, context=self.context)
            sql = """
                select count(k.sale_id), sum(s.amount_total),
                to_char(
                    (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=s.id) limit 1)
                    ,'mm(Month) yyyy') as mon
                 from sale_employee_rel k left join sale_order s on s.id=k.sale_id
                 where k.employee_id=%s
                 and 
                    (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=s.id) limit 1)
                 <=%s and 
                    (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=s.id) limit 1)
                 >=%s 
                 and s.company_id in %s
                 and s.state in ('done','progress')
                 group by  3
                """
            self.cr.execute(sql, (rid, date_to, date_from, tuple(company_ids)))
            total = self.cr.fetchall()
            if total:
                #raise ValueError, total
                total = {o[2]: [o[0], o[1]] for o in total}
                groups.update(total)
            res[rid] = groups

        sql = """
            select k.company_id,count(k.id), sum(k.amount_total),

            to_char(
            (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=k.id) limit 1)
            ,'mm(Month) yyyy') as mon

            from sale_order k
            where k.id not in (select sale_id from sale_employee_rel)
            and 
            (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=k.id) limit 1)
            <=%s and 

            (select i.date_invoice from account_invoice i where i.id in 
            (select si.invoice_id from sale_order_invoice_rel si where si.order_id=k.id) limit 1)
            >=%s 
             and k.company_id in %s
             and k.state in ('done','progress')
            group by 4, company_id
        """
        self.cr.execute(sql, ( date_to, date_from, tuple(company_ids)))
        nres = {}
        for c in company_ids:
            nres[c] = rgroups.copy()
        nonce = self.cr.fetchall()
        #raise ValueError, (nonce, nres)
        ttt = 1
        for cid, count, sum, mon in nonce:
            nres[cid][mon] = [count, sum]
        return (res, nres) 


    def generate(self):
        emp_obj = self.pool.get('hr.employee')
        sale_obj = self.pool.get('sale.order')
        num_style = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')
        res, nonce = self.filter()
        key = 3
        for p in res:
            u = res[p].keys()
            u.sort()
            for m in u:
                self.sheet.write_merge(0, 0, key+1, key+2, m, self.style)
                self.sheet.write(1, key+1, 'No. of SO', self.style)
                self.sheet.write(1, key+2, 'Amount', self.style)
                key += 2
                
            break
        self.sheet.write(1, 2, 'TGT Entity', self.style)
        self.sheet.write(1, 3, 'Employee Name', self.style)

        
        
        i = 2
        for emp_id, data in res.iteritems():
            u = data.keys()
            u.sort()
            emp = emp_obj.browse(self.cr, self.uid, emp_id, context=self.context)
            self.sheet.write(i, 2, emp.company_id.name)
            self.sheet.write(i, 3, emp.name)
            key = 3
            for m in u:
                self.sheet.write(i, key+1, data[m][0], num_style)
                self.sheet.write(i, key+2, data[m][1], num_style)
                key += 2
            i += 1
        comp_obj = self.pool.get('res.company')
        for cid, data in nonce.iteritems():
            u = data.keys()
            u.sort()
            comp = comp_obj.browse(self.cr, self.uid, cid, context=self.context)
            self.sheet.write(i, 2, comp.name)
            self.sheet.write(i, 3, 'None')

            key = 3
            for m in u:
                self.sheet.write(i, key+1, data[m][0], num_style)
                self.sheet.write(i, key+2, data[m][1], num_style)
                key += 2
            i += 1


        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp

