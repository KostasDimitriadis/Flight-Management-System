from flask import Flask, abort, flash, redirect, render_template,request, session
from pymongo import MongoClient
from bson import ObjectId
app = Flask("airlines")
client = MongoClient('mongodb://localhost:27017/')
db = client.DigitalAirlines
userCollection = db.users
availableCollection = db.availableFlights
bookingsCollection = db.bookingsCollection
app.secret_key = 'key'
@app.route('/register', methods=['POST'])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get the registration data from the request
        username = request.form.get('username')
        surname = request.form.get('surname')
        email = request.form.get('email')
        password = request.form.get('password')
        date_of_birth = request.form.get('date_of_birth')
        country = request.form.get('country')
        id = request.form.get('id')

        existing_user = userCollection.find_one({'$or': [{'email': email}, {'username': username}]})

        if existing_user:
            return 'Email or username already exists'

        # Create a new user document
        new_user = {
            'username': username,
            'surname': surname,
            'email': email,
            'password': password,
            'date_of_birth': date_of_birth,
            'country': country,
            'id': id,
            'role': 'ordinary' #default role 
        }

        # Insert the new user document into the MongoDB collection
        result = userCollection.insert_one(new_user)

        if result.inserted_id:
            return render_template('login.html')
        else:
            return 'Registration failed'
    else:
        return render_template('register.html')

    
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
      

        user = userCollection.find_one({'email': email, 'password': password})
        if user:
            session['email'] = email
            session['role'] = user['role']
          

            if user['role'] == 'ordinary':
                return render_template('homepage.html')
            elif user['role'] == 'admin':
                return render_template('adminpage.html')
        else:
            return 'Invalid credentials', 401
    else:
        return render_template('login.html')



@app.route('/logout',methods=['GET'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/homepage',methods=['GET'])
def home():
    return render_template('homepage.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    # Check if the user is logged in
    if 'email' not in session:
        if request.method == 'POST':
            return redirect('/login')
        else:
            return render_template('login.html')

    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        date = request.form.get('date')

        query = {}
        if origin:
            query['origin'] = origin
        if destination:
            query['destination'] = destination
        if date:
            query['date'] = date

        results = availableCollection.find(query)
        return render_template('flight_search_result.html', results=results)

    return render_template('flight_search.html')

@app.route('/show_all_flights', methods=['POST'])
def show_all_flights():
    flights = availableCollection.find()
    return render_template('flight_search_result.html', results=flights)


@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if 'email' not in session:
        if request.method == 'POST':
            return redirect('/login')
        else:
            return render_template('login.html')

    if request.method == 'POST':
        flight_id = request.form.get('flight_id')
        name = request.form.get('name')
        surname = request.form.get('surname')
        date_of_birth = request.form.get('date_of_birth')
        email = request.form.get('email')
        ticket_type = request.form.get('ticket_type')

        flight = availableCollection.find_one({'_id': ObjectId(flight_id)})  # Convert flight_id to ObjectId
        if not flight:
            return 'Flight not found'

        existing_reservation = bookingsCollection.find_one({'flight_id': flight_id, 'email': email})
        if existing_reservation:
            return 'You have already made a reservation for this flight'

        new_reservation = {
            'flight_id': ObjectId(flight_id),  # Convert flight_id to ObjectId
            'name': name,
            'surname': surname,
            'date_of_birth': date_of_birth,
            'email': email,
            'ticket_type': ticket_type
        }

        result = bookingsCollection.insert_one(new_reservation)

        if result.inserted_id:
            return render_template('homepage.html')
        else:
            return 'Failed to make a reservation'

    else:
        flights = availableCollection.find()
        return render_template('reservation.html', flights=flights)


@app.route('/bookings', methods=['GET', 'POST'])
def bookings():
    if 'email' not in session:
        if request.method == 'POST':
            return redirect('/login')
        else:
            return redirect('/login')

    

    bookings = bookingsCollection.find({'email': session['email']})
    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel', methods=['GET', 'POST'])
def cancel():
    if 'email' not in session:
        if request.method == 'POST':
            return redirect('/login')
        else:
            return render_template('login.html')

    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')

        reservation = bookingsCollection.find_one({'_id': ObjectId(reservation_id)})
        if not reservation:
            return 'Reservation not found'

        flight_id = reservation['flight_id']
        flight = availableCollection.find_one({'_id': ObjectId(flight_id)})
        if not flight:
            return 'Flight not found'

      

        # Update the flight document in the MongoDB collection
        availableCollection.update_one({'_id': ObjectId(flight_id)}, {'$set': flight})

        # Delete the reservation from the MongoDB collection
        bookingsCollection.delete_one({'_id': ObjectId(reservation_id)})

        return render_template('homepage.html')

    else:
        bookings = bookingsCollection.find({'email': session['email']})
        return render_template('bookings.html', bookings=bookings)
    
@app.route('/delete_account', methods=['GET', 'POST', 'DELETE'])
def delete_account():
    
    if 'email' not in session:
        return redirect('/login')

   
    email = session['email']

    userCollection.delete_one({'email': email})

    session.clear()

   
    return render_template('homepage.html')

########################################################################################################################################
def is_user_admin():
    email = request.form['email']
    user = userCollection.find_one({'email': email})
    return user and user['role'] == 'admin'

@app.before_request
def restrict_access():
    # List of restricted pages for administrators only
    admin_pages = ['/adminpage', '/create','/renewal']

    # Get the current path
    path = request.path

    # Exclude the login route from the check
    if path == '/login':
        return

    # Check if the user is an ordinary user and trying to access an admin page
    if path in admin_pages and ('email' not in session or session['role'] != 'admin'):
        return redirect('/login')

@app.route('/adminpage',methods=['GET'])
def ahome():
    return render_template('adminpage.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'email' not in session or session['role'] != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        date = request.form.get('date')
        tickets_business = int(request.form.get('tickets_business'))
        cost_business = float(request.form.get('cost_business'))
        tickets_economy = int(request.form.get('tickets_economy'))
        cost_economy = float(request.form.get('cost_economy'))

        
        new_flight = {
            'origin': origin,
            'destination': destination,
            'date': date,
            'tickets_business': tickets_business,
            'cost_business': cost_business,
            'tickets_economy': tickets_economy,
            'cost_economy': cost_economy
        }

     
        result = availableCollection.insert_one(new_flight)
        if result.inserted_id:
            return redirect('/adminpage')
        else:
            return 'Failed to add flight'

    else:
        flights = availableCollection.find()
        return render_template('create.html', flights=flights)
@app.route('/renewal', methods=['GET', 'POST'])
def renewal():
    if 'email' not in session or session['role'] != 'admin':
        return redirect('/login')

    if request.method == 'POST':
        flight_id = request.form.get('flight_id')
        new_cost_business = float(request.form.get('new_cost_business'))
        new_cost_economy = float(request.form.get('new_cost_economy'))

        # Update the ticket prices in the MongoDB collection for the selected flight
        availableCollection.update_one({'_id': ObjectId(flight_id)},
                                       {'$set': {'cost_business': new_cost_business, 'cost_economy': new_cost_economy}})

        return redirect('/adminpage')  # Redirect to the admin_flights function or any other appropriate page

    else:
        flights = availableCollection.find()
        return render_template('renewal.html', flights=flights)
def has_reservations(flight_id):
    reservations = list(bookingsCollection.find({'flight_id': flight_id}))
    return len(reservations) > 0


@app.route('/adminFlights', methods=['GET','POST'])
def adminFlights():
    flights = availableCollection.find()
    return render_template('adminFlights.html', flights=flights,has_reservations=has_reservations)

@app.route('/delete-flight', methods=['POST'])
def delete_flight():
    if 'email' not in session or session['role'] != 'admin':
        return redirect('/login')
    flight_id = request.form.get('flight_id')

    reservations = bookingsCollection.find({'flight_id': flight_id})

    if len(list(reservations)) > 0:
        return 'Cannot delete the flight. There are existing reservations.'

    result = availableCollection.delete_one({'_id': ObjectId(flight_id)})

    if result.deleted_count > 0:
        return redirect('/adminFlights')
    else:
        return 'Failed to delete the flight.'
    
@app.route('/flight-details/<flight_id>', methods=['GET'])
def flight_details(flight_id):
    flight = availableCollection.find_one({'_id': ObjectId(flight_id)})
    if flight:
        return render_template('flight_details.html', flight=flight)
    else:
        abort(404)



if __name__ == '__main__':
    app.run()