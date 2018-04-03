from app import db
from app.main.forms import PostForm, SearchForm, EditAddressForm
from app.helper import clean_list, normalize, convertArrayToString, convertStringToArray
from app.main import bp
from app.models import User, Post, Project, Address
from app.service import GravatarXMLRPC
from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, g
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from guess_language import guess_language
from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

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
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        post = Post(body=form.body.data, author=current_user, language=language)
        db.session.add(post)
        db.session.commit()
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

# @bp.route('edit_address/<address_id>', methods=['GET', 'POST'])
# @login_required
# def edit_project(project_id):
#     address = Address.query.filter_by(id=address_id).first_or_404()
#     form = EditAddressForm()
#     if form.validate_on_submit():
#         project.name = form.name.data
#         project.headline = form.headline.data
#         project.description = form.description.data
#         project.completion_date = form.completion_date.data
#         project.status = form.status.data
#         project.tags = convertArrayToString(form.tags.data)
#         address = Address.query.get(project.address_id)
#         address.address1 = form.address1.data
#         address.address2 = form.address2.data
#         address.city = form.city.data
#         address.state = form.state.data
#         address.zipcode = form.zipcode.data
#         address.country = form.country.data
#         address.full_address =
#         address.lat = form.lat.data
#         address.lng = form.lng.data
#         address.
#         db.session.commit()
#         flash('Your changes have been saved.')
#         return redirect(url_for('project.project', project_id=project.id))
#     elif request.method == 'GET':
#         form.name.data = project.name
#         form.headline.data = project.headline
#         form.description.data = project.description
#         form.completion_date.data = project.completion_date
#         form.status.data = project.status
#         form.address1.data = project.site.address1
#         form.address2.data = project.site.address2
#         form.city.data = project.site.city
#         form.state.data = project.site.state
#         form.zipcode.data = project.site.zipcode
#         form.country.data = project.site.country
#     return render_template('project/edit_project.html', title='Edit Project',
#                            form=form)


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

@bp.route('/search/address')
@login_required
def search_address():
    if not g.search_form.validate():
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    addresses, total = Address.search(g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])
    next_url = url_for('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title='Search', addresses=addresses, next_url=next_url, prev_url=prev_url)

@bp.route('/reply', methods=['GET'])
@login_required
def reply_post():
    return jsonify({'text': '{{ wtf.quick_form(form) }}'})

@bp.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        filename = photos.save(request.files['photo'])
        return filename
    return render_template('upload.html')

@bp.route('/map', methods=['GET', 'POST'])
def mapview():
    # creating a map in the view
    mymap = Map(
        identifier="view-side",
        lat=37.4419,
        lng=-122.1419,
        markers=[(37.4419, -122.1419)]
    )
    sndmap = Map(
        identifier="sndmap",
        lat=37.4419,
        lng=-122.1419,
        markers=[
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
             'lat': 37.4419,
             'lng': -122.1419,
             'infobox': "<b>Hello World</b>"
          },
          {
             'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
             'lat': 37.4300,
             'lng': -122.1400,
             'infobox': "<b>Hello World from other place</b>"
          }
        ]
    )
    return render_template('example.html', mymap=mymap, sndmap=sndmap)
