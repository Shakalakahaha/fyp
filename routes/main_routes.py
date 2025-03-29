from flask import Blueprint, render_template

bp = Blueprint('main', __name__)

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html') 