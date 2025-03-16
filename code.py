import board
import digitalio
import time
import adafruit_requests
import adafruit_connection_manager
import wifi

# In this example, there is an LED connected to D10

led = digitalio.DigitalInOut(board.D10)
led.direction = digitalio.Direction.OUTPUT
pool = adafruit_connection_manager.get_radio_socketpool(wifi.radio)
requests = adafruit_requests.Session(pool, None)
KEEP_ALIVE_INTERVAL = 60
status_check_count = KEEP_ALIVE_INTERVAL


while True:
    try:
        req = requests.get("http://192.168.178.91:9090/api/v1/rules?type=alert")
        res = req.json()
    except Exception:
        print(":", end="")
        for i in range(4):
            led.value = True
            time.sleep(0.25)
            led.value = False
            time.sleep(0.25)
        time.sleep(4)
        status_check_count -= 1
        continue
    is_firing = False
    data = res.get("data", {})
    groups = data.get("groups", [])
    for group in groups:
        rules = group.get("rules", [])
        for rule in rules:
            if rule.get("state", "unset") == "firing":
                is_firing = True
    if is_firing:
        led.value = True  # turn on LED
    time.sleep(3)
    led.value = False  # turn off LED
    if status_check_count <= 0:
        print()
        for i in range(2):
            led.value = True
            time.sleep(0.125)
            led.value = False
            time.sleep(0.125)
        time.sleep(1.75)
        status_check_count = KEEP_ALIVE_INTERVAL
    else:
        time.sleep(2)
    status_check_count -= 1
    print(".", end="")
