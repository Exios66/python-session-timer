# 🕒 Python Session Timer

[![License](https://img.shields.io/github/license/Exios66/python-session-timer)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Documentation Status](https://readthedocs.org/projects/python-session-timer/badge/?version=latest)](https://python-session-timer.readthedocs.io/en/latest/?badge=latest)
[![Pages Build Status](https://github.com/Exios66/python-session-timer/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/Exios66/python-session-timer/actions/workflows/pages/pages-build-deployment)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Live-brightgreen)](https://exios66.github.io/python-session-timer/)
[![Coverage Status](https://coveralls.io/repos/github/Exios66/python-session-timer/badge.svg?branch=main)](https://coveralls.io/github/Exios66/python-session-timer?branch=main)
[![GitHub issues](https://img.shields.io/github/issues/Exios66/python-session-timer)](https://github.com/Exios66/python-session-timer/issues)
[![GitHub stars](https://img.shields.io/github/stars/Exios66/python-session-timer)](https://github.com/Exios66/python-session-timer/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Exios66/python-session-timer)](https://github.com/Exios66/python-session-timer/network)
[![GitHub last commit](https://img.shields.io/github/last-commit/Exios66/python-session-timer)](https://github.com/Exios66/python-session-timer/commits/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A customizable and cross-platform timer script inspired by the Pomodoro Technique. Perfect for managing work sessions and breaks with notifications and sound alerts.

## 📦 Features

- **Customizable Durations:** Set your preferred work and break durations.
- **Cycle Management:** Define the number of work-break cycles.
- **Notifications:** Receive system notifications when timers end.
- **Sound Alerts:** Play a sound when a timer concludes.
- **Cross-Platform:** Works seamlessly on Windows, macOS, and Linux.
- **Easy to Use:** Simple command-line interface with various options.

## 🚀 Installation

### Prerequisites

- **Python 3.8 or higher** installed on your system. Download from [python.org](https://www.python.org/downloads/).

### Clone the Repository

```bash
git clone https://github.com/Exios66/python-session-timer.git
cd python-session-timer

Install Dependencies

Use pip to install the required Python packages:

pip install -r requirements.txt

Alternatively, install them individually:

pip install plyer simpleaudio

Prepare a Sound File

Ensure you have a sound file (e.g., alarm.wav) in the project directory or specify the path to your preferred sound file when running the script.

📝 Usage

Run the timer with default settings:

python timer.py

Customize Timer Settings

You can customize the timer using command-line arguments:

python timer.py -w 50 -b 10 -c 2 -s bell.wav -m "Work session over!" --title "Break Time"

Command-Line Options

Option Description Default
-w, --work-duration Work duration in minutes 25 minutes
-b, --break-duration Break duration in minutes 5 minutes
-c, --cycles Number of work-break cycles 4 cycles
-s, --sound Path to the sound file to play when timer ends alarm.wav
-m, --message Notification message when timer ends Time is up!
--title Notification title Timer Alert

Example Usage

python timer.py -w 45 -b 15 -c 3 -s notification.wav -m "Time for a break!" --title "Work Session Complete"

📜 Script Overview

```python
#!/usr/bin/env python3
"""
Customizable Timer Script

This script implements a customizable timer similar to a Pomodoro timer.
It allows setting custom work and break durations, number of cycles,
and plays a sound and displays a notification when the timer ends.

Dependencies:
- plyer (for notifications)
- simpleaudio (for playing sound)

Install dependencies with:
pip install plyer simpleaudio

Usage:
python timer.py [options]

Options:
- -w, --work-duration: Work duration in minutes (default: 25)
- -b, --break-duration: Break duration in minutes (default: 5)
- -c, --cycles: Number of cycles (default: 4)
- -s, --sound: Path to sound file to play when timer ends (default: alarm.wav)
- -m, --message: Notification message (default: "Time is up!")
- --title: Notification title (default: "Timer Alert")
"""
import time
import argparse
import sys
import os

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Check if sound file exists
    if not os.path.exists(args.sound):
        print(f"Sound file '{args.sound}' not found.")
        sys.exit(1)

    # Import plyer and simpleaudio
    try:
        from plyer import notification
    except ImportError:
        print("Module 'plyer' not found. Install it by running 'pip install plyer'")
        sys.exit(1)

    try:
        import simpleaudio as sa
    except ImportError:
        print("Module 'simpleaudio' not found. Install it by running 'pip install simpleaudio'")
        sys.exit(1)

    # Main loop
    for cycle in range(1, args.cycles + 1):
        print(f"Cycle {cycle}/{args.cycles}: Work for {args.work_duration} minutes.")
        countdown(args.work_duration)

        send_notification(args.title, args.message)
        play_sound(args.sound)

        if cycle != args.cycles:
            print(f"Take a break for {args.break_duration} minutes.")
            countdown(args.break_duration)
            send_notification(args.title, 'Break time is over!')
            play_sound(args.sound)
    print("All cycles completed.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Customizable Timer with Notifications and Sound')

    parser.add_argument('-w', '--work-duration', type=int, default=25,
                        help='Work duration in minutes (default: 25)')
    parser.add_argument('-b', '--break-duration', type=int, default=5,
                        help='Break duration in minutes (default: 5)')
    parser.add_argument('-c', '--cycles', type=int, default=4,
                        help='Number of cycles (default: 4)')
    parser.add_argument('-s', '--sound', type=str, default='alarm.wav',
                        help='Path to sound file to play when timer ends (default: alarm.wav)')
    parser.add_argument('-m', '--message', type=str, default='Time is up!',
                        help='Notification message (default: "Time is up!")')
    parser.add_argument('--title', type=str, default='Timer Alert',
                        help='Notification title (default: "Timer Alert")')

    args = parser.parse_args()
    return args

def countdown(duration):
    total_seconds = duration * 60
    try:
        while total_seconds:
            mins, secs = divmod(total_seconds, 60)
            timer = '{:02d}:{:02d}'.format(mins, secs)
            print(f"Time left: {timer}", end='\r')
            time.sleep(1)
            total_seconds -= 1
        print()  # Move to next line after countdown
    except KeyboardInterrupt:
        print("\nTimer interrupted by user.")
        sys.exit(0)

def send_notification(title, message):
    notification.notify(
        title=title,
        message=message,
        timeout=10
    )

def play_sound(sound_file):
    try:
        import simpleaudio as sa
        wave_obj = sa.WaveObject.from_wave_file(sound_file)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing sound: {e}")

if __name__ == "__main__":
    main()

```python

***

### 🔧 Deployment Considerations

• Cross-Platform Compatibility: The script is designed to work on Windows, macOS, and Linux systems.
• Dependencies: Ensure all dependencies are included in your deployment package or specified in your requirements.txt file.
• Error Handling: The script includes error handling for missing dependencies and sound files.
• Customization: All timer settings are easily customizable via command-line arguments.

```

## 📄 Requirements

Ensure you have the following dependencies installed:

plyer
simpleaudio

You can install them using:

pip install -r requirements.txt

Sample requirements.txt:

plyer
simpleaudio

### 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch (git checkout -b feature/YourFeature).
3. Commit your changes (git commit -m 'Add some feature').
4. Push to the branch (git push origin feature/YourFeature).
5. Open a Pull Request.

Please ensure your code adheres to the project’s coding standards and includes appropriate documentation.

### 📜 License

This project is licensed under the MIT License.

### 📫 Contact

Exios66

 •GitHub: @Exios66
 •Email: <youremail@example.com>

### 🎉 Acknowledgements

 •Inspired by the Pomodoro Technique.
 •Utilizes Plyer for notifications.
 •Utilizes Simpleaudio for sound playback.

Happy Coding!

[![License](https://img.shields.io/github/license/Exios66/python-session-timer)](LICENSE)
