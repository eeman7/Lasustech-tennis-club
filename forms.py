import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField
from wtforms.validators import DataRequired


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
