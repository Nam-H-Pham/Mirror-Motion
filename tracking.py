import cv2


url_start = "http://192.168.1.116:4747/video"
url_end = "http://192.168.1.103:4747/video"

cap_start = cv2.VideoCapture(url_start)
cap_end = cv2.VideoCapture(url_end)

while True:
    ret_start, frame_start = cap_start.read()
    ret_end, frame_end = cap_end.read()

    if ret_start:
        cv2.imshow("Camera Start", frame_start)
    if ret_end:
        cv2.imshow("Camera End", frame_end)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC
        break

cap_start.release()
cap_end.release()
cv2.destroyAllWindows()
