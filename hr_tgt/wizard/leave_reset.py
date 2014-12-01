from openerp.osv import osv, fields
from openerp.tools.translate import _

import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


C_YEAR = datetime.now().year

class reset_leave_registerar(osv.osv):
    _name = 'hr.leave.registrar'

    _columns = {
        'employee_id': fields.many2one('hr.employee', domain=[('is_rotator', '=', False)]),
        'year': fields.integer('Year', readonly=True),
        'days_registered': fields.integer('Registered Num Of days', readonly=True),
        'date': fields.datetime('Date'),
    }

    _defaults = {
        'year': lambda self, cr, uid, context: C_YEAR,
        'date': lambda self, cr, uid, context: datetime.now(),
    }

class reset_leave(osv.osv_memory):

    _name = 'hr.leave.yearly.reset'

    _columns = {
        'year': fields.integer('Year', readonly=True),
    }

    _defaults = {
        'year': lambda self, cr, uid, context: C_YEAR,
    }

    def reset_leave(self, cr, uid, ids, context=None):
        emp_obj = self.pool.get('hr.employee')
        reg_obj = self.pool.get('hr.leave.registrar')
        reg_ids = reg_obj.search(cr, uid, [('year', '=', C_YEAR)])
        #if reg_ids:
        #    raise osv.except_osv('Already Generated!', 'You Already Generate Leaves This Year')
        emp_ids = emp_obj.search(cr, uid, [('is_rotator', '=', False)], context=context)
        for emp in emp_obj.browse(cr, uid, emp_ids, context=context):
            regl = emp.anual_leaves
            rl = emp.remaining_leaves
            if rl + regl > regl * 2:
                regl = (regl * 2) - rl
            emp_obj.write(cr, uid, [emp.id], {'remaining_leaves': regl + rl}, context=context)
            data = {
                'employee_id': emp.id,
                'days_registered': regl,
            }
            reg_obj.create(cr, uid, data, context=context)

        return False


