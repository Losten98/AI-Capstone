from flask import Flask, render_template, json, request, redirect, session
from flask_cors import CORS, cross_origin
from flask_restx import Resource, Api, reqparse

from flask import jsonify
#from auth import SHA256
import sys
import os
import datetime

import numpy as np
from PIL import Image

app = Flask(__name__)
app.secret_key = 'sogang_nice'

session_user = 'none'
deviceStatus = 'ready'
deviceName = None

#app.config.from_envvar('HIT_FLASK_SETTINGS')
app.flaskIP = '0.0.0.0' #app.config['HIT_FLASK_IP']
app.flaskPort = 5000 #app.config['HIT_FLASK_PORT']

print('Flask Server IP:' + str(app.flaskIP))
print('Flask Server PORT:' + str(app.flaskPort))

json_swap ={}

device_db = {
    "titan":"ready",
    "test11":"ready",
    "test22":"ready",
}

time_db = {
    "titan":[],
    "test11":[],
    "test22":[],
}

sensor_db = {
    "titan":[],
    "test11":[],
    "test22":[],
}

judge_db = {
    "titan":[],
    "test11":[],
    "test22":[],
}

# Todo: route '/' is failed due to reset api feature.
# W/A : use '/main' instead of '/' temporary.
@app.route('/')
def main():
    print('enterMain')
    return render_template('index.html')


@app.route('/userMain')
def userHome():
    global device_db
    # global deviceStatus
    # global deviceName
    session_user = session['user']

    print('app user ' + session_user)
    print('history list',  time_db[session_user])
    time_list = time_db[session_user][::-1]
    if len(time_list) > 3:
        time_list = time_list[:3]
    mainData = {
        'user': session_user,
        'status': device_db[session_user],
        'timedb': time_list,
        #'creatorUrl': 'http://' + app.creatorIP + ':' + str(app.creatorPort) + '/index.html?base=Medium'
    }
    if device_db[session_user] == 'start':
        device_db[session_user] = 'ready'
        return render_template('data_rcv.html',data = mainData)
    elif session.get('user'):
        return render_template('userMain.html',data = mainData)
    else:
        return render_template('error.html',error = 'Unauthorized Access')

@app.route('/dataRcv')
def dataRcv():
    global device_db
    session_user = session['user']
    print('app user ' + session_user)
    mainData = {
        'user': session_user,
        'status': device_db[session_user],
    }
    return render_template('data_rcv.html',data = mainData)

@app.route('/dataResult')
def dataResult():
    global device_db
    session_user = session['user']
    print('app user ' + session_user)
    mainData = {
        'user': session_user,
        'sensorData': sensor_db[session_user][-1],
        'judge' : judge_db[session_user][-1],
    }
    return render_template('data_result.html',data = mainData)

@app.route('/dataShow/<device_name>/<id>')
def dataShow(device_name, id):
    global device_db
    session_user = session['user']
    if  session_user in device_db:
        print('datashow session user:', session_user)
        print('datashow device_name:', device_name, len(sensor_db[device_name]))
        if len(sensor_db[device_name]) == 0:
            mainData = {
                'user': device_name,
                'sensorData': "No data recorded.",
            }
            return render_template('data_show.html',data = mainData)
        if device_name in device_db:
            print('data show device name: ' + device_name)
            mainData = {
                'user': device_name,
                'sensorData': sensor_db[device_name][int(id)],
                'judge' : judge_db[session_user][int(id)],
            }
            return render_template('data_show.html',data = mainData)
        else:
            return render_template('error.html',error = str(e))
    else:
        return render_template('error.html',error = str(e))

    

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('username', None)
    session_user = 'none'
    return redirect('/')

@app.route('/updateStatus/<device_name>/<device_status>')
def updateStatus(device_name, device_status):
    print('post from url: ', device_name)
    global device_db
    if device_name in device_db:
        device_db[device_name] = device_status
        print('device udpate success -', device_db[device_name])
    return device_name


@app.route('/dbcheck',methods=['GET'])
def dbcheck():
    global device_db
    try:
        session_user = session['user']
        data = {'status': device_db[session_user]}
        return jsonify(data)
    except Exception as e:
        return render_template('error.html',error = str(e))

@app.route('/sensorData', methods=['POST'])
def sensorDataRcv():
    global sensor_db
    try:
        print(f"receive json ? {request.is_json}")
        if request.is_json:
            now = datetime.datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S")
            data = request.get_json()
            device = data['device']
            judge = data['judge']
            print('device name:', device)
            sensor_db[device].append(data['sensor'])
            judge_db[device].append(judge)
            time_db[device].append([len(time_db[device]),now_str])
            print(time_db[device][-1], sensor_db[device][-1])
            return ok
        else:
            print('data type is not json.')
            return nok
    except Exception as e:
        return render_template('error.html',error = str(e))

@app.route('/validateLogin',methods=['POST'])
def validateLogin():
    print('enterValidateLogin')
    #global session_user
    try:
        _username = request.form['inputUser']

        if len(_username) > 0 and _username in device_db:
            session['user'] = _username
            session['devicename'] = _username
            session['devicestatus'] = 'ready'
            #session_user = _username
            return redirect('/userMain')
        else:
            return render_template('error.html',error = 'Wrong User Name.')          

    except Exception as e:
        return render_template('error.html',error = str(e))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=app.flaskPort, debug=True)
