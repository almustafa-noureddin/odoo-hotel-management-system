from odoo import models,fields

class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'hotel room type'
    _order = 'name'

    name = fields.Char(string="Room Type",required=True, index=True)
    description = fields.Char(string="Room type description")
    capacity = fields.Integer(string="Capacity",default=1)
    default_price = fields.Monetary(string="Base price", currency_field='currency_id')

    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

class HotelRoomAmenity(models.Model):
    _name = 'hotel.room.amenity'
    _description = 'Room Amenity'
    _order = 'name'

    name = fields.Char(string="Amenity",required=True, index=True)
    description = fields.Text(string="Description")


class HotelRoom (models.Model):
    _name= "hotel.room"
    _description= "hotel room"
    _order = 'name'
    _check_company_auto = True  

    name =fields.Char(string="Room number or code",required=True, index=True)
    room_type_id= fields.Many2one('hotel.room.type', string="Room Type")
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Branch",
        required=True,
        index=True,
        default=lambda self: self.env.company,
        ondelete='restrict',
    )
    floor_number= fields.Integer(string="Floor Number")
    status = fields.Selection(
        string='Room Status',
        selection=[('available', 'Available'), 
            ('occupied', 'Occupied'), 
            ('dirty','Dirty'), 
            ('maintenance','Maintenance')]
    )
    price= fields.Monetary(string='Price', currency_field='currency_id')
    
    amenities_ids = fields.Many2many(
        string='Amenities',
        comodel_name='hotel.room.amenity',
        relation='hotel_room_amenity_rel',
        column1='room_id',
        column2='amenity_id',
    )

    currency_id = fields.Many2one(
        'res.currency',
        required=True,
        default=lambda self: self.env.company.currency_id.id,
    )

    
 