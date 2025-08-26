from odoo import models, fields

class HousekeepingMaintenanceBridge(models.Model):
    _inherit = 'hotel.housekeeping.task'

    def action_report_maintenance(self):
        self.ensure_one()
        desc = self.description if hasattr(self, 'description') else ''
        values = {
            'name': 'Maintenance Report from Housekeeping',
            'room_id': self.room_id.id,
            'task_type': 'repair',
            'source': 'housekeeping',
            'status': 'pending',
            'housekeeping_task_id': self.id,
            'description': desc or f'Issue reported from housekeeping task {self.display_name}',
            'date_scheduled': fields.Datetime.now(),
        }
        mt = self.env['hotel.maintenance.task'].create(values)
        return {
            'name': 'Maintenance Task',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.maintenance.task',
            'view_mode': 'form',
            'res_id': mt.id,
            'target': 'current',
        }
