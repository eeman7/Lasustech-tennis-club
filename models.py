from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()


# Models
class PlayerMatch(db.Model):
    __tablename__ = "player_match"
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'), primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), primary_key=True)


class Player(db.Model):
    __tablename__ = "player"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    full_name = db.Column(db.String(250), unique=True, nullable=False)
    rank = db.Column(db.Integer)
    matches = relationship("Match", secondary="player_match", back_populates="players")
    points = db.Column(db.Integer, nullable=False)
    challenge_points = db.Column(db.Integer, nullable=False)
    challenge_matches = db.Column(db.Integer, nullable=False)
    position = db.Column(db.Integer)
    shift = db.Column(db.Integer)


class Match(db.Model):
    __tablename__ = "match"
    id = db.Column(db.Integer, primary_key=True)
    players = relationship("Player", secondary="player_match", back_populates="matches")
    score1 = db.Column(db.Integer, nullable=False)
    score2 = db.Column(db.Integer, nullable=False)
    set2_score1 = db.Column(db.Integer)
    set2_score2 = db.Column(db.Integer)
    set3_score1 = db.Column(db.Integer)
    set3_score2 = db.Column(db.Integer)
    week = relationship("Week", back_populates="matches")
    week_id = db.Column(db.Integer, db.ForeignKey('week.id'))
    is_challenge = db.Column(db.Boolean, nullable=False)
    points_gained = db.Column(db.Integer)


class Week(db.Model):
    __tablename__ = "week"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    first_saturday = db.Column(db.String(250), unique=True, nullable=False)
    matches = relationship("Match", back_populates="week")
    year = relationship("Year", back_populates="weeks")
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'))


class Year(db.Model):
    __tablename__ = "year"
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True)
    weeks = relationship("Week", back_populates="year")


db.create_all()
