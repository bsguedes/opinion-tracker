# auth.py

from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import User
from app import db
import sendgrid
import os
from sendgrid.helpers.mail import Email, Content, Mail, To
import random


auth = Blueprint('auth', __name__)


@auth.route('/login')
def login():
    return render_template('login.html')


@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    if not user or password is None or not check_password_hash(user.password, password):
        flash('Incorrect email or password')
        return redirect(url_for('auth.login'))

    login_user(user, remember=remember)
    return redirect(url_for('main.profile'))


@auth.route('/signup')
def signup():
    code = request.args.get('code')
    user = User.query.filter_by(rec_key=code).first()
    if user is not None and code is not None and code != '':
        return render_template('redefine.html', email=user.email, code=code)
    else:
        flash('Invalid code', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/login/redefine')
def redefine():
    code = request.args.get('code')
    user = User.query.filter_by(rec_key=code).first()
    if user is not None:
        return render_template('redefine.html', email=user.email, code=code)
    else:
        flash('Invalid code', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/login/redefine', methods=['POST'])
def redefine_post():
    code = request.form.get('code')
    password = request.form.get('password')
    user = User.query.filter_by(rec_key=code).first()
    if code is not None and user is not None:
        user.password = generate_password_hash(password, method='sha256')
        user.rec_key = None
        db.session.commit()
        flash('Password created', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('An error occurred when creating a password', 'error')
        return redirect(url_for('auth.login'))


@auth.route('/login/forgot')
def forgot():
    return render_template('forgot.html')


@auth.route('/login/forgot', methods=['POST'])
def forgot_post():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if user:
        h = random.getrandbits(128)
        user.rec_key = "%032x" % h
        db.session.commit()
        sg = sendgrid.SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
        from_email = Email("Instant Ink Survey <bsilvaguedes@gmail.com>")
        subject = "Password redefinition"
        to_email = To(user.email)
        msg = "Click here to redefine a password:"
        url = '%slogin/redefine?code=%s' % (request.host_url, user.rec_key)
        content = Content("text/html", '%s <br/><br/><a href="%s">%s</a>' % (msg, url, url))
        mail = Mail(from_email, to_email, subject, content)
        sg.client.mail.send.post(request_body=mail.get())
        flash('Recovering instructions sent by email', 'success')
        return redirect(url_for('auth.login'))
    else:
        flash('Cannot find the user', 'error')
        return redirect(url_for('auth.forgot'))

