import serial
ser = serial.Serial('/dev/rfcomm0', 57600)
while True:
    data = ser.read(32)
    print(data)