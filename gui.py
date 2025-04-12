"""
This is just a shell which will need to be refactored and features added as needed

For now, use one file for easy organization and development.
"""

import os
import time
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import asyncio
import random  # For simulation purposes only

from nicegui import ui, app
from nicegui.events import UploadEventArguments


class RPiDevice:
    """Class representing a Raspberry Pi device in the distributed network."""

    def __init__(self, device_id: str, ip_address: str):
        """Initialize a new RPi device."""
        self.device_id = device_id
        self.ip_address = ip_address
        self.connected = False
        self.cpu_usage = 0.0  # in percentage
        self.gpu_usage = 0.0  # in percentage
        self.ram_usage = 0.0  # in percentage
        self.last_updated = datetime.now()

    def connect(self) -> bool:
        """Attempt to connect to the RPi device."""
        # Placeholder for actual connection logic
        try:
            # Simulate connection attempt
            self.connected = random.random() > 0.2  # 80% success rate for demo
            if self.connected:
                self.update_stats()
            return self.connected
        except Exception as e:
            print(f"Connection error for device {self.device_id}: {str(e)}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the RPi device."""
        # Placeholder for actual disconnection logic
        try:
            self.connected = False
        except Exception as e:
            print(f"Disconnection error for device {self.device_id}: {str(e)}")

    def update_stats(self) -> None:
        """Update device statistics."""
        # Placeholder for actual stats collection
        if self.connected:
            try:
                # For simulation, generate random values
                self.cpu_usage = random.uniform(10.0, 90.0)
                self.gpu_usage = random.uniform(5.0, 80.0)
                self.ram_usage = random.uniform(20.0, 95.0)
                self.last_updated = datetime.now()
            except Exception as e:
                print(f"Stats update error for device {self.device_id}: {str(e)}")

    def get_status_dict(self) -> Dict[str, Any]:
        """Return device status as a dictionary for UI updates."""
        return {
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "connected": self.connected,
            "cpu_usage": self.cpu_usage,
            "gpu_usage": self.gpu_usage,
            "ram_usage": self.ram_usage,
            "last_updated": self.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }


class DistributedVideoProcessor:
    """Manager for distributed video processing across RPi devices."""

    def __init__(self):
        """Initialize the distributed video processor."""
        self.devices: List[RPiDevice] = []
        self.current_video_path: Optional[str] = None
        self.processing = False
        self.progress = 0.0
        self.cancel_requested = False

    def add_device(self, device_id: str, ip_address: str) -> RPiDevice:
        """Add a new RPi device to the processing network."""
        device = RPiDevice(device_id, ip_address)
        self.devices.append(device)
        return device

    def remove_device(self, device_id: str) -> bool:
        """Remove a device from the processing network."""
        for i, device in enumerate(self.devices):
            if device.device_id == device_id:
                if device.connected:
                    device.disconnect()
                self.devices.pop(i)
                return True
        return False

    def get_connected_devices(self) -> List[RPiDevice]:
        """Get list of currently connected devices."""
        return [device for device in self.devices if device.connected]

    def update_all_device_stats(self) -> None:
        """Update statistics for all connected devices."""
        for device in self.devices:
            if device.connected:
                device.update_stats()

    async def process_video(self, video_path: str, progress_callback: Callable[[float], None]) -> bool:
        """
        Process video file across distributed RPi network.

        Args:
            video_path: Path to the video file
            progress_callback: Function to call with progress updates (0-100)

        Returns:
            True if processing completed successfully, False otherwise
        """
        if not os.path.exists(video_path):
            return False

        connected_devices = self.get_connected_devices()
        if not connected_devices:
            return False

        self.current_video_path = video_path
        self.processing = True
        self.progress = 0.0
        self.cancel_requested = False

        # Placeholder for actual video processing logic
        # In a real implementation, this would distribute work across devices:
        # 1. Split the video into chunks
        # 2. Assign chunks to different devices
        # 3. Monitor processing on each device
        # 4. Combine results when complete

        try:
            # Simulate processing with progress updates
            while self.progress < 100 and not self.cancel_requested:
                await asyncio.sleep(0.2)  # Simulate work being done
                self.progress += random.uniform(0.5, 2.0)
                if self.progress > 100:
                    self.progress = 100

                # Update all device stats periodically
                self.update_all_device_stats()

                # Call progress callback with current progress
                progress_callback(self.progress)

            self.processing = False
            return not self.cancel_requested
        except Exception as e:
            print(f"Error during video processing: {str(e)}")
            self.processing = False
            return False

    def cancel_processing(self) -> None:
        """Cancel the current video processing job."""
        if self.processing:
            self.cancel_requested = True


class VideoProcessingApp:
    """Main application for the distributed video processing GUI."""

    def __init__(self):
        """Initialize the video processing application."""
        self.processor = DistributedVideoProcessor()
        self.upload_path = None
        self.progress_bar = None
        self.upload_area = None
        self.devices_container = None

        # Add some sample devices for demonstration
        self.add_sample_devices()

    def add_sample_devices(self) -> None:
        """Add sample RPi devices for demonstration purposes."""
        devices = [
            ("rpi-01", "192.168.1.100"),
            ("rpi-02", "192.168.1.101"),
            ("rpi-03", "192.168.1.102"),
        ]

        for device_id, ip in devices:
            device = self.processor.add_device(device_id, ip)
            # Randomly connect some devices
            if random.random() > 0.3:
                device.connect()
                device.update_stats()

    def setup_ui(self) -> None:
        """Set up the NiceGUI user interface."""
        # Set up the header
        with ui.header().classes("flex items-center justify-between"):
            ui.label("Distributed Video Processing").classes("text-2xl")
            with ui.row():
                ui.button(icon="refresh", on_click=self.refresh_devices).tooltip("Refresh Devices")

        # Create tabs for different sections
        with ui.tabs().classes("w-full") as tabs:
            video_tab = ui.tab("Video Processing")
            devices_tab = ui.tab("RPi Devices")
            settings_tab = ui.tab("Settings")

        with ui.tab_panels(tabs, value=video_tab).classes("w-full"):
            # Video Processing Tab
            with ui.tab_panel(video_tab):
                self.create_video_processing_ui()

            # Devices Tab
            with ui.tab_panel(devices_tab):
                self.create_devices_ui()

            # Settings Tab
            with ui.tab_panel(settings_tab):
                self.create_settings_ui()

        # Start the background task for updating device stats
        ui.timer(5.0, self.refresh_devices)

    async def handle_upload(self, e: UploadEventArguments) -> None:
        """Handle video file upload events."""
        try:
            self.upload_path = e.paths[0] if e.paths else None
            if self.upload_path:
                file_name = os.path.basename(self.upload_path)
                ui.notify(f"Uploaded: {file_name}")

                # Reset progress bar
                if self.progress_bar:
                    self.progress_bar.value = 0

                # Disable the upload area during processing
                self.upload_area.disable()

                # Process the video
                success = await self.processor.process_video(
                    self.upload_path, lambda progress: self.update_progress(progress)
                )

                # Re-enable the upload area
                self.upload_area.enable()

                if success:
                    ui.notify(f"Video processing completed for {file_name}!", type="positive")
                else:
                    ui.notify("Video processing was cancelled or failed", type="negative")
        except Exception as e:
            ui.notify(f"Error processing upload: {str(e)}", type="negative")
            if self.upload_area:
                self.upload_area.enable()

    def update_progress(self, progress: float) -> None:
        """Update the progress bar."""
        if self.progress_bar:
            # Ensure progress is between 0 and 1 for the UI component
            normalized_progress = max(0, min(progress, 100)) / 100
            self.progress_bar.value = normalized_progress

    def create_video_processing_ui(self) -> None:
        """Create the video processing UI section."""
        with ui.card().classes("w-3/4 mx-auto"):
            ui.label("Upload Video File").classes("text-xl")

            # Create upload area
            self.upload_area = (
                ui.upload(
                    label="Drag and drop video files here",
                    auto_upload=True,
                    on_upload=self.handle_upload,
                    max_files=1,  # Only allow one file at a time
                )
                .props("accept=video/*")
                .classes("w-full")
            )

            # Create progress bar
            with ui.card().classes("w-full mt-4"):
                ui.label("Processing Progress")
                self.progress_bar = ui.linear_progress(value=0).classes("w-full")

            # Create control buttons
            with ui.row().classes("w-full justify-center mt-4"):
                ui.button("Process", icon="play_arrow", on_click=self.start_processing)
                ui.button("Cancel", icon="cancel", on_click=self.cancel_processing).classes("bg-red-500")

    def create_devices_ui(self) -> None:
        """Create the RPi devices UI section."""
        ui.label("Connected Raspberry Pi Devices").classes("text-xl")

        # Container for device cards that will be updated dynamically
        self.devices_container = ui.element("div").classes(
            "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full mt-4"
        )

        # Add device button
        with ui.row().classes("w-full justify-end mt-4"):
            ui.button("Add Device", icon="add", on_click=self.show_add_device_dialog)

        # Initial rendering of devices
        self.refresh_devices()

    def create_settings_ui(self) -> None:
        """Create the settings UI section."""
        with ui.card().classes("w-1/2 mx-auto"):
            ui.label("Application Settings").classes("text-xl")

            with ui.row().classes("w-full items-center"):
                ui.switch("Enable GPU Acceleration", value=True)
                ui.tooltip("Use GPU for faster video processing when available")

            with ui.row().classes("w-full items-center"):
                ui.switch("Auto-connect to devices", value=True)
                ui.tooltip("Automatically connect to previously used devices on startup")

            ui.separator()

            ui.label("Video Processing Settings").classes("text-lg mt-4")

            with ui.row().classes("w-full items-center"):
                ui.select(["Low", "Medium", "High", "Ultra"], value="Medium", label="Processing Quality").classes(
                    "w-1/4"
                )

            with ui.row().classes("w-full items-center"):
                ui.number("Max Concurrent Tasks", value=4, min=1, max=16).classes("w-1/4")

            ui.separator()

            ui.label("Network Settings").classes("text-lg mt-4")

            with ui.row().classes("w-full items-center"):
                ui.input("Network Scan Range", value="192.168.1.0/24").classes("w-1/4")

            with ui.row().classes("w-full items-center"):
                ui.number("Connection Timeout (seconds)", value=5, min=1, max=30).classes("w-1/4")

            with ui.row().classes("w-full justify-end mt-4"):
                ui.button("Save Settings", icon="save")

    def refresh_devices(self) -> None:
        """Refresh the device display with the latest information."""
        try:
            # Update device stats
            self.processor.update_all_device_stats()

            # Clear existing device cards
            if self.devices_container:
                self.devices_container.clear()

                # Add device cards for all devices
                with self.devices_container:
                    for device in self.processor.devices:
                        self.create_device_card(device)
        except Exception as e:
            ui.notify(f"Error refreshing devices: {str(e)}", type="negative")

    def create_device_card(self, device: RPiDevice) -> None:
        """Create a card displaying device information."""
        status_color = "green" if device.connected else "red"
        status_text = "Connected" if device.connected else "Disconnected"

        with ui.card().classes("w-full"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(f"Device: {device.device_id}").classes("text-lg font-bold")
                ui.icon("circle", color=status_color).tooltip(status_text)

            ui.separator()

            ui.label(f"IP Address: {device.ip_address}")

            if device.connected:
                with ui.row().classes("w-full"):
                    ui.label("CPU:")
                    ui.linear_progress(value=device.cpu_usage / 100).classes("w-full")
                    ui.label(f"{device.cpu_usage:.1f}%").classes("ml-2")

                with ui.row().classes("w-full"):
                    ui.label("GPU:")
                    ui.linear_progress(value=device.gpu_usage / 100).classes("w-full")
                    ui.label(f"{device.gpu_usage:.1f}%").classes("ml-2")

                with ui.row().classes("w-full"):
                    ui.label("RAM:")
                    ui.linear_progress(value=device.ram_usage / 100).classes("w-full")
                    ui.label(f"{device.ram_usage:.1f}%").classes("ml-2")

                ui.label(f"Last Updated: {device.last_updated.strftime('%H:%M:%S')}").classes(
                    "text-xs text-gray-500 mt-2"
                )
            else:
                ui.label("Device is offline").classes("text-red-500")

            with ui.row().classes("w-full justify-end mt-2"):
                if device.connected:
                    ui.button("Disconnect", icon="link_off", on_click=lambda d=device: self.disconnect_device(d))
                else:
                    ui.button("Connect", icon="link", on_click=lambda d=device: self.connect_device(d))
                ui.button("Remove", icon="delete", on_click=lambda d=device: self.remove_device(d)).classes(
                    "bg-red-500"
                )

    def connect_device(self, device: RPiDevice) -> None:
        """Connect to a device."""
        if device.connect():
            ui.notify(f"Connected to {device.device_id}", type="positive")
        else:
            ui.notify(f"Failed to connect to {device.device_id}", type="negative")
        self.refresh_devices()

    def disconnect_device(self, device: RPiDevice) -> None:
        """Disconnect from a device."""
        device.disconnect()
        ui.notify(f"Disconnected from {device.device_id}")
        self.refresh_devices()

    def remove_device(self, device: RPiDevice) -> None:
        """Remove a device from the network."""
        if self.processor.remove_device(device.device_id):
            ui.notify(f"Removed device {device.device_id}")
            self.refresh_devices()

    async def start_processing(self) -> None:
        """Start the video processing."""
        if not self.upload_path:
            ui.notify("Please upload a video file first", type="warning")
            return

        if self.processor.processing:
            ui.notify("Processing already in progress", type="warning")
            return

        if not self.processor.get_connected_devices():
            ui.notify("No connected devices available for processing", type="warning")
            return

        try:
            # Reset progress bar
            if self.progress_bar:
                self.progress_bar.value = 0

            # Disable the upload area during processing
            if self.upload_area:
                self.upload_area.disable()

            # Process the video
            success = await self.processor.process_video(
                self.upload_path, lambda progress: self.update_progress(progress)
            )

            # Re-enable the upload area
            if self.upload_area:
                self.upload_area.enable()

            if success:
                ui.notify("Video processing completed!", type="positive")
            else:
                ui.notify("Video processing was cancelled or failed", type="negative")
        except Exception as e:
            ui.notify(f"Error during processing: {str(e)}", type="negative")
            if self.upload_area:
                self.upload_area.enable()

    def cancel_processing(self) -> None:
        """Cancel the current video processing job."""
        if self.processor.processing:
            self.processor.cancel_processing()
            ui.notify("Processing cancelled")
        else:
            ui.notify("No processing job to cancel", type="warning")

    def show_add_device_dialog(self) -> None:
        """Show dialog for adding a new device."""
        with ui.dialog() as dialog, ui.card():
            ui.label("Add New RPi Device").classes("text-xl")

            device_id_input = ui.input("Device ID", validation={"Cannot be empty": lambda value: value != ""})
            ip_input = ui.input("IP Address", validation={"Must be valid IP": lambda value: len(value.split(".")) == 4})

            with ui.row().classes("w-full justify-end"):
                ui.button("Cancel", on_click=dialog.close)
                ui.button("Add Device", on_click=lambda: self.add_device(device_id_input.value, ip_input.value, dialog))

        dialog.open()

    def add_device(self, device_id: str, ip_address: str, dialog) -> None:
        """Add a new device with the given information."""
        try:
            if not device_id or not ip_address:
                ui.notify("Device ID and IP Address are required", type="warning")
                return

            # Check if device ID already exists
            for device in self.processor.devices:
                if device.device_id == device_id:
                    ui.notify(f"Device with ID {device_id} already exists", type="warning")
                    return

            # Add the new device
            self.processor.add_device(device_id, ip_address)
            ui.notify(f"Added new device: {device_id}", type="positive")
            dialog.close()
            self.refresh_devices()
        except Exception as e:
            ui.notify(f"Error adding device: {str(e)}", type="negative")


# Main application setup
def main():
    """Main entry point for the application."""
    # Create the application instance
    video_app = VideoProcessingApp()

    # Set up the UI
    video_app.setup_ui()

    # Start the NiceGUI server
    ui.run(title="Distributed Video Processing")


main()
