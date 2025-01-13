import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import re
import time
import requests
import os

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie URL Downloader")
        
        # URL input
        self.url_label = tk.Label(root, text="Enter .m3u8 URL:")
        self.url_label.pack(pady=10)
        self.url_entry = tk.Entry(root, width=50)
        self.url_entry.pack(pady=5)
        
        # Download button
        self.download_button = tk.Button(root, text="Download", command=self.start_download)
        self.download_button.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(root, length=300, mode='determinate')
        self.progress.pack(pady=10)
        
        # Percentage label
        self.percentage_label = tk.Label(root, text="0%")
        self.percentage_label.pack(pady=5)

        # Error label
        self.error_label = tk.Label(root, text="", fg="red")
        self.error_label.pack(pady=5)

    def start_download(self):
        url = self.url_entry.get()
        if not url:
            self.show_error("Please enter a valid URL.")
            return
        
        # Reset UI
        self.progress['value'] = 0
        self.percentage_label.config(text="0%")
        self.url_entry.config(state='disabled')
        self.download_button.config(state='disabled')
        self.error_label.config(text="")  # Clear any previous error messages
        
        # Validate URL
        if not self.validate_url(url):
            self.show_error("Invalid or inaccessible .m3u8 URL.")
            self.enable_ui()
            return
        
        # Start download in a separate thread
        threading.Thread(target=self.run_ffmpeg, args=(url,), daemon=True).start()

    @staticmethod
    def validate_url(url):
        """Check if the .m3u8 URL is valid and accessible."""
        try:
            response = requests.head(url, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"URL validation failed: {e}")
            return False

    def show_error(self, message):
        """Display an error message."""
        self.error_label.config(text=message)

    def run_ffmpeg(self, url):
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        index = 0
        output_file = os.path.join(downloads_folder, f"output_{index}.mp4")
        
        while os.path.exists(output_file):
            index += 1
            output_file = os.path.join(downloads_folder, f"output_{index}.mp4")
        print(f"Output file will be saved as: {output_file}")

        # Check if the output file exists and delete it
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Deleted existing output file: {output_file}")

        command = [
        'ffmpeg',
        '-i', url,
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        output_file
        ]

        try:
            # Start FFmpeg process and capture output
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            
            # Capture and process output in real-time
            self.process_output(process)

            # Wait for process to finish
            process.wait()

            # Re-enable UI after download completes
            self.root.after(0, self.enable_ui)
        
        except Exception as e:
            print(f"Error running FFmpeg: {e}")
            self.show_error(f"An error occurred while running FFmpeg: {str(e)}")
            self.enable_ui()

    def process_output(self, process):
        """Process FFmpeg output and update progress bar."""
        time_regex = re.compile(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})")
        duration_regex = re.compile(r"Duration: (\d{2}:\d{2}:\d{2}\.\d{2})")
        duration = None
        last_update_time = time.time()

        while True:
            # Read output and error from FFmpeg
            output = process.stderr.readline()
            if output == '' and process.poll() is not None:
                break

            if output:
                print(output.strip())  # Print output to console (for debugging)

                # Check for duration in FFmpeg logs
                if duration is None:
                    duration_match = duration_regex.search(output)
                    if duration_match:
                        duration = self.time_to_seconds(duration_match.group(1))
                
                # Check for current playback time and update progress
                time_match = time_regex.search(output)
                if time_match and duration:
                    current_time = self.time_to_seconds(time_match.group(1))
                    percentage = (current_time / duration) * 100
                    self.update_progress(percentage)

                    last_update_time = time.time()

            # If FFmpeg is stalled (no output for 10 seconds), restart the process
            if time.time() - last_update_time > 10:
                print("FFmpeg stalled. Restarting...")
                process.terminate()
                self.show_error("Download stalled. Please check the URL and try again.")
                self.root.after(0, self.enable_ui)        

    @staticmethod
    def time_to_seconds(time_str):
        """Convert time in HH:MM:SS format to seconds."""
        h, m, s = map(float, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def update_progress(self, percentage):
        """Update progress bar and percentage label."""
        self.progress['value'] = percentage
        self.percentage_label.config(text=f"{int(percentage)}%")
        self.root.update_idletasks()

    def enable_ui(self):
        """Re-enable the URL entry and download button."""
        self.url_entry.config(state='normal')
        self.download_button.config(state='normal')


if __name__ == '__main__':
    rk_root = tk.Tk()
    app = App(rk_root)
    rk_root.mainloop()
