from app import db
from app.main.forms import PostForm, SearchForm, EditAddressForm, TaggingForm, DemoForm
from app.helper import clean_list, normalize, convertArrayToString, convertStringToArray, allowed_file, tryconvert
from app.main import bp
from app.models import User, Post, Project, ProjectImage, Address, Link, Tag
from app.service import *
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, g, session
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from guess_language import guess_language
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map
import geocoder
import re

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.body.data, author=current_user, language=language)
        post.save()
        flash('Your post is now live!')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('main.index', page=posts.next_num) \
        if posts.has_next else None
    prev_num = url_for('main.index', page=posts.prev_num) \
        if posts.has_prev else None
    # projects = current_user.followed_projects().all()
    return render_template('index.html', title='Home', form=form, posts=posts.items, next_url=next_url, prev_num=prev_num)

@bp.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    posts, total = Post.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', posts=posts, next_url=next_url, prev_url=prev_url)

# @bp.route('/search/address')
# @login_required
# def search_address():
#     if not g.search_form.validate():
#         return redirect(url_for('main.index'))
#     page = request.args.get('page', 1, type=int)
#     addresses, total = Address.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
#     next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
#         if total > page * current_app.config['POSTS_PER_PAGE'] else None
#     prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
#         if page > 1 else None
#     return render_template('search.html', title='Search', addresses=addresses, next_url=next_url, prev_url=prev_url)

@bp.route('/reply-form', methods=['POST'])
@login_required
def reply_form():
    form = PostForm()
    form.parent_id.data = request.form['parent_id']
    return render_template('_comment.html', form=form)

@bp.route('/reply-post', methods=['POST'])
@login_required
def reply_post():
    print('INSIDE REPLY_POST')
    form = PostForm(request.form)
    language = guess_language(form.body.data)
    if language == 'UNKNOWN' or len(language) > 5:
        language = ''
    parent = Post.query.filter_by(path=form.parent_id.data).first()
    post = Post(body=form.body.data, parent=parent, author=current_user, language=language)
    post.save()
    flash('Your post is now live!')
    return redirect(url_for('main.index'))

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    aws = AWS_api()
    user = User.query.filter_by(username=current_user.username).first()
    if request.method == 'POST' and 'user_file' in request.files:
        doc = request.files['user_file']
        if doc.filename == '':
            flash('No selected file.')
            return redirect(url_for('main.upload'))
        if doc and allowed_file(doc.filename):
            doc.filename = secure_filename(doc.filename)
            output = aws.upload_file_to_s3(doc, current_app.config['S3_BUCKET_NAME'])
            flash('Your file, {}, has been uploaded to S3'.format(str(output)))
            return redirect(url_for('main.index'))
        # filename = photos.save(request.files['photo'])
            # return filename
    return render_template('upload.html')


@bp.route('/save-tags/', methods=['POST'])
def save_tags(asset):
    form = TaggingForm(request.form)
    tags_data_array = list(map(lambda v: tryconvert(v, v, int), convertStringToArray(form.tags.data)))

    for element in tags_data_array:
        exists = db.session.query(db.exists().where(Tag.id == element)).scalar()
        if not exists:
            # TODO: Defaulting category_id to 0; Either create a logic that can self categorize itself or create a process so that tags are created are automatically in a "bucket" category
            tag = Tag(category_id=0, name=element)
            db.session.add(tag)
        asset.add_tag(tag)
    db.session.commit()
    # return redirect(url_for("main.tag"))


@bp.route("/demo", methods=["GET", "POST"])
def demo():
    form = DemoForm(request.form)
    if form.validate_on_submit():
        current_app.logger.debug(form.data)
    return render_template("demo.html", form=form)


@bp.route("/tag")
def tag():
    form = TaggingForm(request.form)
    # tags_choices_all, tags_choices = get_tags_choices()
    # form.tags_field.choices = tags_choices_all
    # form.tags_field.default = [id for id, title in tags_choices]
    # form.tags_field.process(request.form)
    # return render_template("example.html", form=form)
    if form.validate_on_submit():
        current_app.logger.debug(form.data)
    return render_template("example.html", form=form)
