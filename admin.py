from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import User, Team, Quiz, Question, QuestionInQuiz
from app import db
import random
import sendgrid
import os
from statistics import mean
from sendgrid.helpers.mail import Email, Content, Mail, To


admin = Blueprint('admin', __name__)


quiz_states = ['new', 'available', 'finished']

next_state = {
    'new': 'available',
    'available': 'finished',
    'finished': None
}


@admin.route('/admin')
@login_required
def index():
    if current_user.is_admin_user():
        teams = Team.query.filter_by(answers_questions=1).all()
        surveys = sorted([
            {
                'id': l.id,
                'name': l.name,
                'state': l.state,
                'question_count': len(l.questions),
                'respondents': len(set(sum([[ans.user_id for ans in qiq.answers] for qiq in l.questions], []))),
                'next_state': next_state[l.state]
            } for l in Quiz.query.all()], key=lambda s: (quiz_states.index(s['state']), -s['id']))
        all_teams = [{
            'id': t.id,
            'name': t.name,
            'state': 'Accepts Answers' if t.answers_questions == 1 else 'Guest',
            'member_count': len(t.users)
        } for t in Team.query.all()]
        users = sorted([{
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'checked_in': u.password is not None,
            'team': u.team.name
        } for u in User.query.all()], key=lambda e: e['id'])
        return render_template('admin.html', teams=teams, surveys=surveys, all_teams=all_teams, users=users)
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/quiz/stats/<int:quiz_id>')
@login_required
def stats(quiz_id):
    if current_user.is_admin_user():
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        if quiz is not None:
            team_summary = [
                {
                    'team': t.name,
                    'questions': [
                        {
                            'question': q.question.question,
                            'answers': [float(a.value) for a in q.answers if a.team_id == t.id]
                        } for q in QuestionInQuiz.query.filter_by(quiz_id=quiz.id).all()
                    ]
                } for t in Team.query.filter_by(answers_questions=1).all()
            ]
            print(team_summary)
            team_tops = []
            for team in team_summary:
                for question in team['questions']:
                    if len(question['answers']) > 0:
                        question['average'] = mean(question['answers'])
                        question['average_rd'] = '%.2f' % question['average']
                if len([q for q in team['questions'] if 'average' in q]) >= 6:
                    team['questions'] = sorted([q for q in team['questions'] if 'average' in q],
                                               key=lambda e: e['average'], reverse=True)
                    team_tops.append({
                        'team': team['team'],
                        'top': team['questions'][:3],
                        'bottom': team['questions'][-3:]
                    })
            print(team_tops)
            return render_template('stats.html', quiz_name=quiz.name, tops=team_tops)
        else:
            flash('No available surveys', 'error')
            return redirect(url_for('main.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/quiz/create', methods=['POST'])
@login_required
def quiz_create_post():
    quiz_name = request.form.get('survey_name')
    if current_user.is_admin_user():
        new_quiz = Quiz(name=quiz_name, state='new')
        db.session.add(new_quiz)
        db.session.commit()
        flash('Survey %s created successfully!' % quiz_name, 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/user/create', methods=['POST'])
@login_required
def user_create_post():
    user_name = request.form.get('user_name')
    email = request.form.get('email')
    team_label = request.form.get('team')
    if current_user.is_admin_user():
        user = User.query.filter_by(email=email).first()
        team = Team.query.filter_by(id=int(team_label[2:])).first()
        if user:
            flash('Email already registered', 'error')
            return redirect(url_for('admin.index'))
        if not team:
            flash('Team selection failed', 'error')
            return redirect(url_for('admin.index'))
        new_user = User(name=user_name, email=email, rec_key="%032x" % random.getrandbits(128), team_id=team.id)
        db.session.add(new_user)
        db.session.commit()

        sg = sendgrid.SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
        from_email = Email("Instant Ink Survey <bsilvaguedes@gmail.com>")
        subject = "Instant Ink Survey"
        to_email = To(new_user.email)
        msg = 'Click here to proceed with the registration:'
        url = '%slogin/redefine?code=%s' % (request.host_url, new_user.rec_key)
        content = Content("text/html", '%s <br/><br/><a href="%s">%s</a>' % (msg, url, url))
        mail = Mail(from_email, to_email, subject, content)
        sg.client.mail.send.post(request_body=mail.get())
        flash('Instructions sent to %s (%s)' % (user_name, email), 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/user/team', methods=['POST'])
@login_required
def user_change_team():
    if current_user.is_admin_user():
        user_id = int(request.form.get('user_id'))
        user = User.query.filter_by(id=user_id).first()
        team_label = request.form.get('team')
        team = Team.query.filter_by(id=int(team_label[2:])).first()
        user.team_id = team.id
        db.session.commit()
        flash('Moved %s to %s successfully' % (user.name, team.name), 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/question/create', methods=['POST'])
@login_required
def question_create_post():
    question_name = request.form.get('question_name')
    question_category = request.form.get('question_category')
    if current_user.is_admin_user():
        new_quiz = Question(question=question_name, category=question_category)
        db.session.add(new_quiz)
        db.session.commit()
        flash('Question added successfully!', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/quiz/question/add', methods=['POST'])
@login_required
def add_question():
    quiz_id = int(request.form.get('quiz_id'))
    question_id = int(request.form.get('question_id'))
    if current_user.is_admin_user():
        try:
            new_qiq = QuestionInQuiz(question_id=question_id, quiz_id=quiz_id)
            db.session.add(new_qiq)
            db.session.commit()

            flash('Question added successfully', 'success')
            return redirect(url_for('admin.edit_quiz', quiz_id=quiz_id))
        except:
            flash('Please check your data', 'error')
            return redirect(url_for('admin.edit_quiz', quiz_id=quiz_id))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/team/create', methods=['POST'])
@login_required
def team_create_post():
    team_name = request.form.get('question_name')
    answers_questions = 1 if request.form.get('participation') == 'yes' else 0
    if current_user.is_admin_user():
        new_team = Team(name=team_name, answers_questions=answers_questions)
        db.session.add(new_team)
        db.session.commit()
        flash('Team %s added successfully!' % team_name, 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/quiz/edit/<int:quiz_id>')
@login_required
def edit_quiz(quiz_id):
    if current_user.is_admin_user():
        quiz = Quiz.query.filter_by(id=quiz_id).first()
        questions = list(Question.query.all())
        possible_questions = sorted([q for q in questions if not quiz.has_question(q.id)], key=lambda e: e.category)
        current_questions = sorted([q.question for q in quiz.questions], key=lambda e: e.category)
        return render_template('edit_quiz.html', quiz=quiz, possible_questions=possible_questions,
                               current_questions=current_questions)
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/team/flip', methods=['POST'])
@login_required
def flip_team_state():
    if current_user.is_admin_user():
        team_id = int(request.form.get('team_id'))
        team = Team.query.filter_by(id=team_id).first()
        team.answers_questions ^= 1
        db.session.commit()
        flash('Flipped team state successfully', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))


@admin.route('/quiz/up', methods=['POST'])
@login_required
def quiz_up():
    quiz_id = request.form.get('id')
    if current_user.is_admin_user():
        quiz = Quiz.query.filter_by(id=int(quiz_id)).first()
        if quiz.state == 'new':
            quiz.state = 'available'
        elif quiz.state == 'available':
            quiz.state = 'finished'
        else:
            flash('Cannot change quiz state', 'error')
            return redirect(url_for('admin.index'))
        db.session.commit()
        flash('Quiz state changed successfully', 'success')
        return redirect(url_for('admin.index'))
    else:
        flash('User is not an admin', 'error')
        return redirect(url_for('main.profile'))
