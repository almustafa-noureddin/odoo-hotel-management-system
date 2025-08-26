from odoo import models, fields, api
from datetime import timedelta

class HotelEventAvailabilityWizard(models.TransientModel):
    _name = "hotel.event.availability.wizard"
    _description = "Search Available Event Halls"

    company_id = fields.Many2one(
        'res.company', string="Branch",
        default=lambda self: self.env.company, required=True)
    date_start = fields.Datetime(string="Event Start", required=True)
    duration_hours = fields.Float(string="Duration (hours)", required=True, default=4.0)
    date_end = fields.Datetime(string="Event End", compute="_compute_date_end", store=False)
    hall_type_id = fields.Many2one('hotel.event.hall.type', string="Hall Type")
    capacity_min = fields.Integer(string="Min Capacity", default=1)
    amenity_ids = fields.Many2many('hotel.event.amenity', string="Amenities")
    max_price_per_hour = fields.Monetary(string="Max Price / Hour", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', required=True,
                                  default=lambda self: self.env.company.currency_id.id)
    result_hall_ids = fields.Many2many('hotel.event.hall', string="Available Halls", compute="_compute_results")

    @api.depends('date_start', 'duration_hours')
    def _compute_date_end(self):
        for wiz in self:
            if wiz.date_start and wiz.duration_hours:
                wiz.date_end = wiz.date_start + timedelta(hours=wiz.duration_hours)
            else:
                wiz.date_end = False

    @api.depends('company_id','date_start','duration_hours','hall_type_id','capacity_min','amenity_ids','max_price_per_hour')
    def _compute_results(self):
        for wiz in self:
            wiz.result_hall_ids = [(6, 0, wiz._find_available_hall_ids())]

    def _candidate_hall_domain(self):
        self.ensure_one()
        domain = [('company_id', '=', self.company_id.id)]
        if self.hall_type_id:
            domain += [('hall_type_id', '=', self.hall_type_id.id)]
        if self.capacity_min:
            domain += [('capacity', '>=', self.capacity_min)]
        if self.max_price_per_hour:
            domain += ['|', ('price_per_hour', '!=', False), ('price_per_hour', '=', False)]
            domain += [('price_per_hour', '<=', self.max_price_per_hour)]
        if self.amenity_ids:
            for amenity in self.amenity_ids:
                domain += [('amenities_ids', 'in', amenity.id)]
        return domain

    def _overlap(self, start_a, end_a, start_b, end_b):
        # Overlap if a.start < b.end AND b.start < a.end
        return (start_a < end_b) and (start_b < end_a)

    def _find_available_hall_ids(self):
        self.ensure_one()
        if not (self.date_start and self.duration_hours):
            return []

        start = self.date_start
        end = self.date_start + timedelta(hours=self.duration_hours)

        # filter candidate halls by company + attributes
        halls = self.env['hotel.event.hall'].sudo().search(self._candidate_hall_domain())
        if not halls:
            return []

        # pull bookings on those halls that could overlap
        bookings = self.env['hotel.event.booking'].sudo().search([
            ('hall_id', 'in', halls.ids),
            ('status', '!=', 'cancelled'),
            ('event_date', '<', end),
        ])

        occupied = set()
        for b in bookings:
            b_end = (b.event_date or start) + timedelta(hours=b.duration_hours or 0.0)
            if b.event_date and self._overlap(start, end, b.event_date, b_end):
                occupied.add(b.hall_id.id)

        available_ids = [h.id for h in halls if h.id not in occupied]
        return available_ids

    def action_open_results(self):
        self.ensure_one()
        return {
            'name': 'Available Event Halls',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.event.hall',
            'view_mode': 'list,form',
            'target': 'current',
            'domain': [('id', 'in', self._find_available_hall_ids())],
            'context': {
                'default_company_id': self.company_id.id,
            }
        }

    def action_create_booking(self):
        self.ensure_one()
        hall_id = self.env.context.get('active_id')
        if not hall_id:
            ids = self._find_available_hall_ids()
            hall_id = ids and ids[0]
        if not hall_id:
            return False

        booking = self.env['hotel.event.booking'].create({
            'customer_id': self.env.context.get('default_customer_id') or False,
            'hall_id': hall_id,
            'event_date': self.date_start,
            'duration_hours': self.duration_hours,
            'status': 'draft',
            'currency_id': self.currency_id.id,
        })
        return {
            'name': 'Event Booking',
            'type': 'ir.actions.act_window',
            'res_model': 'hotel.event.booking',
            'view_mode': 'form',
            'res_id': booking.id,
            'target': 'current',
        }
