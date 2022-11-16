import hrcalc
import datetime
import time
import RPi.GPIO as GPIO
import requests
import os

import multi_max30102

s1 = multi_max30102.MAX30102_1()
s2 = multi_max30102.MAX30102_2()

interrupt = 40
status = False

# set gpio mode
GPIO.setmode(GPIO.BOARD)
GPIO.setup(interrupt, GPIO.IN, pull_up_down = GPIO.PUD_UP)

spo2_buf = []

user = os.getlogin()
print('username:', user)

while True:

    button_state = GPIO.input(interrupt)

    # Toggle status by button input
    if button_state == 0:
        if status == False:
            status = True
        else:
            status = False

    if status == True:

        # Push recording status to AWS
        result = requests.get(f"http://18.178.247.148:5000/updateStatus/{user}/record")
        print(result)

        s1.setup()
        s2.setup()

        now = datetime.datetime.now()
        record_time = now.strftime("%Y%m%d_%H%M%S")

        start = time.time()
        last_chk_time = start


        with open(f"./sensor_data_{record_time}.csv", "w") as f:
            f.write("index,red1,ir1,red2,ir2\n")
            f.close()

        with open(f"./hr_spo2_data_{record_time}.csv", "w") as f:
            f.write("index,hr,spo2\n")
            f.close()

        red1_buf = []
        red2_buf = []
        ir1_buf = []
        ir2_buf = []

        for i in range(25):
            red1, ir1 = s1.read_sequential(100)
            red2, ir2 = s2.read_sequential(100)
            red1_buf += red1
            red2_buf += red2
            ir1_buf  += ir1
            ir2_buf  += ir2

            chk_time = time.time() - last_chk_time
            last_chk_time = time.time()

            print(f"record-{i}, elapsed time: {chk_time}")

        print(len(red1_buf), len(red2_buf), len(ir1_buf), len(ir2_buf))

        with open(f"./sensor_data_{record_time}.csv", "a") as f:
            for i in range(2500):
                f.write(f"{i},{red1_buf[i]},{ir1_buf[i]},{red2_buf[i]},{ir2_buf[i]}\n")
            f.close()

        s1.shutdown()
        s2.shutdown()

        red = red1_buf + red2_buf
        ir = ir1_buf + ir2_buf

        hr_buf = []
        spo2_buf = []
        print(len(red))
        print(len(ir))
        for i in range(50):
            hr,hr_valid,spo2,spo2_valid = hrcalc.calc_hr_and_spo2(ir[100*i:100*i+100], red[100*i:100*i+100])
            hr_buf.append(hr)
            spo2_buf.append(spo2)

        with open(f"./hr_spo2_data_{record_time}.csv", "a") as f:
            for i in range(50):
                f.write(f"{i},{hr_buf[i]},{spo2_buf[i]}\n")
            f.close()

        ##### ------ Add ML or TF predict result with sensor data                ---- ####
        ##### ------ Use red1_buf, red2_buf, ir1_buf, ir2_buf, hr_buf, spo2_buf  ---- ####

        if sum(spo2_buf) > 0:
            judge = 'calm and peace.'
        else:
            judge = 'rest required.'

        ##### ----------------------------------------------------------------------- ####

        # Send Sensor data with wraping json format
        result = requests.post('http://18.178.247.148:5000/sensorData', json={"device":f"{user}", "judge":judge, "spo2": spo2_buf, "hr": hr_buf})
        print('data send result', result)
        result = requests.get(f"http://18.178.247.148:5000/updateStatus/{user}/kickdata")
        print("Total elapsed time: ", time.time() - start)
        status = False

    else:
        print('ready...', button_state)

        time.sleep(1)
        if len(spo2_buf) > 0:
            result = requests.get(f"http://18.178.247.148:5000/updateStatus/{user}/ready")

