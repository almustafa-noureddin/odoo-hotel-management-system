# -*- coding: utf-8 -*-
from odoo import models, fields

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

    name=fields.Char(string="Type name",required=True, index=True)
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

