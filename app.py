import os

from cs50 import SQL
from flask import Flask, flash, render_template, redirect, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from helpers import error, login_required, date, rann

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
mail = Mail(app)

uri = os.getenv("DATABASE_URL")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://")
db = SQL(uri)

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    patient = db.execute("SELECT * FROM patient ORDER BY p_dt DESC")

    if request.method == "POST":
        name = request.form.get("name")
        row = db.execute("SELECT * FROM patient WHERE patient_name LIKE ?", '%' + name +'%')

        if len(row) == 0:
            return error("patient is not in datbase", 403) 
               
        return render_template("index.html", data=row)

    return render_template("index.html", data=patient)


@app.route("/details", methods=["POST"])
@login_required
def details():
    id = request.form.get("id")
    
    row = db.execute("SELECT * FROM patient_data WHERE pd_id = ?", id)
    
    for d in row:
        vital = d["vital"]
        d["vital"] = vital.split("\n")

        description = d["description"]
        d["description"] = description.split("\n")

        treatment = d["treatment"]
        d["treatment"] = treatment.split("\n")

    rows = db.execute("SELECT patient_name, age, gender, contact, address FROM patient WHERE patient_id = ?", id)

    name = rows[0]["patient_name"]
    age = rows[0]["age"]
    gender = rows[0]["gender"]
    contact = rows[0]["contact"]
    address = rows[0]["address"]

    return render_template("details.html", data=row, name=name, age=age, gender=gender, contact=contact, address=address)


@app.route("/login" , methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username:
            return error("must provide username", 403)
        
        elif not password:
            return error("missing password", 403)
        
        rows = db.execute("SELECT id, hash, mail FROM members WHERE name = ?", username)


        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return error("invalid username or password", 403)

        session["temp_id"] = rows[0]["id"]
        session["code"] = rann()

        mail_receiver = rows[0]["mail"]

        message = Message("HOSPITAL OTP", sender=("Hospital Admin", "from@me.com"), recipients = [mail_receiver])
        message.body = f'\n \n \r \r Confirmation code:  {session["code"]}'
        mail.send(message)

        flash("Confirmation code have sent into your mail.")
        return redirect("/confirmation")

    else:
        return render_template("login.html")

@app.route("/confirmation", methods=["GET", "POST"])
def confrimation():

    if request.method == "POST":
        code = request.form.get("code")
        
        row = db.execute("SELECT name, status FROM members WHERE id = ?", session["temp_id"])

        if code != session["code"]:
            flash("Login code WRONG!!.")
            return redirect("/login")

        session["user_id"] = session["temp_id"]
        name = row[0]["name"]
        session["user_status"] = row[0]["status"]

        flash(f"logged in as '{name}'.")
        return redirect("/")

    return render_template("confirmation.html")


@app.route("/register/admin", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        phonenumber = request.form.get("phonenumber")
        mail = request.form.get("mail")

        for l in phonenumber:
            if l.isalpha():
                return error("invalid contact", 400)

        rows = db.execute("SELECT * FROM members")

        used_name = [d["name"] for d in rows]

        counts = db.execute("SELECT COUNT(status) AS count FROM members WHERE status = 'admin'")
        count = counts[0]["count"]

        if count > 100:
            return error("admin registration is full", 403)

        elif not username:
            return error("must provide username", 400)

        elif not password:
            return error("must provide password", 400)

        elif not phonenumber:
            return error("must provide phonenumber", 400)

        elif not mail:
            return error("must provide mail", 400)

        elif username in used_name:
            return error("username already exists", 400)

        elif not confirmation:
            return error("missing re-type", 400)

        elif password != confirmation:
            return error("passwords didn't match", 400)

        hash_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        db.execute("INSERT INTO members (status, name, hash, mail, phonenumber) VALUES (?, ?, ?, ?, ?)", "admin", username, hash_password, mail, phonenumber)
        flash("Admin registered.")

        return redirect("/login")
        
    return render_template("register.html")


@app.route("/register/member", methods=["GET", "POST"])
@login_required
def reg_member():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        mail = request.form.get("mail")
        phonenumber = request.form.get("phone")

        for l in phonenumber:
            if l.isalpha():
                return error("invalid contact", 400)

        if not username:
            return error("must provide username", 403)

        elif not password:
            return error("must provide password", 403)

        elif password != confirmation:
            return error("passwords didn't match", 403)

        elif not mail:
            return error("missing mail", 403)

        elif not phonenumber:
            return error("missing phone number", 403)

        rows = db.execute("SELECT name FROM members")
        
        used_name = [d["name"] for d in rows]

        if username in used_name:
            return error("username already exists", 403)

        hash_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        db.execute("INSERT INTO members (status, name, hash, mail, phonenumber) VALUES (?, ?, ?, ?, ?)", "member", username, hash_password, mail, phonenumber)

        flash("A new member added.")

        return redirect("/login")

    return render_template("register_member.html")


@app.route("/change_name", methods=["POST"])
@login_required
def change_name():
    name = request.form.get("name")

    if not name:
        return error("must provide username", 400)

    rows = db.execute("SELECT name FROM members")
    used_name = [d["name"] for d in rows]

    if name in used_name:
        return error("username already exists", 403)

    db.execute("UPDATE members SET name = ? WHERE id = ?", name, session["user_id"])

    flash("Username changed to '{name}'.")

    return redirect("/account")


@app.route("/change_password", methods=["POST"])
@login_required
def change_password():
    old = request.form.get("old")
    new_pass = request.form.get("new")
    confirmation = request.form.get("confirm")

    if not old:
        return error("must provide old password", 400)

    row = db.execute("SELECT hash FROM members WHERE id = ?", session["user_id"])

    if not check_password_hash(row[0]["hash"], old):
            return error("current password wrong", 403)

    elif not new_pass:
            return error("new password missing", 400)

    elif new_pass != confirmation:
            return error("passwords didn't match", 400)

    new_password = generate_password_hash(new_pass, method='pbkdf2:sha256', salt_length=8)

    db.execute("UPDATE members SET hash = ? WHERE id = ?", new_password, session["user_id"])

    flash("New password updated.")

    return redirect("/account")


@app.route("/change_contact", methods=["POST"])
@login_required
def change_contact():
    contact = request.form.get("contact")

    if not contact:
        return error("must provide contact number", 400)

    rows = db.execute("SELECT phonenumber FROM members")
    used_contact = [d["phonenumber"] for d in rows]

    if contact in used_contact:
        return error("contact number already used", 400)
    
    for i in contact:
        if i.isalpha():
            return error("invalid contact number", 400)

    db.execute("UPDATE members SET phonenumber = ? WHERE id = ?", contact, session["user_id"])

    flash("Contact number changed.")

    return redirect("/account")


@app.route("/change_mail", methods=["POST"])
@login_required
def change_mail():
    mail = request.form.get("mail")

    if not mail:
        return error("no input", 400)

    db.execute("UPDATE members SET mail = ? WHERE id = ?", mail, session["user_id"])

    flash("New mail updated.")

    return redirect("/account")


@app.route("/account")
@login_required
def account():
    row = db.execute("SELECT * FROM members WHERE id = ?", session["user_id"])
    return render_template("account.html", data=row)


@app.route("/search_member", methods=["GET", "POST"])
@login_required
def search_member():
    if request.method == "POST":
        name = request.form.get("name")
        if not name:
            return error("member name missing", 404)

        rows =  db.execute("SELECT name, status, mail, phonenumber FROM members WHERE name LIKE ?", "%" + name + "%")

        if len(rows) == 0:
            return error("member not found")

        return render_template("search_member.html", data=rows)

    return render_template("search_member.html")


@app.route("/remove_member", methods=["GET", "POST"])
@login_required
def remove_member():
    if request.method == "POST":
        name = request.form.get("name")

        if not name:
            return error("member name missing", 400)

        rows = db.execute("SELECT id, name, status, dt FROM members WHERE name LIKE ? ORDER BY dt DESC", "%" + name + "%")

        if len(rows) == 0:
            return error("member name not found", 400)

        return render_template("remove_member.html", data=rows)
    return render_template("remove_member.html")


@app.route("/remover_member", methods=["POST"])
@login_required
def remover_member():

    id = int(request.form.get("id"))

    db.execute("DELETE FROM history WHERE mem_id = ?", id)
    db.execute("DELETE FROM members WHERE id = ?", id)

    flash("Member deleted.")

    if id == session["user_id"]:
        session.clear()
        flash("Member deleted.")
        return redirect("/")

    return redirect("/")


@app.route("/Patient_register", methods=["GET", "POST"])
@login_required
def patient_register():
    if request.method == "POST":
        patient_name = request.form.get("name")
        address = request.form.get("address")
        age = request.form.get("age")
        gender = request.form.get("gender")
        phonenumber = request.form.get("phone")
        vital = request.form.get("vital")
        description = request.form.get("description")
        treatment = request.form.get("treatment")
        total = request.form.get("total")

        if not patient_name:
            return error("patient name missing", 403)

        elif not address:
            return error("patient adderss missing", 403)

        elif not age:
            return error("patient age not submitted", 403)

        elif not gender:
            return error("patient gender haven't defined", 403)

        elif not phonenumber:
            return error("patient missing patient phone number", 403)

        if len(total) == 0:
            total = 0     

        try:
            total = float(total)
        except ValueError:
            return error("invalid total")

        for d in phonenumber:
            if d.isalpha():
                return error("invalid contact", 400)

        h = date()

        status = session["user_status"]  

        db.execute("INSERT INTO patient (patient_name, age, gender, contact, address, p_dt) VALUES (?, ?, ?, ?, ?, ?)", patient_name, age, gender, phonenumber, address, h)

        row = db.execute("SELECT patient_id, p_dt FROM patient WHERE patient_name = ? AND contact = ?", patient_name, phonenumber)
        id = row[0]["patient_id"]
        time = row[0]["p_dt"]

        counts = db.execute("SELECT COUNT(*) AS count FROM history")
        count = counts[0]["count"]

        if count > 2000:
            db.execute("DELETE FROM history LIMIT 100")


        if vital or description or treatment:
            db.execute("INSERT INTO patient_data (pd_id, vital, description, treatment, total) VALUES (? ,?, ?, ?, ?)", id, vital, description, treatment, total)

            db.execute("INSERT INTO history (mem_id, pat_id, status, category, his_dt, reg_time) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], id, status, "Registration & datails", h, time)

        else:
            
            db.execute("INSERT INTO history (mem_id, pat_id, category, his_dt, reg_time, status) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], id, "Patient Registration", h, time, session["user_status"])

        flash("New patient added.")

        return redirect("/")
        
    return render_template("patient_register.html")


@app.route("/history")
@login_required
def history():
    row = db.execute("SELECT * FROM history ORDER BY his_dt DESC")

    for d in row:
        mid = d["mem_id"]
        pid = d["pat_id"]

        if mid:
            member = db.execute("SELECT name FROM members WHERE id = ?", mid)
            d["member"] = member[0]["name"]

        if pid:
            patient = db.execute("SELECT patient_name FROM patient WHERE patient_id = ?", pid)
            d["patient"] = patient[0]["patient_name"]

    return render_template("history.html", data=row)


@app.route("/registration/history")
@login_required
def registration_history():
    rows = db.execute("SELECT status, name, dt FROM members ORDER BY dt DESC")

    return render_template("registration_history.html", data=rows)


@app.route("/reupdate/reg", methods=["GET", "POST"])
@login_required
def reupdate_reg():
    if request.method == "POST":
        name = request.form.get("name")  

        rows = db.execute("SELECT patient_id, patient_name, p_dt FROM patient WHERE patient_name LIKE ?", "%" + name + "%")

        if len(rows) == 0:
            return error("patient not found", 404)

        return render_template("reupdate_reg.html", data=rows) 

    return render_template("reupdate_reg.html")


@app.route("/show_reupdate_reg", methods=["POST"])
@login_required
def show_reupdate_reg():
    id = request.form.get("id")
    row = db.execute("SELECT * FROM patient WHERE patient_id = ?", id)

    return render_template("reupdater_reg.html", data=row) 


@app.route("/reupdater/reg", methods=["POST"])
@login_required
def reupdate():
    name = request.form.get("name")
    age = request.form.get("age")
    gender = request.form.get("gender")
    contact = request.form.get("contact")
    address = request.form.get("address")
    id = request.form.get("id")

    for d in contact:
        if d.isalpha():
            return error("invalid contact", 400)

    if name:
        db.execute("UPDATE patient SET patient_name = ? WHERE patient_id = ?", name, id)

    if age:
        db.execute("UPDATE patient SET age = ? WHERE patient_id = ?", age, id)

    if gender:
        db.execute("UPDATE patient SET gender = ? WHERE patient_id = ?", gender, id)
    
    if contact:
        db.execute("UPDATE patient SET contact = ? WHERE patient_id = ?", contact, id)

    if address:
        db.execute("UPDATE patient SET address = ? WHERE patient_id = ?", address, id)

    if not name and not age and not gender and not contact and not address:
        return error("invalid input", 400)
        
    h = date()

    row = db.execute("SELECT p_dt FROM patient WHERE patient_id = ?", id)
    dt = row[0]["p_dt"]

    counts = db.execute("SELECT COUNT(*) AS count FROM history")
    count = counts[0]["count"]

    if count > 2000:
        db.execute("DELETE FROM history LIMIT 100")

    db.execute("INSERT INTO history (mem_id, pat_id, status, category, his_dt, reg_time) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], id, session["user_status"], "Re-update Registration", h, dt)

    flash("Reupdated patient registration form.")

    return redirect("/")


@app.route("/reupdate/details", methods=["GET", "POST"])
@login_required
def reupdate_details():
    if request.method == "POST":
        name = request.form.get("name")

        rows = db.execute("SELECT patient_id, patient_name, p_dt FROM patient WHERE patient_name LIKE ?", "%" + name + "%")

        if len(rows) == 0:
            return error("patient not found", 404)

        return render_template("reupdate_details.html", data=rows)
        
    return render_template("reupdate_details.html")


@app.route("/show_reupdate_details", methods=["POST"])
@login_required
def show_reupdate_details():
    id = request.form.get("id")
    row = db.execute("SELECT patient_name FROM patient WHERE patient_id = ?", id)
    name = row[0]["patient_name"]

    rows = db.execute("SELECT * FROM patient_data WHERE pd_id = ?", id)

    return render_template("reupdater_details.html", name=name, data=rows)


@app.route("/reupdater/details", methods=["POST"])
@login_required
def reupdater_details():
    id = request.form.get("id")
    dt = request.form.get("dt")
    vital = request.form.get("vital")
    description = request.form.get("description")
    treatment = request.form.get("treatment")
    total = request.form.get("total")
    
    if total:
        try:
            total = float(total)
        except ValueError:
            return error("invalid total", 400)

    if vital:
        db.execute("UPDATE patient_data SET vital = ? WHERE pd_id = ? AND pd_dt = ?", vital, id, dt)

    if description:
        db.execute("UPDATE patient_data SET description = ? WHERE pd_id = ? AND pd_dt = ?", description, id, dt)

    if treatment:
        db.execute("UPDATE patient_data SET treatment = ? WHERE pd_id = ? AND pd_dt = ?", treatment, id, dt)

    if total:
        db.execute("UPDATE patient_data SET total = ? WHERE pd_id = ? AND pd_dt = ?", total, id, dt)

    if not vital and not description and not treatment and not total:
        return error("invalid input", 400)

    h = date()

    row = db.execute("SELECT pd_dt FROM patient_data WHERE pd_id = ?", id)
    dt = row[0]["pd_dt"]

    counts = db.execute("SELECT COUNT(*) AS count FROM history")
    count = counts[0]["count"]

    if count > 2000:
        db.execute("DELETE FROM history LIMIT 100")

    db.execute("INSERT INTO history (mem_id, pat_id, status, category, his_dt, reg_time) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], id, session["user_status"], "Re-update patient details", h, dt)

    flash("Reupdated patient details.")
    
    return redirect("/")


@app.route("/update/details", methods=["GET", "POST"])
@login_required
def update_details():
    if request.method == "POST":
        name = request.form.get("name")
        rows = db.execute("SELECT patient_id, patient_name, age, gender, p_dt FROM patient WHERE patient_name LIKE ?", "%" + name + "%")
        
        if len(rows) == 0:
            return error("patient not found", 400)
        
        return render_template("update_details.html", data=rows)
    return render_template("update_details.html")


@app.route("/updater", methods=["POST"])
@login_required
def updater():
    patient_id = request.form.get("id")
    name = request.form.get("p_name")
    return render_template("updater_details.html", name=name, id=patient_id)


@app.route("/updater/details", methods=["POST"])
@login_required
def updater_details():
    patient_id = request.form.get("id")
    vital = request.form.get("vital")
    description = request.form.get("description")
    treatment = request.form.get("treatment")
    total = request.form.get("total")
    
    h = date()

    if len(vital) == 0:
        vital = "-"

    if len(description) == 0:
        description = "-"

    if len(treatment) == 0:
        treatment = "-"

    if len(total) == 0:
        total = 0
    
    try:
        total = float(total)
    except ValueError:
        return error("invalid total")

    db.execute("INSERT INTO patient_data (pd_id, vital, description, treatment, total, pd_dt) VALUES (?, ?, ?, ?, ?, ?)", patient_id, vital, description, treatment, total, h)

    row = db.execute("SELECT pd_dt FROM patient_data WHERE pd_id = ?", patient_id)

    dt = row[0]["pd_dt"]

    counts = db.execute("SELECT COUNT(*) AS count FROM history")
    count = counts[0]["count"]

    if count > 2000:
        db.execute("DELETE FROM history LIMIT 100")

    db.execute("INSERT INTO history (mem_id, pat_id, status, category, his_dt, reg_time) VALUES (?, ?, ?, ?, ?, ?)", session["user_id"], patient_id, session["user_status"], "Update patient details", h, dt)

    flash("Patient details added.")
    return redirect("/")


@app.route("/remove_patient", methods=["GET", "POST"])
@login_required
def remove_patient():
    if request.method == "POST":
        name = request.form.get("name")

        rows = db.execute("SELECT patient_id, patient_name, p_dt FROM patient WHERE patient_name LIKE ?", "%" + name + "%")

        return render_template("remove_patient.html", data=rows)
    return render_template("remove_patient.html")

 
@app.route("/remover_patient", methods=["POST"])
@login_required
def remover_patient():
    id = request.form.get("id")
    rows = db.execute("SELECT patient_name, p_dt FROM patient WHERE patient_id = ?", id)
    name = rows[0]["patient_name"]
    dt = rows[0]["p_dt"]

    db.execute("DELETE FROM patient_data WHERE pd_id = ?", id)
    db.execute("DELETE FROM history WHERE pat_id = ?", id)

    db.execute("DELETE FROM patient WHERE patient_id = ?", id)

    h = date()

    counts = db.execute("SELECT COUNT(*) AS count FROM history")
    count = counts[0]["count"]

    if count > 2000:
        db.execute("DELETE FROM history LIMIT 100")

    db.execute("INSERT INTO history (mem_id, category, status, reg_time, his_dt) VALUES (?, ?, ?, ?, ?)", session["user_id"], f"Remove patient: {name}", session["user_status"], dt, h)

    flash("patient deleted.")
    return redirect("/")
    
@app.route("/logout")
@login_required
def log_out():
    session.clear()
    return redirect("/login")
