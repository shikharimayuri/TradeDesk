from extensions import db


from datetime import datetime





class Trade(db.Model):


    __tablename__ = "trades"





    id = db.Column(db.Integer, primary_key=True)





    user_id = db.Column(


        db.Integer,


        db.ForeignKey("users.id"),


        nullable=False


    )





    trade_date = db.Column(


        db.Date,


        nullable=False


    )





    trade_time = db.Column(


        db.Time,


        nullable=True


    )





    followed_plan = db.Column(


        db.Boolean,


        nullable=False


    )





    is_profit = db.Column(


        db.Boolean,


        nullable=False


    )





    amount = db.Column(


        db.Float(10,2),


        nullable=False


    )





    notes = db.Column(


        db.Text,


        nullable=True


    )





    created_at = db.Column(


        db.DateTime,


        default=datetime.utcnow
    )