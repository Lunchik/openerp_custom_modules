from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields


class revenue_by_avgj_partner(osv.osv):
    _name = 'sale.by.avg.pa.report'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Client'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('Total')
    }
    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'avg_pa')
        cr.execute("""
             CREATE OR REPLACE VIEW avg_pa AS
             SELECT
			 distinct on (i.id, p.job_cat)
             ( SELECT to_char((( SELECT ip.date_start
               FROM account_period ip
               WHERE ip.id = i.period_id))::timestamp with time zone, 'mm(Month) yyyy'::text) AS to_char) AS mon,
             ( SELECT count(u.id)/count(u.id) AS count
            FROM account_invoice_line u, product_product p1
            WHERE u.invoice_id = i.id AND u.product_id = p1.id AND p1.job_cat::text = p.job_cat::text and u.price_subtotal >= 0
            GROUP BY p1.job_cat, u.invoice_id ) AS countx,
             ( SELECT count(u.id)/count(u.id) AS count
            FROM account_invoice_line u, product_product p1
            WHERE u.invoice_id = i.id AND u.product_id = p1.id AND p1.job_cat::text = p.job_cat::text and u.price_subtotal < 0
            GROUP BY p1.job_cat, u.invoice_id ) AS countn,
            account_invoice_line.product_id,
	    (select pt.categ_id from product_template pt where pt.id = account_invoice_line.product_id) as product_category_id,
            p.job_cat,
            (select sum(ail.price_subtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text)
             AS price_subtotal,
             CASE
             WHEN ((select sum(ail.price_nsubtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text) is null)
        OR ((select sum(ail.price_nsubtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text) = 0)
             THEN (select sum(ail.price_subtotal) from account_invoice_line ail, product_product p1
		where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text)
             ELSE (select sum(ail.price_nsubtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text)
             END AS total,
            i.id, i.partner_id,
            ( SELECT s.enduser_id
           FROM sale_order s
            WHERE (s.id IN ( SELECT si.order_id
                   FROM sale_order_invoice_rel si
                  WHERE si.invoice_id = i.id))
            LIMIT 1) AS user_id,
            rp.country_id
           FROM account_invoice i, account_invoice_line, product_product p, res_partner rp
            WHERE account_invoice_line.invoice_id = i.id AND p.id = account_invoice_line.product_id AND i.partner_id = rp.id
                    and i.company_id != 8
            GROUP BY i.id, account_invoice_line.product_id, i.partner_id, p.job_cat, rp.country_id
            ORDER BY i.id;
        """)

        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac AS
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.partner_id
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.partner_id
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        #tools.sql.drop_view_if_exists(cr, 'sale_by_avg_pa_report')
        cr.execute("""
            create or replace view sale_by_avg_pa_report as
            select
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            k.job_cat,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac where product_id = k.product_id and k.partner_id=partner_id and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             
            ) as total
            
            from avg_pa k  where  job_cat!='other'  and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy'); 
        """)

class revenue_by_avgj_partner2(osv.osv):
    _name = 'sale.by.avg.pa.report2'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Client'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('Total')
    }
   
            
    def cv (self,cr,uid,ids,context=None):
        bro= self.pool.get('account.invoice')
        #raise ValueError,ids

        idin2=[]
        idin1=[]

        for rec in bro.browse(cr,uid,ids,context=context):
            #raise ValueError,rec.invoice_line

            for line in rec.invoice_line:
                #raise ValueError,line
                if line.product_id.job_cat != 'other':
                    idin1.append(rec.id)  
                else:
                    idin2.append(rec.id)  
        inter=set(idin2).intersection( set(idin1) )
        idin=set(idin2)-inter
        #raise ValueError, (idin)

        return idin

    def init11(self, cr,uid,ids,context=None):
        
        ids=self.cv(cr,uid,ids,context=context)
        #raise ValueError, ids
        
      
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_pa_report2')
        cr.execute("""
            create or replace view sale_by_avg_pa_report2 as
            select 
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            k.job_cat,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,

            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.partner_id=partner_id) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac where product_id = k.product_id and k.partner_id=partner_id and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id 
             and k.partner_id=partner_id
             
            ) as total
            
            
            from avg_pa k  where  id in %s and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """, (tuple(ids),))

###AVGOPRATER


class revenue_by_avgj_opr(osv.osv):
    _name = 'sale.by.avg.opr.report'
    _description = "Sale By AVGJob/oprater Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('Total')
    }

    def init(self, cr):
        
        cr.execute("""
                CREATE OR REPLACE VIEW avg_pac1 AS 
                SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                FROM avg_pa
                GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                 ORDER BY avg_pa.mon, avg_pa.product_id;
        """)       
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_opr_report')
        cr.execute("""
            create or replace view sale_by_avg_opr_report as
            select 
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id) from avg_pa 
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id)  from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id)  from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id)  from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac1 where product_id = k.product_id and k.user_id=user_id and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             
            ) as total
            
            
            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_oprrtner2(osv.osv):
    _name = 'sale.by.avg.opr.report2'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('Total')
    }
            
    def cv (self,cr,uid,ids,context=None):
        bro= self.pool.get('account.invoice')
        #raise ValueError,ids

        idin2=[]
        idin1=[]

        for rec in bro.browse(cr,uid,ids,context=context):
            #raise ValueError,rec.invoice_line

            for line in rec.invoice_line:
                #raise ValueError,line
                if line.product_id.job_cat != 'other':
                    idin1.append(rec.id)  
                else:
                    idin2.append(rec.id)  
        inter=set(idin2).intersection( set(idin1) )
        idin=set(idin2)-inter
        #raise ValueError, (idin)

        return idin

    def init11(self, cr,uid,ids,context=None):
        
        ids=self.cv(cr,uid,ids,context=context)
        #raise ValueError, ids
   
      
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_opr_report2')
        cr.execute("""
            create or replace view sale_by_avg_opr_report2 as
            select 
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id) from avg_pa 
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id)  from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id)  from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac1 where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.user_id=user_id) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac1 where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.user_id=user_id)  from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac1 where product_id = k.product_id and k.user_id=user_id and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id 
             and k.user_id=user_id
             
            ) as total
            
            
            
            from avg_pa k  where  id in %s and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """, (tuple(ids),))

class revenue_by_avgj_de(osv.osv):
    _name = 'sale.by.avg.de.report'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('Total')
    }

    def init(self, cr):
        
        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac2 AS 
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """) 
      
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_de_report')
        cr.execute("""
            create or replace view sale_by_avg_de_report as
           select 
            distinct on(k.product_id,k.job_cat)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.job_cat as defcol_two_id,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat) from avg_pa 
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat)  from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat)  from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat)  from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac2 where product_id = k.product_id and k.job_cat=job_cat and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             
            ) as total
            
            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_de2(osv.osv):
    _name = 'sale.by.avg.de.report2'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.float('Total')
    }
    def cv (self,cr,uid,ids,context=None):
        bro= self.pool.get('account.invoice')
        #raise ValueError,ids

        idin2=[]
        idin1=[]

        for rec in bro.browse(cr,uid,ids,context=context):
            #raise ValueError,rec.invoice_line

            for line in rec.invoice_line:
                #raise ValueError,line
                if line.product_id.job_cat != 'other':
                    idin1.append(rec.id)  
                else:
                    idin2.append(rec.id)  
        inter=set(idin2).intersection( set(idin1) )
        idin=set(idin2)-inter
        #raise ValueError, (idin)

        return idin

    def init11(self, cr,uid,ids,context=None):
        
        ids=self.cv(cr,uid,ids,context=context)

       
      
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_de_report2')
        cr.execute("""
            create or replace view sale_by_avg_de_report2 as
           select 
            distinct on(k.product_id,k.job_cat)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.job_cat as defcol_two_id,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat) from avg_pa 
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat)  from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat)  from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac2 where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.job_cat=job_cat) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac2 where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.job_cat=job_cat)  from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac2 where product_id = k.product_id and k.job_cat=job_cat and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id 
             and k.job_cat=job_cat
             
            ) as total
            
            from avg_pa k  where  id in %s and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """, (tuple(ids),))
      #EDITED by N 1: beginning
class revenue_by_service_cat2(osv.osv):
    _name = 'sale.by.service.cat2.report'
    _description = "Sale By Service/Category Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.function(_total, type='float', method=True, string='YTD', store=False),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_cat2')
        cr.execute("""
            create or replace view sale_by_service_cat2 as
            
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy') as mon, 
            il.product_id as product_id,
            (
                select job_cat from product_product where id=il.product_id
            ) as category_id,

            sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice'
            group by 1, 2;


        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_cat2_report')
        cr.execute("""
            create or replace view sale_by_service_cat2_report as
            select 
            distinct on(k.product_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.category_id as defcol_two_id,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_service_cat2
             where product_id = k.product_id
            ) as total
            
            
            from sale_by_service_cat2 k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

###Technology/Country
class revenue_by_service_cat3(osv.osv):
    _name = 'sale.by.service.cat3.report'
    _description = "Sale By Service/Category Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'defcol_one_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.function(_total, type='float', method=True, string='YTD', store=False),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_cat3')
        cr.execute("""
            create or replace view sale_by_service_cat3 as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy') as mon,
            il.product_id as product_id,
            (
                select job_cat from product_product where id=il.product_id
            ) as category_id,
	        p.country_id as country_id,
            sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from res_partner p,
            account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice' and i.partner_id = p.id
            group by 1, 2, 4;


        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_cat3_report')
        cr.execute("""
            create or replace view sale_by_service_cat3_report as
            select
            distinct on(k.country_id, k.category_id)
            k.category_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_service_cat3
             where category_id = k.category_id and country_id = k.country_id
            ) as total


            from sale_by_service_cat3 k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

###Service category/Country
class revenue_by_service_cat_cou(osv.osv):
    _name = 'sale.by.service.cat.cou.report'
    _description = "Sale By Service/Category Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'defcol_one_id': fields.many2one('product.category', 'Category'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.function(_total, type='float', method=True, string='YTD', store=False),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_cat_cou')
        cr.execute("""
            create or replace view sale_by_service_cat_cou as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy') as mon,
            il.product_id as product_id,
            (
                select categ_id from product_template where id=il.product_id
            ) as category_id,
	        p.country_id as country_id,
            sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from res_partner p,
            account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice' and i.partner_id = p.id
            group by 1, 2, 4;


        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_cat_cou_report')
        cr.execute("""
            create or replace view sale_by_service_cat_cou_report as
            select distinct on(k.country_id, k.category_id)
            k.country_id as defcol_two_id,
            ROW_NUMBER() OVER() as id,
            k.category_id as defcol_one_id,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_service_cat_cou
             where category_id = k.category_id and country_id = k.country_id
            ) as total


            from sale_by_service_cat_cou k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)


class revenue_by_avgj_country(osv.osv):
    _name = 'sale.by.avg.cou.report'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.function(_total, type='float', method=True, string='YTD', store=False),
    }

    def init(self, cr):
       
        cr.execute("""
            CREATE OR REPLACE VIEW avg_pac3 AS 
             SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                   FROM avg_pa
                  GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                  ORDER BY avg_pa.mon, avg_pa.product_id;
        """)         
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_cou_report')
        cr.execute("""
            create or replace view sale_by_avg_cou_report as
            select
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id

             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id)  from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id)  from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id)  from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac3 where product_id = k.product_id and k.country_id=country_id and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id

            ) as total


            from avg_pa k  where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)


class revenue_by_avgj_country2(osv.osv):
    _name = 'sale.by.avg.cou.report2'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    def _total(self, cr, uid, ids, f, k, context=None):
        #ids = ids and ids or False
        if not ids:
            return {}
        res = {}
        for obj in self.browse(cr, uid, ids, context=context):
            su = self.suma(
                obj.q1,
                obj.q2,
                obj.q3,
                obj.q4,
                )
            res[obj.id] = su
        return res

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'jan': fields.float('Jan'),
        'feb': fields.float('Feb'),
        'mar': fields.float('Mar'),
        'q1': fields.float('Q1'),
        'apr': fields.float('Apr'),
        'may': fields.float('May'),
        'jun': fields.float('Jun'),
        'q2': fields.float('Q2'),
        'jul': fields.float('Jul'),
        'aug': fields.float('Aug'),
        'sep': fields.float('Sep'),
        'q3': fields.float('Q3'),
        'oct': fields.float('Oct'),
        'nov': fields.float('Nov'),
        'des': fields.float('Dec'),
        'q4': fields.float('Q4'),
        'total': fields.function(_total, type='float', method=True, string='YTD', store=False),
    }
    def cv (self,cr,uid,ids,context=None):
        bro= self.pool.get('account.invoice')
        #raise ValueError,ids

        idin2=[]
        idin1=[]

        for rec in bro.browse(cr,uid,ids,context=context):
            #raise ValueError,rec.invoice_line

            for line in rec.invoice_line:
                #raise ValueError,line
                if line.product_id.job_cat != 'other':
                    idin1.append(rec.id)  
                else:
                    idin2.append(rec.id)  
        inter=set(idin2).intersection( set(idin1) )
        idin=set(idin2)-inter
        #raise ValueError, (idin)

        return idin

    def init11(self, cr,uid,ids,context=None):
        
        ids=self.cv(cr,uid,ids,context=context)
        
       
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_cou_report2')
        cr.execute("""
            create or replace view sale_by_avg_cou_report2 as
            select 
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id) from avg_pa 
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id)  from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id)  from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total)/(select count from avg_pac3 where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY') and product_id = k.product_id and k.country_id=country_id) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total)/(select sum(count) from avg_pac3 where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')) and product_id = k.product_id and k.country_id=country_id)  from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total)/(select sum(count) from avg_pac3 where product_id = k.product_id and k.country_id=country_id and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ) from avg_pa
             where product_id = k.product_id 
             and k.country_id=country_id
             
            ) as total
            
            
            
            
            from avg_pa k  where  id in %s and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """, (tuple(ids),))


##Web reports by quarter

##Web reports by Client

class revenue_by_avgj_partner1(osv.osv):
    _name = 'sale.web.avg.pa.reportq1'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Client'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'jjan': fields.float('Jan Jobs'),
        'feb': fields.float('Feb'),
        'jfeb': fields.float('Feb Jobs'),
        'mar': fields.float('Mar'),
        'jmar': fields.float('Mar Jobs'),
        'q1': fields.float('Q1'),
        'jq1': fields.float('Q1 Jobs'),
    }

    def init(self, cr):

        tools.sql.drop_view_if_exists(cr, 'avg_pa')
        cr.execute("""
             CREATE OR REPLACE VIEW avg_pa AS
             SELECT
			 distinct on (i.id, p.job_cat)
             ( SELECT to_char((( SELECT ip.date_start
               FROM account_period ip
               WHERE ip.id = i.period_id))::timestamp with time zone, 'mm(Month) yyyy'::text) AS to_char) AS mon,
             ( SELECT count(u.id)/count(u.id) AS count
            FROM account_invoice_line u, product_product p1
            WHERE u.invoice_id = i.id AND u.product_id = p1.id AND p1.job_cat::text = p.job_cat::text and u.price_subtotal >= 0
            GROUP BY p1.job_cat, u.invoice_id ) AS countx,
             ( SELECT count(u.id)/count(u.id) AS count
            FROM account_invoice_line u, product_product p1
            WHERE u.invoice_id = i.id AND u.product_id = p1.id AND p1.job_cat::text = p.job_cat::text and u.price_subtotal < 0
            GROUP BY p1.job_cat, u.invoice_id ) AS countn,
            account_invoice_line.product_id,
	    (select pt.categ_id from product_template pt where pt.id = account_invoice_line.product_id) as product_category_id,
            p.job_cat,
            (select sum(ail.price_subtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text)
             AS price_subtotal,
             CASE
             WHEN ((select sum(ail.price_nsubtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text) is null)
        OR ((select sum(ail.price_nsubtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text) = 0)
             THEN (select sum(ail.price_subtotal) from account_invoice_line ail, product_product p1
		where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text)
             ELSE (select sum(ail.price_nsubtotal) from account_invoice_line ail, product_product p1
             where ail.invoice_id = i.id and ail.product_id = p1.id AND p1.job_cat::text = p.job_cat::text)
             END AS total,
            i.id, i.partner_id,
            ( SELECT s.enduser_id
           FROM sale_order s
            WHERE (s.id IN ( SELECT si.order_id
                   FROM sale_order_invoice_rel si
                  WHERE si.invoice_id = i.id))
            LIMIT 1) AS user_id,
            rp.country_id
           FROM account_invoice i, account_invoice_line, product_product p, res_partner rp
            WHERE account_invoice_line.invoice_id = i.id AND p.id = account_invoice_line.product_id AND i.partner_id = rp.id
                    and i.company_id != 8
            GROUP BY i.id, account_invoice_line.product_id, i.partner_id, p.job_cat, rp.country_id
            ORDER BY i.id;
        """)
        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac AS
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.partner_id
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.partner_id
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_pa_reportq1')
        cr.execute("""
            create or replace view sale_web_avg_pa_reportq1 as
            select
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.partner_id)
	        as short_name,
            k.job_cat,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jjan,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jfeb,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jmar,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(count) from avg_pac
             where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jq1

            from avg_pa k  where  job_cat!='other'  and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_partner2(osv.osv):
    _name = 'sale.web.avg.pa.reportq2'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Client'),
        'short_name': fields.char('Short Name', size=200),
        'apr': fields.float('Apr'),
        'japr': fields.float('Apr Jobs'),
        'may': fields.float('May'),
        'jmay': fields.float('May Jobs'),
        'jun': fields.float('Jun'),
        'jjun': fields.float('Jun Jobs'),
        'q2': fields.float('Q2'),
        'jq2': fields.float('Q2 Jobs'),
    }

    def init(self, cr):

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_pa_reportq2')
        cr.execute("""
            create or replace view sale_web_avg_pa_reportq2 as
            select
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.partner_id)
	        as short_name,
            k.job_cat,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as japr,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jmay,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jjun,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(count) from avg_pac
             where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jq2

            from avg_pa k  where  job_cat!='other'  and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_partner3(osv.osv):
    _name = 'sale.web.avg.pa.reportq3'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Client'),
        'short_name': fields.char('Short Name', size=200),
        'jul': fields.float('Jul'),
        'jjul': fields.float('Jul Jobs'),
        'aug': fields.float('Aug'),
        'jaug': fields.float('Aug Jobs'),
        'sep': fields.float('Sep'),
        'jsep': fields.float('Sep Jobs'),
        'q3': fields.float('Q3'),
        'jq3': fields.float('Q3 Jobs'),
    }

    def init(self, cr):

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_pa_reportq3')
        cr.execute("""
            create or replace view sale_web_avg_pa_reportq3 as
            select
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.partner_id)
	        as short_name,
            k.job_cat,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jjul,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jaug,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jsep,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(count) from avg_pac
             where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jq3

            from avg_pa k  where  job_cat!='other'  and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_partner4(osv.osv):
    _name = 'sale.web.avg.pa.reportq4'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Client'),
        'short_name': fields.char('Short Name', size=200),
        'oct': fields.float('Oct'),
        'joct': fields.float('Oct Jobs'),
        'nov': fields.float('Nov'),
        'jnov': fields.float('Nov Jobs'),
        'des': fields.float('Dec'),
        'jdes': fields.float('Dec Jobs'),
        'q4': fields.float('Q4'),
        'jq4': fields.float('Q4 Jobs'),
    }

    def init(self, cr):

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_pa_reportq4')
        cr.execute("""
            create or replace view sale_web_avg_pa_reportq4 as
            select
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.partner_id)
	        as short_name,
            k.job_cat,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as joct,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jnov,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select count from avg_pac
             where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jdes,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.partner_id=partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(count) from avg_pac
             where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.partner_id=partner_id
             ) as jq4

            from avg_pa k  where  job_cat!='other'  and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

##end of reports by Q by Client

##By Operator

class revenue_web_avg1_opr(osv.osv):
    _name = 'sale.web.avg.opr.reportq1'
    _description = "Sale By AVGJob/oprater Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'jan': fields.float('Jan'),
        'jjan': fields.float('Jan Jobs'),
        'feb': fields.float('Feb'),
        'jfeb': fields.float('Feb Jobs'),
        'mar': fields.float('Mar'),
        'jmar': fields.float('Mar Jobs'),
        'q1': fields.float('Q1'),
        'jq1': fields.float('Q1 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
                CREATE OR REPLACE VIEW avg_pac1 AS
                SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                FROM avg_pa
                GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                 ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_opr_reportq1')
        cr.execute("""
            create or replace view sale_web_avg_opr_reportq1 as
            select
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.user_id)
	        as short_name,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jjan,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jfeb,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jmar,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(count) from avg_pac1
             where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.user_id=user_id
            ) as jq1

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_web_avg2_opr(osv.osv):
    _name = 'sale.web.avg.opr.reportq2'
    _description = "Sale By AVGJob/oprater Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'apr': fields.float('Apr'),
        'japr': fields.float('Apr Jobs'),
        'may': fields.float('May'),
        'jmay': fields.float('May Jobs'),
        'jun': fields.float('Jun'),
        'jjun': fields.float('Jun Jobs'),
        'q2': fields.float('Q2'),
        'jq2': fields.float('Q2 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
                CREATE OR REPLACE VIEW avg_pac1 AS
                SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                FROM avg_pa
                GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                 ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_opr_reportq2')
        cr.execute("""
            create or replace view sale_web_avg_opr_reportq2 as
            select
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.user_id)
	        as short_name,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as japr,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jmay,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jjun,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(count) from avg_pac1
             where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.user_id=user_id
            ) as jq2

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_web_avg3_opr(osv.osv):
    _name = 'sale.web.avg.opr.reportq3'
    _description = "Sale By AVGJob/oprater Report2"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'jul': fields.float('Jul'),
        'jjul': fields.float('Jul Jobs'),
        'aug': fields.float('Aug'),
        'jaug': fields.float('Aug Jobs'),
        'sep': fields.float('Sep'),
        'jsep': fields.float('Sep Jobs'),
        'q3': fields.float('Q3'),
        'jq3': fields.float('Q3 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
                CREATE OR REPLACE VIEW avg_pac1 AS
                SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                FROM avg_pa
                GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                 ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_opr_reportq3')
        cr.execute("""
            create or replace view sale_web_avg_opr_reportq3 as
            select
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.user_id)
	        as short_name,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jjul,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jaug,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jsep,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(count) from avg_pac1
             where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.user_id=user_id
            ) as jq3

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_web_avg4_opr(osv.osv):
    _name = 'sale.web.avg.opr.reportq4'
    _description = "Sale By AVGJob/oprater Report2"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.partner', 'Country'),
        'short_name': fields.char('Short Name', size=200),
        'oct': fields.float('Oct'),
        'joct': fields.float('Oct Jobs'),
        'nov': fields.float('Nov'),
        'jnov': fields.float('Nov Jobs'),
        'des': fields.float('Dec'),
        'jdes': fields.float('Dec Jobs'),
        'q4': fields.float('Q4'),
        'jq4': fields.float('Q4 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
                CREATE OR REPLACE VIEW avg_pac1 AS
                SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                FROM avg_pa
                GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.user_id
                 ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_opr_reportq4')
        cr.execute("""
            create or replace view sale_web_avg_opr_reportq4 as
            select
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (select p.ref from res_partner p
		    where p.id=k.user_id)
	        as short_name,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as joct,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jnov,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select count from avg_pac1
             where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.user_id=user_id
            ) as jdes,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.user_id=user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(count) from avg_pac1
             where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.user_id=user_id
            ) as jq4

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

##End of web reports for Operator

##By Country

class revenue_by_avgj_country_web1(osv.osv):
    _name = 'sale.web.avg.cou.reportq1'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'jan': fields.float('Jan'),
        'jjan': fields.float('Jan Jobs'),
        'feb': fields.float('Feb'),
        'jfeb': fields.float('Feb Jobs'),
        'mar': fields.float('Mar'),
        'jmar': fields.float('Mar Jobs'),
        'q1': fields.float('Q1'),
        'jq1': fields.float('Q1 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
            CREATE OR REPLACE VIEW avg_pac3 AS
             SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                   FROM avg_pa
                  GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                  ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_cou_reportq1')
        cr.execute("""
            create or replace view sale_web_avg_cou_reportq1 as
            select
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jjan,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jfeb,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jmar,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(count) from avg_pac3
             where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.country_id=country_id
            ) as jq1

            from avg_pa k  where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)

class revenue_by_avgj_country_web2(osv.osv):
    _name = 'sale.web.avg.cou.reportq2'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'apr': fields.float('Apr'),
        'japr': fields.float('Apr Jobs'),
        'may': fields.float('May'),
        'jmay': fields.float('May Jobs'),
        'jun': fields.float('Jun'),
        'jjun': fields.float('Jun Jobs'),
        'q2': fields.float('Q2'),
        'jq2': fields.float('Q2 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
            CREATE OR REPLACE VIEW avg_pac3 AS
             SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                   FROM avg_pa
                  GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                  ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_cou_reportq2')
        cr.execute("""
            create or replace view sale_web_avg_cou_reportq2 as
            select
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as japr,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jmay,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jjun,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(count) from avg_pac3
             where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.country_id=country_id
            ) as jq2

            from avg_pa k  where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)

class revenue_by_avgj_country_web3(osv.osv):
    _name = 'sale.web.avg.cou.reportq3'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'jul': fields.float('Jul'),
        'jjul': fields.float('Jul Jobs'),
        'aug': fields.float('Aug'),
        'jaug': fields.float('Aug Jobs'),
        'sep': fields.float('Sep'),
        'jsep': fields.float('Sep Jobs'),
        'q3': fields.float('Q3'),
        'jq3': fields.float('Q3 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
            CREATE OR REPLACE VIEW avg_pac3 AS
             SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                   FROM avg_pa
                  GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                  ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_cou_reportq3')
        cr.execute("""
            create or replace view sale_web_avg_cou_reportq3 as
            select
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jjul,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jaug,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jsep,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(count) from avg_pac3
             where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.country_id=country_id
            ) as jq3

            from avg_pa k  where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)

class revenue_by_avgj_country_web4(osv.osv):
    _name = 'sale.web.avg.cou.reportq4'
    _description = "Sale By AVGJob/Country Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.many2one('res.country', 'Country'),
        'oct': fields.float('Oct'),
        'joct': fields.float('Oct Jobs'),
        'nov': fields.float('Nov'),
        'jnov': fields.float('Nov Jobs'),
        'des': fields.float('Dec'),
        'jdes': fields.float('Dec Jobs'),
        'q4': fields.float('Q4'),
        'jq4': fields.float('Q4 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
            CREATE OR REPLACE VIEW avg_pac3 AS
             SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                   FROM avg_pa
                  GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.country_id
                  ORDER BY avg_pa.mon, avg_pa.product_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_cou_reportq4')
        cr.execute("""
            create or replace view sale_web_avg_cou_reportq4 as
            select
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as joct,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jnov,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select count from avg_pac3
             where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id and k.country_id=country_id
            ) as jdes,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(count) from avg_pac3
             where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id and k.country_id=country_id
            ) as jq4

            from avg_pa k  where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)

##End of reports by Q by Country


##By Category

class revenue_by_avgj_de1(osv.osv):
    _name = 'sale.web.avg.de.reportq1'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'jan': fields.float('Jan'),
        'jjan': fields.float('Jan Jobs'),
        'feb': fields.float('Feb'),
        'jfeb': fields.float('Feb Jobs'),
        'mar': fields.float('Mar'),
        'jmar': fields.float('Mar Jobs'),
        'q1': fields.float('Q1'),
        'jq1': fields.float('Q1 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac2 AS
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """)

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_de_reportq1')
        cr.execute("""
            create or replace view sale_web_avg_de_reportq1 as
           select
            distinct on(k.product_id,k.job_cat)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.job_cat as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jjan,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jfeb,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jmar,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(count) from avg_pac2
             where mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jq1

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_de2(osv.osv):
    _name = 'sale.web.avg.de.reportq2'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'apr': fields.float('Apr'),
        'japr': fields.float('Apr Jobs'),
        'may': fields.float('May'),
        'jmay': fields.float('May Jobs'),
        'jun': fields.float('Jun'),
        'jjun': fields.float('Jun Jobs'),
        'q2': fields.float('Q2'),
        'jq2': fields.float('Q2 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac2 AS
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """)

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_de_reportq2')
        cr.execute("""
            create or replace view sale_web_avg_de_reportq2 as
           select
            distinct on(k.product_id,k.job_cat)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.job_cat as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as japr,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jmay,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jjun,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(count) from avg_pac2
             where mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jq2

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_de3(osv.osv):
    _name = 'sale.web.avg.de.reportq3'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'jul': fields.float('Jul'),
        'jjul': fields.float('Jul Jobs'),
        'aug': fields.float('Aug'),
        'jaug': fields.float('Aug Jobs'),
        'sep': fields.float('Sep'),
        'jsep': fields.float('Sep Jobs'),
        'q3': fields.float('Q3'),
        'jq3': fields.float('Q3 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac2 AS
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """)

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_de_reportq3')
        cr.execute("""
            create or replace view sale_web_avg_de_reportq3 as
           select
            distinct on(k.product_id,k.job_cat)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.job_cat as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jjul,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jaug,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jsep,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(count) from avg_pac2
             where mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jq3

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)

class revenue_by_avgj_de4(osv.osv):
    _name = 'sale.web.avg.de.reportq4'
    _description = "Sale By AVGJob/Client Report"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i

    _columns = {
        'defcol_one_id': fields.many2one('product.product', 'Service'),
        'defcol_two_id': fields.selection([('hpt', 'HPT'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
        'oct': fields.float('Oct'),
        'joct': fields.float('Oct Jobs'),
        'nov': fields.float('Nov'),
        'jnov': fields.float('Nov Jobs'),
        'des': fields.float('Dec'),
        'jdes': fields.float('Dec Jobs'),
        'q4': fields.float('Q4'),
        'jq4': fields.float('Q4 Jobs'),
    }

    def init(self, cr):

        cr.execute("""
        CREATE OR REPLACE VIEW avg_pac2 AS
         SELECT count(avg_pa.id) AS count, avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
               FROM avg_pa
              GROUP BY avg_pa.mon, avg_pa.product_id, avg_pa.job_cat
              ORDER BY avg_pa.mon, avg_pa.product_id;
        """)

        tools.sql.drop_view_if_exists(cr, 'sale_web_avg_de_reportq4')
        cr.execute("""
            create or replace view sale_web_avg_de_reportq4 as
           select
            distinct on(k.product_id,k.job_cat)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.job_cat as defcol_two_id,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as joct,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jnov,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select count from avg_pac2
             where mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jdes,
            (
             select sum(total) from avg_pa
             where product_id = k.product_id
             and k.job_cat=job_cat
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(count) from avg_pac2
             where mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
             and product_id = k.product_id
             and k.job_cat=job_cat
            ) as jq4

            from avg_pa k where  job_cat!='other' and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)


##End
