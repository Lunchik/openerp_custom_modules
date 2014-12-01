from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields


class revenue_by_cc_client(osv.osv):
    _name = 'sale.by.cc.client.report'
    _description = "Revenue By CostCenter/Client Report"
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
        'defcol_one_id': fields.many2one('account.analytic.account', 'Cost Centre'),
        'defcol_two_id': fields.many2one('res.partner', 'Customer'),
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
        'total': fields.function(_total, type="float", method=True, string='Total', store=False),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_by_cc_client')
        cr.execute("""

            create or replace view sale_by_cc_client as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy') as mon, 
            (select s.project_id from sale_order s where s.id in (
                    select si.order_id from sale_order_invoice_rel si where si.invoice_id=i.id
                ) limit 1)  as parent_id,

            i.partner_id as partner_id,

            sum(i.amount_total) as total

            from  account_invoice i, res_partner p where i.type='out_invoice' 
            and i.state in ('open','paid') and i.partner_id= p.id 
            
            group by 1, 2, 3
            order by i.partner_id;

        """)

        tools.sql.drop_view_if_exists(cr, 'sale_by_cc_client_report')
        cr.execute("""
            create or replace view sale_by_cc_client_report as
            select 
            distinct on(k.partner_id)
            k.partner_id as defcol_two_id,
            ROW_NUMBER() OVER() as id,
            k.parent_id as defcol_one_id,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_cc_client
             where partner_id = k.partner_id
             and parent_id=k.parent_id
            ) as total
            
            
            from sale_by_cc_client k  where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') and parent_id is not NULL

            group by partner_id, parent_id
            order by partner_id;

        """)



class revenue_by_cc_general(osv.osv):
    _name = 'sale.by.cc.report'
    _description = "Revenue By CostCenter Report"
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
        'defcol_one_id': fields.many2one('account.analytic.account', 'Cost Centre'),
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
        'total': fields.function(_total, type="float", method=True, string='Total', store=False),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_by_cc')
        cr.execute("""
            create or replace view sale_by_cc as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy') as mon, 
            (select s.project_id from sale_order s where s.id in (
                    select si.order_id from sale_order_invoice_rel si where si.invoice_id=i.id
                ) limit 1)  as costcentre_id,

            p.country_id as country_id,

            sum(i.amount_total) as total

            from  account_invoice i, res_partner p where i.type='out_invoice' 
            and i.state in ('open','paid') and i.partner_id= p.id 
            
            group by 1, 2, 3;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_cc_report')
        cr.execute("""
            create or replace view sale_by_cc_report as
            select 
            distinct on(k.costcentre_id, k.country_id)
            k.costcentre_id as defcol_one_id,
            k.country_id as defcol_two_id,
            ROW_NUMBER() OVER() as id,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_cc
             where costcentre_id = k.costcentre_id and country_id=k.country_id
            ) as total
            
            
            from sale_by_cc k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') and costcentre_id is not NULL;
        """)


#EDITED by N 1: beginning
class revenue_by_service(osv.osv):
    _name = 'sale.by.service.report'
    _description = "Sale By Service Report"
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
        'defcol_two_id': fields.many2one('product.category', 'Category'),
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
        tools.sql.drop_view_if_exists(cr, 'sale_by_service')
        cr.execute("""
            create or replace view sale_by_service1 as
            
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy') as mon, 
            il.product_id as product_id,
            (
                select categ_id from product_template where id=il.product_id
            ) as category_id,

            sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice'
            group by 1, 2;


        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_report')
        cr.execute("""
            create or replace view sale_by_service_report as
            select 
            distinct on(k.product_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.category_id as defcol_two_id,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service1
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service1
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service1
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from sale_by_service1
             where product_id = k.product_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service1
             where product_id = k.product_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_service1
             where product_id = k.product_id
            ) as total
            
            
            from sale_by_service1 k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)



class revenue_by_service_general(osv.osv):
    _name = 'sale.by.service.general.report'
    _description = "General Revenue By Service Report"
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
        'category_id': fields.many2one('product.category', 'Category'),
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
        'total': fields.function(_total, type="float", method=True, string='YTD', store=False),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_general_report')
        cr.execute("""
            create or replace view sale_by_service_general_report as
            select 
            ROW_NUMBER() OVER() as id,
            k.defcol_two_id as category_id,
            sum(k.jan) as jan,
            sum(k.feb) as feb,
            sum(k.mar) as mar,
            sum(k.q1) as q1,
            sum(k.apr) as apr,
            sum(k.may) as may,
            sum(k.jun) as jun,
            sum(k.q2) as q2,
            sum(k.jul) as jul,
            sum(k.aug) as aug,
            sum(k.sep) as sep,
            sum(k.q3) as q3,
            sum(k.oct) as oct,
            sum(k.nov) as nov,
            sum(k.des) as des,
            sum(k.q4) as q4,
            sum(k.total) as total
    
            from sale_by_service_report k
            group by k.defcol_two_id;
        """)
#EDITED by N 1:end
#EDITED BY N 3: CLIENT REPORT: beginning
class rsa(osv.osv):
    _name = 'sale.by.client.report'
    _description = "Sale By Client Report"
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
        'defcol_one_id': fields.many2one('res.partner', 'Customer'),
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
        'total': fields.function(_total, type="float", method=True, string='YTD', store=False),
    }

    def init(self, cr):

        tools.sql.drop_view_if_exists(cr, 'sale_by_client')
        #raise ValueError ("data[0]['company_id'][0]")

        cr.execute("""
            create or replace view   sale_by_client as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy' ) as mon, 

           partner_id as partner_id,

            sum(amount_total) as total

            from  account_invoice i where type='out_invoice' and state in ('open', 'paid')

            group by 1, 2
            order by partner_id;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_client_report')
        cr.execute("""
            create or replace view sale_by_client_report as
            select 
            distinct on(k.partner_id)
            k.partner_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            (
                select si.country_id from res_partner si where
                si.id = k.partner_id
            ) as defcol_two_id,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_client
             where partner_id = k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_client
             where partner_id = k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_client
             where partner_id = k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from sale_by_client
             where partner_id = k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_client
             where partner_id = k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from sale_by_client
             where partner_id = k.partner_id
            ) as total
            
            
            
            
            from sale_by_client k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)
#N: end
####New By service/ country report
class revenue_by_service_country(osv.osv):
    _name = 'sale.by.service.op.report'
    _description = "Sale By Service/Operator Report"
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
        'defcol_two_id': fields.many2one('res.partner', 'Operator'),
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
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_op')
        cr.execute("""
            create or replace view sale_by_service_op as
            
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy' ) as mon, 
            il.product_id as product_id,
            
            (select s.enduser_id from sale_order s where s.id in (
                    select si.order_id from sale_order_invoice_rel si where si.invoice_id=i.id
                ) limit 1)as user_id

            ,sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice'
            group by 1, 2,3
            order by il.product_id;



        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_op_report')
        cr.execute("""
            create or replace view sale_by_service_op_report as
            select 
            distinct on(k.product_id,k.user_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.user_id as defcol_two_id,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id
             and user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service_op
             where product_id = k.product_id and
             user_id = k.user_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4
            
            
            from sale_by_service_op k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') and  user_id notnull;
        """)


##End


####New seals by oprater by month
class report_operator(osv.osv):
    _name = 'sale.by.operator.report'
    _description = "Sale By Operator Report"
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
        'defcol_one_id': fields.many2one('res.partner', 'Operator'),
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
        'total': fields.function(_total, type="float", method=True, string='YTD', store=False),
    }

    def init(self, cr):

        tools.sql.drop_view_if_exists(cr, 'sale_by_operator')
        #raise ValueError ("data[0]['company_id'][0]")

        cr.execute("""
            create or replace view   sale_by_operator as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy' ) as mon, 

            (select s.enduser_id from sale_order s where s.id in (
                    select si.order_id from sale_order_invoice_rel si where si.invoice_id=i.id
                ) limit 1)as user_id,
          p.country_id as country_id,

            sum(i.amount_total) as total

            from  account_invoice i, res_partner p where i.type='out_invoice' 
            and i.state in ('open','paid') and i.partner_id= p.id 

            
            group by 1, 2,3;
        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_operator_report')
        cr.execute("""
            create or replace view sale_by_operator_report as
            select 
            distinct on(k.user_id,k.country_id)
            k.user_id as defcol_one_id,
            k.country_id as defcol_two_id,
            ROW_NUMBER() OVER() as id,
            
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id

             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id

             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id

             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_operator
             where user_id = k.user_id
             and country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4

            
            
            
            
            from sale_by_operator k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') and  user_id notnull;
        """)


##end
####New By service/ country report
class revenue_by_service_country(osv.osv):
    _name = 'sale.by.service.c.report'
    _description = "Sale By Service/Country Report"
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
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_c')
        cr.execute("""
            create or replace view sale_by_service_c as
            
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy' ) as mon, 
            il.product_id as product_id,
            i.partner_id,
            (select country_id from res_partner r where r.id=i.partner_id)as country_id

            ,sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice'
            group by 1, 2,3
            order by il.product_id;



        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_c_report')
        cr.execute("""
            create or replace view sale_by_service_c_report as
            select 
            distinct on(k.product_id,k.country_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id
             and country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service_c
             where product_id = k.product_id and
             country_id = k.country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4
            
            
            from sale_by_service_c k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)


##End


####New By service/ client report
class revenue_by_service_client(osv.osv):
    _name = 'sale.by.service.client.report'
    _description = "Sale By Service/Country Report"
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
        'defcol_two_id': fields.many2one('res.partner', 'Customer'),
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
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_client')
        cr.execute("""
            
            create or replace view sale_by_service_client as
            select to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy' ) as mon, 
            il.product_id as product_id,
            i.partner_id as partner_id

            ,sum((il.price_unit * (1-il.discount/100)) * il.quantity)
             as total
            from account_invoice i
            left join account_invoice_line il
            on il.invoice_id=i.id
            where i.state in ('open', 'paid') and i.type='out_invoice'
            group by 1, 2,3
            order by il.product_id;

        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_service_client_report')
        cr.execute("""
            create or replace view sale_by_service_client_report as
            select 
            distinct on(k.product_id,k.partner_id)
            k.product_id as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.partner_id as defcol_two_id,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from sale_by_service_client
             where product_id = k.product_id  and partner_id=k.partner_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4
            
            
            from sale_by_service_client k where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy');
        """)


##End
###AVG By Country


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
        'product_id': fields.many2one('product.product', 'Service'),
        'country_id': fields.many2one('res.country', 'Country'),
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
        tools.sql.drop_view_if_exists(cr, 'sale_by_ro_pre1')
        cr.execute("""
                  create or replace view   sale_by_ro_pre1 as
                  SELECT  to_char((select ip.date_start from account_period ip where ip.id=i.period_id),  'mm(Month) yyyy' ) as mon,
                  l.id, 
                  l.product_id,
                  name_template,
                   
                   
                   
                  l.invoice_id,
                  i.number,
                  l.price_subtotal as sub,
                  l.price_unit as prise,
                  rp.country_id,
                  p.job_cat
                  FROM 
                 account_invoice_line l, 
                account_invoice i, 
                  product_product p, 
                  res_partner rp
                WHERE 
                  i.id = l.invoice_id AND
                 p.id = l.product_id 
                   and i.type='out_invoice' 
                   and i.state in ('open', 'paid')
                   and i.partner_id=rp.id
                 


                  order by   l.invoice_id



        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_ro_pre2')
        cr.execute("""
                create or replace view   sale_by_ro_pre2 as
                select i.invoice_id,i.mon,i.country_id, (select sum (sub) from sale_by_ro_pre1 where job_cat!='other' and invoice_id=i.invoice_id) as x,
                (select sum (sub) from sale_by_ro_pre1 where job_cat='other' and invoice_id=i.invoice_id) as y
                from sale_by_ro_pre1 i
                group by invoice_id,mon,country_id
                order by invoice_id


        """)
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_cou')
        cr.execute("""
                create or replace view   sale_by_avg_cou as
                select p1.product_id,p1.job_cat,p1.country_id,p2.y ,p2.x,p1.name_template,p1.invoice_id,p2.mon , 
                p1.sub+COALESCE(COALESCE(p1.sub/p2.x,0)*p2.y,0)as ntotal from sale_by_ro_pre1 p1,sale_by_ro_pre2 p2 where p1.invoice_id=p2.invoice_id
                order by invoice_id


        """)
        tools.sql.drop_view_if_exists(cr, 'avg_cou')
        cr.execute("""
            create or replace view avg_cou as
            select 
            k.product_id as product_id,
            k.mon as mon,
            k.country_id as country_id,
            ROW_NUMBER() OVER() as id,
            sum(ntotal)as total
             
            from sale_by_avg_cou k where 
            to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') 
            and  job_cat!='other'
            group by product_id,country_id,mon 
            order by product_id,country_id



        """)
        
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_cou_report')
        cr.execute("""
            create or replace view sale_by_avg_cou_report as
            select 
            distinct on(k.product_id,k.country_id)
            k.product_id as product_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as country_id,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from avg_cou
             where product_id = k.product_id
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from avg_cou
             where product_id = k.product_id
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from avg_cou
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4
            
            
            from avg_cou k;
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
        'product_id': fields.many2one('product.product', 'Service'),
        'country_id': fields.many2one('res.country', 'Country'),
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

        tools.sql.drop_view_if_exists(cr, 'avg_cou2')
        cr.execute("""
                  create or replace view avg_cou2 as
                  
                    select p1.product_id 
                    ,p1.country_id,
                    p2.mon , 
                    
                    sum(p1.sub) total from sale_by_ro_pre1 p1,sale_by_ro_pre2 p2 where p1.invoice_id=p2.invoice_id and p2.x isnull and p2.y is not null  
                    group by p1.product_id,p1.country_id , p2.mon



        """)
   
       
        tools.sql.drop_view_if_exists(cr, 'sale_by_avg_cou_report2')
        cr.execute("""
            create or replace view sale_by_avg_cou_report2 as
            select 
            distinct on(k.product_id,k.country_id)
            k.product_id as product_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as country_id,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total) from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total) from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select total from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select total from avg_cou2
             where product_id = k.product_id
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select total from avg_cou2
             where product_id = k.product_id
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from avg_cou2
             where product_id = k.product_id 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4
            
            
            from avg_cou2 k;
        """)

##End

class salesRevenueReport(object):
    def __init__(self, data, cr, uid, pool, context=None):
        self.data = data
        self.cr = cr
        self.uid = uid
        self.pool = pool
        self.context = context
        self.book = xlwt.Workbook()
        self.style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green;font: height 250, bold 1, color white;')
        self.temp = tempfile.NamedTemporaryFile()

    def generate(self):
        filter = self.data.get('filter_id')
        self.num_style = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')
        self.num_style1 = xlwt.Style.easyxf('font: height 150, bold 0;', num_format_str='#,##0.00')
        self.header_style = xlwt.Style.easyxf('font: height 200, bold 1;')
        sheet_name = ''
        if filter == 'opreator':
            sheet_name = 'Revenue by Operator by Country'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Operator by Country', 'sale_by_operator_report', 'sale.by.operator.report')
        if filter == 'serviceop':
            sheet_name = 'Revenue by Service by Operator'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Service by Operator', 'sale_by_service_op_report', 'sale.by.service.op.report')
        if filter == 'service2':
            sheet_name = 'Revenue by Service Detailed'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Service', 'sale_by_service_report', 'sale.by.service.report')
        if filter == 'cost':
            sheet_name = 'Revenue by Cost Centres General'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Cost Center by Country', 'sale_by_cc_report', 'sale.by.cc.report')
        if filter == 'cost_client':
            sheet_name = 'Revenue by Cost Centre Client'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Cost Centre by Client','sale_by_cc_client_report','sale.by.cc.client.report')
        if filter == 'country':
            sheet_name = 'Revenue by Country'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_by_country()
        if filter == 'countryc':
            sheet_name = 'Revenue by Client by Country'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue By Client by Country', 'sale_by_client_report', 'sale.by.client.report')
        if filter == 'servisec':
            sheet_name = 'Revenue by Service by Country'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Service by Country', 'sale_by_service_c_report', 'sale.by.service.c.report')
        if filter == 'servise_client':
            sheet_name = 'Revenue by Service by Client'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_common('Revenue by Service by Client', 'sale_by_service_client_report', 'sale.by.service.client.report')
        if filter == 'avg_cou':
            sheet_name = 'Revenue by Avg job by  Country'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_by_avgjcc()
        if filter == 'avg_po':
            sheet_name = 'Revenue by Avg job by Client'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_by_avgpa()
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp



    def generate_common(self, title_name, report_name, report_dot_name):
        self.sheet.write(1, 1, title_name, self.header_style)
        self.sheet.write(1, 2, 'Jan', self.header_style)
        self.sheet.write(1, 3, 'Feb', self.header_style)
        self.sheet.write(1, 4, 'Mar', self.header_style)
        self.sheet.write(1, 5, 'Q1', self.header_style)
        self.sheet.write(1, 6, 'Apr', self.header_style)
        self.sheet.write(1, 7, 'May', self.header_style)
        self.sheet.write(1, 8, 'Jun', self.header_style)
        self.sheet.write(1, 9, 'Q2', self.header_style)
        self.sheet.write(1, 10, 'Jul', self.header_style)
        self.sheet.write(1, 11, 'Aug', self.header_style)
        self.sheet.write(1, 12, 'Sep', self.header_style)
        self.sheet.write(1, 13, 'Q3', self.header_style)
        self.sheet.write(1, 14, 'Oct', self.header_style)
        self.sheet.write(1, 15, 'Nov', self.header_style)
        self.sheet.write(1, 16, 'Dec', self.header_style)
        self.sheet.write(1, 17, 'Q4', self.header_style)
        self.sheet.write(1, 18, 'Total', self.header_style)

        self.cr.execute("""
            SELECT DISTINCT defcol_two_id FROM %s
            """%(report_name))
        cat_ids = [c[0] for c in self.cr.fetchall()]
 
        totaly_bottom = {
            1: 0.0,
            2: 0.0,
            3: 0.0,
            4: 0.0,
            5: 0.0,
            6: 0.0,
            7: 0.0,
            8: 0.0,
            9: 0.0,
            10: 0.0,
            11: 0.0,
            12: 0.0,
            13: 0.0,
            14: 0.0,
            15: 0.0,
            16: 0.0,
            17: 0.0,
        }

        i = 2
        for c in cat_ids:
            obj = self.pool.get(report_dot_name)
            ids = obj.search(self.cr, self.uid, [('defcol_two_id', '=', c)], context=self.context)
            totaly = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }
            cat = ''
            for rec in obj.browse(self.cr, self.uid, ids, context=self.context):
                cat = rec.defcol_two_id.name
                self.sheet.write(i, 1, rec.defcol_one_id.name)
                self.sheet.write(i, 2, rec.jan, self.num_style1)
                totaly[1] += rec.jan
                self.sheet.write(i, 3, rec.feb, self.num_style1)
                totaly[2] += rec.feb
                self.sheet.write(i, 4, rec.mar, self.num_style1)
                totaly[3] += rec.mar
                self.sheet.write(i, 5, rec.q1, self.num_style1)
                totaly[4] += rec.q1
                self.sheet.write(i, 6, rec.apr, self.num_style1)
                totaly[5] += rec.apr
                self.sheet.write(i, 7, rec.may, self.num_style1)
                totaly[6] += rec.may
                self.sheet.write(i, 8, rec.jun, self.num_style1)
                totaly[7] += rec.jun
                self.sheet.write(i, 9, rec.q2, self.num_style1)
                totaly[8] += rec.q2
                self.sheet.write(i, 10, rec.jul, self.num_style1)
                totaly[9] += rec.jul
                self.sheet.write(i, 11, rec.aug, self.num_style1)
                totaly[10] += rec.aug
                self.sheet.write(i, 12, rec.sep, self.num_style1)
                totaly[11] += rec.sep
                self.sheet.write(i, 13, rec.q3, self.num_style1)
                totaly[12] += rec.q3
                self.sheet.write(i, 14, rec.oct, self.num_style1)
                totaly[13] += rec.oct
                self.sheet.write(i, 15, rec.nov, self.num_style1)
                totaly[14] += rec.nov
                self.sheet.write(i, 16, rec.des, self.num_style1)
                totaly[15] += rec.des
                self.sheet.write(i, 17, rec.q4, self.num_style1)
                totaly[16] += rec.q4
                self.sheet.write(i, 18, rec.total, self.num_style1)
                totaly[17] += rec.total
                i += 1
            self.sheet.write(i, 1, cat, self.num_style)
            totaly_bottom[1] += totaly[1]
            self.sheet.write(i, 2, totaly[1], self.num_style)
            totaly_bottom[2] += totaly[2]
            self.sheet.write(i, 3, totaly[2], self.num_style)
            totaly_bottom[3] += totaly[3]
            self.sheet.write(i, 4, totaly[3], self.num_style)
            totaly_bottom[4] += totaly[4]
            self.sheet.write(i, 5, totaly[4], self.num_style)
            totaly_bottom[5] += totaly[5]
            self.sheet.write(i, 6, totaly[5], self.num_style)
            totaly_bottom[6] += totaly[6]
            self.sheet.write(i, 7, totaly[6], self.num_style)
            totaly_bottom[7] += totaly[7]
            self.sheet.write(i, 8, totaly[7], self.num_style)
            totaly_bottom[8] += totaly[8]
            self.sheet.write(i, 9, totaly[8], self.num_style)
            totaly_bottom[9] += totaly[9]
            self.sheet.write(i, 10, totaly[9], self.header_style)
            totaly_bottom[10] += totaly[10]
            self.sheet.write(i, 11, totaly[10], self.num_style)
            totaly_bottom[11] += totaly[11]
            self.sheet.write(i, 12, totaly[11], self.num_style)
            totaly_bottom[12] += totaly[12]
            self.sheet.write(i, 13, totaly[12], self.num_style)
            totaly_bottom[13] += totaly[13]
            self.sheet.write(i, 14, totaly[13], self.num_style)
            totaly_bottom[14] += totaly[14]
            self.sheet.write(i, 15, totaly[14], self.num_style)
            totaly_bottom[15] += totaly[15]
            self.sheet.write(i, 16, totaly[15], self.num_style)
            totaly_bottom[16] += totaly[16]
            self.sheet.write(i, 17, totaly[16], self.num_style)
            totaly_bottom[17] += totaly[17]
            self.sheet.write(i, 18, totaly[17], self.num_style)

            i += 1
#bottom Total line
        i += 2;
        self.sheet.write(i, 1, 'Total', self.header_style)
        self.sheet.write(i, 2, totaly_bottom[1], self.num_style)
        self.sheet.write(i, 3, totaly_bottom[2], self.num_style)
        self.sheet.write(i, 4, totaly_bottom[3], self.num_style)
        self.sheet.write(i, 5, totaly_bottom[4], self.num_style)
        self.sheet.write(i, 6, totaly_bottom[5], self.num_style)
        self.sheet.write(i, 7, totaly_bottom[6], self.num_style)
        self.sheet.write(i, 8, totaly_bottom[7], self.num_style)
        self.sheet.write(i, 9, totaly_bottom[8], self.num_style)
        self.sheet.write(i, 10, totaly_bottom[9], self.num_style)
        self.sheet.write(i, 11, totaly_bottom[10], self.num_style)
        self.sheet.write(i, 12, totaly_bottom[11], self.num_style)
        self.sheet.write(i, 13, totaly_bottom[12], self.num_style)
        self.sheet.write(i, 14, totaly_bottom[13], self.num_style)
        self.sheet.write(i, 15, totaly_bottom[14], self.num_style)
        self.sheet.write(i, 16, totaly_bottom[15], self.num_style)
        self.sheet.write(i, 17, totaly_bottom[16], self.num_style)
        self.sheet.write(i, 18, totaly_bottom[17], self.num_style)

##End

##avg fun

    def generate_by_avgjcc(self):
           
        self.sheet.write(1, 1, 'Sale By AVGJob/Country Report', self.header_style)
        self.sheet.write(1, 2, 'Jan', self.header_style)
        self.sheet.write(1, 3, 'Feb', self.header_style)
        self.sheet.write(1, 4, 'Mar', self.header_style)
        self.sheet.write(1, 5, 'Q1', self.header_style)
        self.sheet.write(1, 6, 'Apr', self.header_style)
        self.sheet.write(1, 7, 'May', self.header_style)
        self.sheet.write(1, 8, 'Jun', self.header_style)
        self.sheet.write(1, 9, 'Q2', self.header_style)
        self.sheet.write(1, 10, 'Jul', self.header_style)
        self.sheet.write(1, 11, 'Aug', self.header_style)
        self.sheet.write(1, 12, 'Sep', self.header_style)
        self.sheet.write(1, 13, 'Q3', self.header_style)
        self.sheet.write(1, 14, 'Oct', self.header_style)
        self.sheet.write(1, 15, 'Nov', self.header_style)
        self.sheet.write(1, 16, 'Dec', self.header_style)
        self.sheet.write(1, 17, 'Q4', self.header_style)
        self.sheet.write(1, 18, 'Total', self.header_style)

        self.cr.execute("""
            SELECT DISTINCT country_id FROM sale_by_avg_cou_report
            """)
        cat_ids = [c[0] for c in self.cr.fetchall()]

        
        i = 2
        for c in cat_ids:
            obj = self.pool.get('sale.by.avg.cou.report')
            ids = obj.search(self.cr, self.uid, [('country_id', '=', c)], context=self.context)
            totaly = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }
            cat = ''
            for rec in obj.browse(self.cr, self.uid, ids, context=self.context):
                cat = rec.country_id.name
                self.sheet.write(i, 1, rec.product_id.name)
                self.sheet.write(i, 2, rec.jan, self.num_style1)
                totaly[1] += rec.jan
                self.sheet.write(i, 3, rec.feb, self.num_style1)
                totaly[2] += rec.feb
                self.sheet.write(i, 4, rec.mar, self.num_style1)
                totaly[3] += rec.mar
                self.sheet.write(i, 5, rec.q1, self.num_style1)
                totaly[4] += rec.q1
                self.sheet.write(i, 6, rec.apr, self.num_style1)
                totaly[5] += rec.apr
                self.sheet.write(i, 7, rec.may, self.num_style1)
                totaly[6] += rec.may
                self.sheet.write(i, 8, rec.jun, self.num_style1)
                totaly[7] += rec.jun
                self.sheet.write(i, 9, rec.q2, self.num_style1)
                totaly[8] += rec.q2
                self.sheet.write(i, 10, rec.jul, self.num_style1)
                totaly[9] += rec.jul
                self.sheet.write(i, 11, rec.aug, self.num_style1)
                totaly[10] += rec.aug
                self.sheet.write(i, 12, rec.sep, self.num_style1)
                totaly[11] += rec.sep
                self.sheet.write(i, 13, rec.q3, self.num_style1)
                totaly[12] += rec.q3
                self.sheet.write(i, 14, rec.oct, self.num_style1)
                totaly[13] += rec.oct
                self.sheet.write(i, 15, rec.nov, self.num_style1)
                totaly[14] += rec.nov
                self.sheet.write(i, 16, rec.des, self.num_style1)
                totaly[15] += rec.des
                self.sheet.write(i, 17, rec.q4, self.num_style1)
                totaly[16] += rec.q4
                self.sheet.write(i, 18, rec.total, self.num_style1)
                totaly[17] += rec.total
                i += 1
            self.sheet.write(i, 1, cat, self.num_style)
            self.sheet.write(i, 2, totaly[1], self.num_style)
            self.sheet.write(i, 3, totaly[2], self.num_style)
            self.sheet.write(i, 4, totaly[3], self.num_style)
            self.sheet.write(i, 5, totaly[4], self.num_style)
            self.sheet.write(i, 6, totaly[5], self.num_style)
            self.sheet.write(i, 7, totaly[6], self.num_style)
            self.sheet.write(i, 8, totaly[7], self.num_style)
            self.sheet.write(i, 9, totaly[8], self.num_style)
            self.sheet.write(i, 10, totaly[9], self.header_style)
            self.sheet.write(i, 11, totaly[10], self.num_style)
            self.sheet.write(i, 12, totaly[11], self.num_style)
            self.sheet.write(i, 13, totaly[12], self.num_style)
            self.sheet.write(i, 14, totaly[13], self.num_style)
            self.sheet.write(i, 15, totaly[14], self.num_style)
            self.sheet.write(i, 16, totaly[15], self.num_style)
            self.sheet.write(i, 17, totaly[16], self.num_style)
            self.sheet.write(i, 18, totaly[17], self.num_style)

            i += 1
        #raise ValueError ,i
        i += 1
        self.sheet.write(i, 1, 'Other Charges', self.header_style)
        i += 1
        self.cr.execute("""
            SELECT DISTINCT country_id FROM sale_by_avg_cou_report2
            """)
        cat_ids2 = [f[0] for f in self.cr.fetchall()]

        for f in cat_ids2:
            obj2 = self.pool.get('sale.by.avg.cou.report2')
            ids = obj2.search(self.cr, self.uid, [('country_id', '=', f)], context=self.context)
            totaly = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }

            cat = ''


            for rec in obj2.browse(self.cr, self.uid, ids, context=self.context):
                cat = rec.country_id.name
                self.sheet.write(i, 1, rec.product_id.name)
                self.sheet.write(i, 2, rec.jan, self.num_style1)
                totaly[1] += rec.jan
                self.sheet.write(i, 3, rec.feb, self.num_style1)
                totaly[2] += rec.feb
                self.sheet.write(i, 4, rec.mar, self.num_style1)
                totaly[3] += rec.mar
                self.sheet.write(i, 5, rec.q1, self.num_style1)
                totaly[4] += rec.q1
                self.sheet.write(i, 6, rec.apr, self.num_style1)
                totaly[5] += rec.apr
                self.sheet.write(i, 7, rec.may, self.num_style1)
                totaly[6] += rec.may
                self.sheet.write(i, 8, rec.jun, self.num_style1)
                totaly[7] += rec.jun
                self.sheet.write(i, 9, rec.q2, self.num_style1)
                totaly[8] += rec.q2
                self.sheet.write(i, 10, rec.jul, self.num_style1)
                totaly[9] += rec.jul
                self.sheet.write(i, 11, rec.aug, self.num_style1)
                totaly[10] += rec.aug
                self.sheet.write(i, 12, rec.sep, self.num_style1)
                totaly[11] += rec.sep
                self.sheet.write(i, 13, rec.q3, self.num_style1)
                totaly[12] += rec.q3
                self.sheet.write(i, 14, rec.oct, self.num_style1)
                totaly[13] += rec.oct
                self.sheet.write(i, 15, rec.nov, self.num_style1)
                totaly[14] += rec.nov
                self.sheet.write(i, 16, rec.des, self.num_style1)
                totaly[15] += rec.des
                self.sheet.write(i, 17, rec.q4, self.num_style1)
                totaly[16] += rec.q4
                self.sheet.write(i, 18, rec.total, self.num_style1)
                totaly[17] += rec.total
                i += 1
            self.sheet.write(i, 1, cat, self.num_style)
            self.sheet.write(i, 2, totaly[1], self.num_style)
            self.sheet.write(i, 3, totaly[2], self.num_style)
            self.sheet.write(i, 4, totaly[3], self.num_style)
            self.sheet.write(i, 5, totaly[4], self.num_style)
            self.sheet.write(i, 6, totaly[5], self.num_style)
            self.sheet.write(i, 7, totaly[6], self.num_style)
            self.sheet.write(i, 8, totaly[7], self.num_style)
            self.sheet.write(i, 9, totaly[8], self.num_style)
            self.sheet.write(i, 10, totaly[9], self.header_style)
            self.sheet.write(i, 11, totaly[10], self.num_style)
            self.sheet.write(i, 12, totaly[11], self.num_style)
            self.sheet.write(i, 13, totaly[12], self.num_style)
            self.sheet.write(i, 14, totaly[13], self.num_style)
            self.sheet.write(i, 15, totaly[14], self.num_style)
            self.sheet.write(i, 16, totaly[15], self.num_style)
            self.sheet.write(i, 17, totaly[16], self.num_style)
            self.sheet.write(i, 18, totaly[17], self.num_style)

            i += 1 
###by opreator
###AVG CLINT
    def generate_by_avgpa(self):
           
        self.sheet.write(1, 1, 'Sale By AVGJob/Client Report', self.header_style)
        self.sheet.write(1, 2, 'Jan', self.header_style)
        self.sheet.write(1, 3, 'Feb', self.header_style)
        self.sheet.write(1, 4, 'Mar', self.header_style)
        self.sheet.write(1, 5, 'Q1', self.header_style)
        self.sheet.write(1, 6, 'Apr', self.header_style)
        self.sheet.write(1, 7, 'May', self.header_style)
        self.sheet.write(1, 8, 'Jun', self.header_style)
        self.sheet.write(1, 9, 'Q2', self.header_style)
        self.sheet.write(1, 10, 'Jul', self.header_style)
        self.sheet.write(1, 11, 'Aug', self.header_style)
        self.sheet.write(1, 12, 'Sep', self.header_style)
        self.sheet.write(1, 13, 'Q3', self.header_style)
        self.sheet.write(1, 14, 'Oct', self.header_style)
        self.sheet.write(1, 15, 'Nov', self.header_style)
        self.sheet.write(1, 16, 'Dec', self.header_style)
        self.sheet.write(1, 17, 'Q4', self.header_style)
        self.sheet.write(1, 18, 'Total', self.header_style)

        self.cr.execute("""
            SELECT DISTINCT partner_id FROM sale_by_avg_pa_report
            """)
        cat_ids = [c[0] for c in self.cr.fetchall()]

        
        i = 2
        for c in cat_ids:
            obj = self.pool.get('sale.by.avg.pa.report')
            ids = obj.search(self.cr, self.uid, [('partner_id', '=', c)], context=self.context)
            totaly = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }
            cat = ''
            for rec in obj.browse(self.cr, self.uid, ids, context=self.context):
                cat = rec.partner_id.name
                self.sheet.write(i, 1, rec.product_id.name)
                self.sheet.write(i, 2, rec.jan, self.num_style1)
                totaly[1] += rec.jan
                self.sheet.write(i, 3, rec.feb, self.num_style1)
                totaly[2] += rec.feb
                self.sheet.write(i, 4, rec.mar, self.num_style1)
                totaly[3] += rec.mar
                self.sheet.write(i, 5, rec.q1, self.num_style1)
                totaly[4] += rec.q1
                self.sheet.write(i, 6, rec.apr, self.num_style1)
                totaly[5] += rec.apr
                self.sheet.write(i, 7, rec.may, self.num_style1)
                totaly[6] += rec.may
                self.sheet.write(i, 8, rec.jun, self.num_style1)
                totaly[7] += rec.jun
                self.sheet.write(i, 9, rec.q2, self.num_style1)
                totaly[8] += rec.q2
                self.sheet.write(i, 10, rec.jul, self.num_style1)
                totaly[9] += rec.jul
                self.sheet.write(i, 11, rec.aug, self.num_style1)
                totaly[10] += rec.aug
                self.sheet.write(i, 12, rec.sep, self.num_style1)
                totaly[11] += rec.sep
                self.sheet.write(i, 13, rec.q3, self.num_style1)
                totaly[12] += rec.q3
                self.sheet.write(i, 14, rec.oct, self.num_style1)
                totaly[13] += rec.oct
                self.sheet.write(i, 15, rec.nov, self.num_style1)
                totaly[14] += rec.nov
                self.sheet.write(i, 16, rec.des, self.num_style1)
                totaly[15] += rec.des
                self.sheet.write(i, 17, rec.q4, self.num_style1)
                totaly[16] += rec.q4
                self.sheet.write(i, 18, rec.total, self.num_style1)
                totaly[17] += rec.total
                i += 1
            self.sheet.write(i, 1, cat, self.num_style)
            self.sheet.write(i, 2, totaly[1], self.num_style)
            self.sheet.write(i, 3, totaly[2], self.num_style)
            self.sheet.write(i, 4, totaly[3], self.num_style)
            self.sheet.write(i, 5, totaly[4], self.num_style)
            self.sheet.write(i, 6, totaly[5], self.num_style)
            self.sheet.write(i, 7, totaly[6], self.num_style)
            self.sheet.write(i, 8, totaly[7], self.num_style)
            self.sheet.write(i, 9, totaly[8], self.num_style)
            self.sheet.write(i, 10, totaly[9], self.header_style)
            self.sheet.write(i, 11, totaly[10], self.num_style)
            self.sheet.write(i, 12, totaly[11], self.num_style)
            self.sheet.write(i, 13, totaly[12], self.num_style)
            self.sheet.write(i, 14, totaly[13], self.num_style)
            self.sheet.write(i, 15, totaly[14], self.num_style)
            self.sheet.write(i, 16, totaly[15], self.num_style)
            self.sheet.write(i, 17, totaly[16], self.num_style)
            self.sheet.write(i, 18, totaly[17], self.num_style)

            i += 1
        #raise ValueError ,i
        i += 1
        self.sheet.write(i, 1, 'Other Charges', self.header_style)
        i += 1
        self.cr.execute("""
            SELECT DISTINCT partner_id FROM sale_by_avg_pa_report2
            """)
        cat_ids2 = [f[0] for f in self.cr.fetchall()]

        for f in cat_ids2:
            obj2 = self.pool.get('sale.by.avg.pa.report2')
            ids = obj2.search(self.cr, self.uid, [('partner_id', '=', f)], context=self.context)
            totaly = {
                1: 0.0,
                2: 0.0,
                3: 0.0,
                4: 0.0,
                5: 0.0,
                6: 0.0,
                7: 0.0,
                8: 0.0,
                9: 0.0,
                10: 0.0,
                11: 0.0,
                12: 0.0,
                13: 0.0,
                14: 0.0,
                15: 0.0,
                16: 0.0,
                17: 0.0,
            }

            cat = ''


            for rec in obj2.browse(self.cr, self.uid, ids, context=self.context):
                cat = rec.partner_id.name
                self.sheet.write(i, 1, rec.product_id.name)
                self.sheet.write(i, 2, rec.jan, self.num_style1)
                totaly[1] += rec.jan
                self.sheet.write(i, 3, rec.feb, self.num_style1)
                totaly[2] += rec.feb
                self.sheet.write(i, 4, rec.mar, self.num_style1)
                totaly[3] += rec.mar
                self.sheet.write(i, 5, rec.q1, self.num_style1)
                totaly[4] += rec.q1
                self.sheet.write(i, 6, rec.apr, self.num_style1)
                totaly[5] += rec.apr
                self.sheet.write(i, 7, rec.may, self.num_style1)
                totaly[6] += rec.may
                self.sheet.write(i, 8, rec.jun, self.num_style1)
                totaly[7] += rec.jun
                self.sheet.write(i, 9, rec.q2, self.num_style1)
                totaly[8] += rec.q2
                self.sheet.write(i, 10, rec.jul, self.num_style1)
                totaly[9] += rec.jul
                self.sheet.write(i, 11, rec.aug, self.num_style1)
                totaly[10] += rec.aug
                self.sheet.write(i, 12, rec.sep, self.num_style1)
                totaly[11] += rec.sep
                self.sheet.write(i, 13, rec.q3, self.num_style1)
                totaly[12] += rec.q3
                self.sheet.write(i, 14, rec.oct, self.num_style1)
                totaly[13] += rec.oct
                self.sheet.write(i, 15, rec.nov, self.num_style1)
                totaly[14] += rec.nov
                self.sheet.write(i, 16, rec.des, self.num_style1)
                totaly[15] += rec.des
                self.sheet.write(i, 17, rec.q4, self.num_style1)
                totaly[16] += rec.q4
                self.sheet.write(i, 18, rec.total, self.num_style1)
                totaly[17] += rec.total
                i += 1
            self.sheet.write(i, 1, cat, self.num_style)
            self.sheet.write(i, 2, totaly[1], self.num_style)
            self.sheet.write(i, 3, totaly[2], self.num_style)
            self.sheet.write(i, 4, totaly[3], self.num_style)
            self.sheet.write(i, 5, totaly[4], self.num_style)
            self.sheet.write(i, 6, totaly[5], self.num_style)
            self.sheet.write(i, 7, totaly[6], self.num_style)
            self.sheet.write(i, 8, totaly[7], self.num_style)
            self.sheet.write(i, 9, totaly[8], self.num_style)
            self.sheet.write(i, 10, totaly[9], self.header_style)
            self.sheet.write(i, 11, totaly[10], self.num_style)
            self.sheet.write(i, 12, totaly[11], self.num_style)
            self.sheet.write(i, 13, totaly[12], self.num_style)
            self.sheet.write(i, 14, totaly[13], self.num_style)
            self.sheet.write(i, 15, totaly[14], self.num_style)
            self.sheet.write(i, 16, totaly[15], self.num_style)
            self.sheet.write(i, 17, totaly[16], self.num_style)
            self.sheet.write(i, 18, totaly[17], self.num_style)

            i += 1 
