from osv import osv, fields

class res_users(osv.osv):
    _inherit = 'res.users'

    def get_regional_group_id(self, cr, uid, context=None):
        ir_mdata = self.pool.get('ir.model.data')
        gid = ir_mdata.get_object(cr, uid, 'base', 'group_regional_user').id
        return gid