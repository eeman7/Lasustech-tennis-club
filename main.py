import datetime
import os
import matplotlib.pyplot as plt
import math
import pandas as pd
import random
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from flask import Flask, flash, render_template, url_for, redirect, request
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from functools import wraps
from math import ceil
from PIL import Image, ImageDraw, ImageFont
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


def split(string: str):
    return string.split()


app.jinja_env.globals.update(split=split)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
USERNAME = os.environ.get('LASUSTENNIS_USERNAME')
PASSWORD = os.environ.get('LASUSTENNIS_PASSWORD')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
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
    week = IntegerField("Day", description="The day number of the current season that the match was played in",
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
    week = IntegerField("Day", description="The week number of the current season that the match was played in",
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


class WeekForm(FlaskForm):
    week = SelectField("Select your desired day", default=None, validators=[DataRequired()])
    submit = SubmitField('Go')


class HeadToHeadForm(FlaskForm):
    player_1 = SelectField("Player 1", default=None, validators=[DataRequired()])
    player_2 = SelectField("Player 2", default=None, validators=[DataRequired()])


def send_member_request(name, phone_no, experience):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'lasustennis@gmail.com'
    smtp_password = EMAIL_PASSWORD

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    message = MIMEMultipart()
    message['From'] = smtp_username
    message['To'] = 'lasustennis@gmail.com'
    message['Subject'] = 'New Member Request!!!'

    body = f'{name} wants to become a member of LASUSTENNIS CLUB.\n' \
           f'Phone Number: 0{phone_no}\nLevel of experience: {experience}'
    message.attach(MIMEText(body, 'plain'))

    server.sendmail(smtp_username, 'lasustennis@gmail.com', message.as_string())
    server.quit()


def send_stat(stat: dict, title: str):
    plt.figure(figsize=(16, 10), facecolor=random.choice(COLORS))
    plt.xticks(fontsize=15, rotation=15)
    plt.yticks(fontsize=20)
    plt.title(title, fontsize=25)
    dic = {}
    n = 0
    for i in stat:
        n = n + 1
        if n == 5:
            fifth = stat[i]
    n = 0
    for i in stat:
        if n > 5:
            if stat[i] == fifth:
                dic[i] = stat[i]
            else:
                break
        dic[i] = stat[i]
        n = n + 1

    for player in dic:
        bar = plt.bar(player, height=dic[player], color='#000000')
        plt.bar_label(bar, padding=3, fontsize=20)
    plt.savefig('stat.png', dpi=1000)

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'lasustennis@gmail.com'
    smtp_password = EMAIL_PASSWORD

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    message = MIMEMultipart()
    message['From'] = smtp_username
    message['To'] = 'lasustennis@gmail.com'
    message['Subject'] = title

    body = ''
    message.attach(MIMEText(body, 'plain'))

    with open('stat.png', 'rb') as f:
        img_data = f.read()
        image = MIMEImage(img_data, name=f'{title.lower().replace(" ", "_")}.png')
        message.attach(image)

    server.sendmail(smtp_username, 'lasustennis@gmail.com', message.as_string())
    server.quit()


def send_cwp():
    weekly_points = get_weekly_points()
    players_in_order = Player.query.order_by(Player.points).all()[::-1]
    cumulative_weekly_points = {"": [0 for _ in players_in_order]}
    for i in range(1, len(weekly_points) + 1):
        cumulative_weekly_points[f"Day {i}"] = [0 for i in range(len(weekly_points[f"Day {i}"]))]
        for j in range(1, i + 1):
            for k in range(len(cumulative_weekly_points[f"Day {i}"])):
                cumulative_weekly_points[f"Day {i}"][k] += weekly_points[f"Day {j}"][players_in_order[k].name]
    df = pd.DataFrame.from_dict(
        cumulative_weekly_points,
        orient='index',
        columns=[player.name for player in players_in_order]
    )
    plt.figure(figsize=(16, 10), facecolor=random.choice(COLORS))
    plt.xticks(fontsize=20)
    plt.yticks(fontsize=20)
    plt.xlabel('Weeks', fontsize=25)
    plt.ylabel('Points', fontsize=25)
    plt.plot(df.index, df, linewidth=3)
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.legend(df.columns, fontsize=17)
    plt.savefig('cwp.png', dpi=1000)

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'lasustennis@gmail.com'
    smtp_password = EMAIL_PASSWORD

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    message = MIMEMultipart()
    message['From'] = smtp_username
    message['To'] = 'lasustennis@gmail.com'
    message['Subject'] = 'CUMULATIVE WEEKLY POINTS'

    with open('cwp.png', 'rb') as f:
        img_data = f.read()
        image = MIMEImage(img_data, name='cwp.png')
        message.attach(image)

    server.sendmail(smtp_username, 'lasustennis@gmail.com', message.as_string())
    server.quit()


def send_week_result(number):
    week = Week.query.filter_by(number=number).first()
    results = ""
    for match in week.matches:
        match_players = match.players_order.split()
        if not match.is_challenge:
            if len(match.players) == 4:
                results = results + f"{match_players[0]}/{match_players[1]} {match.score1} - {match.score2} {match_players[2]}/{match_players[3]}\n\n"
            elif len(match.players) == 2:
                results = results + f"{match_players[0]} {match.score1} - {match.score2} {match_players[1]}\n\n"

    if len(week.matches) < 20:
        img = Image.new('RGB', (800, 1200), (255, 255, 255))
    else:
        img = Image.new('RGB', (800 + (34 * (len(week.matches) - 19)), 1200 + (51 * (len(week.matches) - 19))), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    w, h = img.size

    from_color = (69, 255, 0)
    to_color = (255, 242, 0)
    angle = math.pi * 0 / 180

    for y in range(img.height):
        for x in range(img.width):
            frac = (math.cos(angle) * x + math.sin(angle) * y) / img.width
            color = (
                int(from_color[0] * (1 - frac) + to_color[0] * frac),
                int(from_color[1] * (1 - frac) + to_color[1] * frac),
                int(from_color[2] * (1 - frac) + to_color[2] * frac)
            )
            draw.point((x, y), fill=color)

    # Heading
    text = f"DAY {number} LADDER GAMES"
    heading = ImageFont.truetype("fonts/RadikalTrial-Black-BF642254c139184.otf", 50)
    text_width, text_height = draw.textsize(text, font=heading)
    text_x = (w // 2) - text_width // 2
    text_y = 100 - text_height // 2
    draw.text((text_x, text_y), text=text, fill=(0, 0, 0), font=heading)

    # Matches
    for i in range(len(week.matches)):
        match = week.matches[i]
        match_players = match.players_order.split()
        if not match.is_challenge:
            draw.rectangle((((w // 8), 200 + (i * 50)), ((w - (w // 8)), 244 + (i * 50))), fill=(255, 255, 255))
            draw.rectangle(((((w // 2) - 38), 200 + (i * 50)), (((w // 2) + 38), 244 + (i * 50))), fill=(0, 0, 0))

            score_font = ImageFont.truetype("fonts/arialbd.ttf", 24)
            score = f"{match.score1} - {match.score2}"
            score_w, score_h = draw.textsize(score, font=score_font)
            score_x = (w // 2) - score_w // 2
            score_y = (222 + (i * 50)) - score_h // 2
            draw.text((score_x, score_y), text=score, fill=(255, 255, 255), font=score_font)

            font = ImageFont.truetype("fonts/RadikalTrial-Medium-BF642254c12fd7b.otf", 24)
            if len(match_players) == 4:
                left = f'{match_players[0]}  {match_players[1]}'
                right = f'{match_players[2]} {match_players[3]}'
            else:
                left = match_players[0]
                right = match_players[1]

            left_w, left_h = draw.textsize(left, font=font)
            left_x = ((w // 2) - 50) - left_w
            left_contains_bottom = 'g' in left or 'j' in left or 'p' in left or 'q' in left or 'y' in left
            if left_contains_bottom:
                left_y = (222 + (i * 50)) - left_h // 2
            else:
                left_y = (233 + (i * 50)) - left_h
            draw.text((left_x, left_y), text=left, fill=(0, 0, 0), font=font)

            right_h = draw.textsize(right, font=font)[1]
            right_contains_bottom = 'g' in right or 'j' in right or 'p' in right or 'q' in right or 'y' in right
            if right_contains_bottom:
                right_y = (222 + (i * 50)) - right_h // 2
            else:
                right_y = (233 + (i * 50)) - right_h
            draw.text((((w // 2) + 50), right_y), text=right, fill=(0, 0, 0), font=font)

            if len(match_players) == 4:
                slash = '/'
                l_slash_w, l_slash_h = draw.textsize(slash, font=score_font)
                size1 = draw.textsize(match_players[1], font=font)[0]
                l_slash_x = ((w // 2) - 50) - (size1 + l_slash_w)
                if left_contains_bottom:
                    l_slash_y = (222 + (i * 50)) - l_slash_h // 2
                else:
                    l_slash_y = (233 + (i * 50)) - l_slash_h
                draw.text((l_slash_x, l_slash_y), text=slash, fill=(0, 0, 0), font=score_font)

                r_slash_h = draw.textsize(slash, font=score_font)[1]
                size2 = draw.textsize(match_players[2], font=font)[0]
                r_slash_x = ((w // 2) + 50) + size2
                if right_contains_bottom:
                    r_slash_y = (222 + (i * 50)) - r_slash_h // 2
                else:
                    r_slash_y = (233 + (i * 50)) - r_slash_h
                draw.text((r_slash_x, r_slash_y), text=slash, fill=(0, 0, 0), font=score_font)

            if match.score1 > match.score2:
                draw.polygon((((w // 8), 212 + (i * 50)), (((w // 8) + 10), 222 + (i * 50)), ((w // 8), 232 + (i * 50))), fill=(0, 0, 0), outline=(0, 0, 0))
            else:
                draw.polygon((((w - (w // 8)), 212 + (i * 50)), ((w - (w // 8) - 10), 222 + (i * 50)), ((w - (w // 8)), 232 + (i * 50))), fill=(0, 0, 0), outline=(0, 0, 0))

    img.save('result.png')

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'lasustennis@gmail.com'
    smtp_password = EMAIL_PASSWORD

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    message = MIMEMultipart()
    message['From'] = smtp_username
    message['To'] = 'lasustennis@gmail.com'
    message['Subject'] = f'DAY {number} LADDER GAME RESULTS'

    with open('result.png', 'rb') as f:
        img_data = f.read()
        image = MIMEImage(img_data, name=f'day{number}_ladder_games.png')
        message.attach(image)

    server.sendmail(smtp_username, 'lasustennis@gmail.com', message.as_string())
    server.quit()


def send_table(day):
    points_by_week = dict(sorted(get_cwp_with_players(get_weekly_points())[f"Day {day}"].items(), key=lambda x: x[1], reverse=True))
    only_points = [points_by_week[x] for x in points_by_week]
    if not day == 1:
        points_previous_week = get_cwp_with_players(get_weekly_points())[f"Day {day - 1}"]
        only_previous_week_points = sorted([points_previous_week[x] for x in points_previous_week], reverse=True)
    matches_by_week = get_cwm_with_players(get_weekly_matches())[f"Day {day}"]
    table = {}
    for player in points_by_week:
        shift = only_previous_week_points.index(points_previous_week[player]) - only_points.index(points_by_week[player])
        table[player] = {
            "position": only_points.index(points_by_week[player]) + 1,
            "games": matches_by_week[player],
            "points": points_by_week[player],
            "shift": shift
        }

    if len(table) < 20:
        img = Image.new('RGB', (900, 1350), (255, 255, 255))
    else:
        img = Image.new('RGB', (900 + ((len(table) - 20) * 34), 1350 + ((len(table) - 20) * 51)), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    w, h = img.size

    from_color = (0, 241, 255)
    to_color = (214, 0, 255)
    angle = math.pi * 15 / 180

    for y in range(img.height):
        for x in range(img.width):
            frac = (math.cos(angle) * x + math.sin(angle) * y) / img.width
            color = (
                int(from_color[0] * (1 - frac) + to_color[0] * frac),
                int(from_color[1] * (1 - frac) + to_color[1] * frac),
                int(from_color[2] * (1 - frac) + to_color[2] * frac)
            )
            draw.point((x, y), fill=color)

    # Heading
    text = f"DAY {day} STANDINGS"
    heading = ImageFont.truetype("fonts/RadikalTrial-Black-BF642254c139184.otf", 50)
    text_width, text_height = draw.textsize(text, font=heading)
    text_x = (w // 2) - text_width // 2
    text_y = 100 - text_height // 2
    draw.text((text_x, text_y), text=text, fill=(0, 0, 0), font=heading)

    heading = ImageFont.truetype("fonts/RadikalTrial-Black-BF642254c139184.otf", 30)
    text_width, text_height = draw.textsize("Games", font=heading)
    text_x = ((w - (w // 9)) - 160) - text_width // 2
    text_y = 170 - text_height // 2
    draw.text((text_x, text_y), text="Games", fill=(0, 0, 0), font=heading)

    text_width, text_height = draw.textsize("Pts", font=heading)
    text_x = ((w - (w // 9)) - 50) - text_width // 2
    text_y = 170 - text_height // 2
    draw.text((text_x, text_y), text="Pts", fill=(0, 0, 0), font=heading)

    # Players
    i = 0
    for player in table:
        draw.rectangle((((w // 9), 200 + (i * 50)), ((w - (w // 9)), 244 + (i * 50))), fill=(255, 255, 255))

        numbers_font = ImageFont.truetype("fonts/arialbd.ttf", 24)
        font = ImageFont.truetype("fonts/RadikalTrial-Medium-BF642254c12fd7b.otf", 24)

        pos = str(table[player]['position'])
        pos_w, pos_h = draw.textsize(pos, font=numbers_font)
        pos_x = ((w // 9) + 22) - pos_w // 2
        pos_y = 222 + (i * 50) - pos_h // 2
        draw.text((pos_x, pos_y), text=pos, fill=(0, 0, 0), font=numbers_font)

        for y in range(200 + (i * 50), 245 + (i * 50)):
            color = tuple(
                int(img.getpixel((((w // 9) + 44), 197 + (i * 50)))[a] + ((255, 255, 255)[a] - img.getpixel((((w // 9) + 44), 197 + (i * 50)))[a]) * (y - (200 + (i * 50))) / ((244 + (i * 50)) - (200 + (i * 50)))) for a in range(3)
            )
            draw.line(((((w // 9) + 44), y), (((w // 9) + 47), y)), fill=color)

        if table[player]['shift'] > 0:
            draw.polygon(((((w // 9) + 68), 220 + (i * 50)), (((w // 9) + 80), 220 + (i * 50)), (((w // 9) + 74), 212 + (i * 50))), fill=(0, 255, 0), outline=(0, 255, 0))
        else:
            draw.polygon(((((w // 9) + 68), 220 + (i * 50)), (((w // 9) + 80), 220 + (i * 50)), (((w // 9) + 74), 212 + (i * 50))), fill=(200, 200, 200), outline=(200, 200, 200))

        if table[player]['shift'] < 0:
            draw.polygon(((((w // 9) + 68), 224 + (i * 50)), (((w // 9) + 80), 224 + (i * 50)), (((w // 9) + 74), 232 + (i * 50))), fill=(255, 0, 0), outline=(255, 0, 0))
        else:
            draw.polygon(((((w // 9) + 68), 224 + (i * 50)), (((w // 9) + 80), 224 + (i * 50)), (((w // 9) + 74), 232 + (i * 50))), fill=(200, 200, 200), outline=(200, 200, 200))

        name_h = draw.textsize(player, font=font)[1]
        name_y = 222 + (i * 50) - name_h // 2
        draw.text((((w // 9) + 100), name_y), text=player, fill=(0, 0, 0), font=font)

        text_width, text_height = draw.textsize(str(table[player]['games']), font=numbers_font)
        text_x = ((w - (w // 9)) - 160) - text_width // 2
        text_y = 222 + (i * 50) - text_height // 2
        draw.text((text_x, text_y), text=str(table[player]['games']), fill=(0, 0, 0), font=numbers_font)

        text_width, text_height = draw.textsize(str(table[player]['points']), font=numbers_font)
        text_x = ((w - (w // 9)) - 50) - text_width // 2
        text_y = 222 + (i * 50) - text_height // 2
        draw.text((text_x, text_y), text=str(table[player]['points']), fill=(0, 0, 0), font=numbers_font)

        i = i + 1

    draw.rectangle((((w // 9), 395), ((w - (w // 9)), 400)), fill=(3, 1, 61))
    draw.rectangle((((w // 9), 595), ((w - (w // 9)), 600)), fill=(3, 1, 61))
    img.save('table.png')

    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'lasustennis@gmail.com'
    smtp_password = EMAIL_PASSWORD

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)

    message = MIMEMultipart()
    message['From'] = smtp_username
    message['To'] = 'lasustennis@gmail.com'
    message['Subject'] = f'LADDER GAMES TABLE AS OF DAY {day}'

    with open('table.png', 'rb') as f:
        img_data = f.read()
        image = MIMEImage(img_data, name=f'day{day}_table.png')
        message.attach(image)

    server.sendmail(smtp_username, 'lasustennis@gmail.com', message.as_string())
    server.quit()


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
        weekly_points[f"Day {week.number}"] = all_player_points
    return weekly_points


def get_weekly_points_without_challenge():
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
            all_player_points[player.name] = player_points
        weekly_points[f"Day {week.number}"] = all_player_points
    return weekly_points


def get_cwp_with_players(weekly_points):
    players_in_order = Player.query.order_by(Player.points).all()[::-1]
    cumulative_weekly_points_with_players = {"Day 0": {player.name: 0 for player in players_in_order}}
    for i in range(1, len(weekly_points) + 1):
        cumulative_weekly_points_with_players[f"Day {i}"] = {player.name: 0 for player in players_in_order}
        for j in range(1, i + 1):
            for k in range(len(cumulative_weekly_points_with_players[f"Day {i}"])):
                cumulative_weekly_points_with_players[f"Day {i}"][players_in_order[k].name] += weekly_points[f"Day {j}"][
                    players_in_order[k].name]
    return cumulative_weekly_points_with_players


def get_weekly_matches():
    weekly_matches = {}
    try:
        weeks = Year.query.filter_by(year=datetime.datetime.now().year).first().weeks
    except AttributeError:
        weeks = []
    for week in weeks:
        all_player_matches = {}
        players = Player.query.all()
        for player in players:
            player_matches = 0
            for match in player.matches:
                if match in week.matches:
                    player_matches = player_matches + 1
            all_player_matches[player.name] = player_matches
        weekly_matches[f"Day {week.number}"] = all_player_matches
    return weekly_matches


def get_cwm_with_players(weekly_matches):
    players = Player.query.all()
    cumulative_weekly_matches_with_players = {"Day 0": {player.name: 0 for player in players}}
    for i in range(1, len(weekly_matches) + 1):
        cumulative_weekly_matches_with_players[f"Day {i}"] = {player.name: 0 for player in players}
        for j in range(1, i + 1):
            for k in range(len(cumulative_weekly_matches_with_players[f"Day {i}"])):
                cumulative_weekly_matches_with_players[f"Day {i}"][players[k].name] += weekly_matches[f"Day {j}"][
                    players[k].name]
    return cumulative_weekly_matches_with_players


def get_mpw():
    weekly_points_without_challenge = get_weekly_points_without_challenge()
    mpw = {}
    for i in range(40, 0, -1):
        for week in weekly_points_without_challenge:
            for player in weekly_points_without_challenge[week]:
                if weekly_points_without_challenge[week][player] == i:
                    mpw[f"{player} ({week})"] = i
    return mpw


def get_ppg():
    players_in_order = Player.query.order_by(Player.points).all()[::-1]
    ppg = {}
    for player in players_in_order:
        try:
            ppg[player.name] = round(float((player.points - player.challenge_points) / len(player.matches)), 2)
        except ZeroDivisionError:
            ppg[player.name] = 0
    ppg_in_order = dict(sorted(ppg.items(), key=lambda x: x[1]))
    ppg_in_order = dict(reversed(list(ppg_in_order.items())))
    return ppg_in_order


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
        try:
            wpct[player.name] = round((matches_won / (len(player.matches) - player.challenge_matches)) * 100, 2)
        except ZeroDivisionError:
            wpct[player.name] = 0
    wpct_in_order = dict(sorted(wpct.items(), key=lambda x: x[1]))
    wpct_in_order = dict(reversed(list(wpct_in_order.items())))
    return wpct_in_order


def get_mlgb():
    mlgb = {}
    players = Player.query.all()
    for player in players:
        n = 0
        for match in player.matches:
            if not match.is_challenge:
                match_players = match.players_order.split()
                if len(match_players) == 4:
                    if player.name == match_players[0] or player.name == match_players[1]:
                        if match.score1 == 5:
                            n += 1
                    else:
                        if match.score2 == 5:
                            n += 1
                else:
                    if player.name == match_players[0]:
                        if match.score1 == 5:
                            n += 1
                    else:
                        if match.score2 == 5:
                            n += 1
        mlgb[player.name] = n
    mlgb_in_order = dict(sorted(mlgb.items(), key=lambda x: x[1]))
    mlgb_in_order = dict(reversed(list(mlgb_in_order.items())))
    return mlgb_in_order


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
        for player in match.players:
            match.players.remove(player)
        db.session.delete(match)
        db.session.commit()


@app.route("/")
def home():
    # send_stat(get_mpw(), title='MOST POINTS IN A DAY')
    # send_stat(get_ppg(), title='BEST POINTS PER GAME RATIO')
    # send_stat(get_wpct(), title='BEST LADDER GAMES WIN RATIO')
    # send_stat(get_mlgb(), title='MOST LADDER GAME BAGELS')
    # send_cwp()
    return render_template("index.html")


@app.route("/ladder-games", methods=['GET', 'POST'])
def ladder_games():
    form = HeadToHeadForm()
    with app.app_context():
        player_names = sorted([""] + [player.name for player in Player.query.all()])
    form.player_1.choices = player_names
    form.player_2.choices = player_names
    if request.method == 'POST':
        return redirect(url_for('h2h', p1=form.player_1.data, p2=form.player_2.data))
    with app.app_context():
        players = Player.query.all()

        weekly_points = get_weekly_points()
        cumulative_weekly_points_with_players = get_cwp_with_players(weekly_points)

        mpw = get_mpw()
        ppg = get_ppg()
        wpct = get_wpct()
        mlgb = get_mlgb()

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
                        cumulative_weekly_points_with_players[f"Day {previous_week}"].items(), key=lambda x: x[1]
                    )
                )
                previous_week_arrangement = [cumulative_weekly_points_with_players[f"Day {previous_week}"][x] for x in pwa][::-1]

                cwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Day {current_week}"].items(), key=lambda x: x[1]
                    )
                )
                current_week_arrangement = [cumulative_weekly_points_with_players[f"Day {current_week}"][x] for x in cwa][
                                            ::-1]
            else:
                pwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Day 0"].items(), key=lambda x: x[1]
                    )
                )
                previous_week_arrangement = [cumulative_weekly_points_with_players[f"Day 0"][x] for x in
                                             pwa][::-1]

                cwa = dict(
                    sorted(
                        cumulative_weekly_points_with_players[f"Day {current_week}"].items(), key=lambda x: x[1]
                    )
                )
                current_week_arrangement = [cumulative_weekly_points_with_players[f"Day {current_week}"][x] for x in
                                            cwa][
                                           ::-1]

            for player in players:
                if not player.position:
                    player.position = current_week_arrangement.index(cumulative_weekly_points_with_players[f"Day {current_week}"][player.name]) + 1
                    player.shift = 0
                else:
                    player.position = current_week_arrangement.index(cumulative_weekly_points_with_players[f"Day {current_week}"][player.name]) + 1
                    player.shift = (previous_week_arrangement.index(cumulative_weekly_points_with_players[f"Day {previous_week}"][player.name]) + 1) - player.position
                player.points = cumulative_weekly_points_with_players[f"Day {current_week}"][player.name]
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
        mlgb=mlgb,
        year=datetime.datetime.now().year,
        form=form
    )


@app.route("/head-to-head", methods=['GET', 'POST'])
def h2h():
    player1 = request.args.get('p1')
    player2 = request.args.get('p2')
    form = HeadToHeadForm(player_1=player1, player_2=player2)
    all_matches = Match.query.filter(Match.players_order.contains(player1), Match.players_order.contains(player2))
    matches_all = {
        "singles": {
            "matches": [],
            "played": 0,
            "player1": 0,
            "player2": 0
        },
        "doubles": {
            "matches": [],
            "played": 0,
            "player1": 0,
            "player2": 0
        },
        "teammates": {
            "matches": [],
            "played": 0,
            "won": 0,
        }
    }
    for match in all_matches:
        players = match.players_order.split()
        if len(players) == 2:
            matches_all["singles"]["matches"].append(match)
            if match.score1 > match.score2:
                if player1 == players[0]:
                    matches_all["singles"]["player1"] += 1
                else:
                    matches_all["singles"]["player2"] += 1
            else:
                if player1 == players[1]:
                    matches_all["singles"]["player1"] += 1
                else:
                    matches_all["singles"]["player2"] += 1
        else:
            if sorted([player1, player2]) == sorted(players[0:2]):
                matches_all["teammates"]["matches"].append(match)
                if match.score1 > match.score2:
                    matches_all["teammates"]["won"] += 1
            elif sorted([player1, player2]) == sorted(players[2:]):
                matches_all["teammates"]["matches"].append(match)
                matches_all["teammates"]["played"] += 1
                if match.score1 < match.score2:
                    matches_all["teammates"]["won"] += 1
            else:
                matches_all["doubles"]["matches"].append(match)
                if player1 in players[0:2]:
                    if match.score1 > match.score2:
                        matches_all["doubles"]["player1"] += 1
                    else:
                        matches_all["doubles"]["player2"] += 1
                else:
                    if match.score1 < match.score2:
                        matches_all["doubles"]["player1"] += 1
                    else:
                        matches_all["doubles"]["player2"] += 1
    matches_all["singles"]["played"] = len(matches_all["singles"]["matches"])
    matches_all["doubles"]["played"] = len(matches_all["doubles"]["matches"])
    matches_all["teammates"]["played"] = len(matches_all["teammates"]["matches"])
    with app.app_context():
        player_names = sorted([""] + [player.name for player in Player.query.all()])
    form.player_1.choices = player_names
    form.player_2.choices = player_names
    if request.method == 'POST':
        return redirect(url_for('h2h', p1=form.player_1.data, p2=form.player_2.data))
    return render_template('head2head.html', form=form, h2h=matches_all, year=datetime.datetime.now().year)


@app.route("/join", methods=['GET', 'POST'])
def join():
    form = JoinForm()
    if request.method == 'POST':
        name = form.name.data
        phone_no = form.phone_no.data
        experience = form.experience.data
        send_member_request(name, phone_no, experience)
        flash("Your details have been sent to the board! You will be gotten back to.")
        return redirect(url_for('home'))
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
                if len(Week.query.all()) != 1:
                    send_week_result(Week.query.all()[-1].number)
                    send_table(Week.query.all()[-1].number)
                new_week = Week(number=week, first_saturday=datetime.datetime.now().strftime("%d %B"))
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
                if len(Week.query.all()) != 1:
                    send_week_result(Week.query.all()[-1].number)
                    send_table(Week.query.all()[-1].number)
                new_week = Week(number=week, first_saturday=datetime.datetime.now().strftime("%d %B"))
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
                    first_player.challenge_points += new_match.points_gained
                    first_player.points = second_player.points
            else:
                if first_player.points > second_player.points:
                    new_match.points_gained = first_player.points - second_player.points
                    second_player.challenge_points += new_match.points_gained
                    second_player.points = first_player.points
            yr = Year.query.filter_by(year=form_year).first()
            if len(yr.weeks) > 0:
                weeks_in_years = [wk.number for wk in yr.weeks]
            else:
                weeks_in_years = []
            if week in weeks_in_years:
                new_match.week = Week.query.filter_by(number=week).first()
            else:
                if len(Week.query.all()) != 1:
                    send_week_result(Week.query.all()[-1].number)
                    send_table(Week.query.all()[-1].number)
                new_week = Week(number=week, first_saturday=datetime.datetime.now().strftime("%d %B"))
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
        name = form.name.data.strip()
        full_name = form.full_name.data
        rank = form.rank.data
        with app.app_context():
            new_player = Player(name=name, full_name=full_name, points=0, challenge_points=0, challenge_matches=0)
            if rank in range(1, 9):
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


@app.route("/get-games", methods=['GET', 'POST'])
@admin_only
def get_games():
    weeks = [" "] + [week.number for week in Week.query.all()]
    form = WeekForm(week=weeks[-1])
    form.week.choices = weeks
    if form.validate_on_submit():
        send_week_result(int(form.week.data))
        flash("Check the official email for what you requested.")
        return redirect(url_for("admin"))
    return render_template('get-games.html', form=form)


@app.route("/get-table", methods=['GET', 'POST'])
@admin_only
def get_table():
    weeks = [" "] + [week.number for week in Week.query.all()]
    form = WeekForm(week=weeks[-1])
    form.week.choices = weeks
    if form.validate_on_submit():
        send_table(int(form.week.data))
        flash("Check the official email for what you requested.")
        return redirect(url_for("admin"))
    return render_template('get-table.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)
