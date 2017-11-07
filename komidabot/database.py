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


class Person(db.Model):
    """  """
    __tablename__ = "person"

    id = db.Column(db.String(128), primary_key=True)
    subscribed = db.Column(db.Boolean, default=True)

    @staticmethod
    def subscribe(sender_id):
        person = Person.query.filter_by(id=sender_id).one_or_none()
        if not person:
            person = Person()
            person.id = sender_id
            db.session.add(person)
        person.subscribed = True
        db.session.commit()

    @staticmethod
    def unsubscribe(sender_id):
        person = Person.query.filter_by(id=sender_id).one_or_none()
        if not person:
            person = Person()
            person.id = sender_id
            db.session.add(person)
        person.subscribed = False
        db.session.commit()

db.create_all()
