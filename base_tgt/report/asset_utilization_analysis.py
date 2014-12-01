from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields


class rsa(osv.osv):
    _name = 'asset.utilization.analysis'
    _description = "Asset Utilization Analysis"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i



    _columns = {
        'asset_id': fields.many2one('account.asset.asset', 'Asset'),
        'jan': fields.char('Jan'),
        'feb': fields.char('Feb'),
        'mar': fields.char('Mar'),
        'apr': fields.char('Apr'),
        'may': fields.char('May'),
        'jun': fields.char('Jun'),
        'jul': fields.char('Jul'),
        'aug': fields.char('Aug'),
        'sep': fields.char('Sep'),
        'oct': fields.char('Oct'),
        'nov': fields.char('Nov'),
        'des': fields.char('Dec'),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'preparer3')
        cr.execute("""
            
CREATE OR REPLACE VIEW preparer3 AS
SELECT ROW_NUMBER() OVER () AS id, 
            k.employee_id as asset_id,
             count(k.sale_id) as counter, 
             SUM(s.amount_total) as total,

            to_char(

                            (select i.date_invoice from account_invoice i where i.id in 
                        (select si.invoice_id from sale_order_invoice_rel si
                         where si.order_id=k.sale_id) limit 1)
                            ,'mm(Month) yyyy') as mon

              FROM
            sale_asset_rel k left join sale_order s on s.id=k.sale_id

            where
            s.state in ('done','progress') and
             date_trunc('year', now()) = date_trunc('year',(select i.date_invoice from account_invoice i where i.id in 
                        (select si.invoice_id from sale_order_invoice_rel si
                         where si.order_id=k.sale_id) limit 1))

            group by 2, 5;

            """)
        tools.sql.drop_view_if_exists(cr, 'asset_utilization_analysis')
        cr.execute("""
            create or replace view asset_utilization_analysis as
            
            select 
            distinct on(k.asset_id)
            k.asset_id as asset_id,
            ROW_NUMBER() OVER() as id,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-01-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as jan,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-02-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as feb,
            coalesce(
            (
             select concat_ws(' / ', coalesce(counter,0),coalesce(total,0.0)) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-03-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as mar,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-04-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as apr,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-05-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as may,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-06-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as jun,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-07-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as jul,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-08-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as aug,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-09-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as sep,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-10-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as oct,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-11-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as nov,
            coalesce(
            (
             select concat_ws(' / ',coalesce(counter,0),coalesce(total,0.0)) from preparer3
             where asset_id = k.asset_id
             and mon=to_char(date '2014-12-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as des
            from preparer3 k;


            """)

rsa()


class rsae(osv.osv):
    _name = 'asset.utilization.analysis.empty'
    _description = "Sales Analysis Without Assets"
    _auto = False

    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i



    _columns = {
        'company_id': fields.many2one('res.company', 'TGT Entity'),
        'jan': fields.char('Jan'),
        'feb': fields.char('Feb'),
        'mar': fields.char('Mar'),
        'apr': fields.char('Apr'),
        'may': fields.char('May'),
        'jun': fields.char('Jun'),
        'jul': fields.char('Jul'),
        'aug': fields.char('Aug'),
        'sep': fields.char('Sep'),
        'oct': fields.char('Oct'),
        'nov': fields.char('Nov'),
        'des': fields.char('Dec'),
    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'preparer4')
        cr.execute("""
            CREATE OR REPLACE VIEW preparer4 AS

            SELECT ROW_NUMBER() OVER () AS id, 
            s.company_id,
             count(s.id) as counter, 
             SUM(s.amount_total) as total,

            to_char(

                            (select i.date_invoice from account_invoice i where i.id in 
                        (select si.invoice_id from sale_order_invoice_rel si
                         where si.order_id=s.id) limit 1)
                            ,'mm(Month) yyyy') as mon

              FROM
            sale_order s 

            where
            s.id not in (select sale_id from sale_asset_rel) and
            s.state in ('done','progress') and
             date_trunc('year', now()) = date_trunc('year',(select i.date_invoice from account_invoice i where i.id in 
                        (select si.invoice_id from sale_order_invoice_rel si
                         where si.order_id=s.id) limit 1))

            group by company_id, 5;

            """)
        tools.sql.drop_view_if_exists(cr, 'asset_utilization_analysis_empty')
        cr.execute("""
            create or replace view asset_utilization_analysis_empty as
            select 
            distinct on(k.company_id)
            k.company_id as company_id,
            ROW_NUMBER() OVER() as id,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-01-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as jan,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-02-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as feb,
            coalesce(
            (
             select concat_ws(' / ', coalesce(counter,0),coalesce(total,0.0)) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-03-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as mar,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-04-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as apr,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-05-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as may,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-06-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as jun,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-07-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as jul,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-08-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as aug,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-09-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as sep,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-10-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as oct,
            coalesce(
            (
             select concat_ws(' / ',counter,total) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-11-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as nov,
            coalesce(
            (
             select concat_ws(' / ',coalesce(counter,0),coalesce(total,0.0)) from preparer4
             where company_id = k.company_id
             and mon=to_char(date '2014-12-01', 'mm(Month) YYYY')
            ), '0 / 0.0') as des
            from preparer4 k;


            """)

rsae()