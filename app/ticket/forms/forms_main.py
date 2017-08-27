#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

import bcrypt
from flask import g
from flask_wtf import FlaskForm
from wtforms import (PasswordField,
                     StringField,
                     FileField)
from wtforms.validators import (DataRequired,
                                Length,
                                EqualTo)

#from app.ticket.models import (FlicketUser, user_field_size)
from app.models.users import User

from flask_user import current_user


def check_password_formatting(form, field):
    """
    Check formatting of password.
    :param field:
    :return True / False:
    """
    ok = True
    min = 6
    if len(field.data) < min:
        field.errors.append('Password must be more than {} characters.'.format(min))
        ok = False
    if not any(s.isupper() for s in field.data) and not any(s.islower() for s in field.data):
        field.errors.append('Password must contain upper and lower characters.')
        ok = False

    return ok


def check_password(form, field):
    """
    Check formatting of password.
    :param form:
    :param field:
    :return True / False:
    """
    ok = True
    result = User.query.filter_by(email=current_user.email).first()
    if bcrypt.hashpw(form.password.data.encode('utf-8'), result.password) != result.password:
        field.errors.append('Entered password is incorrect.')
        return False
    return ok


class CheckPasswordCorrect:
    """
    Check that the entered password matches that in the database.
    """
    def __call__(self, form, field):
        self.username = form.username.data
        self.password = form.password.data
        self.password = self.password.encode('utf-8')
        ok = True
        user = User.query.filter_by(email=form.username.data).first()
        # hashed = user.password
        if user and not bcrypt.hashpw(self.password, user.password) == user.password:
            field.errors.append('Your username and password do not match those in the database.')
            ok = False

        return ok

class ConfirmPassword(FlaskForm):
    password = PasswordField('password',
                             validators=[DataRequired(),
                                         check_password
                                         ])
