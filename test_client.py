"""
Distributed Video Processing Client

A GUI application for uploading videos, selecting detection classes,
and sending them for processing.
"""

import os
import sys  # noqa
import tempfile
import threading
import time
from base64 import b64decode, b64encode  # noqa
import random

from nicegui import ui
from nicegui.events import UploadEventArguments
from paho.mqtt import client as MQTT
from utils.common.Messages import Heartbeat, VideoRequest, heartbeat_decode
from utils.common.MQTT_Broker import MQTT_HOST, MQTT_PORT
from utils.common.Topics import CLIENT_TOPIC, HEARTBEAT_TOPIC, REQUEST_INBOX  # noqa


class DistributedVideoProcessingApp:
    def __init__(self, client_name: str = "client", host: str = "192.168.1.138", port: int = 1883):
        # Store uploaded video information
        self.uploaded_content = None
        self.input_video_data = None
        self.input_video_name = None
        self.temp_input_video_path = None
        self.temp_processed_video_path = None
        self.processing_start_ts = None
        self.processing_end_ts = None
        # Worker nodes
        self.nodes: list[str] = []
        self.node_ping: list[str] = []

        # MQTT set up
        self.client_name = client_name  # mqtt client name
        self.client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=self.client_name)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self._mqtt_connect(host, port)

        

        # Acceptable video formats
        self.valid_video_types = [
            "video/mp4",
            "video/mpeg",
        ]

        # Detection Classes based on the COCO dataset (same as before)
        self.detection_classes = {
            0: "person",
            1: "bicycle",
            2: "car",
            3: "motorcycle",
            4: "airplane",
            5: "bus",
            6: "train",
            7: "truck",
            8: "boat",
            9: "traffic light",
            10: "fire hydrant",
            11: "stop sign",
            12: "parking meter",
            13: "bench",
            14: "bird",
            15: "cat",
            16: "dog",
            17: "horse",
            18: "sheep",
            19: "cow",
            20: "elephant",
            21: "bear",
            22: "zebra",
            23: "giraffe",
            24: "backpack",
            25: "umbrella",
            26: "handbag",
            27: "tie",
            28: "suitcase",
            29: "frisbee",
            30: "skis",
            31: "snowboard",
            32: "sports ball",
            33: "kite",
            34: "baseball bat",
            35: "baseball glove",
            36: "skateboard",
            37: "surfboard",
            38: "tennis racket",
            39: "bottle",
            40: "wine glass",
            41: "cup",
            42: "fork",
            43: "knife",
            44: "spoon",
            45: "bowl",
            46: "banana",
            47: "apple",
            48: "sandwich",
            49: "orange",
            50: "broccoli",
            51: "carrot",
            52: "hot dog",
            53: "pizza",
            54: "donut",
            55: "cake",
            56: "chair",
            57: "couch",
            58: "potted plant",
            59: "bed",
            60: "dining table",
            61: "toilet",
            62: "tv",
            63: "laptop",
            64: "mouse",
            65: "remote",
            66: "keyboard",
            67: "cell phone",
            68: "microwave",
            69: "oven",
            70: "toaster",
            71: "sink",
            72: "refrigerator",
            73: "book",
            74: "clock",
            75: "vase",
            76: "scissors",
            77: "teddy bear",
            78: "hair drier",
            79: "toothbrush",
        }

        # UI set up
        self.upload_area = None
        self.class_select = None
        self.status_label = None
        self.video_preview = None
        self._setup_ui()

    def _heartbeat_timeout_loop(self):
        """Updates the list of available nodes on a loop. Meant to run in a thread."""
        while True:
            self.nodes = self.node_ping
            self.node_ping = []
            time.sleep(1)

    def _heartbeat_cb(self, message: Heartbeat):
        """Callback for node heartbeat messages."""
        node = message.node
        if node not in self.node_ping:
            self.node_ping.append(node)

    def _on_connect(self, client: MQTT.Client, userdata, flags, reason_code, properties):
        """MQTT Client on connect, subscribe to topics."""
        client.subscribe(f"{HEARTBEAT_TOPIC}")
        client.subscribe(f"{CLIENT_TOPIC}")

    def _on_message(self, client: MQTT.Client, userdata, message: MQTT.MQTTMessage):
        """MQTT Client on message receipt, do callbacks."""
        if message.topic.endswith(HEARTBEAT_TOPIC):
            hb = heartbeat_decode(message.payload.decode())
            self._heartbeat_cb(hb)
        if message.topic.endswith(CLIENT_TOPIC):
            ################################################################################
            # Process the video and display the result
            self.processed_video = b64decode(message.payload.decode())
            # try:
            #     if self.temp_processed_video_path and os.path.exists(self.temp_processed_video_path):
            #         os.remove(self.temp_processed_video_path)
            # except Exception as e:
            #     ui.notify(f"Error deleting previous video: {str(e)}", type="negative")
            #     self.update_status(f"Error deleting previous video: {str(e)}")

            self.temp_processed_video_path = None
            self.processed_video_preview.clear()

            # Create a temporary file for the video preview            
            
            
            output_video_path = "/home/ryank/School/distributed-predict/output-video-tmp.mp4"
            output_h264_path = f"/home/ryank/School/distributed-predict/output-video-{random.random()}.mp4"

            
            with open(output_video_path, "wb") as f:
                f.write(self.processed_video)
                
            os.system(f"ffmpeg -y -i {output_video_path} -an -vcodec libx264 -crf 23 {output_h264_path}")
            os.remove(output_video_path)
                
            self.temp_processed_video_path = output_h264_path

            # Show the video preview
            with self.processed_video_preview:
                with ui.card().classes("max-w-[400px] max-h-[400px] items-center justify-center"):
                    ui.label("Processed Video:").classes("text-lg text-gray-700 mb-2 mx-auto")
                    ui.video(self.temp_processed_video_path, autoplay=True, muted=True, loop=False).classes(
                        "object-contain mx-auto"
                    )
            self.update_status("Received processed video.")
            self.processing_end_ts = time.time()
            self.update_status(f"Total processing time: {round(self.processing_end_ts - self.processing_start_ts, 2)} seconds.")
            ################################################################################

    def _mqtt_connect(self, host, port):
        """Connects the MQTT client to the broker, and starts the heartbeat loop."""

        # connect to the broker
        while not self.client.is_connected():
            try:
                self.client.connect(host, port)
                self.client.loop_start()
            except OSError as e:
                print(f"MQTT client error: {e}")
                time.sleep(5)
            time.sleep(0.1)

        # start heartbeat loop
        threading.Thread(target=self._heartbeat_timeout_loop, daemon=True).start()

    def _setup_ui(self):
        """Set up the user interface."""
        with ui.header(elevated=True).classes("bg-blue-9"):
            ui.label("Distributed Video Processer").classes("text-2xl mx-auto")

        # Main content in a card
        with ui.card().classes("w-full p-4 no-shadow"):
            ### 1. VIDEO UPLOAD SECTION
            ui.label("1. Upload Video").classes("text-xl mb-2")

            self.upload_area = (
                ui.upload(
                    label="Drag and drop video file here",
                    multiple=False,
                    auto_upload=True,
                    on_upload=self.handle_upload,
                    max_files=1,
                )
                .props(f"accept={','.join(self.valid_video_types)} color=white text-color=grey-9")
                .classes("w-full border border-gray-400 shadow-none")
            )

            ### 2. VIDEO PREVIEW SECTION
            ui.label("2. Verify Video After Upload").classes("text-xl mt-4 mb-2")
            self.video_preview = ui.element("div").classes("w-full")

            ### 3. CLASS SELECTION AND PROCESS SECTION
            ui.label("3. Choose Detection Class").classes("text-xl mt-4 mb-2")

            with ui.row().classes("w-full items-center justify-center gap-2"):
                self.class_select = (
                    ui.select(
                        label="Select Detection Class",
                        value=None,
                        options=self.detection_classes,
                        with_input=True,
                        multiple=False,
                        clearable=True,
                    )
                    .props("color=blue-9 label-color=grey-9 outlined options-dense dense standout")
                    .classes("grow")
                )

                # Process button (only visible when class is selected)
                ui.button("Process Video", icon="play_arrow", on_click=self.process_video).props(
                    "color=white text-color=grey-9 ripple unelevated outline stretch"
                ).classes("").bind_visibility_from(self.class_select, "value")

            self.processed_video_preview = ui.element("div").classes("w-full")

            ### 4. STATUS DISPLAY
            ui.separator().classes("my-4")
            with ui.row().classes("w-full items-center justify-center"):
                ui.label("Status:").classes("font-bold text-gray-700")
                self.status_label = ui.label("Ready").classes("grow text-gray-700")

    async def handle_upload(self, e: UploadEventArguments):
        """Handle the video file upload event."""
        try:
            # Clean up previous video if it exists
            if self.temp_input_video_path and os.path.exists(self.temp_input_video_path):
                try:
                    os.remove(self.temp_input_video_path)
                except Exception as e:
                    ui.notify(f"Error deleting previous video: {str(e)}", type="negative")
                    self.update_status(f"Error deleting previous video: {str(e)}")

            self.temp_input_video_path = None
            self.video_preview.clear()

            # Verify we have content to process
            if not hasattr(e, "content") or not e.content:
                ui.notify("Upload failed: No content received", type="negative")
                return

            # Reset file pointer and get the data
            e.content.seek(0)
            content_data = e.content.read()
            self.uploaded_content = e
            self.input_video_data = b64encode(content_data).decode()
            self.input_video_name = e.name

            # Create a temporary file for the video preview
            fd, self.temp_input_video_path = tempfile.mkstemp(suffix=os.path.splitext(e.name)[1])
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(content_data)

            # Show the video preview
            with self.video_preview:
                # with ui.column().classes("max-w-[400px] max-h-[400px] items-center justify-center"):
                with ui.column().classes("items-center justify-center"):
                    ui.video(self.temp_input_video_path, autoplay=True, muted=True, loop=True).classes(
                        "object-contain mx-auto"
                    )
                    ui.label(f"File: {e.name} ({len(content_data) / (1000 * 1000):.2f} MB)").classes(
                        "text-sm text-gray-700 mt-2 mx-auto text-wrap"
                    )

            # Update status
            self.update_status(f"Video [{self.input_video_name}] ready for processing")

        except Exception as e:
            ui.notify(f"Upload error: {str(e)}", type="negative")
            self.update_status(f"Error: {str(e)}")
            print("Exception in upload handler:", str(e))

    def update_status(self, message):
        """Update the status display with a message."""
        if self.status_label:
            self.status_label.text = message

    def process_video(self) -> None:
        """Handle the process button click."""
        # Check if we have a video
        if not self.input_video_data:
            ui.notify("Please upload a video file first", type="warning")
            return

        # Check if a class is selected
        selected_class = self.class_select.value
        if selected_class is None:
            ui.notify("Please select a detection class", type="warning")
            return

        # Get the class name for display
        class_name = self.detection_classes.get(selected_class, str(selected_class))

        # Update status
        self.update_status(f"Processing video to detect {class_name}...")

        # Print processing information
        print(f"Processing video: {self.input_video_name}")
        print(f"Video size: {len(self.input_video_data) / (1024 * 1024):.2f} MB")
        print(f"Selected class ID: {selected_class} ({class_name})")

        ################################################################################
        # Send the request over MQTT
        try:
            request = VideoRequest(self.input_video_data, selected_class)
            print(f"Sending message to {self.nodes[0]}")
            self.update_status(f"Sending message to {self.nodes[0]}")
            self.client.publish(f"/{self.nodes[0]}/{REQUEST_INBOX}", request.encode_message())
            self.processing_start_ts = time.time()

        except Exception as e:
            ui.notify(f"Error sending message: {str(e)}", type="negative")
            self.update_status(f"Error sending message: {str(e)}")
            print(f"Error sending message: {str(e)}")
            return
        ################################################################################


def main():
    # Create the web application
    app = DistributedVideoProcessingApp(client_name="client", host=MQTT_HOST, port=MQTT_PORT)  # noqa

    # Start the UI
    ui.run(title="Distributed Video Processing Client", reload=False)


if __name__ == "__main__":
    main()
else:
    # Handle module import case
    main()
