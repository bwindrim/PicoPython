# From https://www.instructables.com/How-to-Use-MPU6050-With-Raspberry-Pi-Pico-or-Pico-/
# Requires:
# https://github.com/shillehbean/youtube-channel/blob/main/imu.py
# https://github.com/shillehbean/youtube-channel/blob/main/vector3d.py

from imu import MPU6050
from time import sleep
from machine import Pin, I2C


i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
imu = MPU6050(i2c)


while True:
	ax=round(imu.accel.x,2)
	ay=round(imu.accel.y,2)
	az=round(imu.accel.z,2)
	gx=round(imu.gyro.x)
	gy=round(imu.gyro.y)
	gz=round(imu.gyro.z)
	tem=round(imu.temperature,2)
	print("ax",ax,"\t","ay",ay,"\t","az",az,"\t","gx",gx,"\t","gy",gy,"\t","gz",gz,"\t","Temperature",tem,"        ",end="\r")
	sleep(0.2) 
	