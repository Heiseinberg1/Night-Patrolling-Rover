import RPi.GPIO as GPIO
import time
import socket
import threading
import logging
import csv
import atexit
from datetime import datetime

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Server and GPIO Configuration
HOST_IP = "192.168.130.29"
PORT = 5000
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Motor and Sensor Pins
MOTOR_PINS = {'IN1': 5, 'IN2': 6, 'IN3': 13, 'IN4': 19}
EN_PINS = {'enA': 25, 'enB': 16}
ULTRASONIC_PINS = {'TRIG': 23, 'ECHO': 24}
PIR_PIN = 27

# GPIO Setup
GPIO.setup(list(MOTOR_PINS.values()) + list(EN_PINS.values()), GPIO.OUT)
GPIO.setup(ULTRASONIC_PINS['TRIG'], GPIO.OUT)
GPIO.setup(ULTRASONIC_PINS['ECHO'], GPIO.IN)
GPIO.setup(PIR_PIN, GPIO.IN)

# Motor Control Setup
pwm_A = GPIO.PWM(EN_PINS['enA'], 1000)
pwm_B = GPIO.PWM(EN_PINS['enB'], 1000)
pwm_A.start(20)  # Default speed
pwm_B.start(20)

# System Constants
OBSTACLE_THRESHOLD = 20  # cm
TURN_DURATION = 0.65  # Time for 90-degree turn 

# Data Logging Files
DATA_LOG_FILE = "rover_data.csv"
MOTION_LOG_FILE = "motion_log.txt"

# Initialize CSV file
with open(DATA_LOG_FILE, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Distance (cm)", "Obstacle Avoidance Time (s)"])

def set_motors(left_forward, left_back, right_forward, right_back):
    GPIO.output(MOTOR_PINS['IN1'], left_forward)
    GPIO.output(MOTOR_PINS['IN2'], left_back)
    GPIO.output(MOTOR_PINS['IN3'], right_forward)
    GPIO.output(MOTOR_PINS['IN4'], right_back)

def forward():
    pwm_A.start(20)
    pwm_B.start(20)
    set_motors(GPIO.HIGH, GPIO.LOW, GPIO.HIGH, GPIO.LOW)

def backward(duration=1):
    set_motors(GPIO.LOW, GPIO.HIGH, GPIO.LOW, GPIO.HIGH)
    time.sleep(duration)
    stop()

def turn_right(duration=TURN_DURATION):
    pwm_A.start(50)
    pwm_B.start(50)
    set_motors(GPIO.HIGH, GPIO.LOW, GPIO.LOW, GPIO.HIGH)
    time.sleep(duration)
    stop()

def stop():
    set_motors(GPIO.LOW, GPIO.LOW, GPIO.LOW, GPIO.LOW)

def get_distance():
    GPIO.output(ULTRASONIC_PINS['TRIG'], True)
    time.sleep(0.00001)
    GPIO.output(ULTRASONIC_PINS['TRIG'], False)
    pulse_start = time.time()
    timeout = pulse_start + 0.08
    
    while GPIO.input(ULTRASONIC_PINS['ECHO']) == 0:
        if time.time() > timeout:
            return None
    pulse_start = time.time()
    
    while GPIO.input(ULTRASONIC_PINS['ECHO']) == 1:
        if time.time() > timeout:
            return None
    pulse_end = time.time()
    
    distance = (pulse_end - pulse_start) * 17150
    return round(distance, 2)

def avoid_obstacle():
    start_time = time.time()
    stop()
    backward()
    turn_right()
    forward()
    avoidance_time = round(time.time() - start_time, 2)
    log_data(get_distance(), avoidance_time)

def log_data(distance, avoidance_time):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DATA_LOG_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, distance, avoidance_time])

def navigation_controller():
    while True:
        distance = get_distance()
        if distance and distance < OBSTACLE_THRESHOLD:
            avoid_obstacle()
        else:
            forward()
        time.sleep(0.1)

def security_monitor():
    while True:
        if GPIO.input(PIR_PIN):
            send_alert()
            log_motion()
            while GPIO.input(PIR_PIN):
                time.sleep(0.5)
        time.sleep(0.1)

def send_alert():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.connect((HOST_IP, PORT))
            client.sendall(b"Motion Detected")
    except Exception as e:
        logging.error(f"Alert failed: {e}")

def log_motion():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(MOTION_LOG_FILE, "a") as file:
        file.write(f"Motion detected at: {timestamp}\n")

def cleanup():
    logging.info("System Shutdown")
    pwm_A.stop()
    pwm_B.stop()
    GPIO.cleanup()

atexit.register(cleanup)

# Main Execution
try:
    threading.Thread(target=navigation_controller, daemon=True).start()
    threading.Thread(target=security_monitor, daemon=True).start()
    
    while True:
        logging.info("Rover Running...")
        time.sleep(5)
except KeyboardInterrupt:
    pass
