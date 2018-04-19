from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, g, send_from_directory
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from app.helper import clean_list, normalize, convertArrayToString, convertStringToArray, prepFullAddressSearch, Marker, Error, tryconvert, allowed_file
from app.project import bp
from app.models import User, Post, Project, ProjectImage, Address, Link, Tag, UserRole
from app.main.forms import PostForm, SearchForm, EditAddressForm, TaggingForm, DemoForm, ReviewForm, HiddenDataForm
from app.project.forms import ProjectCreateInitialForm, EditProjectForm, ProjectFilterForm, PhotoForm
from app.service import GoogleMaps_api, AWS_api
from datetime import datetime
from guess_language import guess_language
from flask_googlemaps import GoogleMaps, Map
import geocoder
import os
import flask_s3
import boto3

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

def save_tags(asset, func):
    # form = ProjectCreateInitialForm(request.form)
    form = func(request.form)
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

    next_url = url_for('project.explore', page=projects.next_num) \
        if projects.has_next else None
    prev_url = url_for('project.explore', page=projects.prev_num) \
        if projects.has_prev else None
    return render_template('index.html', title='Explore', projects=projects.items, next_url=next_url, prev_url=prev_url, mymap=mymap)

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
        save_tags(project, ProjectCreateInitialForm)
        db.session.commit()
        flash('Congratulations, you just created a project and address!')
        return redirect(url_for('project.upload', project_id=project.id))
    return render_template('project/create.html', title='Create', form=form)

@bp.route('/upload', methods=['GET', 'POST'])
def upload(*args, **kwargs):
    form = HiddenDataForm()
    form.data.data = request.args.get('project_id') or args
    if request.method == 'POST':
        for key, f in request.files.items():
            if key.startswith('file'):
                f.save(os.path.join(current_app.config['UPLOADED_PATH'], 'project{}-{}'.format(form.data.data, f.filename)))
        #TODO: Give user opportunity to add more image related data here
        if form.validate_on_submit():
            s3 = boto3.client(
                "s3",
                aws_access_key_id=current_app.config['S3_ACCESS_KEY'],
                aws_secret_access_key=current_app.config['S3_SECRET_ACCESS_KEY']
            )
            project = Project.query.filter_by(id=form.data.data).first()
            uploadFileNames = []
            sourceDir = os.path.join(current_app.config['APP_ROOT'], 'app/static/uploads/')
            for (sourceDir, dirname, filename) in os.walk(sourceDir):
                uploadFileNames.extend(filename)
                break
            for filename in uploadFileNames:
                sourcepath = sourceDir + filename
                print('########### SOURCEPATH: {}'.format(sourcepath))
                with open(sourcepath, 'rb') as data:
                    s3.upload_fileobj(
                        data,
                        current_app.config['S3_BUCKET_NAME'],
                        filename,
                        ExtraArgs={
                            "ACL": 'public-read',
                            "ContentType": filename.rsplit('.', 1)[1].lower()
                        }
                    )
                object_url = "https://s3-us-west-2.amazonaws.com/{}/{}".format(current_app.config['S3_BUCKET_NAME'], filename)
                project_image = ProjectImage(description='this is a static description placeholder... will need to refactor', image_url=object_url, image_project=project, photo_uploader=current_user)
                db.session.add(project_image)
            db.session.commit()
            return redirect(url_for('project.project', project_id=form.data.data))
    return render_template('upload.html', form=form)

# @bp.route('/upload-old', methods=['GET', 'POST'])
# def upload(project_id):
#     if form.validate_on_submit():
#         f = form.photo.data
#         filename = secure_filename(f.filename)
#         f.save(os.path.join(
#             app.instance_path, 'photos', filename
#         ))
#         return redirect(url_for('project.project', project_id=project_id))
#     return render_template('upload.html', form=form)

@bp.route('/timeline/<address_id>')
def view_timeline(address_id):
    address = Address.query.filter_by(id=address_id).first()
    projects = Project.query.filter_by(address_id=address_id)
    mymap = Map(
        identifier="view-map",
        lat=address.lat,
        lng=address.lng,
        markers=[(address.lat, address.lng)],
        style="height:400px;width:100%;margin:0;"
    )
    ##TODO: Add functionality that allows user to start the process of creating a review
    return render_template('project/timeline.html', title='Timeline', mymap=mymap, projects=projects)

@bp.route('/<project_id>', methods=['GET', 'POST'])
def project(project_id):
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.body.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        project = Project.query.filter_by(id=project_id).first_or_404()
        post = Post(body=form.body.data, author=current_user, commented_project=project, language=language)
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
    images = project.images.all()
    next_url = url_for('project.project', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('project.project', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('project/project.html', user=user, project=project, form=form, posts=posts.items, next_url=next_url, prev_url=prev_url, mymap=mymap, images=images)


@bp.route('/image/<id>', methods=['GET', 'POST'])
def viewProjectImage(id):
    project_image = ProjectImage.query.filter_by(id=id).first()
    return project_image.image_url

@bp.route('/photo-form', methods=['POST'])
@login_required
def review_form():
    form = PhotoForm()
    form.project_id.data = request.form['project_id']
    return render_template('_comment.html', form=form)

#TODO: Include Photo submission and refactor this. There has to be a better way to do this.
@bp.route('/edit_project/<project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.filter_by(id=project_id).first_or_404()
    form = EditProjectForm()
    if form.validate_on_submit():
        project.name = form.name.data
        project.headline = form.headline.data
        project.description = form.description.data
        project.completion_date = form.completion_date.data
        address = Address.query.get(project.address_id)
        address.address1 = form.address1.data
        address.address2 = form.address2.data
        address.city = form.city.data
        address.state = form.state.data
        address.zipcode = form.zipcode.data
        address.country = form.country.data
        save_tags(project, ProjectCreateInitialForm)
        flash('Your changes have been saved.')
        return redirect(url_for('project.project', project_id=project.id))
    elif request.method == 'GET':
        form.name.data = project.name
        form.headline.data = project.headline
        form.description.data = project.description
        form.completion_date.data = project.completion_date
        form.address1.data = project.site.address1
        form.address2.data = project.site.address2
        form.city.data = project.site.city
        form.state.data = project.site.state
        form.zipcode.data = project.site.zipcode
        form.country.data = project.site.country
        #BUG: tags not populating
        form.tags.data = convertArrayToString(project.tags.all())
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
