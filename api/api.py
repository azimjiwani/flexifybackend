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

# Create user

# Prescribe exercise to user

# user get prescribed exercises

# user upload completed exercise
@app.route('/upload-completed-exercise/', methods=['POST'])
def upload_exercise():
    db_exercises = database.CompletedExercises
    content = request.get_json()
    
    # Extract data from the JSON payload
    exercise_data = {
        'name': content.get('name'),
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)