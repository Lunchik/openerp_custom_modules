from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


import xlwt
import tempfile
import base64

from openerp import tools
from openerp.osv import osv, fields

class hr_vacation_report(osv.osv):
    _name = 'hr.vacation.report'
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
        'land': fields.float('Land (Onshore) '),
        'sea': fields.float('Sea (Off shore) '),
        'base': fields.float('Base '),
        'dayoff': fields.float('Days Off '),
        'vacation': fields.float('Vacation Days'),
        'rotation': fields.many2one('hr_tgt.rotation.method', 'Rotation Method'),
        'is_rotator': fields.boolean('Status'),
        'an_leaves': fields.float('Annual Leave'),

    }

    def init(self, cr):
        tools.sql.drop_view_if_exists(cr, 'hr_vacation_report')
        cr.execute("""
            create or replace view hr_vacation_report as
            select e.id as employee_id,
            e.resident_country as country_id,
            ROW_NUMBER() OVER () AS id,
            e.rotation_id as rotation,
            e.is_rotator  as is_rotator,
            e.anual_leaves as an_leaves,

	        (select COUNT(*) from hr_payslip_working_sheet
                where employee_id = e.id  and EXTRACT(year FROM "date") = EXTRACT(year FROM NOW())
             and  state LIKE '%L%' ) As land,

             (select COUNT(*) from hr_payslip_working_sheet
                where employee_id = e.id  and EXTRACT(year FROM "date") = EXTRACT(year FROM NOW())
             and  state LIKE '%S%' ) As sea,

            (select COUNT(*) from hr_payslip_working_sheet
                where employee_id = e.id  and EXTRACT(year FROM "date") = EXTRACT(year FROM NOW())
             and  state LIKE '%B%' ) As base,


            (select COUNT(*) from hr_payslip_working_sheet
                where employee_id = e.id  and EXTRACT(year FROM "date") = EXTRACT(year FROM NOW())
             and  state LIKE '%O%' ) As dayoff,

            (select COUNT(*) from hr_payslip_working_sheet
                where employee_id = e.id  and EXTRACT(year FROM "date") = EXTRACT(year FROM NOW())
             and  state LIKE '%V%' ) As vacation

            from  hr_employee e, resource_resource r
            where e.resource_id = r.id and r.active = true
            group by e.id, e.country_id, e.rotation_id,e.is_rotator, e.anual_leaves
            """)
hr_vacation_report()



class hr_loading_month_report(osv.osv):
	_name = 'hr.loading.month.report'
	_description = "HR loading Report"
	_auto = False

	def suma(self, *args):
		i = 0.0
		for k in args:
			i += k
		return i
	_columns = {
		'employee_id': fields.many2one('hr.employee', 'Employee'),
		'land1': fields.float('Land (Onshore) 1'),
		'sea1': fields.float('Sea (Off shore) 1'),
		'base1': fields.float('Base 1'),
		'dayoff1': fields.float('Days Off 1'),
		'vacation1': fields.float('Vacation 1'),
		'land2': fields.float('Land (Onshore) 2'),
		'sea2': fields.float('Sea (Off shore) 2'),
		'base2': fields.float('Base 2' ),
		'dayoff2': fields.float('Days Off 2'),
		'vacation2': fields.float('Vacation 2'),
		'res_country' : fields.many2one('res.country', 'Country'),
	}
	def init(self, cr):
		tools.sql.drop_view_if_exists(cr, 'hr_loading_month_report')
		cr.execute("""
            create or replace view hr_loading_month_report as
            select hr.employee_id as employee_id,
            ROW_NUMBER() OVER () AS id,
            e.resident_country as res_country,
            (select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM (NOW() - INTERVAL '1 months' ) )
             and  state LIKE '%L%' ) As land1,
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM NOW())
             and  state LIKE '%L%' ) As land2,

			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM (NOW() - INTERVAL '1 months' ) )
             and  state LIKE '%S%' ) As sea1,
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM NOW())
             and  state LIKE '%S%' ) As sea2,
	
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM (NOW() - INTERVAL '1 months' ) )
             and  state LIKE '%B%' ) As base1,
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM NOW())
             and  state LIKE '%B%' ) As base2,

			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM (NOW() - INTERVAL '1 months' ) )
             and  state LIKE '%O%' ) As dayoff1,
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM NOW())
             and  state LIKE '%O%' ) As dayoff2,
			
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM (NOW() - INTERVAL '1 months' ) )
             and  state LIKE '%V%' ) As vacation1,
			(select COUNT(*) from hr_payslip_working_sheet 
            	where employee_id = hr.employee_id  and EXTRACT(month FROM "date") = EXTRACT(MONTH FROM NOW())
             and  state LIKE '%V%' ) As vacation2
			
			from hr_payslip_working_sheet hr, hr_employee e, resource_resource r
            where hr.employee_id = e.id and e.resource_id = r.id and r.active = true
      		group by 1, e.resident_country
			""")
hr_loading_month_report()


class hrlodingReport(object):
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
        self.num_style2 = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')
        self.num_style = xlwt.Style.easyxf('font: height 150, bold 1;', num_format_str='#,##0.00')
        self.num_style1 = xlwt.Style.easyxf('font: height 150, bold 0;', num_format_str='#,##0.00')
        self.header_style = xlwt.Style.easyxf('pattern: pattern solid, fore_colour blue; align: horiz center;font: height 200, bold 1,color white;')
        self.header_style1 = xlwt.Style.easyxf('pattern: pattern solid, fore_colour green; font: height 200, bold 1,color white;')

        sheet_name = ''
        if filter == 'hr_loading':
            sheet_name = 'HR Loading'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_hr_loading()
        if filter == 'hr_vacation':
            sheet_name = 'HR Vacation'
            self.sheet = self.book.add_sheet(sheet_name)
            self.generate_hr_vacation()
        self.book.save(self.temp)
        self.temp.seek(0)
        return self.temp
    
    def generate_hr_loading(self):
    	stack = []
    	self.sheet.write_merge(1, 1, 2, 7, ' Previous Month', self.header_style)
    	self.sheet.write_merge(1, 1, 8, 13, 'Current Month', self.header_style1)
        self.sheet.write(2, 1, 'Employee Name', self.header_style1)
      
        self.sheet.write(2, 2, 'Base', self.header_style1)
        self.sheet.write(2, 3, 'Offshore', self.header_style1)
        self.sheet.write(2, 4, 'Onshore', self.header_style1)
        self.sheet.write(2, 5, 'Off', self.header_style1)
        self.sheet.write(2, 6, 'Vacation Day', self.header_style1)
        self.sheet.write(2, 7, 'Vacation Balance', self.header_style)

        self.sheet.write(2, 8, 'Base', self.header_style1)
        self.sheet.write(2, 9, 'Offshore', self.header_style1)
        self.sheet.write(2, 10, 'Onshore', self.header_style1)
        self.sheet.write(2, 11, 'Off', self.header_style1)
        self.sheet.write(2, 12, 'Vacation Day', self.header_style1)
        self.sheet.write(2, 13, 'Vacation Balance', self.header_style)

        obj = self.pool.get('hr.loading.month.report')   
        ids = obj.search(self.cr, self.uid, [], context=self.context)

        for codn in obj.browse(self.cr, self.uid, ids, context=self.context):
        	stack.append(codn.employee_id.resident_country.name)
        
        countrys = set(stack)

        i=3

        for cuntry in countrys:

        	self.sheet.write(i, 1,cuntry,self.header_style)
        	base1 =sea1= land1=dayoff1=vacation1=0
        	base2 =sea2= land2=dayoff2=vacation2=0
        	tbase1 =tsea1= tland1=tdayoff1=tvacation1=0
        	tbase2 =tsea2= tland2=tdayoff2=tvacation2=0
        	i += 1
        	k = 0
        	for rec in obj.browse(self.cr, self.uid, ids, context=self.context):
        		cant= rec.employee_id.resident_country.name
        		vb1 = vb2 = 0 
        		if cant == cuntry:
        			all_dayson = rec.base1 + rec.sea1 + rec.land1 + rec.vacation1
        			all_daysoff = rec.dayoff1 
        			all_dayson2 = rec.base2 + rec.sea2 + rec.land2 + rec.dayoff2 + rec.vacation2
        			all_daysoff2 = rec.dayoff2 
        			remaining_days_off = remaining_days_off1 = 0.00
        			rm = rec.employee_id.rotation_id
        			rm_days_off = (rm and int(rm.days_off) or 0) 
        			rm_days_work = (rm and int(rm.days_work) or 0)
        			abc = 0.0
        			if rm_days_work:
        				abc = (1.0 /rm_days_work)
        			remaining_days_off = all_dayson * (rm_days_off * abc) - all_daysoff
        			remaining_days_off2 = all_dayson2 * (rm_days_off * abc) - all_daysoff2

        			k += 1
        			vb1 = rec.base1 + rec.sea1 + rec.land1 + rec.dayoff1 + rec.vacation1
        			vb2 = rec.base2 + rec.sea2 + rec.land2 + rec.dayoff2 + rec.vacation2
        			base1 = base1 + rec.base1 
        			base2 = base2 + rec.base2
        			sea2= sea2 + rec.sea2
        			sea1 = sea1 + rec.sea1
        			land1 = land1 + rec.land1
        			land2 = land2 + rec.land2
        			dayoff1 = dayoff1 + rec.dayoff1
        			dayoff2 = dayoff2 + rec.dayoff2
        			vacation1 = vacation1 + rec.vacation1
        			vacation2 = vacation2 + rec.vacation2
        			self.sheet.write(i, 1, rec.employee_id.name)
        			self.sheet.write(i, 2, rec.base1,self.num_style)
        			self.sheet.write(i, 3, rec.sea1, self.num_style)
        			self.sheet.write(i, 4, rec.land1, self.num_style)
        			self.sheet.write(i, 5, rec.dayoff1, self.num_style)
        			self.sheet.write(i, 6, rec.vacation1, self.num_style)
        			self.sheet.write(i, 7, remaining_days_off, self.num_style)

        			self.sheet.write(i, 8, rec.base2,self.num_style2)
        			self.sheet.write(i, 9, rec.sea2, self.num_style)
        			self.sheet.write(i, 10, rec.land2, self.num_style)
        			self.sheet.write(i, 11, rec.dayoff2, self.num_style)
        			self.sheet.write(i, 12, rec.vacation2, self.num_style)
        			self.sheet.write(i, 13, remaining_days_off2, self.num_style)
        			i += 1
        	if k == 0:
        		pass
        	else:
        		self.sheet.write(i, 1, 'country Total',self.header_style1)
        		self.sheet.write(i, 2, base1,self.num_style)
        		self.sheet.write(i, 3, sea1, self.num_style)
        		self.sheet.write(i, 4, land1, self.num_style)
        		self.sheet.write(i, 5, dayoff1, self.num_style)
        		self.sheet.write(i, 6, vacation1, self.num_style)

        		self.sheet.write(i, 8, base2,self.num_style2)
        		self.sheet.write(i, 9, sea2, self.num_style)
        		self.sheet.write(i, 10,land2, self.num_style)
        		self.sheet.write(i, 11,dayoff2, self.num_style)
        		self.sheet.write(i, 12,vacation2, self.num_style)
        		i +=1
        		self.sheet.write(i, 1, 'Headcount',self.header_style1)
        		self.sheet.write(i, 2, k,self.num_style2)
        		i +=1
        		tbase1 = base1/k
        		tbase2 = base2/k
        		tsea2= sea2/k
        		tsea1 = sea1/k
        		tland1 = land1/k
        		tland2 = land2 /k
        		tdayoff1 = dayoff1/k
        		tdayoff2 = dayoff2/k
        		tvacation1 = vacation1/k
        		tvacation2 = vacation2/k
        		self.sheet.write(i, 1, 'Per engineer',self.header_style1)
        		self.sheet.write(i, 2, tbase1,self.num_style)
        		self.sheet.write(i, 3, tsea1, self.num_style)
        		self.sheet.write(i, 4, tland1, self.num_style)
        		self.sheet.write(i, 5, tdayoff1, self.num_style)
        		self.sheet.write(i, 6, tvacation1, self.num_style)
        		self.sheet.write(i, 8, tbase2,self.num_style2)
        		self.sheet.write(i, 9, tsea2, self.num_style)
        		self.sheet.write(i, 10,tland2, self.num_style)
        		self.sheet.write(i, 11,tdayoff2, self.num_style)
        		self.sheet.write(i, 12,tvacation2, self.num_style)
        		i +=1
    
    def generate_hr_vacation(self):
        stack = []
        self.sheet.write(2, 1, 'Employee Name', self.header_style1)
      
        self.sheet.write(2, 2, 'state', self.header_style1)
        self.sheet.write(2, 3, 'Offshore', self.header_style1)
        self.sheet.write(2, 4, 'Vacation Days', self.header_style1)
        self.sheet.write(2, 5, 'Vacation Balance', self.header_style1)

        objv = self.pool.get('hr.vacation.report')
        ids = objv.search(self.cr, self.uid, [], context=self.context)



        i=3

        for rec in objv.browse(self.cr, self.uid, ids, context=self.context):
            vb1  = 0 

            all_dayson = rec.base + rec.sea + rec.land + rec.vacation
            all_daysoff = rec.dayoff 
            remaining_days_off = 0.00
            rm = rec.employee_id.rotation_id
            rm_days_off = (rm and int(rm.days_off) or 0) 
            rm_days_work = (rm and int(rm.days_work) or 0)
            abc = 0.0
            if rm_days_work:
                abc = (1.0 /rm_days_work)
            remaining_days_off = all_dayson * (rm_days_off * abc) - all_daysoff

      
            
            self.sheet.write(i, 1, rec.employee_id.name)
            self.sheet.write(i, 2, 'Rotator')
            self.sheet.write(i, 3, rec.employee_id.rotation_id.name)
            self.sheet.write(i, 4, rec.vacation, self.num_style)
            self.sheet.write(i, 5, remaining_days_off, self.num_style)

            i += 1

        objem = self.pool.get('hr.employee')   
        ids = objem.search(self.cr, self.uid, [('is_rotator','=',False)], context=self.context)
  
        for resident in objem.browse(self.cr, self.uid, ids, context=self.context):

            self.sheet.write(i, 1, resident.name)
            self.sheet.write(i, 2, 'Resident')
            self.sheet.write(i, 3, '-')
            self.sheet.write(i, 4, '-')
            self.sheet.write(i, 5, resident.anual_leaves , self.num_style)

            i += 1


