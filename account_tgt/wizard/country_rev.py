from openerp.osv import osv, fields

class employee_department(osv.osv):
    
    _name = 'location.rev'
    
    _description = 'Revenue Per Country'
    
    _columns = {
        'name':fields.char('Name', size=32),
        'tar_mo':fields.integer('Target Revenue'),
        'year':fields.integer('Year'),
        'mon':fields.selection([('jan', 'Jan'), ('feb', 'Feb'),('mar', 'Mar'), ('apr', 'Apr'),('may', 'May'), ('jun', 'Jun'),('jul', 'Jul'), ('aug', 'Aug'), ('sep', 'Sep'),('oct', 'Oct'), ('nov', 'Nov') ,('des', 'Dec')], 'Month'),
        'country_id':fields.many2one('res.country', 'Country'),
        
    }    