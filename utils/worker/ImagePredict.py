from ultralytics import YOLO
import cv2


class ImagePredictor:

    def __init__(self,  model : str = None):
        self.yolo = YOLO(model) if model is not None else YOLO()


    def image_predict(self, image : cv2.Mat, device : int | str = "cpu", target : int = 77) -> int:
        '''
        Runs YOLO object detection on a frame, and returns the number of occurances of a target object.
        '''
        
        result = self.yolo.predict(image, device=device, classes=[target], stream=True, verbose=False)[0]
        hits = len(result.boxes)
                
        return hits