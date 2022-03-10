import cv2

cap = cv2.VideoCapture('http://raspberrypi.local:8080/?action=stream')
while(cap.isOpened()):
    ret, frame = cap.read()
    cv2.imshow("hell", frame)
    # Break gracefully
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break