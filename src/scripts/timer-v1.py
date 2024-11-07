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
from plyer import notification

def main():
    # Parse command-line arguments
    args = parse_arguments()

    # Check if sound file exists
    if not os.path.exists(args.sound):
        print(f"Sound file '{args.sound}' not found.")
        sys.exit(1)

    # Import simpleaudio
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
