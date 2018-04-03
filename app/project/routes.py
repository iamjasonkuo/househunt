from flask import render_template, flash, redirect, url_for, request, jsonify, current_app, g
from flask_login import login_required, login_user, logout_user, current_user
from app import db
from app.helper import clean_list, normalize, convertArrayToString, convertStringToArray, prepFullAddressSearch
from app.project import bp
from app.models import User, Project, Post, Address
from app.main.forms import SearchForm, PostForm
from app.project.forms import ProjectCreateInitialForm, EditProjectForm, ProjectFilterForm
from datetime import datetime
from guess_language import guess_language

@bp.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        g.search_form = SearchForm()

@bp.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    projects = Project.query.order_by(Project.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('project.explore', page=projects.next_num) \
        if projects.has_next else None
    prev_url = url_for('project.explore', page=projects.prev_num) \
        if projects.has_prev else None
    return render_template('index.html', title='Explore', projects=projects.items, next_url=next_url, prev_url=prev_url)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_authenticated:
        flash('You need to be a registered user to create projects.')
        return redirect(url_for('main.index'))
    form = ProjectCreateInitialForm()
    if form.validate_on_submit():
        full_address = prepFullAddressSearch(form.address1.data, form.address2.data, form.city.data, form.state.data, form.zipcode.data)
        tags = convertArrayToString(form.tags.data)
        address = Address(address1=form.address1.data, address2=form.address2.data, city=form.city.data, state = form.state.data, zipcode=form.zipcode.data, country=form.country.data)
        ##If address already exists in database, then provide user opportunity to choose the address
        ## after selecting address,
        db.session.add(address)
        project = Project(name=form.name.data, tags=tags, creator=current_user, site=address)
        db.session.add(project)
        db.session.commit()
        flash('Congratulations, you just created a project and address!')
        return redirect(url_for('project.project', project_id=project.id))
    return render_template('project/create.html', title='Create', form=form)

@bp.route('/<project_id>', methods=['GET', 'POST'])
def project(project_id):
    form = PostForm()
    if form.validate_on_submit():
        language = guess_language(form.post.data)
        if language == 'UNKNOWN' or len(language) > 5:
            language = ''
        project = Project.query.filter_by(id=project_id).first_or_404()
        post = Post(body=form.body.data, author=current_user, post_project=project, language=language)
        db.session.add(post)
        db.session.commit()
        flash('Your post is now live!')
        return redirect(url_for('project.project', project_id=project_id))
    page = request.args.get('page', 1, type=int)
    project = Project.query.filter_by(id=project_id).first_or_404()
    user = User.query.filter_by(username=project.creator.username).first()
    posts = project.posts.order_by(Post.timestamp.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('project.project', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('project.project', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('project/project.html', user=user, project=project, form=form, posts=posts.items, next_url=next_url, prev_url=prev_url)


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
