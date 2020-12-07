# main.py

from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import Quiz, QuestionInQuiz, Answer, Question
from app import db
from itertools import groupby
from ii_eval_2020 import evaluate_string


main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/profile')
@login_required
def profile():
    available_quiz = Quiz.query.filter_by(state='available').first()
    if available_quiz is not None:
        questions = sorted([qiq.question for qiq in available_quiz.questions if not qiq.is_answered(current_user)],
                           key=lambda e: e.category)
        groups = [{
                    'category': cat,
                    'questions': [q for q in qst]
                  } for cat, qst in groupby(questions, key=lambda x: x.category)]
        return render_template('profile.html',
                               name=current_user.name,
                               team=current_user.team.name,
                               count=len(groups),
                               categories=groups,
                               quiz_id=available_quiz.id)
    else:
        flash('No surveys available right now', 'error')
        return render_template('profile.html', name=current_user.name, team=current_user.team.name,
                               count=0, categories=[], quiz_id=0)


@main.route('/quiz/answer', methods=['POST'])
@login_required
def answer_post():
    quiz_id = int(request.form.get('quiz_id'))
    if Quiz.query.filter_by(id=quiz_id).first().state == 'available':
        for obj in request.form:
            if obj != 'quiz_id' and obj[0:2] == 'q_':
                question_id = int(obj[2:])
                question_in_quiz = QuestionInQuiz.query.filter_by(question_id=question_id, quiz_id=quiz_id).first()
                question_type = Question.query.filter_by(id=question_id).first().type
                if question_type == 'ii_awards_2020':
                    answer = request.form.get('q_%i' % question_id)
                    person = evaluate_string(answer)
                    if person is not None:
                        new_answer = Answer(question_in_quiz_id=question_in_quiz.id, user_id=current_user.id,
                                            value=0, team_id=current_user.team_id, comments=person)
                    else:
                        flash('Invalid input', 'error')
                        return redirect(url_for('main.profile'))
                else:
                    answer = int(request.form.getlist(obj)[0])
                    comments = request.form.get('c_%i' % question_id)
                    new_answer = Answer(question_in_quiz_id=question_in_quiz.id, user_id=current_user.id, value=answer,
                                        team_id=current_user.team_id, comments=comments)
                db.session.add(new_answer)
                db.session.commit()
        flash('Sent your answers successfully', 'success')
    else:
        flash('Survey no longer available', 'error')
    return redirect(url_for('main.profile'))
