import sys
sys.path.insert(0, '/var/www/basic-flask-app')

activate_this= '/home/user/.local/share/virtualenvs/user-5PivF_Od/bin/activate_this.py'

with open(activate_this) as file_:
        exec(file_.read(), dict(_file_=activate_this))


from app import app as application
