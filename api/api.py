from flask import Flask, jsonify, request
from flask_cors import CORS
import pymongo
import config
import json
import requests
import os
from datetime import datetime, date, timedelta
from pymongo import MongoClient
from bson.json_util import dumps
import uuid
from datetime import datetime, timedelta


app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app) 

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
    db_users = database.Users
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
        'targetWristFlexion': content.get('targetWristFlexion'),
        'targetWristExtension': content.get('targetWristExtension'),
        'targetUlnarDeviation': content.get('targetUlnarDeviation'),
        'targetRadialDeviation': content.get('targetRadialDeviation'),
        'currentWeek': 0,
        'exercisesCompleted': 0,
        'totalExercises': 0,
        'maxWristFlexion': 0,
        'maxWristExtension': 0,
        'maxUlnarDeviation': 0,
        'maxRadialDeviation': 0,
        'wfLastWeek': 0, 'wfLastMonth': 0,'wfAllTime': 0,
        'weLastWeek': 0, 'weLastMonth': 0,'weAllTime': 0,
        'udLastWeek': 0, 'udLastMonth': 0,'udAllTime': 0,
        'rdLastWeek': 0, 'rdLastMonth': 0,'rdAllTime': 0,
    }

    # Calculate rehabEnd
    rehabStart = datetime.strptime(user_data['rehabStart'], '%Y-%m-%d')
    injuryTime = user_data['injuryTime']
    rehabEnd = rehabStart + timedelta(weeks=injuryTime)
    user_data['rehabEnd'] = rehabEnd.strftime('%Y-%m-%d')

     # Insert the exercise data into the database
    result = db_users.insert_one(user_data)

    if result.inserted_id:
        return jsonify({'message': 'New user created successfully'}), 200
    else:
        return jsonify({'message': 'Failed to create new user'}), 500

# Verify entered user exists
@app.route('/verify-username/', methods=['GET'])
def verify_user():
    db_users = database.Users
    username = request.args.get('userName')

    if username is None:
        return jsonify({'message': 'Username is required'}), 400
    else:
        user = db_users.find_one({'userName': username})
        if user is not None:
            return 'true', 200
        else: 
            return 'false', 404

# User upload goals
@app.route('/upload-goals/', methods=['POST'])
def upload_goals():
    db_goals = database.Goals
    content = request.get_json()
    
    # Extract data from the JSON payload
    goal_data = {
        'userName': content.get('userName'),
        'goal1': content.get('goal1'),
        'goal2': content.get('goal2'),
        'goal3': content.get('goal3'),
    }

# Update the goal data in the database, or insert it if it doesn't exist
    result = db_goals.update_one(
        {'userName': goal_data['userName']},  # filter
        {'$set': goal_data},  # update
        upsert=True  # create a new document if no document matches the filter
    )

    if result.upserted_id or result.modified_count > 0:
        return jsonify({'message': 'Goal(s) updated successfully'}), 200
    else:
        return jsonify({'message': 'Failed to update goal(s)'}), 500

# Get user goals
@app.route('/get-goals/', methods=['GET'])
def get_goals():
    username = request.args.get('userName')
    db_goals = database.Goals
    output = []

    if username is None:
        return jsonify({'message': 'Username is required'}), 400
    else:
        goal = db_goals.find({'userName': username})
        if goal is not None:
            for goals in goal:
                data = {
                    key: goals[key] if goals[key] is not None else -1000
                    for key in [
                        'goal1', 'goal2', 'goal3'
                    ]
                }
                output.append(data)
            return jsonify({'result': output})

# Upload patient plan
@app.route('/upload-patient-plan/', methods=['POST'])
def upload_patient_plan():
    db_plans = database.Plans
    content = request.get_json()

    # Extract data from the JSON payload
    plan_data = {
        'userName': content.get('userName'),
        'rehabWeeks': content.get('rehabWeeks'),
        'sets': content.get('sets'),
        'reps': content.get('reps'),
    }

# Update the plan data in the database, or insert it if it doesn't exist
    result = db_plans.update_one(
        {'userName': plan_data['userName']},  # filter
        [{'$set': plan_data}],  # update
        upsert=True  # create a new document if no document matches the filter
    )

    # Populate prescribed exercises collection with exercises for user based on patient plan 
    # time.sleep(3)
    db_prescribed_exercises = database.PrescribedExercises
    db_valid_exercises = database.ValidExercises
    db_users = database.Users
    content = request.get_json()

    # Extract the username from the JSON payload
    username = content['userName']
    # 'userName': content.get('userName'),

    # Fetch valid exercises, relevant user plan
    valid_exercises = db_valid_exercises.find_one({'uniqueId' : '9999'})
    plan = db_plans.find_one({'userName': username})
    user = db_users.find_one({'userName': username})

    # Extract exercise names, rehabWeeks, sets, and reps information from the plan
    exercises = valid_exercises['exercises']
    rehabWeeks = plan['rehabWeeks']
    sets = plan['sets']
    reps = plan['reps']
    hand = user['hand']
    rehabStart = user['rehabStart']
    
    totalDays = len(rehabWeeks) * len(rehabWeeks[0])

    currentDate = datetime.strptime(rehabStart, '%Y-%m-%d')

    for day in range(totalDays):
        if day % 7 == 0:
            dailyExerciseAmount = rehabWeeks[day//7][0]
        for session in range(dailyExerciseAmount):
            for type in exercises:
                uniqueId = str(uuid.uuid4())
                prescribed_exercise = {
                    'uniqueId': uniqueId,
                    'userName': username,
                    'exerciseName': type,
                    'hand': hand,
                    'reps': reps[day//7],
                    'sets': sets[day//7],
                    'completedReps': 0,
                    'completedSets': 0,
                    'maxAngle': 0,
                    'difficultyRating': 0,
                    'painRating': 0,
                    'notes': 'N/A',
                    'date': (currentDate + timedelta(days=day)).strftime("%Y-%m-%d"),
                    'isCompleted': False
                }
                insertResult = db_prescribed_exercises.insert_one(prescribed_exercise) 

    if result.upserted_id or result.modified_count > 0:
        return jsonify({'message': 'Plan updated successfully'}), 200
    else:
        return jsonify({'message': 'Failed to update plan'}), 404

# Get patient plan
@app.route('/get-patient-plan/', methods=['GET'])
def get_patient_plan():
    db_plans = database.Plans
    userName = request.args.get('userName')
    output = []

    if userName is None:
        return jsonify({'message': 'Username is required'}), 400
    else:
        plan = db_plans.find({'userName': userName})
        if plan is not None:
            for plans in plan:
                data = {
                    key: plans[key] if plans[key] is not None else -1000
                    for key in [
                        'rehabWeeks', 'sets', 'reps'
                    ]
                }
                output.append(data)
            return jsonify({'result': output})         

# Prescribe exercise to user
@app.route('/prescribe-exercise/', methods=['POST'])
def prescribe_exercise():
    db_prescribed_exercises = database.PrescribedExercises
    content = request.get_json()
    uniqueId = str(uuid.uuid4())

    # Extract data from the JSON payload
    prescribed_exercise_data = {
        'uniqueId': uniqueId, 
        'userName': content.get('userName'),
        'exerciseName': content.get('exerciseName'),
        'hand': content.get('hand'),
        'reps': content.get('reps'),
        'sets': content.get('sets'),
        'date': content.get('date'),
        'isCompleted' : content.get('isCompleted', False)
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
    username = request.args.get('userName')
    date = request.args.get('date')
    db_presribed_exercises = database.PrescribedExercises
    output = []

    if username and date:
        exercises = db_presribed_exercises.find({'userName': username, 'date': date})
        for exercise in exercises:
            data = {
                key: exercise[key] if key in exercise and exercise[key] is not None else -1000
                for key in [
                    'userName', 'exerciseName', 'hand', 'reps', 'sets', 'date', 'isCompleted', 'uniqueId'
                ]
            }
            output.append(data)
        return jsonify({'result': output})
    
    elif username:
        exercises = db_presribed_exercises.find({'userName': username})
        for exercise in exercises:
            data = {
                key: exercise[key] if key in exercise and exercise[key] is not None else -1000
                for key in [
                    'userName', 'exerciseName', 'hand', 'reps', 'sets', 'date', 'isCompleted', 'uniqueId'
                ]
            }
            output.append(data)
        return jsonify({'result': output})
    else:
        return jsonify({'message': 'Username and date are required'}), 400

# Get completed exercises
@app.route('/get-completed-exercises/', methods=['GET'])
def get_completed_exercises():
    username = request.args.get('userName')
    date = request.args.get('date')
    db_completed_exercises = database.PrescribedExercises
    output = []

    if username and date:
        exercises = db_completed_exercises.find({'userName': username, 'date': date})
    elif username:
        exercises = db_completed_exercises.find({'userName': username})
    else:
        return jsonify({'message': 'Username and date are required'}), 400

    for exercise in exercises:
        data = {
            key: exercise[key] if exercise[key] is not None else -1000
            for key in [
                'userName',
                'exerciseName', 
                'hand', 
                'reps', 
                'sets', 
                'completedReps', 
                'completedSets', 
                'maxAngle', 
                'difficultyRating', 
                'painRating', 
                'notes', 
                'date',
                'isCompleted',
                'uniqueId'
            ]
        }
        output.append(data)
    
    return jsonify({'result': output})

# User upload completed exercise
@app.route('/upload-completed-exercise/', methods=['POST'])
def upload_exercise():
    db_exercises = database.PrescribedExercises
    username = request.args.get('userName')
    uniqueId = request.args.get('uniqueId')
    content = request.get_json()

    myQuery = { "uniqueId": uniqueId}
    newValues = {"$set":
                 {"isCompleted": True,
                  "completedReps": content['completedReps'],
                  "completedSets": content['completedSets'],
                  "maxAngle": content['maxAngle'],
                  "difficultyRating": content['difficultyRating'],
                  "painRating": content['painRating'],
                  "notes": content['notes']}
                 }
    
    result = db_exercises.update_one(myQuery,newValues)

    # get user from DB
    db_users = database.Users

    if uniqueId is None:
        return jsonify({'message': 'Unique ID is required'}), 400

    if username is None:
        return jsonify({'message': 'Username is required'}), 300
    
    user = db_users.find_one({'userName': username})

    if user is not None:
        userWeek = user['currentWeek']

        userExercisesCompleted = user['exercisesCompleted']
        userMaxWristFlexion = user['maxWristFlexion']
        userMaxWristExtension = user['maxWristExtension']
        userMaxUlnarDeviation = user['maxUlnarDeviation']
        userMaxRadialDeviation = user['maxRadialDeviation']

        # compute number of weeks between userWeek and current date
        userWeek = datetime.strptime(user['rehabStart'], '%Y-%m-%d')
        currentDate = datetime.now()
        diff = currentDate - userWeek
        currentWeek = diff.days // 7
        if currentWeek < 1:
            currentWeek = 1

        # update user week, exercises completed, and max angles
        userQuery = {"userName": username}
        userNewValues = {"$set": 
                        {
                            "currentWeek": currentWeek,
                            "exercisesCompleted": userExercisesCompleted + 1
                        }
                        }
        
        if content['name'] == "Wrist Flexion":
            userNewValues['$set']['maxWristFlexion'] = max(userMaxWristFlexion, content['maxAngle'])

            # all time percent difference
            date = user['rehabStart']
            firstEntry = db_exercises.find_one({'userName': username, 'date': date})
            if firstEntry is not None:
                firstEntryMaxAngle = firstEntry['maxAngle']
                allTimePercentDifference = ((content['maxAngle'] - firstEntryMaxAngle) / firstEntryMaxAngle) * 100
                userNewValues['$set']['wfAllTime'] = allTimePercentDifference

            # last week percent difference
            lastWeek = datetime.now() - timedelta(days=7)
            date = lastWeek.strftime('%Y-%m-%d')
            lastWeekEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastWeekEntry is not None:
                lastWeekEntryMaxAngle = lastWeekEntry['maxAngle']
                lastWeekPercentDifference = ((content['maxAngle'] - lastWeekEntryMaxAngle) / lastWeekEntryMaxAngle) * 100
                userNewValues['$set']['wfLastWeek'] = lastWeekPercentDifference

            # last month percent difference
            lastMonth = datetime.now() - timedelta(days=30)
            date = lastMonth.strftime('%Y-%m-%d')
            lastMonthEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastMonthEntry is not None:
                lastMonthEntryMaxAngle = lastMonthEntry['maxAngle']
                lastMonthPercentDifference = ((content['maxAngle'] - lastMonthEntryMaxAngle) / lastMonthEntryMaxAngle) * 100
                userNewValues['$set']['wfLastMonth'] = lastMonthPercentDifference
        
        elif content['name'] == "Wrist Extension":
            userNewValues['$set']['maxWristExtension'] = max(userMaxWristExtension, content['maxAngle'])

            # all time percent difference
            date = user['rehabStart']
            firstEntry = db_exercises.find_one({'userName': username, 'date': date})
            if firstEntry is not None:
                firstEntryMaxAngle = firstEntry['maxAngle']
                allTimePercentDifference = ((content['maxAngle'] - firstEntryMaxAngle) / firstEntryMaxAngle) * 100
                userNewValues['$set']['weAllTime'] = allTimePercentDifference

            # last week percent difference
            lastWeek = datetime.now() - timedelta(days=7)
            date = lastWeek.strftime('%Y-%m-%d')
            lastWeekEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastWeekEntry is not None:
                lastWeekEntryMaxAngle = lastWeekEntry['maxAngle']
                lastWeekPercentDifference = ((content['maxAngle'] - lastWeekEntryMaxAngle) / lastWeekEntryMaxAngle) * 100
                userNewValues['$set']['weLastWeek'] = lastWeekPercentDifference

            # last month percent difference
            lastMonth = datetime.now() - timedelta(days=30)
            date = lastMonth.strftime('%Y-%m-%d')
            lastMonthEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastMonthEntry is not None:
                lastMonthEntryMaxAngle = lastMonthEntry['maxAngle']
                lastMonthPercentDifference = ((content['maxAngle'] - lastMonthEntryMaxAngle) / lastMonthEntryMaxAngle) * 100
                userNewValues['$set']['weLastMonth'] = lastMonthPercentDifference
        
        elif content['name'] == "Ulnar Deviation":
            userNewValues['$set']['maxUlnarDeviation'] = max(userMaxUlnarDeviation, content['maxAngle'])

            # all time percent difference
            date = user['rehabStart']
            firstEntry = db_exercises.find_one({'userName': username, 'date': date})
            if firstEntry is not None:
                firstEntryMaxAngle = firstEntry['maxAngle']
                allTimePercentDifference = ((content['maxAngle'] - firstEntryMaxAngle) / firstEntryMaxAngle) * 100
                userNewValues['$set']['udAllTime'] = allTimePercentDifference

            # last week percent difference
            lastWeek = datetime.now() - timedelta(days=7)
            date = lastWeek.strftime('%Y-%m-%d')
            lastWeekEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastWeekEntry is not None:
                lastWeekEntryMaxAngle = lastWeekEntry['maxAngle']
                lastWeekPercentDifference = ((content['maxAngle'] - lastWeekEntryMaxAngle) / lastWeekEntryMaxAngle) * 100
                userNewValues['$set']['udLastWeek'] = lastWeekPercentDifference

            # last month percent difference
            lastMonth = datetime.now() - timedelta(days=30)
            date = lastMonth.strftime('%Y-%m-%d')
            lastMonthEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastMonthEntry is not None:
                lastMonthEntryMaxAngle = lastMonthEntry['maxAngle']
                lastMonthPercentDifference = ((content['maxAngle'] - lastMonthEntryMaxAngle) / lastMonthEntryMaxAngle) * 100
                userNewValues['$set']['udLastMonth'] = lastMonthPercentDifference

        elif content['name'] == "Radial Deviation":
            userNewValues['$set']['maxRadialDeviation'] = max(userMaxRadialDeviation, content['maxAngle'])

            # all time percent difference
            date = user['rehabStart']
            firstEntry = db_exercises.find_one({'userName': username, 'date': date})
            if firstEntry is not None:
                firstEntryMaxAngle = firstEntry['maxAngle']
                allTimePercentDifference = ((content['maxAngle'] - firstEntryMaxAngle) / firstEntryMaxAngle) * 100
                userNewValues['$set']['rdAllTime'] = allTimePercentDifference

            # last week percent difference
            lastWeek = datetime.now() - timedelta(days=7)
            date = lastWeek.strftime('%Y-%m-%d')
            lastWeekEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastWeekEntry is not None:
                lastWeekEntryMaxAngle = lastWeekEntry['maxAngle']
                lastWeekPercentDifference = ((content['maxAngle'] - lastWeekEntryMaxAngle) / lastWeekEntryMaxAngle) * 100
                userNewValues['$set']['rdLastWeek'] = lastWeekPercentDifference

            # last month percent difference
            lastMonth = datetime.now() - timedelta(days=30)
            date = lastMonth.strftime('%Y-%m-%d')
            lastMonthEntry = db_exercises.find_one({'userName': username, 'date': date})
            if lastMonthEntry is not None:
                lastMonthEntryMaxAngle = lastMonthEntry['maxAngle']
                lastMonthPercentDifference = ((content['maxAngle'] - lastMonthEntryMaxAngle) / lastMonthEntryMaxAngle) * 100
                userNewValues['$set']['rdLastMonth'] = lastMonthPercentDifference
        
        updateResult = db_users.update_one(userQuery, userNewValues)

        if updateResult.modified_count > 0:
            return jsonify({'message': 'matched'}), 200
        else:
            return jsonify({'message': 'not matched'}), 305

    else:
        return jsonify({'message': 'User not found'}), 404

# Get user info for mobile dashboard
@app.route('/get-profile-data-app/', methods=['GET'])
def get_profile_data():
    username = request.args.get('userName')
    db_users = database.Users

    if username is None:
        return jsonify({'message': 'Username is required'}), 400
    
    user = db_users.find_one({'userName': username})

    data = {key: user[key] if key in user and user[key] is not None else -1000
                for key in [
                    'firstName', 'lastName',
                    'userName',
                    'hand', 'injury',
                    'rehabStart', 'rehabEnd'
                    'goals',
                ]
            }
    return jsonify({'result': data})

# Get user info for mobile dashboard
@app.route('/get-dashboard-data-app/', methods=['GET'])
def get_dashboard_data():
    username = request.args.get('userName')
    db_users = database.Users

    if username is None:
        return jsonify({'message': 'Username is required'}), 400
    
    user = db_users.find_one({'userName': username})

    data = {key: user[key] if key in user and user[key] is not None else -1000
                for key in [
                    'currentWeek', 'injuryTime',
                    'exercisesCompleted', 'totalExercises',
                    'maxWristFlexion', 'targetWristFlexion',
                    'maxWristExtension', 'targetWristExtension',
                    'maxUlnarDeviation', 'targetUlnarDeviation',
                    'maxRadialDeviation', 'targetRadialDeviation',
                ]
            }
    return jsonify({'result': data})

# Get app dashboard data
#     # Call functions within app route to process data from database
#         # Where should insight data vs collected exercise data be stored?
# @app.route('/get-app-dashboard/', methods=['GET'])
# def get_app_dashboard():
#     username = request.args.get('userName')
#     exercisename = request.args.get('name')
#     db_users = database.users
#     db_completed_exercises = database.CompletedExercises
#     ang_diff = {}
#     output = []

#     # Verify if username and/or exercisename is provided
#     if username and exercisename:
#         users = db_users.find({'userName': username})
#         db_completed_exercises = database.CompletedExercises.find({'userName': username})
#         total_completed_exercises = db_completed_exercises.count_documents({'userName' : username})
#         total_prescribed_exercises = database.PrescribedExercises.count_documents({'userName' : username})
        
#         # Time periods for insights
#         week_ago = datetime.now() - timedelta(days=7)
#         month_ago = datetime.now() - timedelta(days=30)
        
#         # Find and sort completed exercises for user, by date
#         completed_exercises = list(db_completed_exercises.find({
#             'userName': username, 
#             'name': exercisename,
#             'date': {'$gte': month_ago.strftime('%Y/%m/%d')}
#         }).sort('date', -1))

#         # Calculate the difference in max angle for each period
#         periods = {
#             'lastExercise': completed_exercises[:2],
#             'last7Days': [exercise for exercise in completed_exercises if exercise['date'] >= week_ago.strftime('%Y-%m-%d')][:2],
#             'last30Days': completed_exercises[:2]
#         }
        
#         for period, exercises in periods.itemsI():
#             if len(exercise) >= 2:
#                 last_exercise = exercises[0]
#                 second_last_exercise = exercise[1]
#                 angle_difference = last_exercise['maxAngle'] - second_last_exercise['maxAngle']
#                 ang_diff['angleDifference'] = angle_difference

#     elif username:
#         users = db_users.find({'userName': username})
#         db_completed_exercises = database.CompletedExercises.find({'userName': username})
#         db_prescribed_exercises = database.PrescribedExercises.find({'userName': username})
#         total_completed_exercises = db_completed_exercises.count_documents({'userName' : username})
#         total_prescribed_exercises = database.PrescribedExercises.count_documents({'userName' : username})
#     else:
#         return jsonify({'message': 'Username is required'}), 400
    
#     for user in users:
#         userData = {
#             key: user[key] if user[key] is not None else -1000
#             for key in [
#                 'userName', 'rehabStart'
#             ]
#         }
#         # Calculate elapsed time since rehab start
#         rehab_start = datetime.strptime(userData['rehabStart'], '%Y/%m/%d')
#         time_progress = datetime.now() - rehab_start
#         userData['timeProgress'] = time_progress.days // 7
    
#     for exercise in db_completed_exercises:
#         exerciseData = {
#             key: exercise[key] if exercise[key] is not None else -1000
#             for key in [
#                 'maxAngle', 'name'
#             ]
#         }
#         exerciseData['totalCompletedExercises'] = total_completed_exercises
#         exerciseData['totalPrescribedExercises'] = total_prescribed_exercises

#         output.append(userData)
#         output.append(exerciseData)
#         output.append(ang_diff)
    
#     return jsonify({'results': output})

# Get web patient dashboard data 
@app.route('/get-dashboard-data-web/', methods=['GET'])
def get_web_dashboard_data_():
    username = request.args.get('userName')
    db_users = database.Users

    if username is None:
        return jsonify({'message': 'Username is required'}), 400

    user = db_users.find_one({'userName': username})

    if user is None:
        return jsonify({'message': 'User not found'}), 404

    data = {key: user[key] if key in user and user[key] is not None else 0
                for key in [
                    'firstName', 'lastName',
                    'userName',
                    'email', 'dateOfBirth',
                    'hand', 'injury',
                    'rehabStart', 'rehabEnd',
                    'goals',
                    'currentWeek', 'injuryTime',
                    'exercisesCompleted', 'totalExercises',
                    'maxWristFlexion', 'targetWristFlexion',
                    'maxWristExtension', 'targetWristExtension',
                    'maxUlnarDeviation', 'targetUlnarDeviation',
                    'maxRadialDeviation', 'targetRadialDeviation',
                    'wfLastWeek', 'wfLastMonth', 'wfAllTime',
                    'weLastWeek', 'weLastMonth', 'weAllTime',
                    'udLastWeek', 'udLastMonth', 'udAllTime',
                    'rdLastWeek', 'rdLastMonth', 'rdAllTime'
                ]
            }
    return jsonify({'result': data})

# add user property for 1 week ago or 1 month ago that gets updated, use upload-completed-exercise for base
# Get line graph data
@app.route('/get-exercise-data/', methods=['GET'])
def get_exercise_data():
    db_user_maxes = database.PrescribedExercises
    userName = request.args.get('userName')
    output = {
        'maxWristFlexionArray': [],
        'maxWristExtensionArray': [],
        'maxUlnarDeviationArray': [],
        'maxRadialDeviationArray': [],
        'painArray': [],
        'difficultyArray': [],
    }

    if userName is None:
        return jsonify({'message': 'Username is required'}), 400
    else:
        userData = db_user_maxes.find({'userName': userName, 'isCompleted': True})
        for data in userData:
            if data['exerciseName'] == "Wrist Flexion":
                output['maxWristFlexionArray'].append(data['maxAngle'])
            elif data['exerciseName'] == "Wrist Extension":
                output['maxWristExtensionArray'].append(data['maxAngle'])
            elif data['exerciseName'] == "Ulnar Deviation":
                output['maxUlnarDeviationArray'].append(data['maxAngle'])
            elif data['exerciseName'] == "Radial Deviation":
                output['maxRadialDeviationArray'].append(data['maxAngle'])

            output['painArray'].append(data['painRating'])
            output['difficultyArray'].append(data['difficultyRating'])

        return jsonify({'result': output})


        # Fetch the completed exercises for each week
        
        # if maxes is not None:
        #     for max in maxes:
        #         week = max['week']
        #         # Calculate the max values for each exercise type
        #         output['maxWristFlexion'].append((week, max(exercise['wristFlexion'])))
        #         output['maxWristExtension'].append((week, max(exercise['wristExtension'])))
        #         output['maxUlnarDeviation'].append((week, max(exercise['ulnarDeviation'])))
        #         output['maxRadialDeviation'].append((week, max(exercise['radialDeviation'])))
        #     return jsonify(output)

# Get all-patients page data
@app.route('/get-all-patients/', methods=['GET'])
def get_all_patients():
    db_users = database.Users
    output = []

    for user in db_users.find():
        data = {
            key: user[key] if user[key] is not None else -1000
            for key in [
                'userName', 'firstName', 'lastName', 'email', 'dateOfBirth', 'hand', 'rehabStart', 'injuryTime'
            ]
        }
        output.append(data)
    
    return jsonify({'results': output})

# Get list of all exercises
@app.route('/get-all-exercises/', methods=['GET'], )
def get_exercises():
    db_exercises = database.ValidExercises
    output = []
    for exercise in db_exercises.find():
        data = {
            key: exercise[key] if exercise[key] is not None else -1000
            for key in [
                'exerciseName', 'hand', 'reps', 'sets'
            ]
        }
        output.append(data)

    return jsonify({'result': output})

# Delete all user data
@app.route('/delete-user/', methods=['DELETE'])
def delete_user():
    username = request.args.get('userName')
    allCollections = database.list_collection_names()

    for collectionName in allCollections:
        collection = database[collectionName]
        collection.delete_many({'userName' : username})
        
    return {'message': 'User data deleted successfully'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)