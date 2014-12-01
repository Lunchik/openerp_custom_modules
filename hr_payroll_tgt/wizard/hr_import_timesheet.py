from openerp.osv import osv, fields
from openerp.tools.translate import _

import datetime
import csv, base64

try:
    import cStringIO as strio
except ImportError, e:
    import StringIO as strio


MONTHS_NAMES = [
    ('1', 'Jan'),
    ('2', 'Feb'),
    ('3', 'Mar'),
    ('4', 'Apr'),
    ('5', 'May'),
    ('6', 'Jun'),
    ('7', 'Jul'),
    ('8', 'Aug'),
    ('9', 'Sep'),
    ('10', 'Oct'),
    ('11', 'Nov'),
    ('12', 'Dec'),
]

SIGNS = [
    ('L', 'Land (Onshore)'),
    ('S', 'Sea (Off shore)'),
    ('B', 'Base'),
    ('O', 'Days Off'),
    ('SL', 'Sick leave'),
    ('T', 'Travel'),
    ('T+', 'Travel with Allowance'),
    ('W', 'Week end / Holiday'),
    ('PL', 'Public Holiday (Onshore)'),
    ('PS', 'Public Holiday (Offshore)'),
    ('V', 'Vacation'),
] 


HELP = '''
NOTE:
you must convert excel timesheet file into CSV file format 
before uploading. todo so, open excel sheet and go to file -> save as
then from the option select CSV and click save.
if you face any problem, please refer to helpdesk person.
'''



class hr_working_sheet(osv.osv_memory):
    ''' HR working Sheet'''

    _name = 'hr_tgt.working.sheet'
    _rec_name = 'date_from'

    _columns = {
        'date_from': fields.date('From Date'),
        'date_to': fields.date('To Date'),
        'employee_id': fields.many2one('hr.employee', 'Employee'),
        'with_allow': fields.boolean('With Allowance?'),
        'state': fields.selection([
            ('L', '[L] Land (Onshore)'),
            ('S', '[S] Sea (off shore)'),
            ('B', '[B] Base'),
            ('O', '[O] Days Off'),
            ('SL', '[SL] Sick leave'),
            ('T', '[T] Travel'),
            ('T+', '[T+] Travel with Allowance'),
            ('W', '[W] Week end / Holiday'),
            ('PL', '[PL] Public Holiday (Onshore)'),
            ('PS', '[PS] Public Holiday (Offshore)'),
            ('V', '[V] Vacation'),
        ], 'State'),
    }

    _defaults = {
        'with_allow': False,
    }

    def on_change_date_from(self, cr, uid, ids, date_from, context=None):

        today = datetime.datetime.now()
        date_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')

        if date_from > today:
            raise osv.except_osv('Future Dates not allowed', 'you cannot set future date.')

        c = today - date_from
        if c.days > 7:
            date_to = date_from + datetime.timedelta(days=7)
            if date_to.month != date_from.month:
                date_to = datetime.datetime(date_to.year, date_to.month, 1) - datetime.timedelta(days=1)

        else:
            date_to = today

        return {'value': {'date_to': date_to.strftime('%Y-%m-%d')}}

    def default_get(self, cr, uid, fields_list, context=None):
        employee_id = context.get('employee_id', False) 
        date_from = context.get('date_from', datetime.datetime.now().strftime('%Y-%m-%d')) 
        date_to = context.get('date_to', datetime.datetime.now().strftime('%Y-%m-%d'))

        return {
            'employee_id': employee_id,
            'date_from': date_from,
            'date_to': date_to,
        }


    def add_sheet(self, cr, uid, ids, context=None):
        
        if not ids:
            return False

        if isinstance(ids, list):
            ids = ids[0]

        today = datetime.datetime.now()

        log = self.browse(cr, uid, ids, context=context)

        date_from = datetime.datetime.strptime(log.date_from, '%Y-%m-%d')
        date_to = datetime.datetime.strptime(log.date_to, '%Y-%m-%d')

        delta = date_to - date_from

        sheet_obj = self.pool.get('hr.payslip.working_sheet')

        for i in range(delta.days + 1):
            date = date_from + datetime.timedelta(days=i)
            idds = sheet_obj.search(cr, uid, [('employee_id', '=', log.employee_id.id), ('date', '=', date.strftime('%Y-%m-%d'))])
            data = {
                'employee_id': log.employee_id.id,
                'name': '%s Attendance for %s' % (log.employee_id.name, date.strftime('%Y-%m-%d')),
                'state': log.state,
                'day': str(date.day),
                'month': str(date.month),
                'year': date.year,
                'with_allow': log.with_allow,
            }
            if idds:
                sheet_obj.write(cr, uid, idds, data, context=context)
            else:
                sheet_obj.create(cr, uid, data, context=context)

        next_date = date_to + datetime.timedelta(days=1)
        next_date_to = next_date + datetime.timedelta(days=7)
        if next_date_to > today:
            next_date_to = today
        if next_date > today:
            next_date = today

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr_tgt.working.sheet',
            'view_mode': 'form',
            'target': 'new',
            'name': 'Insert Work Load',
            'context': {'employee_id': log.employee_id.id, 'date_from': next_date.strftime('%Y-%m-%d'), 'date_to': next_date_to.strftime('%Y-%m-%d') },
        }



class hr_rotator_timesheet(osv.osv_memory):
    ''' importing timesheet wizard '''

    _name = 'hr_tgt.rotator.timesheet.import'

    _columns = {
        'year': fields.integer('Year'),
        'month': fields.selection(MONTHS_NAMES, 'Month',
            help="select the month of the timesheet"),
        'csv': fields.binary('Upload Timesheet', help=HELP),  
    }

    _defaults = {
        'year': datetime.datetime.now().year,
        'month': str(datetime.datetime.now().month),
    }

    def import_sheet(self, cr, uid, ids, context=None):
        if not ids:
            return ids[0]

        ids = ids[0]
        sheet = self.browse(cr, uid, ids, context=context)
        
        csv_file = strio.StringIO(base64.decodestring(sheet.csv))

        reader = csv.DictReader(csv_file)

        current_month = str(datetime.datetime.now().month)
        current_year = datetime.datetime.now().year
        current_day = datetime.datetime.now().day

        year = sheet.year

        if year < 2000 or year > current_year:
            raise osv.except_osv(_('Year Error !'), _('Please set a regular year e.g. "%s"' % current_year))


        if int(current_month) < int(sheet.month) and current_year == sheet.year:
            raise osv.except_osv(_('Month Error !'), _('you cannot upload a workload sheet for a future month %s-%s. please select a correct month.' % (sheet.month, sheet.year)))

        # now, we check if correct cvs format

        fieldnames = reader.fieldnames

        bad = False

        if fieldnames[0].strip().lower() != 'id':
            bad = True
        if fieldnames[1].strip().lower() != 'name':
            bad = True
        dayss = [str(i) for i in range(1, 32)]
        for fn in fieldnames[2:]:
            if not fn.strip() in dayss:
                bad = True
                break

        if bad:
            raise osv.except_osv(_('Bad Sheet format !'), HELP)

        # start parsing and loading data.
        # first record is always week days names
        # we will skip it

        emp_obj = self.pool.get('hr.employee')
        sheet_obj = self.pool.get('hr.payslip.working_sheet')
        ID, NAME = fieldnames[0], fieldnames[1]
        reader.next()

        notifications = []

        for record in reader:
            emp_code = record[ID].strip()
            emp_id = emp_obj.search(cr, uid, [('employee_id', '=', emp_code)], context=context)

            if not emp_id:
                notifications.append((emp_code, record[NAME].strip()))
                continue

            emp_id = emp_id[0]

            employee = emp_obj.browse(cr, uid, emp_id, context=context)

            # now, collect month attendance and insert
            # them into hr.payslip.worksheet
            # if the month is a current month
            # we will start importing from today and
            # go desc

            month = int(sheet.month)
            delta_day = datetime.timedelta(days=1)
            prev_date = datetime.datetime(sheet.year, month + 1, 1)
            start = prev_date - delta_day

            start_day = start.day

            if sheet.month == current_month and sheet.year == current_year:
                start_day = current_day


            for i in range(start_day, 0, -1):
                d = str(i)
                sign = record.get(d, False)
                # we will set this to continue for now
                # but it needs more revise logically.
                # because people could start on a field 
                # in 15 of the month.
                # or end in 13 of the month. so, ....
                if sign == False:
                    #notifications.append((emp_code, record[NAME].strip()))
                    #break
                    continue
                if not sign.strip():
                    continue
                sign = sign.upper()
                if not sign in dict(SIGNS).keys():
                    notifications.append((emp_code, record[NAME].strip(), 'bad signature "%s" in Day %s' % (sign, d)))
                    break
                name = '%s [%s-%s-%s]' % (employee.name, d, month, sheet.year)
                res = {
                    'employee_id': emp_id,
                    'name': name,
                    'day': d,
                    'month': sheet.month,
                    'year': sheet.year,
                    'state': sign,
                }

                sheet_obj.create(cr, uid, res, context=context)

        return False


hr_rotator_timesheet()
