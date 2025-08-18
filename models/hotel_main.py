from odoo import models,fields

class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'hotel room type'

    name = fields.Char(string="Room type")
    description = fields.Char(string="Description")
    capacity = fields.Char(string="Capacity")


class HotelRoom (models.Model):
    _name= "hotel.room"
    _description= "hotel room"

    name =fields.Char(String="Room No.")
    room_type_id= fields.Many2one('hotel.room.type', string="Room Type")
    branch_id = fields.Many2one(
        string='Branch',
        comodel_name='res.branch',
        ondelete='restrict',
    )
    floor_number= fields.Integer(string="Floor Number")
    status = fields.Selection(
        string='Room Status',
        selection=[('available', 'Available'), ('occupied', 'Occupied'), ('dirty','Dirty'), ('maintenance','Maintenance')]
    )
    price= fields.monetary(string='Price')
    
    amenities_ids = fields.Many2many(
        string='SAmenities',
        comodel_name='model.name',
        relation='model.name_this_model_rel',
        column1='model.name_id',
        column2='this_model_id',
    )
    
    
class HotelBooking (models.model):
    _name="hotel.booking"
    _description="Hotel Booking"

    
    guest_id = fields.Many2one(
        string='Guest Id',
        comodel_name='res.partner',
        ondelete='restrict',
    )
    
    room_id = fields.Many2one(
        string='Room Id',
        comodel_name='hotel.room',
        ondelete='restrict',
    )

    
    check_in_date = fields.Date(
        string='Check In Date',
        default=fields.Date.context_today,
    )
    

    
    check_out_date = fields.Date(
        string='Check Out Date',
        default=fields.Date.context_today,
    )
    
    
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('confirmed', 'Confirmed'),('checked_in','Checked In'),('done','Done'),('cancelled','Cancelled')]
    )
    
    
 