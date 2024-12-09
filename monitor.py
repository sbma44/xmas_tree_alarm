import os
import time
import threading
import xled
import paho.mqtt.client as mqtt

# Retrieve environment variables
MQTT_SERVER = os.getenv("MQTT_SERVER", "localhost")
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "sensor/data")
THRESHOLD = float(os.getenv("THRESHOLD", "50.0"))
ALARM_PERIOD = int(os.getenv("ALARM_PERIOD", "10"))
NODATA_TIMEOUT = int(os.getenv("NODATA_TIMEOUT", "300"))

# State tracking
last_message_time = None
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
        control.set_color(*color)
        print(f"Set Twinkly to color: {color}")
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
        print(f"Received MQTT message: {current_value}")

        if current_value > THRESHOLD:
            print("Threshold exceeded, setting Twinkly to yellow.")
            if not alarm_triggered_threshold:
                event_start_threshold = time.time()

            if time.time() - event_start_threshold > ALARM_PERIOD:
                set_twinkly_color((255, 255, 0))  # Yellow color

            alarm_triggered_threshold = True
        else:
            if alarm_triggered_threshold:
                print("Threshold below, resuming normal operation.")
                alarm_triggered_threshold = False
                resume_twinkly_normal_operation()

    except ValueError:
        print(f"Invalid payload: {payload}")

def monitor_nodata():
    """Monitor for no data condition and set the Twinkly to red if timeout occurs."""
    global last_message_time
    while True:
        if last_message_time and (time.time() - last_message_time) > NODATA_TIMEOUT:
            print("No data received in specified timeout, setting Twinkly to red.")
            set_twinkly_color((255, 0, 0))  # Red color
        time.sleep(1)

def main():
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