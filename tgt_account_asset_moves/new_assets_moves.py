from osv import osv, fields

import openerp.exceptions
from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from openerp import netsvc
import time
from datetime import date, datetime, timedelta
from openerp.tools import config
from openerp.tools.translate import _

class account_asset_asset(osv.osv):
    _inherit = 'account.asset.category'


    _columns = {
        'account_asset_new_cr': fields.many2one('account.account', ' New credit Asset Account', required=True),
        #'account_asset_new_de': fields.many2one('account.account', ' New Asset debit Account', required=True),
        
        

    }


###Class
class sale_by_asst_cou_report(osv.osv):
    _name = 'sale.by.asst.cou.report'
    _description = "Sale By Asset/Country Report"
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
        'defcol_one_id': fields.selection([('hpt', 'Sakmar / Geo'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
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
        'total': fields.float('tot'),
        'janc': fields.float('Jan'),
        'febc': fields.float('Feb'),
        'marc': fields.float('Mar'),
        'q1c': fields.float('Q1'),
        'aprc': fields.float('Apr'),
        'mayc': fields.float('May'),
        'junc': fields.float('Jun'),
        'q2c': fields.float('Q2'),
        'julc': fields.float('Jul'),
        'augc': fields.float('Aug'),
        'sepc': fields.float('Sep'),
        'q3c': fields.float('Q3'),
        'octc': fields.float('Oct'),
        'novc': fields.float('Nov'),
        'desc': fields.float('Dec'),
        'q4c': fields.float('Q4'),
        'totalc': fields.float('tot'),
    }

    def init(self, cr):
       
        cr.execute("""
            create or replace view avg_pau as
            select
                ap.id,
                ap.mon,
                ap.job_cat,
                ap.country_id,
                ap.product_category_id as cat_id,

                CASE
		   WHEN (((select sum(ap2.total) from avg_pa ap2 where ap2.id = ap.id and (ap2.job_cat='other' or ap2.product_category_id not in (3, 5, 8))) is null ) or
			((select sum(ap2.total) from avg_pa ap2 where ap2.id = ap.id and (ap2.job_cat='other' or ap2.product_category_id not in (3, 5, 8))) = 0))
		   THEN ap.total
		   ELSE ap.total*(1+((select sum(ap2.total) from avg_pa ap2 where ap2.id = ap.id and (ap2.job_cat='other' or ap2.product_category_id not in (3, 5, 8)))/
		   (select sum(ap2.total) from avg_pa ap2 where ap2.id = ap.id and ap2.job_cat!='other' and ap2.product_category_id in (3, 5, 8) and ap2.total != 0)))

              END as total
             from avg_pa ap where ap.job_cat!='other' and ap.product_category_id in (3, 5, 8)
             group by id,job_cat,mon ,country_id, product_category_id, total  order by id
	    """)

        #tools.sql.drop_view_if_exists(cr, 'sale_by_asst_cou_report')
        cr.execute("""
            create or replace view sale_by_asst_cou_report as
            select 
            distinct on(k.job_cat,k.country_id)
            k.job_cat as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select sum(total)  from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select sum(total)  from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select sum(total) from avg_pau
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')
            ) as total,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
              
             and mon=concat_ws('-',extract(year from now()), '01-01')::date
            ) as janc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and
              mon=concat_ws('-',extract(year from now()), '02-02')::date
            ) as febc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '03-03')::date
            ) as marc,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '01-01')::date,concat_ws('-',extract(year from now()), '02-02')::date,concat_ws('-',extract(year from now()), '03-03')::date)
            ) as q1c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '04-04')::date
            ) as aprc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '05-05')::date
            ) as mayc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '06-06')::date
            ) as junc,
            (
             select sum(count)  from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '04-04')::date,concat_ws('-',extract(year from now()), '05-05')::date,concat_ws('-',extract(year from now()), '06-06')::date)
            ) as q2c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '07-07')::date
            ) as julc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '08-08')::date
            ) as augc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '09-09')::date
            ) as sepc,
            (
             select sum(count)  from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '07-07')::date,concat_ws('-',extract(year from now()), '08-08')::date,concat_ws('-',extract(year from now()), '09-09')::date)
            ) as q3c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '10-10')::date
            ) as octc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat
             and k.country_id=location_id 
             and mon=concat_ws('-',extract(year from now()), '11-11')::date
            ) as novc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat
             and k.country_id=location_id 
             and mon=concat_ws('-',extract(year from now()), '12-12')::date
            ) as desc,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '10-10')::date,concat_ws('-',extract(year from now()), '11-11')::date,concat_ws('-',extract(year from now()), '12-12')::date)
            ) as q4c,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             
            ) as totalc
            
            
            from avg_pau k  where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)
sale_by_asst_cou_report()

###############asset u 2
class job_by_avgj_country(osv.osv):
    _name = 'job.by.asst.cou.report'
    _description = "Job By Asset/Country Report"
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
        'defcol_one_id': fields.selection([('hpt', 'Sakmar / Geo'),('mid', 'MID'),('snl', 'SNL'),('other', 'OTHER')],'Job Category'),
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
        'total': fields.float('tot'),
        'janc': fields.float('Jan'),
        'febc': fields.float('Feb'),
        'marc': fields.float('Mar'),
        'q1c': fields.float('Q1'),
        'aprc': fields.float('Apr'),
        'mayc': fields.float('May'),
        'junc': fields.float('Jun'),
        'q2c': fields.float('Q2'),
        'julc': fields.float('Jul'),
        'augc': fields.float('Aug'),
        'sepc': fields.float('Sep'),
        'q3c': fields.float('Q3'),
        'octc': fields.float('Oct'),
        'novc': fields.float('Nov'),
        'desc': fields.float('Dec'),
        'q4c': fields.float('Q4'),
        'totalc': fields.float('tot'),
    }

    def init(self, cr):
        cr.execute("""         
                create or replace view avg_pa11 as

                select  COALESCE(countx,0) as countx,

                CASE
                WHEN COALESCE(countx,0) > 0
		        THEN 0
		        ELSE COALESCE(countn,0)
		        END as countn,
		        id, job_cat, product_category_id, country_id,mon

		        from avg_pa
                where product_category_id in (3,5,8) and job_cat != 'other'

                group by id,job_cat,mon ,countx, countn, product_category_id,country_id  order by id

        """)

        #tools.sql.drop_view_if_exists(cr, 'job_by_asst_cou_report')
        cr.execute("""
            create or replace view job_by_asst_cou_report as
            select 
            distinct on(k.job_cat,k.country_id)
            k.job_cat as defcol_one_id,
            ROW_NUMBER() OVER() as id,
            k.country_id as defcol_two_id,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
              
             and mon=to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY')
            ) as jan,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and
              mon=to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY')
            ) as feb,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY')
            ) as mar,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '01-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '02-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '03-01')::date, 'mm(Month) YYYY'))
            ) as q1,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY')
            ) as apr,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY')
            ) as may,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY')
            ) as jun,
            (
             select (sum(countx)-sum(countn))  from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '04-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '05-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '06-01')::date, 'mm(Month) YYYY'))
            ) as q2,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY')
            ) as jul,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY')
            ) as aug,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY')
            ) as sep,
            (
             select (sum(countx)-sum(countn))  from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '07-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '08-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '09-01')::date, 'mm(Month) YYYY'))
            ) as q3,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon=to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY')
            ) as oct,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY')
            ) as nov,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat
             and k.country_id=country_id 
             and mon=to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY')
            ) as des,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and mon in (to_char(concat_ws('-',extract(year from now()), '10-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '11-01')::date, 'mm(Month) YYYY'),to_char(concat_ws('-',extract(year from now()), '12-01')::date, 'mm(Month) YYYY'))
            ) as q4,
            (
             select (sum(countx)-sum(countn)) from avg_pa11
             where job_cat = k.job_cat 
             and k.country_id=country_id
             and to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy')
            ) as total,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
              
             and mon=concat_ws('-',extract(year from now()), '01-01')::date
            ) as janc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and
              mon=concat_ws('-',extract(year from now()), '02-02')::date
            ) as febc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '03-03')::date
            ) as marc,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '01-01')::date,concat_ws('-',extract(year from now()), '02-02')::date,concat_ws('-',extract(year from now()), '03-03')::date)
            ) as q1c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '04-04')::date
            ) as aprc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '05-05')::date
            ) as mayc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '06-06')::date
            ) as junc,
            (
             select sum(count)  from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '04-04')::date,concat_ws('-',extract(year from now()), '05-05')::date,concat_ws('-',extract(year from now()), '06-06')::date)
            ) as q2c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '07-07')::date
            ) as julc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '08-08')::date
            ) as augc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '09-09')::date
            ) as sepc,
            (
             select sum(count)  from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '07-07')::date,concat_ws('-',extract(year from now()), '08-08')::date,concat_ws('-',extract(year from now()), '09-09')::date)
            ) as q3c,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon=concat_ws('-',extract(year from now()), '10-10')::date
            ) as octc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat
             and k.country_id=location_id 
             and mon=concat_ws('-',extract(year from now()), '11-11')::date
            ) as novc,
            (
             select count from tgt_asset_number
             where job_cat = k.job_cat
             and k.country_id=location_id 
             and mon=concat_ws('-',extract(year from now()), '12-12')::date
            ) as desc,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             and mon in (concat_ws('-',extract(year from now()), '10-10')::date,concat_ws('-',extract(year from now()), '11-11')::date,concat_ws('-',extract(year from now()), '12-12')::date)
            ) as q4c,
            (
             select sum(count) from tgt_asset_number
             where job_cat = k.job_cat 
             and k.country_id=location_id
             
            ) as totalc
            
            
            from avg_pa11 k  where to_char(mon::date,'yyyy')=to_char(concat_ws('-',extract(year from now()), '10-01')::date,'yyyy') ;
        """)

