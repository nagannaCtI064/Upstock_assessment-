from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import os
app = Flask(__name__)
client = MongoClient(os.getenv('MONGODB_URI'))

db = client['train_booking']
seats_collection = db['seats']

def init_db():
    if seats_collection.count_documents({}) == 0:
        for row in range(1, 12):
            num_seats = 7 if row < 11 else 3  # 7 seats for rows 1-10, 3 seats for row 11
            for seat in range(1, num_seats + 1):
                seats_collection.insert_one({
                    "_id": (row - 1) * 7 + seat,
                    "status": False,
                    "row_number": row,
                    "seat_number": seat
                })

init_db()

# Function to get all seats with their status
def get_seats():
    return list(seats_collection.find().sort([("row_number", 1), ("seat_number", 1)]))

# Function to get available seats
def get_available_seats():
    return list(seats_collection.find({"status": False}).sort([("row_number", 1), ("seat_number", 1)]))

def book_seats(num_seats):
    available_seats = get_available_seats()

    if len(available_seats) < num_seats:
        return None  # Not enough seats available

    booked_seats = []

    # Try to book in the same row first
    for row in range(1, 12):
        seats_in_row = [seat for seat in available_seats if seat['row_number'] == row]
        if len(seats_in_row) >= num_seats:
            for seat in seats_in_row[:num_seats]:
                seats_collection.update_one({'_id': seat['_id']}, {'$set': {'status': True}})
                booked_seats.append(seat)
            return booked_seats

    
    for seat in available_seats[:num_seats]:
        seats_collection.update_one({'_id': seat['_id']}, {'$set': {'status': True}})
        booked_seats.append(seat)

    return booked_seats

@app.route('/book', methods=['POST'])
def book():
    num_seats = int(request.form['num_seats'])
    booked_seats = book_seats(num_seats)

    if booked_seats is None:
        return jsonify({'message': 'Not enough seats available'}), 400

    booked_seat_numbers = [f"Row {seat['row_number']} Seat {seat['seat_number']}" for seat in booked_seats]
    
    
    return render_template('index.html', 
                           booked_seat_numbers=book_seat_numbers,
                           seats=get_seats())


@app.route('/')
def home():
    seats = get_seats()  # Get all seats with status
    return render_template('index.html', seats=seats)

if __name__ == '__main__':
    app.run(debug=True)
