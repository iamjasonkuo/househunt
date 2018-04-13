from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, g
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from app.helper import clean_list, normalize, convertArrayToString, convertStringToArray, prepFullAddressSearch, Marker, Error, tryconvert
from app.project import bp
from app.models import User, Post, Project, ProjectImage, Address, Link, Tag
from app.main.forms import SearchForm, PostForm
from app.project.forms import ProjectCreateInitialForm, EditProjectForm, ProjectFilterForm
from app.service import GoogleMaps_api
from datetime import datetime
from guess_language import guess_language
from flask_googlemaps import GoogleMaps, Map
import geocoder


@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

def save_tags(asset):
    form = ProjectCreateInitialForm(request.form)
    tags_data_array = list(map(lambda v: tryconvert(v, v, int), convertStringToArray(form.tags.data)))

    for element in tags_data_array:
        exists = db.session.query(db.exists().where(Tag.id == element)).scalar()
        if not exists:
            # TODO: Defaulting category_id to 0; Either create a logic that can self categorize itself or create a process so that tags are created are automatically in a "bucket" category.
            # BUG: Newly created tags' name property is not visible from admin panel. Name is however viewable from app view.
            tag = Tag(category_id=0, name=element)
            db.session.add(tag)
        else:
            tag = Tag.query.get(element)
        asset.add_tag(tag)
    db.session.commit()

@bp.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    geo = geocoder.ip('me')
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    filtered = list(filter(lambda x: x.site.lat != None, projects.items))
    # avgLat = sum(project.site.lat for project in filtered)/len(filtered)
    avgLat = geo.latlng[0]
    # avgLng = sum(project.site.lng for project in filtered)/len(filtered)
    avgLng = geo.latlng[1]

    #TODO: Preset center and markers according to filter
    mymap = Map(
    identifier="view-map",
    lat=avgLat,
    lng=avgLng,
    markers=[(project.site.lat, project.site.lng) for project in filtered],
    style="height:400px;width:100%;margin:0;"
    )
    print('#### mymap: {}'.format(mymap.__dict__))

    next_url = url_for('project.explore', page=projects.next_num) \
        if projects.has_next else None
    prev_url = url_for('project.explore', page=projects.prev_num) \
        if projects.has_prev else None
    return render_template('index.html', title='Explore', projects=projects.items, next_url=next_url, prev_url=prev_url, mymap=mymap)

@bp.route('/timeline/<address_id>')
def view_timeline(address_id):
    # address = Address.query.filter_by(id=address_id).first()
    projects = Project.query.filter_by(address_id=address_id)
    return render_template('index.html', title='Timeline')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_authenticated:
        flash('You need to be a registered user to create projects.')
        return redirect(url_for('main.index'))
    form = ProjectCreateInitialForm()
    if form.validate_on_submit():
        g = GoogleMaps_api()
        citystate = form.city.data + ' ' + form.state.data
        full_address = prepFullAddressSearch(form.address1.data, form.address2.data, citystate, form.zipcode.data)
        exists = db.session.query(db.exists().where(Address.full_address == full_address)).scalar()
        if not exists:
            print('form address1: {}, form city: {}, form state: {}'.format(form.address1.data, form.city.data, form.state.data))
            geocode = g.getGeocode(form.address1.data, form.city.data, form.state.data)
            address = Address(address1=form.address1.data, address2=form.address2.data, city=form.city.data, state = form.state.data, zipcode=form.zipcode.data, country=form.country.data, full_address=full_address, lat=geocode['lat'], lng=geocode['lng'])
            db.session.add(address)
        else:
            address = Address.query.filter_by(full_address=full_address).first()
        project = Project(name=form.name.data, creator=current_user, site=address)
        db.session.add(project)
        save_tags(project)
        # for tag in form.tags.data:
        #     # check if tag exists in database
        #     #if exists then add tag to project
        #     project.add_tag(tag)
        #     #if doesn't exists then create tag
        #     # add tag to project
        db.session.commit()
        flash('Congratulations, you just created a project and address!')
        return redirect(url_for('project.project', project_id=project.id))
    return render_template('project/create.html', title='Create', form=form)

@bp.route('/<project_id>', methods=['GET', 'POST'])
def project(project_id):
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        project = Project.query.filter_by(id=project_id).first_or_404()
        post = Post(body=form.body.data, author=current_user, post_project=project, language=language)
        post.save()
        flash('Your post is now live!')
        return redirect(url_for('project.project', project_id=project_id))
    page = request.args.get('page', 1, type=int)
    project = Project.query.filter_by(id=project_id).first_or_404()
    user = User.query.filter_by(username=project.creator.username).first()
    mymap = Map(
    identifier="view-map",
    lat=project.site.lat,
    lng=project.site.lng,
    markers=[(project.site.lat, project.site.lng)],
    style="height:400px;width:100%;margin:0;",
    fit_markers_to_bounds = True
    )
    posts = project.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('project.project', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('project.project', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('project/project.html', user=user, project=project, form=form, posts=posts.items, next_url=next_url, prev_url=prev_url, mymap=mymap)


@bp.route('/image/<id>', methods=['GET', 'POST'])
def viewProjectImage(id):
    project_image = ProjectImage.query.filter_by(id=id).first()
    return project_image.image_url

#TODO: Include Photo submission and refactor this. There has to be a better way to do this.
@bp.route('edit_project/<project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    form = EditProjectForm(project.name)
    if form.validate_on_submit():
        project.name = form.name.data
        project.headline = form.headline.data
        project.description = form.description.data
        project.completion_date = form.completion_date.data
        project.status = form.status.data
        project.tags = convertArrayToString(form.tags.data)
        address = Address.query.get(project.address_id)
        address.address1 = form.address1.data
        address.address2 = form.address2.data
        address.city = form.city.data
        address.state = form.state.data
        address.zipcode = form.zipcode.data
        address.country = form.country.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('project.project', project_id=project.id))
    elif request.method == 'GET':
        form.name.data = project.name
        form.headline.data = project.headline
        form.description.data = project.description
        form.completion_date.data = project.completion_date
        form.status.data = project.status
        form.address1.data = project.site.address1
        form.address2.data = project.site.address2
        form.city.data = project.site.city
        form.state.data = project.site.state
        form.zipcode.data = project.site.zipcode
        form.country.data = project.site.country
    return render_template('project/edit_project.html', title='Edit Project',
                           form=form)

@bp.route('/favorite/<project_id>')
@login_required
def favorite(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project is None:
        flash('Project not found.')
        return redirect(url_for('project.project', project_id=project_id))
    if current_user.is_favorited(project):
        flash('You already favorited this project.')
        return redirect(url_for('project.project', project_id=project_id))
    current_user.favorite(project)
    db.session.commit()
    flash('You favorited this project!')
    return redirect(url_for('project.project', project_id=project_id))

@bp.route('/unfavorite/<project_id>')
@login_required
def unfavorite(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project is None:
        flash('Project not found.')
        return redirect(url_for('project.project', project_id=project_id))
    if not current_user.is_favorited(project):
        flash('You already unfavorited this project.')
        return redirect(url_for('project.project', project_id=project_id))
    current_user.unfavorite(project)
    db.session.commit()
    flash('You unfavorited this project!')
    return redirect(url_for('project.project', project_id=project_id))

##TODO: The contribution feature will need to be refactored; Feature will need the following: 1) contribution request form will need to allow users to indicate which project they are trying to contribute to and attach proof of contribution, 2) send email to platform support for verification, 3) support to send email back to approve or decline contribution request, 4) verified contributors will be identified as verified
@bp.route('/contribute/<project_id>')
@login_required
def contribute(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project is None:
        flash('Project not found.')
        return redirect(url_for('project.project', project_id=project_id))
    if current_user.has_contributed(project):
        flash('You already unfavorited this project.')
        return redirect(url_for('project.project', project_id=project_id))
    current_user.contribute(project)
    db.session.commit()
    flash('You contributed to this project!')
    return redirect(url_for('project.project', project_id=project_id))

@bp.route('/uncontribute/<project_id>')
@login_required
def uncontribute(project_id):
    project = Project.query.filter_by(id=project_id).first()
    if project is None:
        flash('Project not found.')
        return redirect(url_for('project.project', project_id=project_id))
    if not current_user.has_contributed(project):
        flash('You already uncontributed this project.')
        return redirect(url_for('project.project', project_id=project_id))
    current_user.uncontribute(project)
    db.session.commit()
    flash('You uncontributed to this project!')
    return redirect(url_for('project.project', project_id=project_id))
