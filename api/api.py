from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo
import config
import json
import requests
import os
from pymongo import MongoClient

app = Flask(__name__)
app.config["DEBUG"] = True

username  = os.environ.get('username')
password = os.environ.get('password')

connection_url = "mongodb+srv://{}:{}@projectdata.0iwnpaz.mongodb.net/?retryWrites=true&w=majority".format(username, password)
client = pymongo.MongoClient(connection_url)
database = client.get_database('ProjectData')

@app.route('/')
def home():
    return "Backend is running"

# Create user
@app.route('/create-user/', methods=['POST']) 
def create_user():
    db_Users = database.Users
    content = request.get_json()

    # Extract data from the JSON payload
    user_data = {
        'firstName': content.get('firstName'),
        'lastName': content.get('lastName'),
        'userName': content.get('userName'),
        # 'password': content.get('password'),
        'email': content.get('email'),
        'dateOfBirth': content.get('dateOfBirth'),
        'hand': content.get('hand'),
        'injury': content.get('injury'),
        'rehabStart': content.get('rehabStart'),
        'injuryTime': content.get('injuryTime'),
        'targets': content.get('targets'),
    }
    
     # Insert the exercise data into the database
    result = db_Users.insert_one(user_data)

    if result.inserted_id:
        return jsonify({'message': 'New user created successfully'}), 200
    else:
        return jsonify({'message': 'Failed to create new user'}), 500

# Verify entered user exists
@app.route('/verify-username/', methods=['GET'])
def verify_user():
    db_Users = database.Users
    content = request.get_json()
    user = db_Users.find_one({'userName': content.get('userName')})
    if user:
        return jsonify({'status': 'success', 'message': 'User exists'}), 200
    else:
        return jsonify({'status': 'error', 'message': 'User does not exist'}), 404

# User upload goals

# Get user goals

# Prescribe exercise to user
@app.route('/prescribe-exercise/', methods=['POST'])
def prescribe_exercise():
    db_prescribed_exercises = database.PrescribedExercises
    content = request.get_json()

    # Extract data from the JSON payload
    prescribed_exercise_data = {
        'userName': content.get('userName'),
        'exerciseName': content.get('exerciseName'),
        'description': content.get('description'),
        'hand': content.get('hand'),
        'reps': content.get('reps'),
        'sets': content.get('sets'),
    }

    # Insert the presribed exercise data into the database
    result = db_prescribed_exercises.insert_one(prescribed_exercise_data)

    if result.inserted_id:
        return jsonify({'message': 'Exercise uploaded successfully'}), 200
    else:
        return jsonify({'message': 'Failed to upload exercise'}), 500

# User get prescribed exercises
@app.route('/get-prescribed-exercises/', methods=['GET'])
def get_prescribed_exercises():
    db_presribed_exercises = database.PrescribedExercises
    output = []
    for exercise in db_presribed_exercises.find():
        data = {
            key: exercise[key] if exercise[key] is not None else -1000
            for key in [
                'userName', 'exerciseName', 'description', 'hand', 'reps', 'sets'
            ]
        }
        output.append(data)

    return jsonify({'result': output})
    
# User upload completed exercise
@app.route('/upload-completed-exercise/', methods=['POST'])
def upload_exercise():
    db_exercises = database.CompletedExercises
    content = request.get_json()
    
    # Extract data from the JSON payload
    exercise_data = {
        'name': content.get('name'),
        'userName': content.get('userName'),
        'description': content.get('description'),
        'sets': content.get('sets'),
        'reps': content.get('reps'),
        'hand': content.get('hand'),
        'completedSets': content.get('completedSets', 0),  # Default to 0 if not provided
        'completedReps': content.get('completedReps', 0),  # Default to 0 if not provided
        'maxAngle': content.get('maxAngle', 0.0),  # Default to 0.0 if not provided
        'difficultyRating': content.get('difficultyRating', 0.0),  # Default to 'easy' if not provided
        'painRating': content.get('painRating', 0.0),  # Default to 0.0 if not provided
        'notes': content.get('notes', 'N/A'),  # Default to '' if not provided
    }

    # Insert the exercise data into the database
    result = db_exercises.insert_one(exercise_data)

    if result.inserted_id:
        return jsonify({'message': 'Exercise uploaded successfully'}), 200
    else:
        return jsonify({'message': 'Failed to upload exercise'}), 500

# Get app dashboard data
    # Call functions within app route to process data from database
        # Where should insight data vs collected exercise data be stored?

# Get web dashboard data 

# Get list of all exercises
@app.route('/get-all-exercises/', methods=['GET'])
def get_exercises():
    db_exercises = database.ValidExercises
    output = []
    for exercise in db_exercises.find():
        data = {
            key: exercise[key] if exercise[key] is not None else -1000
            for key in [
                'exerciseName', 'description', 'hand', 'reps', 'sets'
            ]
        }
        output.append(data)

    return jsonify({'result': output})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)