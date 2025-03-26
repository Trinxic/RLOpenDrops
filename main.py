from datetime import datetime
from os import makedirs, path
from random import uniform
from threading import Thread
from time import sleep

import pytesseract
from keyboard import wait
from PIL import ImageGrab
from pyautogui import getWindowsWithTitle, press

RUNNING: bool = False
EXITING: bool = False
TOGGLE_KEY: str = "t"
EXIT_KEY: str = "e"
DROP_COUNT: int = None
CURSOR_UP = "\033[1A"
CLEAR_LINE = "\x1b[2K"


def get_rocket_league_window():  # -> <whatever object `windows[0]` is>
    windows = getWindowsWithTitle("Rocket League")
    if not windows:
        print("Rocket League window not found!")
        return None
    return windows[0]


def save_screenshot(screenshot) -> None:
    script_dir = path.dirname(path.abspath(__file__))
    save_dir = path.join(script_dir, "drops-screenshots")

    makedirs(save_dir, exist_ok=True)  # only creates if it doesn't exist already

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"drops_screenshot_{timestamp}.jpeg"
    filepath = path.join(save_dir, filename)

    screenshot.save(filepath, "JPEG")
    print(f"Screenshot saved: {filepath}")


def get_drops_count() -> int:
    global DROP_COUNT
    window = get_rocket_league_window()
    if not window:
        return None

    # get dimensions of screenshot
    left_bound = window.left + int(window.width * 0.15625)  # 5/32
    top_bound = window.top + int(window.height * 0.1851852)  # 5/27
    right_bound = window.left + int(window.width * 0.21875)  # 7/32
    bottom_bound = window.top + int(window.height * 0.225)  # 9/40

    # ic(window.left, window.top, window.right, window.bottom)
    # ic(window.width, window.height, left_bound, top_bound, right_bound, bottom_bound)

    screenshot = ImageGrab.grab(bbox=(left_bound, top_bound, right_bound, bottom_bound))
    save_screenshot(screenshot)

    num_drops = (
        pytesseract.image_to_string(screenshot, config="--psm 6")
        .strip()
        .replace("x", "")
    )

    try:
        DROP_COUNT = int(num_drops)
        print(f"Detected {DROP_COUNT} drops to open.")
    except ValueError:
        DROP_COUNT = None
        print("Could not detect drops count!")

    return DROP_COUNT


def open_drops():
    global RUNNING, EXITING, DROP_COUNT

    if RUNNING and not EXITING:
        print()
        DROP_COUNT = get_drops_count()
        if DROP_COUNT is None:
            print("No drop count => Continuing indefinitely...")

    while RUNNING and not EXITING:
        if DROP_COUNT is not None and DROP_COUNT <= 0:
            print("All drops opened. Stopping...")
            RUNNING = False
            break

        print(CURSOR_UP + CLEAR_LINE, end="")
        print(f"{DROP_COUNT} drop{'' if DROP_COUNT == 0 else 's'} left")

        press("enter")  # click "OPEN DROP"
        sleep(uniform(0.2, 0.4))
        press("left")  # select "YES"
        sleep(uniform(0.2, 0.4))
        press("enter")  # Proceed
        sleep(uniform(7.9, 8.1))  # wait for reward presentation
        press("enter")  # confirm reward
        sleep(uniform(0.2, 0.4))

        if DROP_COUNT is not None:
            DROP_COUNT -= 1


def listen_for_key():
    global RUNNING
    worker = None  # keep track of running thread

    while True:
        wait(TOGGLE_KEY)
        RUNNING = not RUNNING
        print(f"Update: {'' if RUNNING else 'No Longer '}Opening Drops...")

        if RUNNING and (worker is None or not worker.is_alive()):
            worker = Thread(target=open_drops, daemon=True)
            worker.start()


def main():
    print('ATTENTION: Ensure you are at the "Possible Contents" screen!')

    Thread(target=listen_for_key, daemon=True).start()

    wait(EXIT_KEY)
    EXITING = True  # noqa: F841  # set flag to allow clean exit
    print("Terminating program...")
    sleep(0.5)


if __name__ == "__main__":
    main()
