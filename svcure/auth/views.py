import functools

from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from svcure import db
from svcure.auth.models import User
# from svcure.annotations.models import StaticFiles, Genomes, Variants, Annotations

# executemany:
from sqlalchemy.sql.expression import bindparam


bp = Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    user_id = session.get("user_id")
    g.user = User.query.get(user_id) if user_id is not None else None


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."
        elif db.session.query(
            User.query.filter_by(username=username).exists()
        ).scalar():
            error = f"User {username} is already registered."

        if error is None:
            # the name is available, create the user and go to the login page
            db.session.add(User(username=username, password=password))
            db.session.commit()

            # # pre-populate annotations table:
            # # insert ids into annotations table; get ids from variants:
            # # HERE: GET ONE USER'S ANNOTATIONS TABLE COLS AS SHWON BELOW.
            # # USING THESE COLS BUT G.USER.ID AND G.USER.USERNAME, INSERT INTO ANNOTATIONS
            # # IGNORE TMP_DATA
            # # tmp = db.session.query(Variants.id,Variants.genome).all()
            # # temp_data = [
            # #     {
            # #         'genome':i[1], 
            # #         'static_file_id':static_id,
            # #         'user_id':g.user.id,
            # #         'user_name':g.user.username,
            # #         'variant_id':i[0]
            # #     } for i in tmp
            # # ]

            # # executemany:
            # statement = Annotations.__table__.insert().prefix_with('OR IGNORE').values({
            #         'genome' : bindparam('genome'),
            #         'static_file_id' : bindparam('static_file_id'),
            #         'user_id' : bindparam('user_id'),
            #         'user_name' : bindparam('user_name'),
            #         'variant_id' : bindparam('variant_id'),
            #         })
            # db.session.execute(statement, temp_data)
            # db.session.commit()

            return redirect(url_for("auth.login"))

        flash(error)

    return render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        error = None
        user = User.query.filter_by(username=username).first()

        if user is None:
            error = "Incorrect username."
        elif not user.check_password(password):
            error = "Incorrect password."

        if error is None:
            # store the user id in a new session and return to the index
            session.clear()
            session["user_id"] = user.id
            return redirect(url_for("index"))

        flash(error)

    return render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    session.clear()
    return redirect(url_for("index"))
