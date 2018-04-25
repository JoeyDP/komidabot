import datetime
from komidabot import db
from sqlalchemy import ForeignKey, UniqueConstraint

from .facebook import user_profile

CAMPUSSES = ['cmi', 'cde', 'cst']
DEFAULT_CAMPUS = CAMPUSSES[0]
DEFAULT_LANGUAGE = 'nl_BE'
DEFAULT_LANGUAGE_VARIANTS = ['nl_BE', 'nl_NL']


class Menu(db.Model):
    """ Database table for Komida menu. """
    __tablename__ = "menu"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime)
    campus = db.Column(db.String)
    type = db.Column(db.String)
    text = db.Column(db.String)
    price_student = db.Column(db.REAL)
    price_staff = db.Column(db.REAL)

    UniqueConstraint(date, campus, type, name="constraint_unique_menu_item")

    @staticmethod
    def getItemsOn(date, campus):
        return Menu.query.filter_by(date=date, campus=campus).all()

    @staticmethod
    def hasEntryOn(date, campus):
        item = Menu.query.filter_by(date=date, campus=campus, type='meat').one_or_none()
        return item is not None


class TranslatedMenu(db.Model):
    id = db.Column(ForeignKey("menu.id"), primary_key=True)
    item = db.relationship(Menu)
    language = db.Column(db.String, primary_key=True)
    translation = db.Column(db.String)

    @property
    def text(self):
        return self.translation

    @text.setter
    def text(self, value):
        self.translation = value

    @property
    def type(self):
        return self.item.type

    @property
    def price_student(self):
        return self.item.price_student

    @property
    def price_staff(self):
        return self.item.price_staff

    @property
    def date(self):
        return self.item.date

    @property
    def campus(self):
        return self.item.campus

    @staticmethod
    def getItemsInLanguage(date, campus, language):
        if language == DEFAULT_LANGUAGE or language is None or language in DEFAULT_LANGUAGE_VARIANTS:
            return Menu.getItemsOn(date, campus)
        else:
            return TranslatedMenu.query \
                .filter_by(language=language)\
                .join(Menu)\
                .filter(Menu.date == date, Menu.campus == campus)\
                .all()

    @staticmethod
    def addTranslatedItems(items):
        for item in items:
            db.session.add(item)
        db.session.commit()


class Person(db.Model):
    __tablename__ = "person"

    id = db.Column(db.String(128), primary_key=True)
    subscribed = db.Column(db.Boolean, default=True)

    default_mo = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_tu = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_we = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_th = db.Column(db.String(5), default=DEFAULT_CAMPUS)
    default_fr = db.Column(db.String(5), default=DEFAULT_CAMPUS)

    language = db.Column(db.String(5), default=DEFAULT_LANGUAGE, server_default=DEFAULT_LANGUAGE)

    time_joined = db.Column(db.DateTime, default=datetime.datetime.now)
    time_updated = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __init__(self, sender_id=None):
        if sender_id is not None:
            self.id = sender_id
            self.language = user_profile.getLocale(sender_id)
            db.session.add(self)

    @staticmethod
    def findByIdOrCreate(sender_id):
        p = Person.query.filter_by(id=sender_id).one_or_none()
        if not p:
            p = Person(sender_id)
            db.session.commit()
        elif p.language is None:
            p.language = user_profile.getLocale(sender_id)  # set language

        return p

    @staticmethod
    def subscribe(sender_id):
        person = Person.query.filter_by(id=sender_id).one_or_none()
        if not person:
            person = Person(sender_id)
        person.subscribed = True
        db.session.commit()

    @staticmethod
    def unsubscribe(sender_id):
        person = Person.query.filter_by(id=sender_id).one_or_none()
        if not person:
            person = Person(sender_id)
        person.subscribed = False
        db.session.commit()

    @staticmethod
    def getSubscribed():
        return Person.query.filter_by(subscribed=True).all()

    def save(self):
        db.session.commit()

    def getLanguage(self):
        if self.language is None:
            self.language = user_profile.getLocale(self.id)
        return self.language

    def setDefault(self, campus):
        assert(campus in CAMPUSSES)
        self.default_mo = self.default_tu = self.default_we = self.default_th = self.default_fr = campus

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
