from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from db import MONGO_URI
from bson.errors import InvalidId 

# ✅ Initialize Flask app
app = Flask(__name__)
CORS(app)

# ✅ Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['careconnect']
tasks_collection = db['tasks']
users_collection = db['users']

# ✅ Home route
@app.route('/')
def home():
    return "CareConnect API Running"

# ✅ Request Help (Elder)
@app.route('/request-help', methods=['POST'])
def request_help():
    data = request.get_json()
    name = data.get('name')
    task = data.get('task')
    location = data.get('location')
    date = data.get('date')
    time = data.get('time')
    notes = data.get('notes')

    status = data.get('status', 'pending')  # Default status

    if not all([name, task, location]):
        return jsonify({'error': 'Missing fields'}), 400

    task_entry = {
    'name': name,
    'task': task,
    'location': location,
    'date': date,
    'time': time,
    'notes': notes,
    'status': status
}

    tasks_collection.insert_one(task_entry)
    return jsonify({'message': 'Task submitted successfully'}), 201

# ✅ Get All Requests (Volunteer)
@app.route('/get-requests', methods=['GET'])
def get_requests():
    tasks = list(tasks_collection.find())
    for task in tasks:
        task['_id'] = str(task['_id'])  # Convert ObjectId to string
    return jsonify(tasks)

# ✅ Update Status (Volunteer Accept/Decline)
@app.route('/update-status', methods=['POST'])
def update_status():
    data = request.get_json()
    task_id = data.get('id')
    new_status = data.get('status')

    if not task_id or not new_status:
        return jsonify({'error': 'Missing task ID or status'}), 400

    try:
        # ✅ Validate ObjectId format
        object_id = ObjectId(task_id)

        result = tasks_collection.update_one(
            {'_id': object_id},
            {'$set': {'status': new_status}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Task not found'}), 404

        return jsonify({'message': 'Status updated'}), 200

    except InvalidId:
        return jsonify({'error': 'Invalid task ID format'}), 400

    except Exception as e:
        print("❌ Error updating task:", e)
        return jsonify({'error': 'Server error'}), 500

# ✅ Signup (Elder or Volunteer)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')  # 'elder' or 'volunteer'

    if not all([email, password, role]):
        return jsonify({'error': 'Missing fields'}), 400

    if users_collection.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 409

    users_collection.insert_one({
        'email': email,
        'password': password,
        'role': role
    })

    return jsonify({'message': 'Signup successful'}), 201

# ✅ Login
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = users_collection.find_one({'email': email, 'password': password})
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401

    return jsonify({
        'email': user['email'],
        'role': user['role']
    }), 200

# ✅ Start the server
if __name__ == '__main__':
    app.run(debug=True)
