import cv2
from ultralytics import YOLO


class ImagePredictor:
    def __init__(self, model: str = None):
        self.yolo = YOLO(model) if model is not None else YOLO()

    def image_predict(self, image: cv2.Mat, device: int | str = "cpu", target: int = 76) -> int:
        """
        Runs YOLO object detection on a frame, and returns the number of occurances of a target object.
        """

        result = self.yolo.predict(image, device=device, classes=[target], verbose=False)[0]
        hits = len(result.boxes)

        return hits
