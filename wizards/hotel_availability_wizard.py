from odoo import models, fields, api
from datetime import datetime

class HotelAvailabilityWizard(models.TransientModel):
    _name = "hotel.availability.wizard"
    _description = "Search Available Rooms"

    company_id = fields.Many2one(
        'res.company', string="Branch",
        default=lambda self: self.env.company, required=True)
    date_start = fields.Datetime(string="Check-in", required=True)
    date_end = fields.Datetime(string="Check-out", required=True)
    room_type_id = fields.Many2one('hotel.room.type', string="Room Type")
    capacity_min = fields.Integer(string="Min Capacity", default=1)
    amenity_ids = fields.Many2many('hotel.room.amenity', string="Amenities")
    max_price = fields.Monetary(string="Max Price", currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency', required=True,
        default=lambda self: self.env.company.currency_id.id)

    result_room_ids = fields.Many2many('hotel.room', string="Available Rooms", compute="_compute_results")

    @api.depends('company_id','date_start','date_end','room_type_id','capacity_min','amenity_ids','max_price')
    def _compute_results(self):
        for wiz in self:
            wiz.result_room_ids = [(6, 0, wiz._find_available_room_ids())]

    def _active_reservation_domain(self, date_start, date_end):
        # overlap: start < check_out AND end > check_in
        return [
            ('check_in', '<', date_end),
            ('check_out', '>', date_start),
            ('status', 'not in', ['cancelled']),
        ]

    def _find_available_room_ids(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id)]
        if self.room_type_id:
            domain += [('room_type_id', '=', self.room_type_id.id)]
        if self.capacity_min:
            domain += [('room_type_id.capacity', '>=', self.capacity_min)]
        if self.max_price:
            domain += ['|', ('price', '!=', False), ('price', '=', False)]
            domain += ['|', ('price', '<=', self.max_price), ('room_type_id.default_price', '<=', self.max_price)]
        if self.amenity_ids:
            for amenity in self.amenity_ids:
                domain += [('amenities_ids', 'in', amenity.id)]

        rooms = self.env['hotel.room'].sudo().search(domain)
        if not rooms:
            return []

        # exclude rooms with overlapping reservations
        res_domain = self._active_reservation_domain(self.date_start, self.date_end)
        res_by_room = self.env['hotel.reservation'].sudo().read_group(
            domain=res_domain + [('room_id', 'in', rooms.ids)],
            fields=['room_id'],
            groupby=['room_id']
        )
        occupied_room_ids = set([r['room_id'][0] for r in res_by_room if r.get('room_id')])
        available_room_ids = [r.id for r in rooms if r.id not in occupied_room_ids]
        return available_room_ids

    def action_open_results(self):
        self.ensure_one()
        return {
            'name': 'Available Rooms',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.room',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('id', 'in', self._find_available_room_ids())],
            'context': {
                'default_company_id': self.company_id.id,
            }
        }

    def action_create_reservation(self):
        self.ensure_one()
        # If exactly one room selected, create a draft reservation
        room_id = self.env.context.get('active_id')
        if not room_id:
            # Fallback: pick the first available room
            ids = self._find_available_room_ids()
            room_id = ids and ids[0]
        if not room_id:
            return False
        res = self.env['hotel.reservation'].create({
            'guest_id': self.env.context.get('default_guest_id') or False,
            'room_id': room_id,
            'check_in': self.date_start,
            'check_out': self.date_end,
            'status': 'draft',
            'booking_source': 'phone',
            'rate_type': 'standard',
            'currency_id': self.currency_id.id,
        })
        return {
            'name': 'Reservation',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.reservation',
            'view_mode': 'form',
            'res_id': res.id,
            'target': 'current',
        }
