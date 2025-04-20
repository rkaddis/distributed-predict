import cv2
from ultralytics import YOLO


def video_inference(
    video: cv2.VideoCapture | str, model: str = None, device: int | str = "cpu", classes: list = None
) -> dict:
    """
    Runs YOLO object detection on every frame in a video, and returns the results in a dictionary.
    """

    if type(video) is str:
        video = cv2.VideoCapture(video)

    assert type(video) is cv2.VideoCapture

    yolo = YOLO(model) if model is not None else YOLO()
    frame_id = 0
    results = {}

    while video.isOpened():
        _, image = video.read()
        result = yolo.predict(image, device=device, classes=classes)[0]

        for i in range(len(result.names)):
            results[f"frame_{frame_id}_{i}"] = {
                "class": result.names[i],
                "conf": result.probs[i],
                "box": result.boxes[i],
            }

    return results
