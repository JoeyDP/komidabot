import datetime
from komidabot import db

CAMPUSSES = ['cmi', 'cde', 'cst']
DEFAULT_CAMPUS = CAMPUSSES[0]

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

    default_mo = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_tu = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_we = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_th = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_fr = db.Column(db.String(5), default=DEFAULT_CAMPUS)

    time_joined = db.Column(db.DateTime, default=datetime.datetime.now)
    time_updated = db.Column(db.DateTime, onupdate=datetime.datetime.now)

    @staticmethod
    def findByIdOrCreate(sender_id):
        p = Person.query.filter_by(id=sender_id).one()
        if not p:
            p = Person()
            p.id = sender_id
            db.session.add(p)
            db.session.commit()
        return p

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

    @staticmethod
    def getSubscribed():
        return Person.query.filter_by(subscribed=True).all()

    def save(self):
        db.session.commit()

    def getDefaultCampus(self, dayOfWeek):
        assert(dayOfWeek in range(1, 6))
        attributes = [self.default_mo, self.default_tu, self.default_we, self.default_th, self.default_fr]
        return attributes[dayOfWeek - 1]

    def setDefaultCampus(self, campus, dayOfWeek):
        assert(campus in CAMPUSSES)
        assert(dayOfWeek in range(1, 6))
        if dayOfWeek == 1:
            self.default_mo = campus
        elif dayOfWeek == 2:
            self.default_tu = campus
        elif dayOfWeek == 3:
            self.default_we = campus
        elif dayOfWeek == 4:
            self.default_th = campus
        elif dayOfWeek == 5:
            self.default_fr = campus

db.create_all()
