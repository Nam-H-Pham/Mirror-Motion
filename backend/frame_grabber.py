import cv2
import threading
import time

class FrameGrabber:
    def __init__(self, url: str, name: str = "cam"):
        self.cap = cv2.VideoCapture(url)
        self.name = name
        self.lock = threading.Lock()
        self.frame = None
        self.ret = False
        self.stopped = False
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def _loop(self):
        while not self.stopped:
            ret, frame = self.cap.read()  # blocking read
            with self.lock:
                self.ret = ret
                self.frame = frame
            # tiny sleep prevents pegging CPU if stream glitches
            time.sleep(0.001)

    def read_latest(self):
        with self.lock:
            # return a copy/reference; copy if you mutate frames downstream
            return self.ret, self.frame

    def release(self):
        self.stopped = True
        self.thread.join(timeout=1.0)
        self.cap.release()
