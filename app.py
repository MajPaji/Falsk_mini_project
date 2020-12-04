import os
from flask import (
    Flask,  flash, render_template,
    session, redirect, url_for, request)
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from flask_pymongo import PyMongo
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/get_task")
def get_task():
    tasks = list(mongo.db.tasks.find())
    return render_template("tasks.html", tasks=tasks)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username exists
        exsiting_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if exsiting_user:
            flash("Username already exists")
            return redirect(url_for('register'))

        register = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get("password"))
        }

        mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration successful")
        return redirect(url_for('profile', username=session["user"]))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in database
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})
        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                flash(
                    "Welcome, {}".format(request.form.get("username").lower()))
                session["user"] = request.form.get("username").lower()
                return redirect(url_for('profile', username=session["user"]))
            else:
                flash("Invalid Username and/or Password")
                return redirect(url_for('login'))
        else:
            flash("Invalid Username and/or Password")
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):

    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]

    if session["user"]:
        return render_template("profile.html", username=username)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("user")
    flash("You have been logged out")
    return redirect(url_for('login'))


@app.route("/add_task", methods=["GET", "POST"])
def add_task():
    if request.method == "POST":
        urgent = "on" if request.form.get("is_urgent") else "off"
        task = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        mongo.db.tasks.insert_one(task)
        flash("Task successfully added")
        return redirect(url_for('get_task'))

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("add_task.html", categories=categories)


@app.route("/edit_task/<task_id>", methods=["GET", "POST"])
def edit_task(task_id):
    if request.method == "POST":
        urgent = "on" if request.form.get("is_urgent") else "off"
        submit = {
            "category_name": request.form.get("category_name"),
            "task_name": request.form.get("task_name"),
            "task_description": request.form.get("task_description"),
            "is_urgent": urgent,
            "due_date": request.form.get("due_date"),
            "created_by": session["user"]
        }
        mongo.db.tasks.update({"_id": ObjectId(task_id)}, submit)
        flash("Task successfully updated")

    task = mongo.db.tasks.find_one({"_id": ObjectId(task_id)})

    categories = mongo.db.categories.find().sort("category_name", 1)
    return render_template("edit_task.html", task=task, categories=categories)


@app.route("/delete_task/<task_id>")
def delete_task(task_id):
    mongo.db.tasks.remove({"_id": ObjectId(task_id)})
    flash("Task successfully deleted")
    return redirect(url_for("get_task"))


@app.route("/get_category")
def get_category():
    categories = list(mongo.db.categories.find().sort("category_name", 1))

    return render_template("get_category.html", categories=categories)


@app.route("/add_category", methods=["GET", "POST"])
def add_category():

    if request.method == "POST":
        category = {
            "category_name": request.form.get("category_name")
        }

        mongo.db.categories.insert_one(category)
        flash("New Category Added")
        return redirect(url_for('get_category'))

    return render_template("add_category.html")


@app.route("/edit_category/<category_id>", methods=["GET", "POST"])
def edit_category(category_id):
    if request.method == "POST":
        submit = {
            "category_name": request.form.get("category_name")
        }
        mongo.db.categories.update({"_id": ObjectId(category_id)}, submit)
        flash("Category successfully updated")
        return redirect(url_for('get_category'))

    category = mongo.db.categories.find_one({"_id": ObjectId(category_id)})

    return render_template("edit_category.html", category=category)


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
