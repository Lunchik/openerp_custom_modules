'''
Created on Sep 23, 2013

@author: vision valley 
'''
from openerp.osv import fields, osv
#import openerp
import openerp.exceptions
import datetime
import time

#from datetime import datetime, timedelta
#from dateutil.relativedelta import relativedelta
#from openerp import pooler
#from openerp.tools.translate import _
#from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP, float_compare
#import openerp.addons.decimal_precision as dp
from openerp import netsvc
class multiple_analytic_view_template(osv.osv):
        _name = 'multiple.analytic.view.template'
        _description = 'Create Multiple Analytical Views'
        _columns ={                
                 'name':fields.char('Template Name',size=32, required=True),
                 #'description':fields.char('Description',size=64),
                 'description': fields.text('Description'),
                 'view_detailes':fields.one2many('multiple.analytic.view.template.details','template_id','View')
                   }
        
        _sql_constraints = [

            ('template_name', 'UNIQUE (name)', 'Name of the Template must be unique !'),
        ]
     
        

        def apply_template2(self, cr, uid,ids,data, context=None):
            if not len(ids):
                return False
            cr.execute('select id from multiple_analytic_view_template_details where template_id = %s ', (ids[0],))
            template_line_ids = map(lambda x: x[0], cr.fetchall())
            for template_line_id in template_line_ids:
                list_template_line_id=[]
                list_template_line_id+=[template_line_id]
                strsql_statement = "select account_analytic_id, parent_account_analytic_id from multiple_analytic_view_template_details where id= "
                strsql_statement = strsql_statement + str(template_line_id)
                #cr.execute('select account_analytic_id, parent_account_analytic_id from multiple_analytic_view_template_details where id = %s ', (list_template_line_id[0template_line_account_analytic_id_and_parentid = cr.fetchone()
                cr.execute(str(strsql_statement))             
                template_line_account_analytic_id_and_parentid = cr.fetchone()                                                                                                                                                              
                #account_analytic_id = template_line_account_analytic_id_and_parentid['account_analytic_id']
                #list_account_analytic_id=[account_analytic_id]
                #parent_account_analytic_id = template_line_account_analytic_id_and_parentid['parent_account_analytic_id']
                #list_parent_account_analytic_id=[parent_account_analytic_id]
                if template_line_account_analytic_id_and_parentid[1] != None:
                    strsql_update_statement = "update account_analytic_account  set parent_id= "
                    parent_account_analytic_id = str(template_line_account_analytic_id_and_parentid[1])
                    strsql_update_statement = strsql_update_statement + parent_account_analytic_id
                    strsql_update_statement = strsql_update_statement + " where id= "
                    account_analytic_id = str(template_line_account_analytic_id_and_parentid[0])
                    strsql_update_statement = strsql_update_statement + account_analytic_id
                    cr.execute(str(strsql_update_statement))     
                    #cr.execute('update account_analytic_account  set parent_id=%s where id=%s',(template_line_account_analytic_id_and_parentid['parent_account_analytic_id'],template_line_account_analytic_id_and_parentid['account_analytic_id']))
            return True
         
        def apply_template3(self, cr, uid,ids,data, context=None):
                if not len(ids):
                    return False
           
                #msgalert = {'title':'Warning','message':'Account Can Not Be A Parent Of Its Self !'}
                #return {'warning':msgalert}
                cr.execute('select id, account_analytic_id, parent_account_analytic_id from multiple_analytic_view_template_details where template_id = %s ', (ids[0],))
                template_lines = cr.fetchall()
                #try:
                for template_line in template_lines:                  
                       
                            if template_line[2] != None:
                                if  int(template_line[1]) != int(template_line[2]):
                                    strsql_update_statement = "update account_analytic_account  set parent_id= "
                                    parent_account_analytic_id = str(template_line[2])
                                    #parent_account_analytic_id = str(template_line['parent_account_analytic_id'])
                                    strsql_update_statement = strsql_update_statement + parent_account_analytic_id
                                else:
                                    raise openerp.exceptions.Warning('Error: Account Can Not Be A parent Of Itself !')
                            else: # template_line[2] = None:
                                strsql_update_statement = "update account_analytic_account  set parent_id=NUll "
                                    
                            strsql_update_statement = strsql_update_statement + " where id= "
                            account_analytic_id = str(template_line[1])
                            #account_analytic_id = str(template_line['account_analytic_id'])
                            strsql_update_statement = strsql_update_statement + account_analytic_id
                            cr.execute(str(strsql_update_statement))
                            
               # except TypeError, e:
               #     print e.message
               #     return False
                            
                return True

            
               
class multiple_analytic_template_details(osv.osv):
    _name = 'multiple.analytic.view.template.details'
    _description = 'create analytic accounts '
    _columns ={    
                 'name':fields.char('Description',size=64),
                 'template_id':fields.many2one('multiple.analytic.view.template','template name'),
                 'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account', required=True),
                 'parent_account_analytic_id':  fields.many2one('account.analytic.account', 'Parent Analytic Account'),
                   } 


    _sql_constraints = [      
        ('trmplate_line', 'unique(template_id, account_analytic_id, parent_account_analytic_id)', 'The Combination Of Template, Account, Parent account Must Be Unique!'),
  
    ]

                       
		
		
class self_relation(osv.osv):
    _name = 'self.relation'
    _description = 'self relation'    
 
# def create(self, cr, uid, vals, context=None):                		
#		super(self_relation, self).create(cr, uid, vals, context=context)				
#		_update(self, cr, uid, vals)
#		return True

#    def _update(self, cr, uid, vals, context=None):                		
#		cr.execute('UPDATE self_relation SET parent_real_id = B.id from self_relation B join self_relation A on B.account_analytic_id = A.parent_account_analytic_id')
#		return True
				
    def _child_compute(self, cr, uid, ids, name, arg, context=None):
        result = {}
        if context is None:
            context = {}

        for account in self.browse(cr, uid, ids, context=context):            
            result[account.id] = map(lambda x: x.id, [child for child in account.child_ids if child.state != 'template'])
        return result    
    _columns ={  				 				 
                 'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),				 				 
                 'parent_account_analytic_id':  fields.many2one('account.analytic.account', 'Parent Analytic Account'),
				 'name' : fields.related('parent_account_analytic_id','name',type='char' , string='Account Name'),				 				 
				 'parent_real_id':fields.integer('Real Parent ID', help="Real Parent ID"),
                 'child_ids': fields.one2many('self.relation', 'parent_real_id', 'Child Accounts'),
                 'child_complete_ids': fields.function(_child_compute, relation='self.relation', string="Account Hierarchy", type='many2many'),
                 'state': fields.selection([('template', 'Template'),('draft','New'),('open','In Progress'),('pending','To Renew'),\
                                            ('close','Closed'),('cancelled', 'Cancelled')], 'Status', track_visibility='onchange'),				                                                 
                 }   
				 
    def init(self, cr):        
        cr.execute("""
    CREATE OR REPLACE FUNCTION insert_real_ids() RETURNS TRIGGER AS $self_relation$
    BEGIN
        NEW.parent_real_id := (select b.id from self_relation B where b.account_analytic_id=NEW.parent_account_analytic_id order by id  limit 1) ;        
        RETURN NEW;
    END;
$self_relation$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS self_relation_insert ON self_relation; 

CREATE TRIGGER self_relation_insert BEFORE INSERT OR UPDATE ON self_relation
    FOR EACH ROW EXECUTE PROCEDURE insert_real_ids();
	""")
	
		
	


class account_analytic_line(osv.osv):
        #_name = 'account.analytic.line2'
        _inherit = "account.analytic.line"
        _description = ''
    
        _columns ={                   
                 #'map_to':  fields.many2one('account.analytic.account', 'Map To Account'),              
                   }

        #def create(self, cr, uid, data, context=None):
        #result = super(bank, self).create(cr, uid, data, context=context)
        #self.post_write(cr, uid, [result], context=context)
        #    return result


        def createtmp2(self, cr, uid, data, context=None):           
           
            

                # get parent analytic account Id
                parent_analytic_account_id = 1 #data['account_id']    #int(analytic_account_line_object.account_id)
                if parent_analytic_account_id != None:
                    refrence_analytic_account_ids = self.pool.get('account.analytic.account').search(cr, uid, [('map_to', '=', parent_analytic_account_id)])
                    if len(refrence_analytic_account_ids) > 0:
                        # for the parent analytic account get all refrence analytic accounts that maped to this analytic accounts (mean has map_to = account.analytic.account.id
                        # for each refrence analytic accounts in the list
                        for refrence_analytic_account_object in self.pool.get('account.analytic.account').browse(cr, uid, refrence_analytic_account_ids, context=context):            
                            # create analytic line with the same data of current analytic line except the parent id
                            #analytic_line_id = self.create(cr, uid, data, context=context)
                            analytic_line_id = 1

                        analytic_line_id_s = super(account_analytic_line, self).create(cr, uid, data, context=context)
                        #timeline_id = obj_timesheet.create(cr, uid, vals=vals_line, context=context)
                        #super(project_work,self).create(cr, uid, vals, *args, **kwargs)


                return True


        

        
        def createTmp(self, cr, uid, ids, vals, context=None):                
            #super(account_analytic_line, self).create(cr, uid, ids[0], context)
            
            for analytic_account_line_object in self.browse(cr, uid, ids, context=context):         
                # get parent analytic account Id
                parent_analytic_account_id = int(analytic_account_line_object.account_id)
                if parent_analytic_account_id != None:
                    refrence_analytic_account_ids = self.pool.get('account.analytic.account').search(cr, uid, [('map_to', '=', parent_analytic_account_id)])
                    if len(refrence_analytic_account_ids) > 0:
                        # for the parent analytic account get all refrence analytic accounts that maped to this analytic accounts (mean has map_to = account.analytic.account.id
                        # for each refrence analytic accounts in the list
                        for refrence_analytic_account_object in self.pool.get('account.analytic.account').browse(cr, uid, refrence_analytic_account_ids, context=context):            
                            # create analytic line with the same data of current analytic line except the parent id
                            analytic_line_id = self.create(cr, uid, {
                                                            'name': analytic_account_line_object.name,                                                            
                                                            'date': analytic_account_line_object.date,
                                                            #set the parent id = the current refrence analytic accounts id
                                                            'account_id':refrence_analytic_account_object.id, # 1, # refrence_analytic_account_object.id,
                                                            'unit_amount': analytic_account_line_object.unit_amount,
                                                            'product_id': analytic_account_line_object.product_id,
                                                            'product_uom_id': analytic_account_line_object.product_uom_id,
                                                            'amount': analytic_account_line_object.amount, # 0.0, # amt,
                                                            'general_account_id': analytic_account_line_object.account_id.id,
                                                            'journal_id':  analytic_account_line_object.journal_id.id,
                                                            'ref': analytic_account_line_object.ref,
                                                            #'move_id': analytic_account_line_object.id,
                                                            'user_id': uid                                                                                        
                                                            })

                        #super(account_analytic_line, self).create(cr, uid, ids, context)
                        #timeline_id = obj_timesheet.create(cr, uid, vals=vals_line, context=context)
                        #super(project_work,self).create(cr, uid, vals, *args, **kwargs)

                return True


        def create2(self, cr, uid, ids, context=None):          
            
            for analytic_account_line_object in self.browse(cr, uid, ids, context=context):
                vals_line = {}        
                vals_line['name'] = analytic_account_line_object.name
                vals_line['date'] = analytic_account_line_object.date
                vals_line['account_id'] = 1 # analytic_account_line_object.account_id
                vals_line['unit_amount'] = analytic_account_line_object.unit_amount
                vals_line['product_id'] = analytic_account_line_object.product_id
                vals_line['product_uom_id'] = analytic_account_line_object.product_uom_id
                vals_line['amount'] = analytic_account_line_object.amount
                vals_line['general_account_id'] = analytic_account_line_object.account_id.id
                vals_line['journal_id'] = analytic_account_line_object.journal_id.id
                vals_line['ref'] = analytic_account_line_object.ref
                vals_line['user_id'] = uid 
                # get parent analytic account Id
                parent_analytic_account_id = int(analytic_account_line_object.account_id)
                if parent_analytic_account_id != None:
                    refrence_analytic_account_ids = self.pool.get('account.analytic.account').search(cr, uid, [('map_to', '=', parent_analytic_account_id)])
                    if len(refrence_analytic_account_ids) > 0:
                        # for the parent analytic account get all refrence analytic accounts that maped to this analytic accounts (mean has map_to = account.analytic.account.id
                        # for each refrence analytic accounts in the list
                        for refrence_analytic_account_object in self.pool.get('account.analytic.account').browse(cr, uid, refrence_analytic_account_ids, context=context):            
                            # create analytic line with the same data of current analytic line except the parent id
                            analytic_line_id = super(account_analytic_line, self).create(cr, uid, {
                                                            'name': analytic_account_line_object.name,                                                            
                                                            'date': analytic_account_line_object.date,
                                                            #set the parent id = the current refrence analytic accounts id
                                                            'account_id':refrence_analytic_account_object.id, # 1, # refrence_analytic_account_object.id,
                                                            'unit_amount': analytic_account_line_object.unit_amount,
                                                            'product_id': analytic_account_line_object.product_id,
                                                            'product_uom_id': analytic_account_line_object.product_uom_id,
                                                            'amount': analytic_account_line_object.amount, # 0.0, # amt,
                                                            'general_account_id': analytic_account_line_object.account_id.id,
                                                            'journal_id':  analytic_account_line_object.journal_id.id,
                                                            'ref': analytic_account_line_object.ref,
                                                            #'move_id': analytic_account_line_object.id,
                                                            'user_id': uid                                                                                        
                                                            })

                        super(account_analytic_line, self).create(cr, uid, vals_line, context=context)
                        #timeline_id = obj_timesheet.create(cr, uid, vals=vals_line, context=context)
                        #super(project_work,self).create(cr, uid, vals, *args, **kwargs)


                return True

        def create(self, cr, uid, data, context=None):
            create_analytic_account_id = super(account_analytic_line, self).create(cr, uid, data, context=context)            
            #strsql_select_statement = "select  amount, name,date, account_id, general_account_id, journal_id from account_analytic_line where id = "
            strsql_select_statement = "select  create_uid, create_date, write_date, write_uid, amount_currency, ref from account_analytic_line where id = "
            strsql_select_statement = strsql_select_statement + str(create_analytic_account_id)            
            cr.execute(strsql_select_statement)
            orignal_inserted_analytic_line_data = cr.fetchone()
            strsql_select_all_refrences_accounts_statement = "select id  from account_analytic_account where analytic_account_ref_id = "
            if data['account_id'] !=None:
                #strsql_select_all_refrences_accounts_statement = strsql_select_all_refrences_accounts_statement + str(orignal_inserted_analytic_line_data[3])
                strsql_select_all_refrences_accounts_statement = strsql_select_all_refrences_accounts_statement + str(data['account_id'])
                cr.execute(strsql_select_all_refrences_accounts_statement)
                all_refrences_analytic_accounts_ids = cr.fetchall()
                #all_refrences_analytic_accounts_ids = map(lambda x: x[0], cr.fetchall())               
                if len(all_refrences_analytic_accounts_ids) > 0:
                    
                    for row_current_refrence_analytic_account_id in all_refrences_analytic_accounts_ids:                                                          
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc = None 
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc = " insert into account_analytic_line (amount, name, date, account_id, general_account_id, move_id, "
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "create_uid, create_date, write_date, write_uid, amount_currency, ref, user_id, unit_amount, journal_id) "
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += " values ( "
                       
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "'" + str(data['amount']) + "'"  + " , "
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "'" + str(data['name']) + "'"  + " , "
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "'" + str(data['date']) + "'" + " , "
                       ################# here set the row_current_refrence_analytic_account_id as aprent for the analytic line that will be inserted
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "'" + str(row_current_refrence_analytic_account_id[0]) + "'" + " , "
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "'" + str(data['general_account_id']) + "'" + " , "


                       if data['move_id']!= None: # move_id
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  str(data['move_id']) + " , "
                       else:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "Null" + " , "
                       
                       ################    create_uid ####################                  
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + str(orignal_inserted_analytic_line_data[0]) + "'" + " , "
                       ################    create_date ####################
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + str(orignal_inserted_analytic_line_data[1]) + "'" + " , "
                       ################    write_date ####################
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + str(orignal_inserted_analytic_line_data[2]) + "'" + " , "
                       ################    write_uid ####################
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + str(orignal_inserted_analytic_line_data[3]) + "'" + " , "
                       ################    amount_currency ############### 
                       if orignal_inserted_analytic_line_data[4] != None:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + str(orignal_inserted_analytic_line_data[4]) + "'" + " , "
                       else:                               
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + "0.00" + "'" + " , "
                       ################    ref  ####################
                       if orignal_inserted_analytic_line_data[5] != None:    
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  "'" + str(orignal_inserted_analytic_line_data[5]) + "'" + " , "
                       else:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "Null" + " , "
                           
                       if data['user_id'] != None:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  str(data['user_id']) + " , "
                       else:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "Null" + " , "

                       if data['unit_amount'] != None:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  str(data['unit_amount']) + " , "
                       else:
                           str_sql_insert_copy_of_analytic_line_for_current_ref_acc += "Null" + " , "
                           
                       str_sql_insert_copy_of_analytic_line_for_current_ref_acc +=  str(data['journal_id']) + " ) "
                       cr.execute(str_sql_insert_copy_of_analytic_line_for_current_ref_acc)

            return create_analytic_account_id
 
class account_analytic_account(osv.osv):
        #_name = ''
        _inherit = "account.analytic.account"
        _description = 'to add a method that create a copy of all analytic line of the refrenced analytic account'
        

        
        def create(self, cr, uid, data, context=None):
            created_analytic_account_id = super(account_analytic_account, self).create(cr, uid, data, context=context)
            if data.get('analytic_account_ref_id', None): 
                #strsql_select_statement = "select  amount, name,date, account_id, general_account_id, journal_id from account_analytic_line where id = "
                str_sql_select_all_old_analytic_lines =  "select amount, name, date, account_id, general_account_id, move_id, "
                str_sql_select_all_old_analytic_lines += "create_uid, create_date, write_date, write_uid, amount_currency, "
                str_sql_select_all_old_analytic_lines += "ref, user_id, unit_amount, journal_id "
                str_sql_select_all_old_analytic_lines += "from account_analytic_line where account_id = "
                str_sql_select_all_old_analytic_lines += str(data['analytic_account_ref_id'])

                
                cr.execute(str_sql_select_all_old_analytic_lines)
                all_old_analytic_lines = cr.fetchall()          
                if len(all_old_analytic_lines) > 0:                    
                    for row_current_analytic_line in all_old_analytic_lines:                                                          
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc = None 
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc = " insert into account_analytic_line (amount, name, date, account_id, general_account_id, move_id, "
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "create_uid, create_date, write_date, write_uid, amount_currency, ref, user_id, unit_amount, journal_id) "
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc += " values ( "                       
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "'" + str(row_current_analytic_line[0]) + "'" + " , "                     
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "'" + str(row_current_analytic_line[1]) + "'" + " , "                     
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "'" + str(row_current_analytic_line[2]) + "'" + " , "
                       #################### here set the created analytic account id as a parent account id ########################
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "'" + str(created_analytic_account_id) + "'" + " , "                     
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[4]) + "'" + " , "

                       if row_current_analytic_line[5]!= None: # move_id
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[5]) + "'" + " , "
                       else:                               
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "Null" + " , "                           

                       #str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[6]) + "'" + " , "
                       if row_current_analytic_line[6]!= None: # 
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[6]) + "'" + " , "
                       else:                               
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "Null" + " , "
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[7]) + "'" + " , "
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[8]) + "'" + " , "
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[9]) + "'" + " , "

                       if row_current_analytic_line[10] != None: # amount_currency
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[10]) + "'" + " , "
                       else:                               
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + "0.00" + "'" + " , "                           
                           
                       if row_current_analytic_line[11]!= None: # ref    
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[11]) + "'" + " , "
                       else:                               
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "Null" + " , "
                           
                       if row_current_analytic_line[12]!= None: # user_id   
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[12]) + "'" + " , "
                       else: 
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "Null" + " , "
                           
                       if row_current_analytic_line[13]!= None: # unit_amount
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[13]) + "'" + " , "
                       else: 
                           str_sql_insert_copy_of_current_analytic_line_for_ref_acc += "0.00" + " , "
                      
                       str_sql_insert_copy_of_current_analytic_line_for_ref_acc +=  "'" + str(row_current_analytic_line[14]) + "'" + " ) "
                       
                       #raise osv.except_osv(_('debug!'),_(str_sql_insert_copy_of_current_analytic_line_for_ref_acc))    

                       cr.execute(str_sql_insert_copy_of_current_analytic_line_for_ref_acc)
            return created_analytic_account_id

        _columns ={                
                  'analytic_account_ref_id': fields.many2one('account.analytic.account', 'Refrence Analytic Account', select=2),				 
		  'use_Mapping': fields.boolean('Mapping',help="If checked, "),
                  }        

                           
 
