# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import timedelta

class HotelEventAmenity(models.Model):
    _name = 'hotel.event.amenity'
    _description = 'Event Hall Amenity'
    _order = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()

class HotelEventHallType(models.Model):
    _name="hotel.event.hall.type"
    _description="Event / Banquet Hall Type"
    _order="name"

    name=fields.Char(string="Hall Type",required=True, index=True)
    capacity = fields.Integer(string="Capacity")
    price_per_hour = fields.Monetary(string="Price Per Hour", currency_field='currency_id')
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    

class HotelEventHall(models.Model):
    _name = 'hotel.event.hall'
    _description = 'Event / Banquet Hall'
    _order = 'name'

    name = fields.Char(string="Hall Name or Number",required=True, index=True)
    branch_id = fields.Many2one(
        string="Branch",
        comodel_name='res.branch', 
        required=True, 
        ondelete='restrict'
        )
    
    hall_type_id = fields.Many2one(
        string='Hall Type',
        comodel_name='hotel.event.hall.type',
        required=True,
        ondelete='restrict'
    )
    
    capacity = fields.Integer(string="Capacity")
    price_per_hour = fields.Monetary(string="Price Per Hour", currency_field='currency_id')
    amenities_ids = fields.Many2many(
        string="Amenities",
        comodel_name='hotel.event.amenity',
        relation='hotel_event_hall_amenity_rel',
        column1='hall_id', 
        column2='amenity_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

class HotelEventPackage(models.Model):
    _name = 'hotel.event.package'
    _description = 'Event Package'
    _order = 'name'

    name = fields.Char(string="Package Name", required=True, index=True)
    description = fields.Text(string="Description")
    price = fields.Monetary(string="Price", currency_field='currency_id')
    services_ids = fields.Many2many(
        string="Included Services/Items",
        comodel_name='product.product',
        relation='hotel_event_package_service_rel', 
        column1='package_id', 
        column2='product_id',
    )
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

class HotelEventBooking(models.Model):
    _name = 'hotel.event.booking'
    _description = 'Event Booking'
    _order = 'event_date desc, id desc'

    name = fields.Char(string="Reference", copy=False, readonly=True, default="/")

    hall_id = fields.Many2one(
        string="Hall",
        comodel_name='hotel.event.hall', 
        required=True, 
        ondelete='restrict'
        )
    customer_id = fields.Many2one(
        string="Customer",
        comodel_name='res.partner', 
        required=True, 
        ondelete='restrict'
        )
    event_date = fields.Datetime(string='Event Date',required=True, index=True)
    duration_hours = fields.Float(string='Event Duration in Hours',required=True)

    package_id = fields.Many2one(
        string="Event Package",
        comodel_name='hotel.event.package', 
        ondelete='set null'
        )
    deposit_amount = fields.Monetary(string='Deposit Amount', currency_field='currency_id')
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id')

    status = fields.Selection(
        string='Status',
        selection=[('draft', 'Draft'),
         ('confirmed', 'Confirmed'),
         ('cancelled', 'Cancelled')],
        default='draft',
        required=True,
        index=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if rec.name in (False, "/"):
            rec.name = self.env['ir.sequence'].next_by_code('hotel.reservation') or '/'
        return rec


class HotelEventBooking(models.Model):
    _inherit = "hotel.event.booking"

    @api.constrains('hall_id', 'event_date', 'duration_hours')
    def _check_overlap(self):
        """Naive time overlap: [start, end) vs others on same hall."""
        for rec in self:
            if not (rec.hall_id and rec.event_date and rec.duration_hours):
                continue
            start = rec.event_date
            end = start + timedelta(hours=rec.duration_hours)

            # quick shortlist: anything that starts before our end on the same hall
            others = self.search([
                ('id', '!=', rec.id),
                ('hall_id', '=', rec.hall_id.id),
                ('event_date', '<', end),
            ])

            for o in others:
                o_end = (o.event_date or start) + timedelta(hours=o.duration_hours or 0)
                # overlap if o.start < end AND start < o.end
                if o.event_date and (o.event_date < end and start < o_end):
                    raise models.ValidationError("Hall is already booked for that time window.")
