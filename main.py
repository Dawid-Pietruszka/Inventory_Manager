import csv
from flask import Flask, render_template, url_for, session, request, redirect, send_from_directory, send_file
from flask_pymongo import PyMongo, MongoClient
from flask_mail import Mail, Message
from flask_bootstrap import Bootstrap
from datetime import date
import copy


app = Flask(__name__)
Bootstrap(app)
app.config["MONGO_URI"] = ""
mongo = PyMongo(app)
app.config.from_object(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = ''
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

app.secret_key = ''
app.config['SESSION_TYPE'] = 'filesystem'

mail = Mail(app)
client = MongoClient("")
db = client["softwarearchdb"]
products = db["softwarearch"]

cur = products.find()
prod = []
chosenProduct = []


@app.route("/")
def home():
    if 'username' in session:
        return render_template("index.html", s=session)#If user is logged in, show home page

    return redirect("login")


@app.route("/view/", methods=['GET', 'POST'])
def view():
    if 'username' in session:

        if request.method == "POST": #If data is sent to page, update data in MongoDB

            price = request.form.get("Price")
            offer = request.form.get("Offer")
            loyalty = request.form.get("Loyalty")
            inventory = request.form.get("Inventory")
            layaway = request.form.get("Layaway")
            purchases = request.form.get("Purchases")

            for variable in chosenProduct:
                if price != None:
                    variable['Price'] = int(price)
                if purchases != None:
                    variable['Purchases'] = purchases
                if layaway != None:
                    variable['Layaway'] = layaway
                if inventory != None:
                    variable['Inventory'] = inventory
                if loyalty != None:
                    variable['Loyalty'] = loyalty
                if offer != None:
                    variable['Offer'] = offer
                query = {"_id": variable['_id']}
                update = {"$set": {"_id": variable['_id'], "Product": variable['Product'], "Price": variable['Price'],
                                   "Offer": variable['Offer'], "Loyalty": variable['Loyalty'],
                                   "Inventory": variable['Inventory'], "Layaway": variable['Layaway'],
                                   "Purchases": variable['Purchases']}}
                products.update_one(query, update)
            return render_template("view.html", prod=prod, s=session)
        setproducts()
        low_inventory = []
        for inv in prod:            #Check if inventory is low, and send emails letting the user know
            if int(inv['Inventory']) < 5:
                low_inventory.append(inv)
                msg = Message("The stocks of " + inv['Product'] + " are low. They will be resupplied shortly.",
                sender="softwarearchcoursework@gmail.com",
                recipients=["40484662@live.napier.ac.uk"])
                mail.send(msg)

        return render_template("view.html", prod=prod, s=session)

    return redirect(url_for('login'))


@app.route('/product/<product>', methods=['GET'])
def productpage(product):#Displays only the chosen product
    chosenProduct.clear()
    for result in prod:
        if result['_id'] == int(product):
            chosenProduct.append(result)

    return render_template("product.html", chosenProduct=chosenProduct, s=session)


@app.route("/login/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':#Authentication
        users = db["users"]
        user = users.find_one({'username': request.form['Username']})

        if user:
            if request.form['Password'] == user['password']:
                session['username'] = request.form['Username']
                return redirect(url_for('home'))
        return 'invalid username/password'

    return render_template("login.html", s=session)


@app.route("/register/", methods=['GET', 'POST'])
def register():#Registration & Authentication
    if request.method == 'POST':
        users = db["users"]
        user = users.find_one({'name': request.form['Username']})

        if user is None:
            passwrd = request.form['Password']
            users.insert({'username': request.form['Username'], 'password': passwrd})
            session['username'] = request.form['Username']
            return render_template("index.html")
    return render_template("register.html", s=session)


@app.route("/report_page/", methods=['GET', 'POST'])
def report_page():
    if 'username' in session:
        return render_template("report_page.html", s=session)
    return redirect(url_for('login'))


@app.route("/report/", methods=['GET', 'POST'])
def report():#Generates a report on the inventory and amount of purchases
    setproducts()
    report = copy.deepcopy(prod)

    for result in report:
        del result['Price']
        del result['Offer']
        del result['Loyalty']
        del result['Layaway']
    keys = report[0].keys()
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    with open("UPLOAD_FOLDER/report.csv", "w") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(report)
    return send_file('UPLOAD_FOLDER/report.csv',
                     mimetype='text/csv',
                     attachment_filename=d1 + ' report.csv',
                     as_attachment=True)


@app.route('/sign_out')
def sign_out():
    session.pop('username')
    return redirect(url_for('home'))


def setproducts():
    for result in cur:
        prod.append(result)

if __name__ == "__main__":
    app.run()
