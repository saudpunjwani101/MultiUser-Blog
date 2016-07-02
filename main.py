from flask import Flask, render_template, request, url_for, redirect, flash, jsonify
from flask import session as login_session
from flask_uploads import UploadSet, configure_uploads, IMAGES
from flask.ext.bcrypt import Bcrypt
from sqlalchemy import create_engine, desc, asc, text
from sqlalchemy.sql import exists
import sys
import os
from sqlalchemy.orm import sessionmaker
from blog_database import Base, User, Post, UserPhoto, Tweet, Like

 #Connecting to the database using session
engine = create_engine('sqlite:///multiblog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

 #naming flask app
app = Flask(__name__)

 #initializing the bycrpt object
bcrypt = Bcrypt(app)

"""
	Configuring the flask-upload 
	All the images uploaded by users will go into the 'static/uploaded' directory
"""
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST']='static/uploaded' #destination for uploaded user photos
configure_uploads(app, photos)


#Root route and Registration route
@app.route('/')
@app.route('/registration', methods=['Get', 'Post'])
def registration():
	if request.method=='POST':
		username = request.form['username'].lower() #converting username into lowercase
		user_password = request.form['password']
		confirm_pass = request.form['confirm']

		#Querying whether the user already exists in the database
		user = session.query(User).filter_by(username=username).first()
		
		#Registration Form validation
		if user is None:
			if int(len(username))==0:
				flash("Enter a username")
				return redirect(url_for('registration'))

			if int(len(username))<3:
				flash("username must be greater than 3 characters")
				return redirect(url_for('registration'))

			if (' ' in username)==True:
				flash("Spaces are not allowed in usernames")
				return redirect(url_for('registration'))
			
			if user_password!=confirm_pass:
				flash("passwords do not match")
				return redirect(url_for('registration'))
			
			if int(len(user_password))<6 and int(len(user_password))<6:
				flash("password must be greater than 6 characters")
				return redirect(url_for('registration'))

			#Adding the user to the database and hashing the password			
			user = User(username=username,
						password=bcrypt.generate_password_hash(user_password))

			session.add(user)
			session.commit()
			return redirect(url_for('Login'))
		else:
			flash("Username already taken!")
			return redirect(url_for('registration'))
	else:
		return render_template('registration.html')


#route for login
@app.route('/login', methods=['Get', 'Post'])
def Login():
	if request.method=='POST':
		username = request.form['username'].lower()
		user_password = request.form['password']
		
		#checking the login credencials
		user = session.query(User).filter_by(username=username).first()
		
		if user:
			if int(len(username))==0:
				flash('Username or password is invalid')
				return redirect(url_for('Login'))

			if int(len(user_password))==0:
				flash('Username or password is invalid')
				return redirect(url_for('Login'))

			"""
			comparing the hash password with user entered password
			if they match, user will be redirected to the home page
			else they will be redirected to login
			"""
			if bcrypt.check_password_hash(user.password, user_password): #compare hash passwords
				login_session['username'] = request.form['username']
				return redirect(url_for('Home'))

		else:
			flash('Username or password is invalid')
			return redirect(url_for('Login'))
	
	else:
		return render_template('login.html')

#logout route 
@app.route('/logout')
def logout():
		login_session.pop('username', None)
		return redirect(url_for('Login'))

 #Home route
@app.route('/home', methods=['Get', 'Post'])
def Home():
	#User Authorization
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	username = login_session['username']
	allPosts = session.query(Post).filter(Post.user_name==username).order_by(Post.id.desc())
	
	"""
	When the user logins for the first time, he does not have a profile picture,
	if that's the case, then we apply the default user photo.
	"""
	if session.query(UserPhoto).filter_by(user_name=username).count()==0:
		defaultPhoto = UserPhoto(filename='user.png',
									user_name=username,
									url=(photos.url('user.png')))
		session.add(defaultPhoto)
		session.commit()

	#Querying for the lastest user photo
	photo = session.query(UserPhoto).filter(UserPhoto.user_name==username).order_by(UserPhoto.id.desc()).first()

	if request.method=="POST":
		post = request.form['post']
		addPost = Post(content=post, user_name=username)
		session.add(addPost)
		session.commit()
		return redirect(url_for('Home'))

			
	return render_template('home.html', login=username,
										photo=photo,
										posts=allPosts)

#route for user image upload
@app.route('/uploadphoto', methods=['GET', 'POST'])
def uploadUserImage():
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	"""
	If user selects a photo to upload, we save the filename and url to the database
	"""
	if request.method=='POST' and 'photo' in request.files:
		filename = photos.save(request.files['photo'])
		rec = UserPhoto(filename=filename, 
						user_name=login_session['username'],
						url=(photos.url(filename))
						)

		session.add(rec)
		session.commit()

		"""
		When the user updates the profile picture, we query for the lastest photo uploaded
		and put it in the url
		"""
		session.query(User).filter_by(username=login_session['username']).update({"profile_photo_url":photos.url(filename)})

		return redirect(url_for('Home'))

	return render_template('userphoto.html')

#Editing post route
@app.route('/editpost/<int:post_id>/', methods=['GET', 'POST'])
def editPost(post_id):
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	"""
	Putting currentuser from to username variable.
	Getting the post that is to be edited.
	We can get photo from post.user.profile_photo_url because we have setup the relations
	"""
	username=login_session['username']
	post = session.query(Post).filter_by(id=post_id).first()

	if request.method=="POST":
		editedPost = request.form['post']
		post.content = editedPost
		session.add(post)
		session.commit()
		return redirect(url_for('Home'))

	return render_template('editpost.html', post=post,
											username=username)

 #delete post route
@app.route('/deletepost/<int:post_id>/', methods=['GET', 'POST'])
def deletePost(post_id):
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	#Querying the post we want to delete
	post = session.query(Post).filter_by(id=post_id).first()
	
	#Deleting the post from the database
	if request.method=="POST":
		session.delete(post)
		session.commit()
		return redirect(url_for('Home'))

	return render_template('deletepost.html', post=post)

#route for all the users
@app.route('/people')
def People():
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	"""
	Need to get all the list of users, and by != operator,
	we make sure that we don't get the logged in user to show himself in the list of users.
	All posts in this route is irrelevant, I just needed to pass it in the Friend url.
	"""
	people = session.query(User).filter(User.username != login_session['username']).order_by(User.username.desc())
	allPosts = session.query(Post).filter(Post.user_name==login_session['username']).order_by(Post.id.desc()).count()

	"""
	Putting all the users in users.
	Creating an empty dictionary.
	We will get the username and picture of all the users by iterating over each user
	"""
	users = people.all()
	
	return render_template('people.html', users=users,
											post_id=allPosts)


 #route for other user
@app.route('/friend/<string:username>/<int:post_id>/info', methods=['GET', 'POST'])
def Friend(username, post_id):
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	"""
	Getting all the posts of the user
	Getting the user photo
	Counting up all the posts
	"""
	allPosts = session.query(Post).filter(Post.user_name==username).order_by(Post.id.desc())
	photo = session.query(UserPhoto).filter(UserPhoto.user_name==username).order_by(UserPhoto.id.desc()).first()
	total_posts = allPosts.count()

	if request.method=="POST":
		post = session.query(Post).filter_by(id=post_id).first()

		"""
		If users have already liked a particular post, their like will be deleted
		if they press the like button again.

		Else their like will be added to the database
		"""

		if session.query(Like).filter_by(post_id=post_id, username=login_session['username']).first():
			like = session.query(Like).filter_by(post_id=post_id, username=login_session['username']).first()
			session.delete(like)
			session.commit()

			#Recounting the likes of a post
			count = session.query(Like).filter_by(post_id=post_id).count()
			query = session.query(Post).filter_by(id=post_id).first()
			query.likes = count
			session.add(query)
			session.commit()
			return redirect(url_for('Friend', username=username,
												post_id=post_id))

		else:
			like = Like(post_id=post_id, username=login_session['username'])
			session.add(like)
			session.commit()

			count = session.query(Like).filter_by(post_id=post_id).count()
			query = session.query(Post).filter_by(id=post_id).first()
			query.likes = count
			session.add(query)
			session.commit()
			return redirect(url_for('Friend', username=username,
												post_id=post_id))

 
	return render_template('friend.html', username=username,
											photo=photo,
											posts=allPosts,
											total_posts=total_posts)

 #comments route
@app.route('/comment/<string:username>/<int:post_id>', methods=['GET', 'POST'])
def Comment(username, post_id):
	if 'username' not in login_session:
		flash("You need to be logged in")
		return redirect(url_for('Login'))

	"""
	putting the logged in user in currentuser variable.
	Getting a particular post.
	Getting the user photo who posted.
	Getting all the comments in tweets object
	"""
	currentuser = login_session['username']
	post = session.query(Post).filter_by(id=post_id).first()
	photo = session.query(UserPhoto).filter(UserPhoto.user_name==username).order_by(UserPhoto.id.desc()).first()
	tweets = session.query(Tweet).filter_by(post_id=post_id).order_by(Tweet.id.desc())
	
	#Inserting the comment in the database
	if request.method=='POST':
		content = request.form['tweet']
		tweet = Tweet(post_id=post_id, 
						content=content,
						username=currentuser)

		session.add(tweet)
		session.commit()

		return redirect(url_for('Comment', post_id=post_id,
											username=username))


	return render_template('comment.html', post=post,
											post_id=post_id,
											photo=photo,
											username=username,
											tweets=tweets)


if __name__ == '__main__':
	app.debug = True
	app.secret_key = "hejasikflqoJiwjkeMJ"
	app.run(host = '0.0.0.0', port=8080)



