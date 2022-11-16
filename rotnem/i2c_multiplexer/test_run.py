import max30102
import hrcalc
import time
import RPi.GPIO as GPIO
import requests
import os

m = max30102.MAX30102()

m.setup()

red_buf = []
ir_buf = []
spo2_buf = []

interrupt = 40
status = False
# set gpio mode
GPIO.setmode(GPIO.BOARD)
GPIO.setup(interrupt, GPIO.IN,pull_up_down=GPIO.PUD_UP)

data_cnt = 0

user = os.getlogin()
print('username:', user)

while True:

    button = GPIO.input(interrupt)

    if button == 0:
        if status == False:
            status = True
        else:
            status = False

    if status == True:
        if data_cnt == 0:
            result = requests.get(f"http://18.178.247.148:5000/updateStatus/{user}/record")
            print(result)
        m.setup()
        red, ir = m.read_sequential()
        data_cnt += 1
        hr, hr_valid, spo2, spo2_valid = hrcalc.calc_hr_and_spo2(ir, red)
        print(hr, hr_valid, spo2, spo2_valid)
        spo2_buf.append(round(spo2, 1))
        if data_cnt > 3:
            m.shutdown()
            status = False
            if sum(spo2_buf) > 0:
                judge = 'calm and peace.'
            else:
                judge = 'rest required.'
            result = requests.post('http://18.178.247.148:5000/sensorData', json={"device":f"{user}", "judge":judge, "sensor": spo2_buf})
            print('data send result', result)
            spo2_buf=[]
            result = requests.get(f"http://18.178.247.148:5000/updateStatus/{user}/kickdata")

    else:
        print('ready...', button)

        time.sleep(1)
        if data_cnt > 0:
            data_cnt = 0
            result = requests.get(f"http://18.178.247.148:5000/updateStatus/{user}/ready")

