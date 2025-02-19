from flask_bootstrap import Bootstrap5
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
import random

'''
Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

Pip install the packages from requirements.txt
On Windows: python -m pip install -r requirements.txt
On MacOS: pip3 install -r requirements.txt
'''

app = Flask(__name__)
Bootstrap5(app)  # Initialize Bootstrap with the app

# Configure the app with the database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(app)
# db.init_app(app) # this only needs to be run once, otherwise returns an error

# Create a table
# Mapped and mapped_column introduced in day 66 causing an error, updated to traditional method of defining models
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)

    # Create new entries in dictionary using column name as key and column value as the assigned value
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

# New function inserted for day 88 project
@app.route("/random")
def get_random_cafe():
    result = db.session.execute(db.select(Cafe))
    all_cafes = result.scalars().all()
    random_cafe = random.choice(all_cafes)
    # converts the relevant row Object in database to a dictionary and then converts dictionary to JSON
    return jsonify(cafe=random_cafe.to_dict())

@app.route("/all")
def get_all_cafes():
    result = db.session.execute(db.select(Cafe).order_by(Cafe.name))
    all_cafes = result.scalars().all()
    return jsonify(cafe=[cafe.to_dict() for cafe in all_cafes])

@app.route("/search_loc")
def get_cafe_at_location():
    query_location = request.args.get("loc")
    # .where() allows user to select and filter results
    result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location))
    all_cafes = result.scalars().all() # Can provide more than one cafe per location
    if all_cafes:
        return jsonify(cafe=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404

@app.route("/search_loc_and_wifi")
def get_cafe_at_location_with_wifi():
    query_location = request.args.get("loc")
    query_wifi = request.args.get("wifi")
    # .where() allows user to select and filter results
    result = db.session.execute(db.select(Cafe).where(Cafe.location == query_location, Cafe.has_wifi == query_wifi))
    all_cafes = result.scalars().all() # Can provide more than one cafe per location
    if all_cafes:
        return jsonify(cafe=[cafe.to_dict() for cafe in all_cafes])
    else:
        return jsonify(error={"Not Found": "Sorry, we don't have a cafe at that location."}), 404

@app.route("/post_new_cafe", methods=["POST"])
def post_new_cafe():
    # Ensure required fields are present
    name = request.form.get("name")
    if not name:
        return jsonify(response={"error": "Cafe name is required."}), 400

    # Add other validations as needed
    new_cafe = Cafe(
        name=name,
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("loc"),
        has_sockets=bool(request.form.get("sockets")),
        has_toilet=bool(request.form.get("toilet")),
        has_wifi=bool(request.form.get("wifi")),
        can_take_calls=bool(request.form.get("calls")),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
    )

    # Add new cafe to the session and commit in database
    db.session.add(new_cafe)
    db.session.commit()
    return jsonify(response={"success": "Successfully added the new cafe."})

# Updates the price of black coffee in a cafe
@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def patch_new_price(cafe_id):
    new_price = request.args.get("new_price")
    # Below line of code replaced as get_or_404 returns a standard 404 message that renders the else statement useless
    # cafe_to_update = db.get_or_404(Cafe, cafe_id)
    # Below get function returns a value if it matches or None, code progresses to the else statement
    cafe_to_update = db.session.get(Cafe, cafe_id)
    if cafe_to_update:
        # this line assigns the 'new_price' to the 'coffee_price' of the relevant cafe using cafe's id
        cafe_to_update.coffee_price = new_price
        db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."}), 200
    else:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404

# Deletes a cafe with a particular id. Change the request type to 'Delete' in Postman
@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    api_key = request.args.get("api-key")
    if api_key == "TopSecretAPIKey":
        cafe = db.get_or_404(Cafe, cafe_id)
        if cafe:
            db.session.delete(cafe)
            db.session.commit()
            return jsonify(response={"success": "Successfully deleted the cafe from the database."}), 200
        else:
            return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."}), 404
    else:
        return jsonify(error={"Forbidden": "Sorry, that's not allowed. Make sure you have the correct api_key"}), 403

if __name__ == '__main__':
    app.run(debug=True, port=5002)
