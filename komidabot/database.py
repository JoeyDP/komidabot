from komidabot import db



class Menu(db.Model):
    """ Database table for Komida menu. """
    __tablename__ = "menu"

    date = db.Column(db.DateTime, primary_key=True)
    campus = db.Column(db.String, primary_key=True)
    type = db.Column(db.String, primary_key=True)
    item = db.Column(db.String)
    price_student = db.Column(db.REAL)
    price_staff = db.Column(db.REAL)






db.create_all()
