from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
app.config['MONGO_URI'] = 'mongodb://localhost:27017/university_connect'
app.config['UPLOAD_FOLDER'] = 'static/profile_photos'  
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit
mongo = PyMongo(app)


# Stripe configuration



# Ensure the upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        department = request.form['department']
        institute = request.form['institute']
        year = request.form['year']
        semester = request.form['semester']
        interests = request.form['interests']
        instagram_id = request.form['instagram_id']

        profile_photo = request.files.get('profile_photo')
        if profile_photo:
            photo_filename = secure_filename(profile_photo.filename)
            profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            profile_photo_url = f"/{app.config['UPLOAD_FOLDER']}/{photo_filename}"
        else:
            flash('Profile photo is required!', 'danger')
            return redirect(url_for('register'))

        existing_user = mongo.db.users.find_one({'username': username})
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        new_user = {
            'username': username,
            'password': password,  # Consider hashing passwords in a real application
            'name': name,
            'department': department,
            'institute': institute,
            'year': year,
            'semester': semester,
            'interests': interests,
            'instagram_id': instagram_id,
            'profile_photo': profile_photo_url
        }
        mongo.db.users.insert_one(new_user)
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({'username': username, 'password': password})

        if user:
            session['username'] = username
            session['user_id'] = str(user['_id'])
            flash('Login successful!', 'success')
            return redirect(url_for('profiles'))
        else:
            flash('Invalid username or password.', 'danger')

    return render_template('login.html')

@app.route('/profiles', methods=['GET', 'POST'])
def profiles():
    if 'username' not in session:
        flash('You must log in to view profiles.', 'warning')
        return redirect(url_for('login'))

    search_query = request.form.get('search_query', '').strip()

    if search_query:
        users = mongo.db.users.find({"username": {"$regex": search_query, "$options": "i"}})
    else:
        users = mongo.db.users.find()

    users = list(users)

    return render_template('profiles.html', users=users)

@app.route('/delete_profile/<user_id>', methods=['POST'])
def delete_profile(user_id):
    # Check if the user is logged in
    if 'user_id' not in session or session['user_id'] != user_id:
        flash('You do not have permission to delete this profile.', 'danger')
        return redirect(url_for('profiles'))

    # Logic to delete the user profile from the database
    try:
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        flash('Your profile has been deleted successfully.', 'success')
        session.clear()  # Clear the session after deletion
        return redirect(url_for('index'))  # Redirect to home or login page
    except Exception as e:
        flash('An error occurred while trying to delete your profile.', 'danger')
        return redirect(url_for('profiles'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash("You need to log in first.")
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})

    if request.method == 'POST':
        username = request.form.get('username')
        department = request.form.get('department')
        institute = request.form.get('institute')
        year = request.form.get('year')
        semester = request.form.get('semester')
        interests = request.form.get('interests')
        instagram_id = request.form.get('instagram_id')

        profile_photo = request.files.get('profile_photo')
        if profile_photo:
            photo_filename = secure_filename(profile_photo.filename)
            profile_photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
            profile_photo_url = f"/{app.config['UPLOAD_FOLDER']}/{photo_filename}"
        else:
            profile_photo_url = user['profile_photo']  # Retain the existing photo if no new photo is uploaded

        mongo.db.users.update_one(
            {'_id': ObjectId(user_id)},
            {
                '$set': {
                    'username': username,
                    'department': department,
                    'institute': institute,
                    'year': year,
                    'semester': semester,
                    'interests': interests,
                    'instagram_id': instagram_id,
                    'profile_photo': profile_photo_url
                }
            }
        )
        flash("Profile updated successfully!")
        return redirect(url_for('profiles'))

    return render_template('edit_profile.html', user=user)

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# New route for the Merchandise page
@app.route('/merchandise')
def merchandise():
    return render_template('merchandise.html')

if __name__ == '__main__':
    app.run(debug=True)
