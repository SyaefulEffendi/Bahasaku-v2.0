from marshmallow import Schema, fields, validate

class FeedbackSchema(Schema):

    id = fields.Int(dump_only=True)  # hanya untuk response
    user_id = fields.Int(required=True)
    message = fields.Str(required=True, validate=validate.Length(min=1))
    
    # Perbaikan: Hapus 'default='
    status = fields.Str(validate=validate.OneOf(['Baru', 'Ditinjau', 'Selesai'])) 
    
    created_at = fields.DateTime(dump_only=True)  # hanya untuk response

feedback_schema = FeedbackSchema()
feedbacks_schema = FeedbackSchema(many=True)