#! /usr/bin/env python3

import bottle
from beaker.middleware import SessionMiddleware
from cork import Cork

from netcontrol.monitor import MachineMonitor

class MyMailer:
    def send_email(self, addr, subject, text):
        print('Subject: {}'.format(subject))
        print(text)

aaa = Cork('conf', email_sender='bzobl@gmx.net', smtp_url='mail.gmx.net')
aaa.mailer = MyMailer()

app = bottle.app();
session_opts = {
    'session.cookie_expires': True,
    'session.encrypt_key': 'please use a random key and keep it secret!',
    'session.httponly': True,
    'session.timeout': 3600 * 24,  # 1 day
    'session.type': 'cookie',
    'session.validate_key': True,
}
app = SessionMiddleware(app, session_opts)

machines = { 'CompanionCube': { 'ip': '192.168.1.110', 'mac': 'BC:AE:C5:8D:7E:6B' }}

def postd():
    return bottle.request.forms

def post_get(name, default=''):
    return bottle.request.POST.get(name, default).strip()

@bottle.post('/login')
def login():
    username = post_get('username')
    password = post_get('password')
    aaa.login(username, password, success_redirect='/', fail_redirect='/login')

@bottle.route('/user_is_anonymous')
def user_is_anonymous():
    if aaa.user_is_anonymous:
        return 'True'
    return 'False'

@bottle.route('/logout')
def logout():
    aaa.logout(success_redirect='/login')

@bottle.post('/register')
def register():
    user = post_get('username')
    password = post_get('password')
    email = post_get('email_address')
    aaa.register(user, password, email)
    return 'Please check your mailbox'

@bottle.route('/validate_registration/:registration_code')
def validate_registration(registration_code):
    aaa.validate_registration(registration_code)
    return 'Thanks. <a href="/login">login</a>'

@bottle.route('/reset_password')
def send_password_reset_mail():
    aaa.send_password_reset_mail(username=post_get('username'), email_addr=post_get('email_address'))
    return 'Check your mailbox'

@bottle.route('/change_password/:reset_code')
@bottle.view('password_change_form')
def change_password(reset_code):
    return dict(reset_code=reset_code)

@bottle.route('/change_password')
def change_password():
    aaa.reset_password(post_get('reset_code'), post_get('password'))
    return 'Thanks. <a href="/login">login</a>'

@bottle.route('/my_role')
def show_current_user_role():
    session = bottle.request.environ.get('beaker.session')
    print('Session: {!r}'.format(session))
    aaa.require(fail_redirect('/login'))
    return aaa.current_user.role

@bottle.route('/login')
@bottle.view('login_form')
def login_from():
    return {}

def get_machine(name):
    if not name in machines:
        return None
    return MachineMonitor(name, mac=machines[name]['mac'], ip=machines[name]['ip'])

def restricted(func, role='user'):
    def f(*args, **kwargs):
        aaa.require(role=role, fail_redirect='/login')
        return func(*args, **kwargs)
    return f

@bottle.route('/')
@bottle.view('machines')
@restricted
def index():
    return dict(machines=machines)

@bottle.route('/machines/<machine_name>')
@restricted
def machine_overview(machine_name):
    machine = get_machine(machine_name)
    if machine:
        return bottle.template('machine_overview', machine=machine)
    return 'Machine {} does not exist'.format(machine_name)

@bottle.route('/machines/<machine_name>/wakeup')
@restricted
def machine_wakeup(machine_name):
    machine = get_machine(machine_name)
    if machine:
        machine.wakeup()
        return "Woke up {}".format(machine_name)
    return bottle.template('Machine {{machine_name}} does not exist', machine_name=machine_name)

bottle.run(app, host='localhost', port=8080, debug=True)
