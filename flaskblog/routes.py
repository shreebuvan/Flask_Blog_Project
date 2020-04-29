from flask import render_template, url_for, flash, redirect, request, abort, session , make_response
from flaskblog import app,db,bcrypt,mail
from flaskblog.forms import RegistrationForm,LoginForm,UpdateAccountForm,PostForm,RequestResetForm,ResetPasswordForm
from flaskblog.models import User,Post
from flask_login import login_user,current_user,logout_user, login_required
import secrets
import os
from PIL import Image
from flask_mail import Message
import requests
from bs4 import BeautifulSoup

@app.route('/')
@app.route('/home')
def home():
    page=request.args.get('page',1,type=int)
    posts=Post.query.order_by(Post.date_posted.desc()).paginate(page=page,per_page=4)
    return render_template('home.html', posts=posts)
@app.route('/top_book_')
def top_book_():
    return redirect(url_for('top_book'))
@app.route('/top_book')
def top_book():
    url = 'http://books.toscrape.com/index.html'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    div = soup.findAll('div', class_='side_categories')
    li = div[0].ul.li.ul.findAll('li')
    rowe=dict()
    for j in range(len(li)):
        rowe[j]=li[j].a.text.strip()
    session['table1']=rowe
    session['len1']=len(li)
    return render_template('top_book.html',title="TOP")

@app.route('/top_book', methods=['POST'])
def top_book_sel():
    a=request.form['b']
    if a=='done':
        ch1=request.form['input_no']
        ch=int(ch1)
        url = 'http://books.toscrape.com/index.html'
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        session['ch']=ch
        div = soup.findAll('div', class_='side_categories')
        li = div[0].ul.li.ul.findAll('li')
        url = 'http://books.toscrape.com/'
        url += li[ch - 1].a['href']
        page = requests.get(url)
        soup = BeautifulSoup(page.content, 'html.parser')
        div = soup.findAll('div', class_='col-sm-8 col-md-9')
        sec = div[0].section
        ol = sec.findAll('ol', class_='row')
        li = ol[0].findAll('li')
        rowe1 = dict()
        m = dict()
        for j in range(len(li)):
            k = li[j].h3.a['title']
            m[j] = k
            divp = li[j].findAll('div', class_='product_price')
            rowe1[k] = divp[0].p.text
        session['table1'] = rowe1
        session['li'] = m
        session['len1'] = len(m)
        response = make_response(render_template('top_book_selected.html', title="Selected Book Category"))
        if len(m)>2:
            response.set_cookie('b1', m[0])
            response.set_cookie('b2', m[1])
            response.set_cookie('b3', m[2])
        elif len(m)>1:
            response.set_cookie('b1', m[0])
            response.set_cookie('b2', m[1])
        elif len(m)==1:
            response.set_cookie('b1', m[0])
        else:
            return 0
        return response

@app.route('/register', methods=['GET','POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RegistrationForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data,email=form.email.data,password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account is now created. You can now Log In ','success')
        return redirect(url_for('login'))
    return render_template('register.html',title="Register",form=form)

@app.route('/login' , methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.remember.data)
            next_page=request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Check for your email and password correctness','danger')
    response_out=request.cookies.get('b1')
    response_out1= request.cookies.get('b2')
    response_out2= request.cookies.get('b3')
    return render_template('login.html',title="Login",form=form,response_out=response_out,response_out1=response_out1,response_out2=response_out2)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))



def save_picture(form_picture):
    random_hex=secrets.token_hex(8)
    _,f_ext=os.path.splitext(form_picture.filename)
    picture_fn=random_hex+f_ext
    picture_path=os.path.join(app.root_path ,'static/profile_pics', picture_fn)
    form_picture.save(picture_path)

    output_size=(180,180)
    i=Image.open(form_picture)
    i.thumbnail(output_size)
    return picture_fn


@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file=save_picture(form.picture.data)
            current_user.image_file=picture_file
        current_user.username=form.username.data;
        current_user.email=form.email.data
        db.session.commit()
        flash('Your account has been successfully updated!','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    image_file=url_for('static',filename='profile_pics/'+ current_user.image_file)
    return render_template('account.html',title="Account", image_file=image_file,form=form)

@app.route('/post/new', methods=['GET','POST'])
@login_required
def new_post():
    form=PostForm()
    if form.validate_on_submit():
        post=Post(title=form.title.data,content=form.content.data ,author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post has been created successfully!','success')
        return  redirect(url_for('home'))
    return render_template('create_post.html', title="New Post",form=form,legend='New Post')

@app.route('/post/<int:post_id>')
def post(post_id):
    post=Post.query.get_or_404(post_id)
    return render_template('post.html',title=post.title, post=post)

@app.route('/post/<int:post_id>/update' , methods=['GET','POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Your post message has been Upadated!','success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method=='GET':
        form.title.data=post.title
        form.content.data=post.content
    return render_template('create_post.html', title="Update Post", form=form,legend='Update Post')


@app.route('/post/<int:post_id>/delete' , methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your post message has been Deleted!', 'success')
    return redirect(url_for('home'))


@app.route('/user/<string:username>')
def user_posts(username):
    page=request.args.get('page',1,type=int)
    user=User.query.filter_by(username=username).first_or_404()
    posts=Post.query.filter_by(author=user).order_by(Post.date_posted.desc()).paginate(page=page,per_page=4)
    return render_template('user_posts.html', posts=posts , user=user)


def send_reset_email(user):
    token=user.get_reset_token()
    msg=Message('Password Reset Request',sender='noreply@demo.com',recipients=[user.email])
    msg.body=f'''To reset your password, visit the following link:
{url_for('reset_token',token=token,_external=True)}    
If you did not request then simply ignore this mail!!
    '''
    mail.send(msg)


@app.route('/reset_password' , methods=['GET','POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RequestResetForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An Email has been sent with the instructions to rest password','info')
        return redirect(url_for('login'))
    return render_template('reset_request.html',title="Reset Password",form=form)

@app.route('/reset_password/<token>' , methods=['GET','POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user=User.verify_reset_token(token)
    if user is None:
        flash('The token is invalid or it has expired','warning')
    form=ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password=hashed_password
        db.session.commit()
        flash('Your Password has been Updated!. You can now Log In ','success')
    return render_template('reset_token.html',title="Reset Password",form=form)