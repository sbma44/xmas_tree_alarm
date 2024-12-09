import os
import time
import threading
import xled
import paho.mqtt.client as mqtt

# Retrieve environment variables
MQTT_SERVER = os.getenv("MQTT_SERVER", "192.168.1.2")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "xmas/tree/water/raw")
THRESHOLD = float(os.getenv("THRESHOLD", "60.0"))
ALARM_PERIOD = int(os.getenv("ALARM_PERIOD", "90"))
NODATA_TIMEOUT = int(os.getenv("NODATA_TIMEOUT", "300"))
TEST_MODE = int(os.getenv("TEST_MODE", "0")) == 1

# State tracking
last_message_time = time.time()
alarm_triggered_nodata = False
alarm_triggered_threshold = False
current_value = None
event_start_threshold = None

def set_twinkly_color(color):
    """Set the first discovered Twinkly device to a specified color."""
    try:
        discovered_device = xled.discover.discover()
        control = xled.ControlInterface(discovered_device.ip_address, discovered_device.hw_address)
        control.set_mode('color')
        control.set_led_color_rgb(*color)
        print(f"Set Twinkly to color: {color}")
    except Exception as e:
        print(f"Error controlling Twinkly device: {e}")

def test_color_cycle(n=-1):
    try:
        discovered_device = xled.discover.discover()
        control = xled.ControlInterface(discovered_device.ip_address, discovered_device.hw_address)
        control.set_mode('color')
        count = 0
        while n < 0 or count < n:
            for c in [(255, 0, 0), (0, 255, 0), (0, 0, 255)]:
                control.set_led_color_rgb(*c)
                print(f"Set Twinkly to color: {c}")
                time.sleep(0.5)
            count += 1
    except Exception as e:
        print(f"Error controlling Twinkly device: {e}")

def resume_twinkly_normal_operation():
    try:
        discovered_device = xled.discover.discover()
        control = xled.ControlInterface(discovered_device.ip_address, discovered_device.hw_address)
        control.set_mode('effect')
    except Exception as e:
        print(f"Error controlling Twinkly device: {e}")

def on_message(client, userdata, msg):
    global last_message_time, current_value, alarm_triggered_nodata, alarm_triggered_threshold, event_start_threshold

    if alarm_triggered_nodata:
        alarm_triggered_nodata = False
        resume_twinkly_normal_operation()

    last_message_time = time.time()
    payload = msg.payload.decode()
    try:
        current_value = float(payload)

        # mark time of each dip above threshold
        # if below threshold, set to None
        if current_value >= THRESHOLD:
            if event_start_threshold is None:
                event_start_threshold = time.time()
        else:
            event_start_threshold = None

        # if:
        # - above threshold
        # - alarm is not yet active and
        # - time period has passed
        # then trigger alarm
        if (not alarm_triggered_threshold) and (event_start_threshold is not None) and (time.time() - event_start_threshold > ALARM_PERIOD):
            print(f"Threshold ({THRESHOLD}) exceeded for {ALARM_PERIOD}s, setting Twinkly to yellow.")
            alarm_triggered_threshold = True
            set_twinkly_color((255, 255, 0))  # Yellow color

        # if:
        # - alarm is triggered
        # - value is below threshold
        # turn off alarm
        if alarm_triggered_threshold and current_value < THRESHOLD:
            print(f"Threshold below ({THRESHOLD}), resuming normal operation.")
            alarm_triggered_threshold = False
            resume_twinkly_normal_operation()

    except ValueError:
        print(f"Invalid payload: {payload}")

def monitor_nodata():
    """Monitor for no data condition and set the Twinkly to red if timeout occurs."""
    global last_message_time, alarm_triggered_nodata
    while True:
        receiving_data = (time.time() - last_message_time) < NODATA_TIMEOUT

        if not alarm_triggered_nodata and not receiving_data:
            alarm_triggered_nodata = True
            print(f"No data received in specified timeout ({NODATA_TIMEOUT}s), setting Twinkly to red.")
            set_twinkly_color((255, 0, 0))  # Red color

        elif alarm_triggered_nodata and receiving_data:
            alarm_triggered_nodata = False
            print(f"Data received, resuming normal operation.")
            resume_twinkly_normal_operation()

        time.sleep(1)

def main():
    # log global variables to stdout
    print("=== xmas_tree_alarm starting ===")
    print(f"MQTT_SERVER={MQTT_SERVER}")
    print(f"MQTT_TOPIC={MQTT_TOPIC}")
    print(f"THRESHOLD={THRESHOLD}")
    print(f"ALARM_PERIOD={ALARM_PERIOD}")
    print(f"NODATA_TIMEOUT={NODATA_TIMEOUT}")
    print(f"TEST_MODE={TEST_MODE}")

    if TEST_MODE:
        print("Running in test mode, not connecting to MQTT server.")
        test_color_cycle()
        return

    # announce initialization
    test_color_cycle(1)
    resume_twinkly_normal_operation()

    # Initialize MQTT client
    client = mqtt.Client()
    client.on_message = on_message

    try:
        client.connect(MQTT_SERVER)
    except Exception as e:
        print(f"Failed to connect to MQTT server: {e}")
        return

    client.subscribe(MQTT_TOPIC)
    threading.Thread(target=monitor_nodata, daemon=True).start()

    print(f"Listening to MQTT topic '{MQTT_TOPIC}' on server '{MQTT_SERVER}'...")
    client.loop_forever()

if __name__ == "__main__":
    main()