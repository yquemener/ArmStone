import cv2


cap1 = cv2.VideoCapture("/dev/video32")
cap2 = cv2.VideoCapture("/dev/video33")

cv2.namedWindow("Video Device 1", cv2.WINDOW_NORMAL)
cv2.namedWindow("Video Device 2", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap1.read()
    cv2.imshow("Video Device 1", frame)
    ret, frame = cap2.read()
    cv2.imshow("Video Device 2", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap1.release()
cap2.release()
cv2.destroyAllWindows()
