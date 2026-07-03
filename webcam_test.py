import cv2

# 0 = default webcam. If you have multiple cameras, try 1 or 2.
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Could not open webcam. Try changing the index (0, 1, 2...)")
    exit()

while True:
    success, frame = cap.read()
    if not success:
        print("Failed to grab frame")
        break

    # Flip horizontally so it acts like a mirror (feels natural)
    frame = cv2.flip(frame, 1)

    cv2.imshow("Webcam Test", frame)

    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()