count = 0
hour_in_ms = 60 * 60 * 1000

while True:
    print ("count =", count)
    count += 1
    machine.lightsleep(hour_in_ms)
