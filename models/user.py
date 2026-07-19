from flask_login import UserMixin


from extensions import db





class User(UserMixin, db.Model):


    __tablename__="users"


    id=db.Column(db.Integer,primary_key=True)


    username=db.Column(db.String(100),nullable=False)


    email=db.Column(db.String(255),unique=True,nullable=False)


    password=db.Column(db.String(255),nullable=False)


    theme=db.Column(db.String(10),default="dark")





    trades = db.relationship(


        "Trade",


        backref="user",


        lazy=True,


        cascade="all,delete-orphan"
    )