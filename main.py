import datetime
import os
import random
from dotenv import load_dotenv
from flask import Flask, flash, render_template, url_for, redirect, request
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from functools import wraps
from math import ceil
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash
from wtforms import StringField, SubmitField, IntegerField, SelectField, PasswordField
from wtforms.validators import DataRequired

login_manager = LoginManager()

app = Flask(__name__)
Bootstrap(app)
load_dotenv()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
USERNAME = os.environ.get('LASUSTENNIS_USERNAME')
PASSWORD = os.environ.get('LASUSTENNIS_PASSWORD')
COLORS = ['#FFF200', '#F7FF00', '#E1FF00', '#CCFF00', '#B7FF00', '#A2FF00', '#8CFF00']


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)


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
    players_order = db.Column(db.String(250), nullable=False)
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
    first_saturday = db.Column(db.String(250), nullable=False)
    matches = relationship("Match", back_populates="week")
    year = relationship("Year", back_populates="weeks")
    year_id = db.Column(db.Integer, db.ForeignKey('year.id'))


class Year(db.Model):
    __tablename__ = "year"
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True)
    weeks = relationship("Week", back_populates="year")


# with app.app_context():
#     db.create_all()


# Forms
class LadderGameForm(FlaskForm):
    player_1 = SelectField("Player 1", default=None, validators=[DataRequired()])
    player_2 = SelectField("Player 2", default=None, validators=[DataRequired()])
    player_3 = SelectField("Player 3", default=None)
    player_4 = SelectField("Player 4", default=None)
    score_1 = IntegerField("Score", description="The score of the first team/player", validators=[DataRequired()])
    score_2 = IntegerField("Score", description="The score of the second team/player", validators=[DataRequired()])
    week = IntegerField("Week", description="The week number of the current season that the match was played in",
                        validators=[DataRequired()])
    year = IntegerField("Year", default=datetime.datetime.now().year, validators=[DataRequired()])
    submit = SubmitField("Upload")


class ChallengeGameForm(FlaskForm):
    player_1 = SelectField("Player 1", default=None, validators=[DataRequired()])
    player_2 = SelectField("Player 2", default=None, validators=[DataRequired()])
    set1_score1 = IntegerField("Score", validators=[DataRequired()])
    set1_score2 = IntegerField("Score", validators=[DataRequired()])
    set2_score1 = IntegerField("Score", validators=[DataRequired()])
    set2_score2 = IntegerField("Score", validators=[DataRequired()])
    set3_score1 = IntegerField("Score")
    set3_score2 = IntegerField("Score")
    week = IntegerField("Week", description="The week number of the current season that the match was played in",
                        validators=[DataRequired()])
    year = IntegerField("Year", default=datetime.datetime.now().year, validators=[DataRequired()])
    submit = SubmitField("Upload")


class AddPlayerForm(FlaskForm):
    name = StringField('Player Court Name', validators=[DataRequired()])
    full_name = StringField('Player Full Name', validators=[DataRequired()])
    rank = SelectField("Player Rank", choices=[None, 1, 2, 3, 4, 5, 6, 7, 8], default=None)
    submit = SubmitField('Add')


class JoinForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    phone_no = IntegerField('Phone Number', validators=[DataRequired()])
    experience = StringField('How long have you been playing tennis?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')


def get_weekly_points():
    weekly_points = {}
    try:
        weeks = Year.query.filter_by(year=datetime.datetime.now().year).first().weeks
    except AttributeError:
        weeks = []
    for week in weeks:
        all_player_points = {}
        players = Player.query.all()
        for player in players:
            player_points = 0
            player_matches = player.matches
            for match in player_matches:
                if match in week.matches:
                    match_players = match.players_order.split()
                    if not match.is_challenge:
                        if len(match_players) == 4:
                            if match_players[0] == player.name or match_players[1] == player.name:
                                player_points += match.score1
                            elif match_players[2] == player.name or match_players[3] == player.name:
                                player_points += match.score2
                        elif len(match_players) == 2:
                            if match_players[0] == player.name:
                                player_points += match.score1
                            elif match_players[1] == player.name:
                                player_points += match.score2
                    else:
                        first_player_sets = 0
                        second_player_sets = 0
                        if match.score1 > match.score2:
                            first_player_sets += 1
                        else:
                            second_player_sets += 1
                        if match.set2_score1 > match.set2_score2:
                            first_player_sets += 1
                        else:
                            second_player_sets += 1
                        if first_player_sets == second_player_sets:
                            if match.set3_score1 > match.set3_score2:
                                first_player_sets += 1
                            else:
                                second_player_sets += 1
                        if first_player_sets > second_player_sets:
                            if player.name == match_players[0]:
                                player_points += match.points_gained
                        else:
                            if player.name == match_players[1]:
                                player_points += match.points_gained
            all_player_points[player.name] = player_points
        weekly_points[f"Wk {week.number}"] = all_player_points
    return weekly_points


def get_cwp_with_players(weekly_points):
    players_in_order = Player.query.order_by(Player.points).all()[::-1]
    cumulative_weekly_points_with_players = {"Wk 0": {player.name: 0 for player in players_in_order}}
    for i in range(1, len(weekly_points) + 1):
        cumulative_weekly_points_with_players[f"Wk {i}"] = {player.name: 0 for player in players_in_order}
        for j in range(1, i + 1):
            for k in range(len(cumulative_weekly_points_with_players[f"Wk {i}"])):
                cumulative_weekly_points_with_players[f"Wk {i}"][players_in_order[k].name] += weekly_points[f"Wk {j}"][
                    players_in_order[k].name]
    return cumulative_weekly_points_with_players


def get_ppg():
    players_in_order = Player.query.order_by(Player.points).all()[::-1]
    ppg = {}
    for player in players_in_order:
        ppg[player.name] = round(float((player.points - player.challenge_points) / len(player.matches)), 2)
    ppg_in_order = dict(sorted(ppg.items(), key=lambda x: x[1]))
    ppg_in_order = dict(reversed(list(ppg_in_order.items())))
    top_5 = {}
    n = 0
    for p in ppg_in_order:
        top_5[p] = ppg_in_order[p]
        n += 1
        if n >= 5:
            break
    return top_5


def get_wpct():
    wpct = {}
    players = Player.query.all()
    for player in players:
        matches_won = 0
        for match in player.matches:
            if not match.is_challenge:
                match_players = match.players_order.split()
                if len(match_players) == 4:
                    if player.name == match_players[0] or player.name == match_players[1]:
                        if match.score1 > match.score2:
                            matches_won += 1
                    else:
                        if match.score1 < match.score2:
                            matches_won += 1
                else:
                    if player.name == match_players[0]:
                        if match.score1 > match.score2:
                            matches_won += 1
                    else:
                        if match.score1 < match.score2:
                            matches_won += 1
        wpct[player.name] = round((matches_won / (len(player.matches) - player.challenge_matches)) * 100, 2)
    wpct_in_order = dict(sorted(wpct.items(), key=lambda x: x[1]))
    wpct_in_order = dict(reversed(list(wpct_in_order.items())))
    top_5 = {}
    n = 0
    for p in wpct_in_order:
        top_5[p] = wpct_in_order[p]
        n += 1
        if n >= 5:
            break
    return top_5


def del_match(match_id):
    with app.app_context():
        match = Match.query.get(match_id)
        match_players = match.players_order.split()
        if match.is_challenge:
            player2 = Player.query.filter_by(name=match_players[-1]).first()
            player2.challenge_matches -= 1
            player1 = Player.query.filter_by(name=match_players[-1]).first()
            player1.challenge_matches -= 1
            first_player_sets = 0
            second_player_sets = 0
            if match.score1 > match.score2:
                first_player_sets += 1
            else:
                second_player_sets += 1
            if match.set2_score1 > match.set2_score2:
                first_player_sets += 1
            else:
                second_player_sets += 1
            if first_player_sets == second_player_sets:
                if match.set3_score1 > match.set3_score2:
                    first_player_sets += 1
                else:
                    second_player_sets += 1
            if first_player_sets > second_player_sets:
                player1.challenge_points -= match.points_gained
                player1.points -= match.points_gained
            else:
                player2.challenge_points -= match.points_gained
                player2.points -= match.points_gained
        else:
            if len(match_players) == 4:
                player4 = Player.query.filter_by(name=match_players[-1]).first()
                player4.points = player4.points - match.score2
                player3 = Player.query.filter_by(name=match_players[-1]).first()
                player3.points = player3.points - match.score2
                player2 = Player.query.filter_by(name=match_players[-1]).first()
                player2.points = player2.points - match.score1
                player1 = Player.query.filter_by(name=match_players[-1]).first()
                player1.points = player1.points - match.score1
            elif len(match_players) == 2:
                player2 = Player.query.filter_by(name=match_players[-1]).first()
                player2.points = player2.points - match.score2
                player1 = Player.query.filter_by(name=match_players[-1]).first()
                player1.points = player1.points - match.score1
        for player in match.players:
            match.players.remove(player)
        db.session.delete(match)
        db.session.commit()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/ladder-games")
def ladder_games():
    with app.app_context():
        players = Player.query.all()

        weekly_points = get_weekly_points()
        cumulative_weekly_points_with_players = get_cwp_with_players(weekly_points)

        mpw = {}
        for i in range(25, 0, -1):
            for week in weekly_points:
                for player in weekly_points[week]:
                    if weekly_points[week][player] == i:
                        mpw[f"{player} ({week})"] = i
            if len(mpw) >= 5:
                break

        ppg = get_ppg()
        wpct = get_wpct()

        try:
            weeks_in_year = Year.query.filter_by(year=datetime.datetime.now().year).first().weeks
        except AttributeError:
            pass
        else:
            if len(weeks_in_year) > 1:
                previous_week = weeks_in_year[-2].number
            elif len(weeks_in_year) == 1:
                previous_week = 0
            else:
                previous_week = -1

            current_week = previous_week + 1
            if previous_week >= 0:
                pwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Wk {previous_week}"].items(), key=lambda x: x[1]
                    )
                )
                previous_week_arrangement = [cumulative_weekly_points_with_players[f"Wk {previous_week}"][x] for x in pwa][::-1]

                cwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Wk {current_week}"].items(), key=lambda x: x[1]
                    )
                )
                current_week_arrangement = [cumulative_weekly_points_with_players[f"Wk {current_week}"][x] for x in cwa][
                                            ::-1]
            else:
                pwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Wk 0"].items(), key=lambda x: x[1]
                    )
                )
                previous_week_arrangement = [cumulative_weekly_points_with_players[f"Wk 0"][x] for x in
                                             pwa][::-1]

                cwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Wk {current_week}"].items(), key=lambda x: x[1]
                    )
                )
                current_week_arrangement = [cumulative_weekly_points_with_players[f"Wk {current_week}"][x] for x in
                                            cwa][
                                           ::-1]

            for player in players:
                if not player.position:
                    player.position = current_week_arrangement.index(cumulative_weekly_points_with_players[f"Wk {current_week}"][player.name]) + 1
                    player.shift = 0
                else:
                    player.position = current_week_arrangement.index(cumulative_weekly_points_with_players[f"Wk {current_week}"][player.name]) + 1
                    player.shift = (previous_week_arrangement.index(cumulative_weekly_points_with_players[f"Wk {previous_week}"][player.name]) + 1) - player.position
                player.points = cumulative_weekly_points_with_players[f"Wk {current_week}"][player.name]
            db.session.commit()
    try:
        players = Player.query.order_by(Player.points).all()[::-1]
        weeks = Year.query.filter_by(year=datetime.datetime.now().year).first().weeks[::-1]
        no_of_weeks = len(weeks)
        no_of_matches = [len(week.matches) for week in weeks]
        players_in_matches = [[len(match.players) for match in week.matches] for week in weeks]
        match_players = [[match.players_order.split() for match in week.matches] for week in weeks]
        games_played = [len(player.matches) for player in players]
    except AttributeError:
        players = []
        weeks = []
        no_of_weeks = len(weeks)
        no_of_matches = []
        players_in_matches = [[]]
        match_players = [[]]
        games_played = []

    return render_template(
        "ladder-games.html",
        players=players,
        games=games_played,
        no_of_players=len(players),
        weeks=weeks,
        no_of_weeks=no_of_weeks,
        no_of_matches=no_of_matches,
        players_in_matches=players_in_matches,
        match_players=match_players,
        mpw=mpw,
        ppg=ppg,
        wpct=wpct,
        year=datetime.datetime.now().year
    )


@app.route("/join", methods=['GET', 'POST'])
def join():
    form = JoinForm()
    if request.method == 'POST':
        name = form.name.data
        phone_no = form.phone_no.data
        experience = form.experience.data
        return redirect(
            f"mailto:lasustennis@gmail.com?subject=New Member Request!!!&"
            f"body={name} wants to become a member of LASUSTENNIS CLUB.\n"
            f"Phone Number: 0{phone_no}\nLevel of experience: {experience}"
        )
    return render_template("join.html", form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('admin'))
            else:
                flash("Password incorrect, please try again.")
                redirect(url_for('login'))
        else:
            flash("Username incorrect, please try again.")
            redirect(url_for('login'))
    return render_template("login.html", form=form)


@app.route("/admin")
@admin_only
def admin():
    return render_template("admin.html")


@app.route("/ladder-match-singles", methods=['GET', 'POST'])
@admin_only
def singles_ladder_match():
    p1 = request.args.get('p1')
    p2 = request.args.get('p2')
    if request.args.get('match_id'):
        match = Match.query.get(request.args.get('match_id'))
        match_players = match.players_order.split()
        form = LadderGameForm(
            player_1=match_players[0],
            player_2=match_players[1],
            score_1=match.score1,
            score_2=match.score2,
            week=match.week.number,
            year=match.week.year.year
        )
    else:
        form = LadderGameForm(player_1=p1, player_2=p2)
    with app.app_context():
        player_names = sorted([""] + [player.name for player in Player.query.all()])
    form.player_1.choices = player_names
    form.player_2.choices = player_names
    form.player_3.choices = player_names
    form.player_4.choices = player_names
    if request.method == 'POST':
        if request.args.get('match_id'):
            del_match(match.id)
        player_1 = form.player_1.data
        player_2 = form.player_2.data
        score_1 = form.score_1.data
        score_2 = form.score_2.data
        week = form.week.data
        form_year = form.year.data
        with app.app_context():
            new_match = Match(score1=score_1, score2=score_2, is_challenge=False)
            player1 = Player.query.filter_by(name=player_1).first()
            new_match.players.append(player1)
            player1.points += score_1
            player2 = Player.query.filter_by(name=player_2).first()
            new_match.players.append(player2)
            player2.points += score_2
            new_match.players_order = f"{player_1} {player_2}"
            yr = Year.query.filter_by(year=form_year).first()
            if yr:
                yr_weeks = yr.weeks
                weeks_in_years = [wk.number for wk in yr_weeks]
            else:
                weeks_in_years = []
            if week in weeks_in_years:
                new_match.week = Week.query.filter_by(number=week).first()
            else:
                new_week = Week(number=week, first_saturday=datetime.datetime.now().strftime("%d %B"))
                weekday = datetime.datetime.now().weekday()
                if weekday != 5:
                    if weekday > 5:
                        new_week.first_saturday = (
                                    datetime.datetime.now() - datetime.timedelta(days=weekday - 5)).strftime(
                            "%d %B")
                    else:
                        new_week.first_saturday = (
                                    datetime.datetime.now() - datetime.timedelta(days=weekday + 2)).strftime(
                            "%d %B")
                if form_year in [y.year for y in Year.query.all()]:
                    new_week.year = Year.query.filter_by(year=form_year).first()
                else:
                    new_year = Year(year=form_year)
                    db.session.add(new_year)
                    new_week.year = new_year
                new_match.week = new_week
                db.session.add(new_week)
            db.session.add(new_match)
            db.session.commit()
        return redirect(url_for("admin"))
    return render_template("singles-ladder-match.html", form=form)


@app.route("/ladder-match-doubles", methods=['GET', 'POST'])
@admin_only
def doubles_ladder_match():
    p1 = request.args.get('p1')
    p2 = request.args.get('p2')
    p3 = request.args.get('p3')
    p4 = request.args.get('p4')
    if request.args.get('match_id'):
        match = Match.query.get(request.args.get('match_id'))
        match_players = match.players_order.split()
        form = LadderGameForm(
            player_1=match_players[0],
            player_2=match_players[1],
            player_3=match_players[2],
            player_4=match_players[3],
            score_1=match.score1,
            score_2=match.score2,
            week=match.week.number,
            year=match.week.year.year
        )
    else:
        form = LadderGameForm(player_1=p1, player_2=p2, player_3=p3, player_4=p4)
    with app.app_context():
        player_names = sorted([""] + [player.name for player in Player.query.all()])
    form.player_1.choices = player_names
    form.player_2.choices = player_names
    form.player_3.choices = player_names
    form.player_4.choices = player_names
    if request.method == 'POST':
        if request.args.get('match_id'):
            del_match(match.id)
        player_1 = form.player_1.data
        player_2 = form.player_2.data
        player_3 = form.player_3.data
        player_4 = form.player_4.data
        score_1 = form.score_1.data
        score_2 = form.score_2.data
        week = form.week.data
        form_year = form.year.data
        with app.app_context():
            new_match = Match(score1=score_1, score2=score_2, is_challenge=False)
            player1 = Player.query.filter_by(name=player_1).first()
            new_match.players.append(player1)
            player1.points += score_1
            player2 = Player.query.filter_by(name=player_2).first()
            new_match.players.append(player2)
            player2.points += score_1
            player3 = Player.query.filter_by(name=player_3).first()
            new_match.players.append(player3)
            player3.points += score_2
            player4 = Player.query.filter_by(name=player_4).first()
            new_match.players.append(player4)
            player4.points += score_2
            new_match.players_order = f"{player_1} {player_2} {player_3} {player_4}"
            yr = Year.query.filter_by(year=form_year).first()
            if yr:
                yr_weeks = yr.weeks
                weeks_in_years = [wk.number for wk in yr_weeks]
            else:
                weeks_in_years = []
            if week in weeks_in_years:
                new_match.week = Week.query.filter_by(number=week).first()
            else:
                new_week = Week(number=week, first_saturday=datetime.datetime.now().strftime("%d %B"))
                weekday = datetime.datetime.now().weekday()
                if weekday != 5:
                    if weekday > 5:
                        new_week.first_saturday = (datetime.datetime.now() - datetime.timedelta(days=weekday - 5)).strftime(
                            "%d %B")
                    else:
                        new_week.first_saturday = (datetime.datetime.now() - datetime.timedelta(days=weekday + 2)).strftime(
                            "%d %B")
                if form_year in [y.year for y in Year.query.all()]:
                    new_week.year = Year.query.filter_by(year=form_year).first()
                else:
                    new_year = Year(year=form_year)
                    db.session.add(new_year)
                    new_week.year = new_year
                new_match.week = new_week
                db.session.add(new_week)
            db.session.add(new_match)
            db.session.commit()
        return redirect(url_for("admin"))
    return render_template("doubles-ladder-match.html", form=form)


@app.route("/generate-match", methods=['GET', 'POST'])
@admin_only
def generate_match():
    players = sorted([player.name for player in Player.query.all()])
    if request.method == 'POST':
        try:
            match_type = request.form['match-type']
        except:
            match_type = ""
        if match_type == 'singles':
            available = []
            for player in players:
                try:
                    request.form[player]
                except:
                    pass
                else:
                    available.append(player)
            if len(available) >= 2:
                player_1 = random.choice(available)
                available.remove(player_1)
                player_2 = random.choice(available)
                return redirect(url_for("singles_ladder_match", p1=player_1, p2=player_2))
        elif match_type == 'doubles':
            available = []
            for player in players:
                try:
                    request.form[player]
                except:
                    pass
                else:
                    available.append(player)
            if len(available) >= 4:
                player_1 = random.choice(available)
                available.remove(player_1)
                player_2 = random.choice(available)
                available.remove(player_2)
                player_3 = random.choice(available)
                available.remove(player_3)
                player_4 = random.choice(available)
                return redirect(url_for("doubles_ladder_match", p1=player_1, p2=player_2, p3=player_3, p4=player_4))
    return render_template("generate-match.html", players=players, length=len(players), cut=ceil(len(players) / 2))


@app.route("/challenge-match", methods=['GET', 'POST'])
@admin_only
def challenge_match():
    if request.args.get('match_id'):
        match = Match.query.get(request.args.get('match_id'))
        match_players = match.players_order.split()
        form = ChallengeGameForm(
            player_1=match_players[0],
            player_2=match_players[1],
            set1_score_1=match.score1,
            set1_score_2=match.score2,
            set2_score_1=match.set2_score1,
            set2_score_2=match.set2_score2,
            set3_score_1=match.set3_score1,
            set3_score_2=match.set3_score2,
            week=match.week.number,
            year=match.week.year.year
        )
    else:
        form = ChallengeGameForm()
    with app.app_context():
        player_names = sorted([""] + [player.name for player in Player.query.all()])
    form.player_1.choices = player_names
    form.player_2.choices = player_names
    if request.method == 'POST':
        if request.args.get('match_id'):
            del_match(match.id)
        player_1 = form.player_1.data
        player_2 = form.player_2.data
        set1_score_1 = form.set1_score1.data
        set1_score_2 = form.set1_score2.data
        set2_score_1 = form.set2_score1.data
        set2_score_2 = form.set2_score2.data
        set3_score_1 = form.set3_score1.data
        set3_score_2 = form.set3_score2.data
        week = form.week.data
        form_year = form.year.data
        with app.app_context():
            new_match = Match(score1=set1_score_1, score2=set1_score_2, set2_score1=set2_score_1, set2_score2=set2_score_2,
                              set3_score1=set3_score_1, set3_score2=set3_score_2, is_challenge=True)
            first_player = Player.query.filter_by(name=player_1).first()
            new_match.players.append(first_player)
            first_player.challenge_matches += 1
            second_player = Player.query.filter_by(name=player_2).first()
            new_match.players.append(second_player)
            second_player.challenge_matches += 1
            new_match.players_order = f"{player_1} {player_2}"
            first_player_sets = 0
            second_player_sets = 0
            if set1_score_1 > set1_score_2:
                first_player_sets += 1
            else:
                second_player_sets += 1
            if set2_score_1 > set2_score_2:
                first_player_sets += 1
            else:
                second_player_sets += 1
            if first_player_sets == second_player_sets:
                if set3_score_1 > set3_score_2:
                    first_player_sets += 1
                else:
                    second_player_sets += 1
            if first_player_sets > second_player_sets:
                if first_player.points < second_player.points:
                    new_match.points_gained = second_player.points - first_player.points
                    first_player.challenge_points = new_match.points_gained
                    first_player.points = second_player.points
            else:
                if first_player.points > second_player.points:
                    new_match.points_gained = first_player.points - second_player.points
                    second_player.challenge_points = new_match.points_gained
                    second_player.points = first_player.points
            yr = Year.query.filter_by(year=form_year).first()
            if len(yr.weeks) > 0:
                weeks_in_years = [wk.number for wk in yr.weeks]
            else:
                weeks_in_years = []
            if week in weeks_in_years:
                new_match.week = Week.query.filter_by(number=week).first()
            else:
                new_week = Week(number=week, first_saturday=datetime.datetime.now().strftime("%d %B"))
                weekday = datetime.datetime.now().weekday()
                if weekday != 5:
                    if weekday > 5:
                        new_week.first_saturday = (datetime.datetime.now() - datetime.timedelta(days=weekday - 5)).strftime(
                            "%d %B")
                    else:
                        new_week.first_saturday = (datetime.datetime.now() - datetime.timedelta(days=weekday + 2)).strftime(
                            "%d %B")
                if form_year in [y.year for y in Year.query.all()]:
                    new_week.year = Year.query.filter_by(year=form_year).first()
                else:
                    new_year = Year(year=form_year)
                    db.session.add(new_year)
                    new_week.year = new_year
                new_match.week = new_week
                db.session.add(new_week)
            db.session.add(new_match)
            db.session.commit()
        return redirect(url_for("admin"))
    return render_template("challenge-match.html", form=form)


@app.route("/add-player", methods=['GET', 'POST'])
@admin_only
def add_player():
    form = AddPlayerForm()
    if form.validate_on_submit():
        name = form.name.data
        full_name = form.full_name.data
        with app.app_context():
            new_player = Player(name=name, full_name=full_name, points=0, challenge_points=0, challenge_matches=0)
            if form.rank.data in range(1, 9):
                new_player.rank = form.rank.data
            db.session.add(new_player)
            db.session.commit()
        return redirect(url_for("admin"))
    return render_template("add-player.html", form=form)


@app.route("/matches")
@admin_only
def matches():
    match_list = Match.query.all()
    no_of_players = [len(match.players) for match in match_list]
    match_players = [match.players_order.split() for match in match_list]
    return render_template(
        "matches.html",
        matches=match_list,
        no_of_players=no_of_players,
        match_players=match_players,
        length=len(match_list)
    )


@app.route("/delete-match/<int:match_id>")
@admin_only
def delete_match(match_id):
    match = Match.query.get(match_id)
    del_match(match.id)
    return redirect(url_for("admin"))


if __name__ == "__main__":
    app.run(debug=True)
