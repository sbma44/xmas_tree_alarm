# Christmas Tree Water Alarm

Reads a value from an MQTT topic representing mm between sensor and water surface. When the value exceeds THRESHOLD for more than ALARM_PERIOD seconds, it will attempt to discover a Twinkly device on the network and set its color to yellow. When the water level returns below THRESHOLD, the device will be returned to 'effect' mode. The device is set to red when it stops receiving MQTT messages beyond the specified period.

## Note on Docker deployment
You'll need to use `host` network mode to get the xled device discovery functionality working. If this is a problem, it shouldn't be too hard to modify the code to specify the device IP directly, which will likely work over Docker's default `bridge` mode networking.
