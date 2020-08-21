# models.py

from flask_login import UserMixin
from app import db


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(100), unique=True)
    answers_questions = db.Column(db.Integer)
    users = db.relationship('User', lazy=True, foreign_keys="User.team_id")


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    name = db.Column(db.String(100), unique=True)
    state = db.Column(db.String(20), nullable=False)
    questions = db.relationship('QuestionInQuiz', lazy=True, foreign_keys="QuestionInQuiz.quiz_id")

    def has_question(self, question_id):
        for q in self.questions:
            if question_id == q.id:
                return True
        return False


class QuestionInQuiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    answers = db.relationship('Answer', lazy=True, foreign_keys="Answer.question_in_quiz_id")
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    quiz = db.relationship("Quiz", back_populates="questions")
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    question = db.relationship("Question", back_populates="quizzes")

    def is_answered(self, user):
        return any(a for a in self.answers if a.user_id == user.id)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    question = db.Column(db.String(100))
    category = db.Column(db.String(100))
    type = db.Column(db.String(100))
    quizzes = db.relationship('QuestionInQuiz', lazy=True, foreign_keys="QuestionInQuiz.question_id")


class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # primary keys are required by SQLAlchemy
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship("User", back_populates="answers")
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team = db.relationship("Team")
    value = db.Column(db.Integer, nullable=False)
    question_in_quiz_id = db.Column(db.Integer, db.ForeignKey('question_in_quiz.id'), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    team = db.relationship("Team", back_populates="users")
    answers = db.relationship('Answer', lazy=True, foreign_keys="Answer.user_id")
    rec_key = db.Column(db.String(1000), nullable=True)
    access_level = db.Column(db.Integer, default=0)

    def is_admin_user(self):
        return self.access_level == 1

