from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields



class hr_consolidated_report0(osv.osv):
    _name = 'hr.consolidated.report0'
    _description = "HR Vacation Report"
    _auto = False


    def suma(self, *args):
        i = 0.0
        for k in args:
            i += k
        return i
    _columns = {
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'country_id': fields.many2one('res.country', 'Country'),
        'tar_mon': fields.date('Corresponding Month'),
        'is_log': fields.boolean('Is Logging Engineer'),
        'rotation': fields.many2one('hr_tgt.rotation.method', 'Rotation Method'),
        'is_rotator': fields.boolean('Status'),
        'is_loc_engineer': fields.boolean('Is Local Engineer'),

        #these are values for the current month
        'land': fields.float('Land (Onshore) '),
        'sea': fields.float('Sea (Off shore) '),
        'base': fields.float('Base '),
        'dayoff': fields.float('Days Off '),
        'sick': fields.float('Sick days '),
        #'trav': fields.float('Travelled '),
        #'trav_al': fields.float('Travelled with Allowance '),
        'wend': fields.float('Weekend / Holiday'),
        #'ph_nw': fields.float('Public Holiday, didnt work '),
        #'vac': fields.float('Vacation Days'),
        'adjust': fields.float('Adjustment'),
        
        #these are for the regular employees
        'an_leaves': fields.float('Annual Leave'),
        'vac_balance': fields.float('Vacation balance'),
        'vac_taken': fields.float('Vacation days taken'),

    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'hr_months_help1')
        cr.execute("""
            CREATE OR REPLACE VIEW hr_months_help1 AS
            select
                date_part('month', ws.date) as tar_mon,
                date_part('year', ws.date) as tar_year
                from hr_payslip_working_sheet ws;
        """)

        tools.sql.drop_view_if_exists(cr, 'hr_months_help2')
        cr.execute("""
            CREATE OR REPLACE VIEW hr_months_help2 AS
            select distinct on(tar_year, tar_mon)
            	*
            	from hr_months_help1;
        """)

        tools.sql.drop_view_if_exists(cr, 'hr_consolidated_report0')
        cr.execute("""
            create or replace view hr_consolidated_report0 as
            select
            	e.id as employee_id,
                        e.resident_country as country_id,
                        ROW_NUMBER() OVER () AS id,
                        e.rotation_id as rotation,
                        e.is_rotator  as is_rotator,
                        e.is_loc_engineer as is_loc_engineer,
                        e.anual_leaves as an_leaves,

                        (SELECT CASE WHEN EXISTS (
                        SELECT *
                        FROM hr_payslip_working_sheet
                        WHERE employee_id = e.id
                        )
                        THEN CAST(1 AS BIT)
                        ELSE CAST(0 AS BIT) END) as is_log,

                        (concat_ws('-', hl.tar_year, hl.tar_mon,'01')::date) as tar_mon,

                        (select COUNT(*) from hr_payslip_working_sheet ws
                            where ws.employee_id = e.id and date_part('month', ws.date) = hl.tar_mon and date_part('year', ws.date) = hl.tar_year
                         and  state LIKE '%L%' ) As land,

                         (select COUNT(*) from hr_payslip_working_sheet ws
                            where ws.employee_id = e.id and date_part('month', ws.date) = hl.tar_mon and date_part('year', ws.date) = hl.tar_year
                         and  state LIKE '%S%' ) As sea,

                        (select COUNT(*) from hr_payslip_working_sheet ws
                            where ws.employee_id = e.id  and date_part('month', ws.date) = hl.tar_mon and date_part('year', ws.date) = hl.tar_year
                         and  state LIKE '%B%' ) As base,

                        (select COUNT(*) from hr_payslip_working_sheet ws
                            where ws.employee_id = e.id and date_part('month', ws.date) = hl.tar_mon and date_part('year', ws.date) = hl.tar_year
                         and  state LIKE '%O%' ) As dayoff,

                        (select COUNT(*) from hr_payslip_working_sheet ws
                            where ws.employee_id = e.id and date_part('month', ws.date) = hl.tar_mon and date_part('year', ws.date) = hl.tar_year
                         and  state LIKE '%SL%' ) As sick,

                         (select COUNT(*) from hr_payslip_working_sheet ws
                            where ws.employee_id = e.id and date_part('month', ws.date) = hl.tar_mon and date_part('year', ws.date) = hl.tar_year
                         and  state LIKE '%W%' ) As wend,

                        (select sum(adjust_value * adjust_sign) from hr_payslip_worksheet_adjustment wsa
                            where wsa.employee_id = e.id and date_part('month', wsa.date) = hl.tar_mon and date_part('year', wsa.date) = hl.tar_year
                        ) As adjust,

                                    (SELECT
                                        sum(h.number_of_days) as days from hr_holidays h
                                        join hr_holidays_status s on (s.id=h.holiday_status_id)
                                        where
                                        h.state='validate' and
                                        s.limit=False and
                                        h.employee_id=e.id and
                                        (
                                            (date_part('month', h.date_from) = hl.tar_mon and date_part('year', h.date_from) = hl.tar_year)
                                            or (date_part('month', h.write_date) = hl.tar_mon and date_part('year', h.write_date) = hl.tar_year)
                        		) and h.number_of_days >= 0
                                    ) as vac_balance,

                                    (SELECT
                                        sum(h.number_of_days) as days from hr_holidays h
                                        join hr_holidays_status s on (s.id=h.holiday_status_id)
                                        where
                                        h.state='validate' and
                                        s.limit=False and
                                        h.employee_id=e.id and
                                        (
                                            (date_part('month', h.date_from) = hl.tar_mon and date_part('year', h.date_from) = hl.tar_year)
                                            or (date_part('month', h.write_date) = hl.tar_mon and date_part('year', h.write_date) = hl.tar_year)
                                        ) and h.number_of_days < 0
                                    ) as vac_taken

                        from  hr_employee e, resource_resource r, hr_months_help2 hl
                        where e.resource_id = r.id and r.active = true
                        group by e.id, e.country_id, e.rotation_id,e.is_rotator, e.anual_leaves, hl.tar_year, hl.tar_mon
                        order by e.id
            """)
hr_consolidated_report0()

