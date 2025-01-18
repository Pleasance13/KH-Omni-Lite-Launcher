import os
import pygame
import sys
import ctypes
import time
import math
import json
import platform
import subprocess
from enum import Enum
from pygame.locals import *
from tkinter import Tk, filedialog, messagebox

def get_heroic_launch_command(game_id):

    heroic_path = config.get("HeroicPath")
    return [
        heroic_path,
        "--no-gui",
        "--no-sandbox",
        f"heroic://launch/{game_id}"
    ]

# Configurations
DEBUG = False
ASSET_RESOLUTION = (1920, 1080)

# Colors
BLACK = (0, 0, 0)

# File name for saving configuration
CONFIG_FILE = "LauncherConfig.json"

# Required files for validation
KH_REQUIRED_FILES = {
    "KH1.5+2.5": [
        "KINGDOM HEARTS Birth by Sleep FINAL MIX.exe",
        "KINGDOM HEARTS FINAL MIX.exe",
        "KINGDOM HEARTS Re_Chain of Memories.exe",
        "KINGDOM HEARTS II FINAL MIX.exe",
    ],
    "KH2.8": [
        "KINGDOM HEARTS Dream Drop Distance.exe",
        "KINGDOM HEARTS 0.2 Birth by Sleep/Binaries/Win64/KINGDOM HEARTS 0.2 Birth by Sleep.exe",
    ],
    "KH3": [
        "KINGDOM HEARTS III/Binaries/Win64/KINGDOM HEARTS III.exe",
    ]
}

gamesconfig_required_files = [
    "fd711544a06543e0ab1b0808de334120.json",
    "68c214c58f694ae88c2dab6f209b43e4.json",
    "d1a8f7c478d4439b8c60a5808715dc05.json"
]

GAME_CONFIGS = {
    # KH1.5+2.5 Games (json: 68c214c58f694ae88c2dab6f209b43e4)
    0: {"json": "68c214c58f694ae88c2dab6f209b43e4.json", "exe": "KINGDOM HEARTS FINAL MIX.exe", "collection": "KH1.5+2.5"},
    1: {"json": "68c214c58f694ae88c2dab6f209b43e4.json", "exe": "KINGDOM HEARTS Re_Chain of Memories.exe", "collection": "KH1.5+2.5"},
    2: {"json": "68c214c58f694ae88c2dab6f209b43e4.json", "exe": "KINGDOM HEARTS II FINAL MIX.exe", "collection": "KH1.5+2.5"},
    3: {"json": "68c214c58f694ae88c2dab6f209b43e4.json", "exe": "KINGDOM HEARTS Birth by Sleep FINAL MIX.exe", "collection": "KH1.5+2.5"},
    
    # KH2.8 Games (json: d1a8f7c478d4439b8c60a5808715dc05)
    4: {"json": "d1a8f7c478d4439b8c60a5808715dc05.json", "exe": "KINGDOM HEARTS Dream Drop Distance.exe", "collection": "KH2.8"},
    5: {"json": "d1a8f7c478d4439b8c60a5808715dc05.json", "exe": "KINGDOM HEARTS 0.2 Birth by Sleep/Binaries/Win64/KINGDOM HEARTS 0.2 Birth by Sleep.exe", "collection": "KH2.8"},
    
    # KH3 (json: fd711544a06543e0ab1b0808de334120)
    6: {"json": "fd711544a06543e0ab1b0808de334120.json", "exe": "KINGDOM HEARTS III/Binaries/Win64/KINGDOM HEARTS III.exe", "collection": "KH3"}
}

# States for the Confirm dialog
class ConfirmState(Enum):
    CLOSED = 0
    OPENING = 1
    OPEN = 2
    CLOSING = 3

# Add these new global variables
CONFIRM_STATE = ConfirmState.CLOSED
CONFIRM_SCALE = 0.0
CONFIRM_SCALE_UP_SPEED = 3.0  # Adjust for faster/slower animation
CONFIRM_SCALE_DOWN_SPEED = 8.0
SELECTED_CONFIRM_BUTTON = "YES"  # Default to YES
CONFIRM_ALPHA = 200  # For the black overlay (about 30% opacity)

# Add these new image loading variables where you load other images
def load_confirm_images():
    """Load confirm dialog images after pygame is initialized"""
    global CONFIRM_IMAGES
    CONFIRM_IMAGES = {
        "BOX": pygame.image.load(os.path.join(os.path.dirname(__file__), "confirm-box.png")).convert_alpha(),
        "TEXT": pygame.image.load(os.path.join(os.path.dirname(__file__), "confirm-text.png")).convert_alpha(),
        "CURSOR": pygame.image.load(os.path.join(os.path.dirname(__file__), "confirm-cursor.png")).convert_alpha(),
        "GLOW": pygame.image.load(os.path.join(os.path.dirname(__file__), "confirm-button-glow.png")).convert_alpha(),
        "BUTTON_ACTIVE": pygame.image.load(os.path.join(os.path.dirname(__file__), "confirm-button-active.png")).convert_alpha(),
        "BUTTON_INACTIVE": pygame.image.load(os.path.join(os.path.dirname(__file__), "confirm-button-inactive.png")).convert_alpha()
    }

# Function to load existing configuration or return an empty dictionary
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                if not config:  # Handle empty file
                    print(f"Warning: {CONFIG_FILE} is empty. Starting with a fresh configuration.")
                    return {}
                return config
        except json.JSONDecodeError:
            print(f"Warning: {CONFIG_FILE} is corrupted or empty. A backup will be created, and a fresh configuration will be used.")
            os.rename(CONFIG_FILE, CONFIG_FILE + ".bak")
            print(f"A backup of the corrupted file was saved as {CONFIG_FILE}.bak")
            return {}
    return {}

# Function to save configuration
def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
    debug_log(f"Configuration saved: {config}", DEBUG)

# Function to prompt for a folder and return its path
def prompt_for_folder(title, initialdir=None):
    root = Tk()
    root.withdraw()  # Hide the main tkinter window
    folder_path = filedialog.askdirectory(title=title, initialdir=initialdir)
    root.destroy()
    return folder_path

# Function to validate folder paths based on required files
def validate_install_path(folder, required_files):
    for file in required_files:
        if not os.path.exists(os.path.join(folder, file)):
            return False
    return True

def validate_gamesconfig_path(folder):
    for file in gamesconfig_required_files:
        if os.path.exists(os.path.join(folder, file)):
            return True
    return False

# Add to the config validation section near the top
heroic_default_path = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Programs', 'heroic', 'heroic.exe')
gamesconfig_default_path = os.path.join(os.getenv('APPDATA', ''), 'heroic', 'GamesConfig')
    
# Add to the load_config function's validation checks
def prompt_for_heroic_exe():

    # Existing Windows-specific Heroic exe selection logic
    while True:
        root = Tk()
        root.withdraw()
        initial_dir = os.path.dirname(heroic_default_path) if os.path.exists(heroic_default_path) else None
        file_path = filedialog.askopenfilename(
            title="Select Heroic.exe",
            initialdir=initial_dir,
            filetypes=[("Executable files", "*.exe")]
        )
        root.destroy()

        if not file_path:
            messagebox.showerror("Missing Heroic", "You must select the Heroic executable to proceed. The launcher will now exit.")
            sys.exit(1)

        if os.path.basename(file_path).lower() == 'heroic.exe':
            return file_path
        else:
            messagebox.showerror("Invalid File", "Please select the Heroic.exe executable.")

def prompt_for_all_paths():
    config = {}
    kh_titles = {
        "KH1.5+2.5": "KINGDOM HEARTS HD 1.5+2.5 ReMIX",
        "KH2.8": "KINGDOM HEARTS HD 2.8 Final Chapter Prologue",
        "KH3": "KINGDOM HEARTS III"
    }

    for key, title in kh_titles.items():
        while True:
            debug_log(f"Prompting for {title} installation folder.", DEBUG)
            folder = prompt_for_folder(f"Select the installation folder for {title}")
            if not folder:
                response = messagebox.askyesno("Missing Path", f"You did not select a folder for {title}. Do you want to continue without this game?")
                if response:
                    config[key] = "Not Installed"
                    break
                else:
                    continue

            if validate_install_path(folder, KH_REQUIRED_FILES[key]):
                config[key] = folder
                break
            else:
                messagebox.showerror("Invalid Path", f"The selected folder is not a valid installation path for {title}. Please try again.")

    while True:
        root = Tk()
        root.withdraw()
        initial_dir = os.path.dirname(gamesconfig_default_path) if os.path.exists(gamesconfig_default_path) else None
        folder = prompt_for_folder(f"Select the Heroic GamesConfig folder (This  be found in AppData/Roaming/heroic/GamesConfig)", initialdir=gamesconfig_default_path)
        if not folder:
            messagebox.showerror("Missing Path", "You must select the Heroic GamesConfig folder to proceed. The launcher will now exit.")
            sys.exit(1)

        if validate_gamesconfig_path(folder):
            config["HeroicGamesConfig"] = folder
            break
        else:
            messagebox.showerror("Invalid Path", "The selected folder is not a valid GamesConfig path or no games are installed via Heroic. Please try again.")

    save_config(config)
    return config

def handle_launch_arguments(config):
    """
    Parse launch arguments and potentially launch a specific game.
    Returns True if a game should be launched, False if launcher should proceed normally.
    """
    game_args = {
        "-kh1": 0,   # KINGDOM HEARTS FINAL MIX
        "-com": 1,   # Re: Chain of Memories
        "-kh2": 2,   # KINGDOM HEARTS II FINAL MIX
        "-bbs": 3,   # Birth by Sleep FINAL MIX
        "-ddd": 4,   # Dream Drop Distance
        "-afp": 5,   # 0.2 Birth by Sleep
        "-kh3": 6    # KINGDOM HEARTS III
    }
    
    # Count game-specific arguments
    game_args_used = [arg for arg in sys.argv if arg in game_args]
    
    # If multiple game arguments are used, proceed normally
    if len(game_args_used) > 1:
        return False
    
    # If a single game argument is used
    if game_args_used:
        game_arg = game_args_used[0]
        game_index = game_args[game_arg]
        
        # Validate game path is configured
        game_info = GAME_CONFIGS[game_index]
        collection = game_info["collection"]
        
        if config.get(collection) in ["Not Installed", None]:
            print(f"Error: {collection} is not installed.")
            return False
        
        # Attempt to launch the game
        if launch_game(config, game_index):
            pygame.quit()
            sys.exit()
        else:
            print(f"Failed to launch game for argument: {game_arg}")
            return False
    
    return False

# Function to play sound
def play_sound(sound_file):
    try:
        sound_path = os.path.join(os.path.dirname(__file__), sound_file)
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

# Debugging Function
def debug_log(message, debug=False):
    if DEBUG:
        print(f"[DEBUG]: {message}")

# DPI Detection for Windows
def get_system_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return dpi / 96.0
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG]: Failed to detect DPI scaling: {e}")
        return 1.0

def toggle_fullscreen():
    global screen, fullscreen
    fullscreen = not fullscreen
    
    if fullscreen:
        # Store the current window size before going fullscreen
        previous_size = screen.get_size()
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.DOUBLEBUF)
    else:
        # Return to a predefined windowed resolution
        screen = pygame.display.set_mode((logical_width, logical_height), pygame.RESIZABLE | pygame.DOUBLEBUF)
    
    return screen

# Detect DPI scaling
DPI_SCALING = get_system_dpi()

# Initialize Pygame
pygame.init()

# Set the application icon
icon_path = os.path.join(os.path.dirname(__file__), "heart.png")
icon = pygame.image.load(icon_path)
icon = pygame.transform.smoothscale(icon, (96, 96))
pygame.display.set_icon(icon)

# Initialize Pygame Joystick Support
pygame.joystick.init()

# Check joystick initialization and button press
if pygame.joystick.get_count() > 0:
    controller = pygame.joystick.Joystick(0)
    controller.init()
    debug_log("Controller initialized.")
else:
    controller = None
    debug_log("No controller detected.")

# Setup Display
flags = pygame.RESIZABLE | pygame.DOUBLEBUF
default_width = int(1280 / DPI_SCALING)
default_height = int(720 / DPI_SCALING)
screen = pygame.display.set_mode((default_width, default_height), flags)
fullscreen = "-f" in sys.argv  # Set fullscreen based on launch argument

# Initialize display mode
flags = pygame.DOUBLEBUF
screen = None
if fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | flags)
else:
    screen = pygame.display.set_mode((default_width, default_height), flags)

# Setup Display - Override DPI scaling by manually controlling the window size
# Let's set the window size explicitly based on logical resolution and disable DPI scaling
logical_width, logical_height = 1280, 720  # Logical resolution we want to work with

if fullscreen:
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | flags)
else:
    screen = pygame.display.set_mode((logical_width, logical_height), pygame.RESIZABLE | flags)

pygame.display.set_caption("KINGDOM HEARTS Omni Lite Launcher")

# Clock for FPS management
clock = pygame.time.Clock()

# Title Images
TITLE_IMAGES = [
    os.path.join(os.path.dirname(__file__), "kh1-title.png"), os.path.join(os.path.dirname(__file__), "com-title.png"), os.path.join(os.path.dirname(__file__), "kh2-title.png"),
    os.path.join(os.path.dirname(__file__), "bbs-title.png"), os.path.join(os.path.dirname(__file__), "ddd-title.png"), os.path.join(os.path.dirname(__file__), "afp-title.png"), os.path.join(os.path.dirname(__file__), "kh3-title.png"),
    os.path.join(os.path.dirname(__file__), "no-title.png")
]

# Background Images
BG_IMAGES = [
    os.path.join(os.path.dirname(__file__), "kh1-bg.png"), os.path.join(os.path.dirname(__file__), "com-bg.png"), os.path.join(os.path.dirname(__file__), "kh2-bg.png"),
    os.path.join(os.path.dirname(__file__), "bbs-bg.png"), os.path.join(os.path.dirname(__file__), "ddd-bg.png"), os.path.join(os.path.dirname(__file__), "afp-bg.png"), os.path.join(os.path.dirname(__file__), "kh3-bg.png")
]
background_index = 0
background = pygame.image.load(BG_IMAGES[background_index]).convert()

# Logo Image
logo_index = 0
LOGO_IMAGES = [
    os.path.join(os.path.dirname(__file__), "kh1-logo.png"), os.path.join(os.path.dirname(__file__), "com-logo.png"), os.path.join(os.path.dirname(__file__), "kh2-logo.png"),
    os.path.join(os.path.dirname(__file__), "bbs-logo.png"), os.path.join(os.path.dirname(__file__), "ddd-logo.png"), os.path.join(os.path.dirname(__file__), "afp-logo.png"), os.path.join(os.path.dirname(__file__), "kh3-logo.png")
]
logo = pygame.image.load(LOGO_IMAGES[logo_index]).convert_alpha()  # Load the logo with transparency
logo_rect = logo.get_rect()

# Starting position for the logo (relative percentage coordinates)
logo_x = int(screen.get_width() * 0.3932)  # 39.32% of the screen width
logo_y = int(screen.get_height() * 0.1935)  # 19.35% of the screen height
logo_rect.topleft = (logo_x, logo_y)

# Floating Parameters
FLOAT_AMPLITUDE = 0.01  # Percent of the canvas height
FLOAT_SPEED = 2.0  # Speed of the sine wave (higher = faster)
start_time = time.time()  # Track the starting time

# Button States
BUTTON_STATES = {
    "INACTIVE": os.path.join(os.path.dirname(__file__), "button-0.png"),
    "HOVERED": os.path.join(os.path.dirname(__file__), "button-3.png"),
    "PRESSED": os.path.join(os.path.dirname(__file__), "button-2.png"),
    "ACTIVE": os.path.join(os.path.dirname(__file__), "button-1.png"),
    "DEACTIVATED": os.path.join(os.path.dirname(__file__), "button-2.png")
}
        
NUM_BUTTONS = 7
buttons = []
selected_button_index = 0  # Controller navigation index
active_button_index = None  # Track the currently active button
pressed_button_index = None  # Track the currently pressed button
pressed_button_time = 0  # Time when the button was pressed
button_press_duration = 200  # Time for the pressed state animation

load_confirm_images()

# Initialize the button rects with placeholder dimensions, INACTIVE state, and hovered_flag
for i in range(NUM_BUTTONS):
    button_rect = pygame.Rect(0, 0, 500, 122)  # Placeholder rect, will be scaled
    buttons.append({
        "state": "INACTIVE",
        "rect": button_rect,
        "hovered_flag": False  # Ensure the hovered_flag key is initialized
    })

# Helper Functions
def calculate_canvas_fit(window_width, window_height):
    target_aspect = 16 / 9
    window_aspect = window_width / window_height

    if window_aspect > target_aspect:
        canvas_height = window_height
        canvas_width = int(canvas_height * target_aspect)
    else:
        canvas_width = window_width
        canvas_height = int(canvas_width / target_aspect)

    return pygame.Rect(
        (window_width - canvas_width) // 2,
        (window_height - canvas_height) // 2,
        canvas_width,
        canvas_height
    )

def update_background(window_width, window_height):
    """Re-scale the background while maintaining 16:9 aspect ratio."""
    # Calculate the scaled background
    target_aspect = 16 / 9
    window_aspect = window_width / window_height

    if window_aspect > target_aspect:
        new_height = window_height
        new_width = int(new_height * target_aspect)
    else:
        new_width = window_width
        new_height = int(new_width / target_aspect)

    # Scale the background image to the new size
    return pygame.transform.smoothscale(background, (new_width, new_height))

# Global flag to track active input mode (controller, mouse or keyboard)
active_input = "controller"  # Can be "controller", "mouse" or "keyboard"

def handle_controller_navigation(event):
    global selected_button_index, active_input
    active_input = "controller"

    # Block button interaction if confirm dialog is open
    if CONFIRM_STATE != ConfirmState.CLOSED:
        return

    if event.type == pygame.JOYHATMOTION:
        direction = None
        if event.value == (0, 1):  # D-pad Up
            direction = -1
        elif event.value == (0, -1):  # D-pad Down
            direction = 1

        if direction is not None:
            original_index = selected_button_index
            # Find the next non-DEACTIVATED button
            attempts = 0
            while attempts < NUM_BUTTONS:
                next_index = (selected_button_index + direction) % NUM_BUTTONS
                if buttons[next_index]["state"] != "DEACTIVATED":
                    selected_button_index = next_index
                    play_sound("select.wav")
                    break
                selected_button_index = next_index
                attempts += 1

            if attempts == NUM_BUTTONS:
                selected_button_index = original_index  # Reset if all buttons are DEACTIVATED

            debug_log(f"Controller moved: Selected {selected_button_index}")

    elif event.type == pygame.JOYBUTTONDOWN:
        direction = None
        if event.button == 11:  # D-pad Up
            direction = -1
        elif event.button == 12:  # D-pad Down
            direction = 1

        if direction is not None:
            original_index = selected_button_index
            # Find the next non-DEACTIVATED button
            attempts = 0
            while attempts < NUM_BUTTONS:
                next_index = (selected_button_index + direction) % NUM_BUTTONS
                if buttons[next_index]["state"] != "DEACTIVATED":
                    selected_button_index = next_index
                    play_sound("select.wav")
                    break
                selected_button_index = next_index
                attempts += 1

            if attempts == NUM_BUTTONS:
                selected_button_index = original_index  # Reset if all buttons are DEACTIVATED

            debug_log(f"Controller moved: Selected {selected_button_index}")

    # Update hover flags only for non-DEACTIVATED buttons
    for i, button in enumerate(buttons):
        if button["state"] != "DEACTIVATED":
            button["hovered_flag"] = (i == selected_button_index)
        else:
            button["hovered_flag"] = False

    if event.type == pygame.JOYBUTTONDOWN and event.button == 0:  # A button
        if buttons[selected_button_index]["state"] in ["HOVERED", "ACTIVE"]:
            activate_button(selected_button_index)
            
# Similarly update handle_keyboard_navigation
def handle_keyboard_navigation(event):
    global selected_button_index, active_input
    active_input = "keyboard"

    # Block button interaction if confirm dialog is open
    if CONFIRM_STATE != ConfirmState.CLOSED:
        return
    
    if event.key in [K_UP, K_DOWN]:
        direction = -1 if event.key == K_UP else 1
        original_index = selected_button_index
        
        # Keep trying next button until we find a non-DEACTIVATED one or complete a full cycle
        attempts = 0
        while attempts < NUM_BUTTONS:
            next_index = (selected_button_index + direction) % NUM_BUTTONS
            if buttons[next_index]["state"] != "DEACTIVATED":
                selected_button_index = next_index
                play_sound("select.wav")
                break
            selected_button_index = next_index
            attempts += 1
        
        if attempts == NUM_BUTTONS:
            selected_button_index = original_index  # Reset if all buttons are DEACTIVATED

        debug_log(f"Keyboard moved: Selected {selected_button_index}")

    # Update hover flags only for non-DEACTIVATED buttons
    for i, button in enumerate(buttons):
        if button["state"] != "DEACTIVATED":
            button["hovered_flag"] = (i == selected_button_index)
        else:
            button["hovered_flag"] = False

    if event.type == KEYDOWN:
        if event.key == K_SPACE:
            if buttons[selected_button_index]["state"] in ["HOVERED", "ACTIVE"]:
                activate_button(selected_button_index)
            
# Add this global variable to track the last mouse position
last_mouse_position = None
last_hovered_button_index = 0

def handle_mouse_navigation(event):
    global active_input, selected_button_index, last_hovered_button_index

    # Block button interaction if confirm dialog is open
    if CONFIRM_STATE != ConfirmState.CLOSED:
        return

    if active_input == "mouse":
        # Map mouse position to canvas coordinates
        mouse_x, mouse_y = event.pos
        canvas_mouse_x = mouse_x - canvas_rect.x
        canvas_mouse_y = mouse_y - canvas_rect.y

        hovered_any = False
        for i, button in enumerate(buttons):
            if button["rect"].collidepoint((canvas_mouse_x, canvas_mouse_y)):
                if button["state"] != "DEACTIVATED":  # Only allow hovering non-DEACTIVATED buttons
                    hovered_any = True
                    if not button["hovered_flag"]:
                        button["hovered_flag"] = True
                        debug_log(f"Mouse hovered over button {i}")

                    # Play sound if a new button is hovered over
                    if last_hovered_button_index != i:
                        play_sound("select.wav")
                        last_hovered_button_index = i

                    selected_button_index = i
            else:
                if button["state"] != "DEACTIVATED":  # Only modify non-DEACTIVATED buttons
                    button["hovered_flag"] = False

        # If no button was hovered, do not change the selected index
        if not hovered_any:
            return

def handle_mouse_selection(event):
    global active_input, selected_button_index

    # Block button interaction if confirm dialog is open
    if CONFIRM_STATE != ConfirmState.CLOSED:
        return

    if active_input == "mouse":
        mouse_x, mouse_y = event.pos
        canvas_mouse_x = mouse_x - canvas_rect.x
        canvas_mouse_y = mouse_y - canvas_rect.y

        button_clicked = False
        for i, button in enumerate(buttons):
            if button["rect"].collidepoint((canvas_mouse_x, canvas_mouse_y)):
                button_clicked = True
                if button["state"] == "DEACTIVATED":
                    play_sound("denied.wav")
                    return
                elif button["state"] in ["HOVERED", "ACTIVE"]:  # Allow ACTIVE buttons to be pressed
                    activate_button(i)
                    break
        
        # Only update states if a button was actually clicked
        if button_clicked:
            update_button_states(selected_button_index)

# Add a variable to track the last selected button
last_selected_button_index = None 
# Add a variable to track the last state of each button
last_button_state = [None] * len(buttons)  # None means no state has been set yet

# Update the button states function to handle initialization
def update_button_states(selected_index):
    global active_button_index, pressed_button_index, last_button_state
    global background_index, background, scaled_background
    global logo_index, logo

    # Only update if the selected index is different from the current background/logo index
    if selected_index == background_index and selected_index == logo_index:
        return

    for i, button in enumerate(buttons):
        # Preserve DEACTIVATED state
        if button["state"] == "DEACTIVATED":
            continue
            
        if i == pressed_button_index:
            button["state"] = "PRESSED"
        elif i == active_button_index:
            button["state"] = "ACTIVE"
        elif i == selected_index and button["hovered_flag"]:
            button["state"] = "HOVERED"
        else:
            button["state"] = "INACTIVE"
        
    # Change the background based on the selected button index
    background_index = selected_index
    background = pygame.image.load(BG_IMAGES[background_index]).convert()
    window_width, window_height = screen.get_size()
    scaled_background = update_background(window_width, window_height)

    # Change the logo based on the selected button index
    logo_index = selected_index
    logo = pygame.image.load(LOGO_IMAGES[logo_index]).convert_alpha()
    debug_log(f"Logo changed to {LOGO_IMAGES[logo_index]}")
    debug_log(f"Background changed to {BG_IMAGES[background_index]}")
    
def apply_deactivated_states(config):
    """Apply deactivated states based on configuration."""
    if config.get("KH1.5+2.5") == "Not Installed":
        for i in [0, 1, 2, 3]:  # KH1, CoM, KH2, BBS (using 0-based indices)
            buttons[i]["state"] = "DEACTIVATED"
    
    if config.get("KH2.8") == "Not Installed":
        for i in [4, 5]:  # DDD, AFP
            buttons[i]["state"] = "DEACTIVATED"
    
    if config.get("KH3") == "Not Installed":
        buttons[6]["state"] = "DEACTIVATED"  # KH3

def reapply_deactivated_states(config):
    for i, button in enumerate(buttons):
        # Reset DEACTIVATED state for KH1.5+2.5 buttons
        if i <= 3 and config.get("KH1.5+2.5") == "Not Installed":  # Buttons 0-3 (KH1, CoM, KH2, BBS)
            button["state"] = "DEACTIVATED"
            button["hovered_flag"] = False
            
        # Reset DEACTIVATED state for KH2.8 buttons
        elif i in [4, 5] and config.get("KH2.8") == "Not Installed":  # Buttons 4-5 (DDD, AFP)
            button["state"] = "DEACTIVATED"
            button["hovered_flag"] = False
            
        # Reset DEACTIVATED state for KH3 button
        elif i == 6 and config.get("KH3") == "Not Installed":  # Button 6 (KH3)
            button["state"] = "DEACTIVATED"
            button["hovered_flag"] = False
            
def scale_and_draw_buttons(canvas, scale_factor, elapsed_time):
    """Draw buttons to canvas according to their state, with hover and pulsing effects."""
    button_height = int(122 * scale_factor)
    button_width = int(500 * scale_factor)
    vertical_spacing = canvas.get_height() / (NUM_BUTTONS + 1)
    x_margin = int(canvas.get_width() * 0.026)

    for i, button in enumerate(buttons):
        button["rect"].width, button["rect"].height = button_width, button_height
        button["rect"].topleft = (
            x_margin,
            int(vertical_spacing * (i + 1) - button_height // 2)
        )

        # Draw ACTIVE or PRESSED states if applicable
        if button["state"] == "PRESSED":
            button_image = pygame.image.load(BUTTON_STATES["PRESSED"])
        elif button["state"] == "ACTIVE":
            button_image = pygame.image.load(BUTTON_STATES["ACTIVE"])
        elif button["state"] == "DEACTIVATED":
            button_image = pygame.image.load(BUTTON_STATES["DEACTIVATED"])   
        else:
            button_image = pygame.image.load(BUTTON_STATES["INACTIVE"])

        button_image = pygame.transform.smoothscale(button_image, (button_width, button_height))
        canvas.blit(button_image, button["rect"].topleft)

        if button["state"] == "DEACTIVATED":
            title_image = pygame.image.load(os.path.join(os.path.dirname(__file__), "no-title.png"))
        else:
            title_image = pygame.image.load(TITLE_IMAGES[i])

        title_image = pygame.transform.smoothscale(title_image, (button_width, button_height))
        canvas.blit(title_image, button["rect"].topleft)

        # Handle hover state
        if button["hovered_flag"]:
            hovered_image_path = (
                os.path.join(os.path.dirname(__file__), "button-3.png") if button["state"] == "ACTIVE" else os.path.join(os.path.dirname(__file__), "button-3b.png")
            )
            hovered_image = pygame.image.load(hovered_image_path)
            hovered_image = pygame.transform.smoothscale(hovered_image, (button_width, button_height))

            # Apply pulsing effect with a sine wave
            alpha = int((math.sin(elapsed_time * 1.0 * math.pi) + 1) * 127.5)  # Slower pulsing
            hovered_image.set_alpha(alpha)

            # Blend hovered image onto the canvas
            canvas.blit(hovered_image, button["rect"].topleft)

# Add a cooldown for switching input modes
last_input_switch_time = 0  # Track the last switch time
input_switch_cooldown = 200  # 200ms cooldown

def handle_input_switch(event):
    global active_input, last_input_switch_time
    current_time = pygame.time.get_ticks()

    # Prevent switching too quickly
    if current_time - last_input_switch_time < input_switch_cooldown:
        return

    if event.type in (pygame.MOUSEMOTION, MOUSEBUTTONDOWN):
        if active_input != "mouse":
            active_input = "mouse"
            last_input_switch_time = current_time
            debug_log("Switched to mouse input.")
    elif event.type in (pygame.JOYAXISMOTION, JOYBUTTONDOWN, JOYHATMOTION):
        if active_input != "controller":
            active_input = "controller"
            last_input_switch_time = current_time
            debug_log("Switched to controller input.")
    elif event.type == KEYDOWN:
        if active_input != "keyboard":
            active_input = "keyboard"
            last_input_switch_time = current_time
            debug_log("Switched to keyboard input.")

# Function to activate the selected button and change the background and logo
def activate_button(index):
    """Set a button's state to PRESSED and trigger the confirm dialog."""
    global active_button_index, pressed_button_index, pressed_button_time
    global CONFIRM_STATE, CONFIRM_SCALE, SELECTED_CONFIRM_BUTTON

    # If a button is already pressed, prevent further changes until it's done
    if pressed_button_index is not None and pressed_button_index != index:
         buttons[pressed_button_index]["state"] = "INACTIVE"
         pressed_button_index = None

    active_button_index = index
    pressed_button_index = index
    pressed_button_time = pygame.time.get_ticks()

    # Play confirm sound immediately when the button is activated
    play_sound("confirm.wav")
    debug_log(f"Playing confirm sound for button {index}")

    for i, button in enumerate(buttons):
        if i == index:
            button["state"] = "PRESSED"
        else:
            button["state"] = "INACTIVE"

    # Start the confirm dialog animation
    CONFIRM_STATE = ConfirmState.OPENING
    CONFIRM_SCALE = 0.0
    SELECTED_CONFIRM_BUTTON = "YES"
   
def handle_pressed_state():
    """Handle the transition from PRESSED to ACTIVE after the specified time."""
    global pressed_button_index, pressed_button_time
    if pressed_button_index is not None:
        # Transition to ACTIVE after duration
        elapsed_time = pygame.time.get_ticks() - pressed_button_time
        if elapsed_time >= button_press_duration:
            #play_sound("confirm.wav")
            debug_log(f"Button {pressed_button_index} transitioning to ACTIVE after {elapsed_time} ms")
            buttons[pressed_button_index]["state"] = "ACTIVE"
            pressed_button_index = None  # Reset the pressed state

def handle_input_and_states(event, config):
    global active_input, selected_button_index

    # Handle input mode switching
    handle_input_switch(event)

    # Handle input based on active mode
    if active_input == "controller" and event.type in [pygame.JOYBUTTONDOWN, pygame.JOYHATMOTION]:
        handle_controller_navigation(event)
    elif active_input == "mouse":
        if event.type == pygame.MOUSEMOTION:
            handle_mouse_navigation(event)
        elif event.type == MOUSEBUTTONDOWN:
            handle_mouse_selection(event)
    elif active_input == "keyboard" and event.type == KEYDOWN:
        handle_keyboard_navigation(event)

    # Update states and ensure DEACTIVATED states persist
    update_button_states(selected_button_index)
    reapply_deactivated_states(config)
    
# Add these functions for the confirm dialog system
def handle_confirm_input(event):
    global CONFIRM_STATE, SELECTED_CONFIRM_BUTTON, active_input

    if CONFIRM_STATE != ConfirmState.OPEN:
        return

    if active_input == "controller":
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button in [13, 14]:  # Left/Right on existing controllers
                SELECTED_CONFIRM_BUTTON = "NO" if SELECTED_CONFIRM_BUTTON == "YES" else "YES"
                play_sound("select.wav")
            if event.button == 0:  # A button (confirm)
                handle_confirm_selection()

        elif event.type == pygame.JOYHATMOTION:
            if event.value in [(-1, 0), (1, 0)]:  # Steam Deck D-pad Left/Right
                SELECTED_CONFIRM_BUTTON = "NO" if SELECTED_CONFIRM_BUTTON == "YES" else "YES"
                play_sound("select.wav")

    elif active_input == "keyboard" and event.type == KEYDOWN:
        if event.key in [K_LEFT, K_RIGHT]:  # Arrow keys for keyboard
            SELECTED_CONFIRM_BUTTON = "NO" if SELECTED_CONFIRM_BUTTON == "YES" else "YES"
            play_sound("select.wav")
        elif event.key == K_SPACE:  # Spacebar for confirm
            handle_confirm_selection()

def handle_confirm_selection():
    """Process the user's confirm or cancel choice."""
    global CONFIRM_STATE

    if SELECTED_CONFIRM_BUTTON == "NO":
        CONFIRM_STATE = ConfirmState.CLOSING
        play_sound("close.wav")
    else:
        play_sound("confirm.wav")
        if launch_game(config, active_button_index):
            pygame.quit()
            sys.exit()
        else:
            CONFIRM_STATE = ConfirmState.CLOSING
            play_sound("denied.wav")

def handle_confirm_mouse(mouse_pos, canvas_rect):
    global SELECTED_CONFIRM_BUTTON, active_input
    
    if CONFIRM_STATE != ConfirmState.OPEN:
        return

    # Calculate button dimensions based on canvas size
    button_width = int(177 * (canvas_rect.width / 1920))
    button_height = int(41 * (canvas_rect.height / 1080))
    
    # Button positions as percentages of canvas
    yes_button_x = int(canvas_rect.width * 0.3984)
    no_button_x = int(canvas_rect.width * 0.5089)
    button_y = int(canvas_rect.height * 0.5528)

    # Create precise rects for hit detection using top-left positioning
    yes_button_rect = pygame.Rect(
        yes_button_x, 
        button_y, 
        button_width, 
        button_height
    )

    no_button_rect = pygame.Rect(
        no_button_x, 
        button_y, 
        button_width, 
        button_height
    )

    # Check if mouse is over either button
    if yes_button_rect.collidepoint(mouse_pos[0] - canvas_rect.x, mouse_pos[1] - canvas_rect.y):
        if SELECTED_CONFIRM_BUTTON != "YES":
            SELECTED_CONFIRM_BUTTON = "YES"
            play_sound("select.wav")
    elif no_button_rect.collidepoint(mouse_pos[0] - canvas_rect.x, mouse_pos[1] - canvas_rect.y):
        if SELECTED_CONFIRM_BUTTON != "NO":
            SELECTED_CONFIRM_BUTTON = "NO"
            play_sound("select.wav")

def handle_confirm_mouse_click(event, canvas_rect):
    global CONFIRM_STATE
    
    if CONFIRM_STATE != ConfirmState.OPEN:
        return

    # Calculate button dimensions based on canvas size
    button_width = int(177 * (canvas_rect.width / 1920))
    button_height = int(41 * (canvas_rect.height / 1080))
    
    # Button positions as percentages of canvas
    yes_button_x = int(canvas_rect.width * 0.3984)
    no_button_x = int(canvas_rect.width * 0.5089)
    button_y = int(canvas_rect.height * 0.5528)

    # Create precise rects for hit detection using top-left positioning
    yes_button_rect = pygame.Rect(
        yes_button_x, 
        button_y, 
        button_width, 
        button_height
    )

    no_button_rect = pygame.Rect(
        no_button_x, 
        button_y, 
        button_width, 
        button_height
    )

    # Adjust mouse position to canvas coordinates
    canvas_mouse_x = event.pos[0] - canvas_rect.x
    canvas_mouse_y = event.pos[1] - canvas_rect.y

    # Check if mouse click is on either button
    if yes_button_rect.collidepoint(canvas_mouse_x, canvas_mouse_y):
        play_sound("confirm.wav")
        if launch_game(config, active_button_index):
            pygame.quit()
            sys.exit()
        else:
            CONFIRM_STATE = ConfirmState.CLOSING
            play_sound("denied.wav")
    elif no_button_rect.collidepoint(canvas_mouse_x, canvas_mouse_y):
        CONFIRM_STATE = ConfirmState.CLOSING
        play_sound("close.wav")

def scale_and_draw_confirm_dialog(canvas, scale_factor, elapsed_time):
    global CONFIRM_SCALE, CONFIRM_STATE
    
    # Handle animation states
    if CONFIRM_STATE == ConfirmState.OPENING:
        CONFIRM_SCALE += CONFIRM_SCALE_UP_SPEED * clock.get_time() / 1000.0
        if CONFIRM_SCALE >= 1.0:
            CONFIRM_SCALE = 1.0
            play_sound("open.wav")
            CONFIRM_STATE = ConfirmState.OPEN
    elif CONFIRM_STATE == ConfirmState.CLOSING:
        CONFIRM_SCALE -= CONFIRM_SCALE_DOWN_SPEED * clock.get_time() / 1000.0
        if CONFIRM_SCALE <= 0.0:
            CONFIRM_SCALE = 0.0
            CONFIRM_STATE = ConfirmState.CLOSED
            
    if CONFIRM_STATE == ConfirmState.CLOSED:
        return

    # Draw semi-transparent black overlay
    overlay = pygame.Surface((canvas.get_width(), canvas.get_height()))
    overlay.fill((0, 0, 0))
    overlay.set_alpha(CONFIRM_ALPHA)
    canvas.blit(overlay, (0, 0))

    # Only draw the dialog if we're in an active state
    if CONFIRM_SCALE > 0:
        # Explicitly set to 700x240 at full scale
        base_width = 700
        base_height = 240
        
        confirm_box_width = int(base_width * scale_factor * CONFIRM_SCALE)
        confirm_box_height = int(base_height * scale_factor * CONFIRM_SCALE)
        
        # Center the dialog box
        confirm_box_x = (canvas.get_width() - confirm_box_width) // 2
        confirm_box_y = (canvas.get_height() - confirm_box_height) // 2

        # Draw the box and text with preserved aspect ratios
        confirm_box = pygame.transform.smoothscale(CONFIRM_IMAGES["BOX"], (confirm_box_width, confirm_box_height))
        confirm_text = pygame.transform.smoothscale(CONFIRM_IMAGES["TEXT"], (confirm_box_width, confirm_box_height))
        
        canvas.blit(confirm_box, (confirm_box_x, confirm_box_y))

        # Draw buttons and cursor only when fully opened
        if CONFIRM_STATE == ConfirmState.OPEN:
            # Adjusted button positioning
            confirm_button_width = int(178 * scale_factor)
            confirm_button_height = int(42 * scale_factor)
            confirm_button_y = int(canvas.get_height() * 0.5528)
            
            # Adjusted x-positions for buttons
            yes_button_x = int(canvas.get_width() * 0.3984)
            no_button_x = int(canvas.get_width() * 0.5089)

            # YES button
            yes_button_image = CONFIRM_IMAGES["BUTTON_ACTIVE"] if SELECTED_CONFIRM_BUTTON == "YES" else CONFIRM_IMAGES["BUTTON_INACTIVE"]
            yes_button = pygame.transform.smoothscale(yes_button_image, (confirm_button_width, confirm_button_height))

            # NO button
            no_button_image = CONFIRM_IMAGES["BUTTON_ACTIVE"] if SELECTED_CONFIRM_BUTTON == "NO" else CONFIRM_IMAGES["BUTTON_INACTIVE"]
            no_button = pygame.transform.smoothscale(no_button_image, (confirm_button_width, confirm_button_height))

            # Add glow effect to active button
            glow = pygame.transform.smoothscale(CONFIRM_IMAGES["GLOW"], (confirm_button_width, confirm_button_height))
            alpha = int((math.sin(elapsed_time * 1.0 * math.pi) + 1) * 127.5)
            glow.set_alpha(alpha)

            canvas.blit(confirm_box, (confirm_box_x, confirm_box_y))
            canvas.blit(yes_button, (yes_button_x, confirm_button_y))
            canvas.blit(no_button, (no_button_x, confirm_button_y))
            
            # Update cursor position based on adjusted button positions
            if SELECTED_CONFIRM_BUTTON == "YES":
                canvas.blit(glow, (yes_button_x, confirm_button_y))
                cursor_x = int(canvas.get_width() * 0.3740)
            else:
                canvas.blit(glow, (no_button_x, confirm_button_y))
                cursor_x = int(canvas.get_width() * 0.4844)

            # Draw cursor
            cursor_width = int(63 * scale_factor)
            cursor_height = int(45 * scale_factor)
            cursor_y = int(canvas.get_height() * 0.5546)
            
            cursor_image = pygame.transform.smoothscale(CONFIRM_IMAGES["CURSOR"], (cursor_width, cursor_height))

            canvas.blit(cursor_image, (cursor_x, cursor_y))
            canvas.blit(confirm_text, (confirm_box_x, confirm_box_y))

def update_game_config(config, button_index):
    """Update the game's configuration JSON file with the correct targetExe path."""
    if button_index not in GAME_CONFIGS:
        debug_log(f"Invalid button index: {button_index}")
        return False
        
    game_info = GAME_CONFIGS[button_index]
    collection = game_info["collection"]
    
    # Get the installation path from config
    install_path = config.get(collection)
    if not install_path or install_path == "Not Installed":
        debug_log(f"Game collection {collection} is not installed")
        return False
        
    # Construct the full paths
    json_path = os.path.join(config["HeroicGamesConfig"], game_info["json"])
    target_exe = os.path.join(install_path, game_info["exe"])
    
    # Validate that the exe exists
    if not os.path.exists(target_exe):
        debug_log(f"Target exe not found: {target_exe}")
        return False
    
    try:
        # Read existing JSON config if it exists
        json_data = {}
        if os.path.exists(json_path):
            with open(json_path, 'r') as f:
                content = f.read().strip()
                if content:  # Only parse if file is not empty
                    json_data = json.loads(content)
        
        # Get the JSON ID (filename without extension)
        json_id = os.path.splitext(game_info["json"])[0]
        
        # Create or update the configuration
        if json_id not in json_data:
            json_data[json_id] = {}
        
        # Update targetExe while preserving other settings
        json_data[json_id]["targetExe"] = target_exe.replace('\\', '/')  # Use forward slashes for paths
        
        # Ensure required fields exist
        if "version" not in json_data:
            json_data["version"] = "v0"
        if "explicit" not in json_data:
            json_data["explicit"] = True
            
        # Write the updated config back to file
        with open(json_path, 'w') as f:
            json.dump(json_data, f, indent=2)
            
        debug_log(f"Successfully updated game config: {json_path}")
        return True
        
    except Exception as e:
        debug_log(f"Error updating game config: {e}")
        return False

def launch_game(config, button_index):
    """Update the game config and launch the game using Heroic."""
    if update_game_config(config, button_index):
        game_info = GAME_CONFIGS[button_index]
        
        try:
            # Get game ID and launch command based on OS
            game_id = os.path.splitext(game_info["json"])[0]
            launch_cmd = get_heroic_launch_command(game_id)
            
            process = subprocess.Popen(launch_cmd)
            
            # Wait a short time to ensure the process starts
            time.sleep(2)
            
            # Check if process is running
            if process.poll() is None:  # None means process is still running
                debug_log(f"Game launch process started successfully: {game_id}")
                return True
            else:
                debug_log(f"Game launch process failed to start: {game_id}")
                return False
                
        except Exception as e:
            debug_log(f"Error launching game: {e}")
            return False
    return False
            
# Main Game Loop (with floating logo logic)
def main():
    global config  # Make config global so it can be accessed in the game loop
    
    # Load existing configuration
    config = load_config()

    # Parse launch arguments before main launcher logic
    if handle_launch_arguments(config):
        return None  # Indicates game was launched

    # Check if all games are marked as "Not Installed"
    if not config:
        debug_log("No configuration file found. Running initial setup.", DEBUG)
        config = prompt_for_all_paths()
    elif all(value == "Not Installed" for key, value in config.items() if key in KH_REQUIRED_FILES):
        # messagebox.showinfo("No Game Paths Set", "No game paths are selected. You will be prompted to select paths again.")
        config = prompt_for_all_paths()

    # Prompt for Kingdom Hearts paths if not already configured
    kh_titles = {
        "KH1.5+2.5": "KINGDOM HEARTS HD 1.5+2.5 ReMIX",
        "KH2.8": "KINGDOM HEARTS HD 2.8 Final Chapter Prologue",
        "KH3": "KINGDOM HEARTS III"
    }

    for key, title in kh_titles.items():
        if key not in config or (config.get(key) not in ["Not Installed", None] and not os.path.exists(config[key])):
            while True:
                debug_log(f"Prompting for {title} installation folder.", DEBUG)
                folder = prompt_for_folder(f"Select the installation folder for {title} or cancel to proceed without it.")
                if not folder:
                    response = messagebox.askyesno("Missing Path", f"You did not select a folder for {title}. Do you want to continue without this game?")
                    if response:
                        config[key] = "Not Installed"
                        break
                    else:
                        continue

                if validate_install_path(folder, KH_REQUIRED_FILES[key]):
                    config[key] = folder
                    break
                else:
                    messagebox.showerror("Invalid Path", f"The selected folder is not a valid installation path for {title}. Please try again.")

    # Prompt for Heroic GamesConfig folder
    if "HeroicGamesConfig" not in config:
        debug_log("Prompting for Heroic GamesConfig folder.", DEBUG)
        while True:
            folder = prompt_for_folder("Select the Heroic GamesConfig folder (This should be found in AppData/Roaming/heroic/GamesConfig)", initialdir=appdata_folder)
            if not folder:
                messagebox.showerror("Missing Path", "You must select the Heroic GamesConfig folder to proceed. The launcher will now exit.")
                sys.exit(1)

            if validate_gamesconfig_path(folder):
                config["HeroicGamesConfig"] = folder
                break
            else:
                messagebox.showerror("Invalid Path", "The selected folder is not a valid GamesConfig path or no games are installed via Heroic. Please try again.")

    # Add Heroic executable check
    if "HeroicPath" not in config:
        debug_log("Prompting for Heroic executable location.", DEBUG)
        config["HeroicPath"] = prompt_for_heroic_exe()
        save_config(config)
    elif not os.path.exists(config["HeroicPath"]):
        debug_log("Heroic executable not found at saved location.", DEBUG)
        config["HeroicPath"] = prompt_for_heroic_exe()
        save_config(config)
        
    # Save configuration
    save_config(config)

    apply_deactivated_states(config)
    reapply_deactivated_states(config)
    
    return config  # Return the config so it can be used in the game loop

if __name__ == "__main__":
    config = main()  # Store the returned config

    if config is not None:
        running = True
        fullscreen = False
        previous_width, previous_height = screen.get_size()  # Store initial screen size

        # Initialize scaled_background with the current screen size
        scaled_background = update_background(previous_width, previous_height)

        # Store the initial logo size once
        initial_logo_width = logo.get_width()
        initial_logo_height = logo.get_height()

        # Handle scaling the canvas to the window
        window_width, window_height = screen.get_size()
        canvas_rect = calculate_canvas_fit(window_width, window_height)
        canvas = pygame.Surface((canvas_rect.width, canvas_rect.height))

        while running:
            # Get the current time
            current_time = pygame.time.get_ticks()
            elapsed_time = time.time() - start_time  # Time elapsed since the start
            
            # Detect if the window has been resized
            current_width, current_height = screen.get_size()
            
            if current_width != previous_width or current_height != previous_height:
                # The screen size has changed, so rescale the background
                scaled_background = update_background(current_width, current_height)
                previous_width, previous_height = current_width, current_height  # Update the previous size

            # Handle exiting with ESC
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                elif event.type == KEYDOWN:
                    # Handle ESC to quit
                    if event.key == K_ESCAPE:
                        running = False
                        
                # Handle fullscreen toggle (F11 or Alt+Enter)
                if event.type == KEYDOWN:
                    if event.key == K_F11 or (event.key == K_RETURN and pygame.key.get_mods() & KMOD_ALT):
                        screen = toggle_fullscreen()
                        debug_log(f"Fullscreen toggled: {fullscreen}")

                # Handle all input and state updates in one place
                handle_input_and_states(event, config)
                        
                # Confirm dialog        
                if event.type == MOUSEMOTION:
                    handle_mouse_navigation(event)
                    if CONFIRM_STATE == ConfirmState.OPEN:
                        handle_confirm_mouse(event.pos, canvas_rect)
                elif event.type == MOUSEBUTTONDOWN:
                    if CONFIRM_STATE == ConfirmState.OPEN:
                        handle_confirm_mouse_click(event, canvas_rect)
                    else:
                        handle_mouse_selection(event)

                # Handle confirm dialog input
                handle_confirm_input(event)

            # Handle PRESSED state timeout
            handle_pressed_state()

            # Ensure DEACTIVATED states persist after any state changes
            reapply_deactivated_states(config)

            # Handle scaling the canvas to the window
            window_width, window_height = screen.get_size()
            canvas_rect = calculate_canvas_fit(window_width, window_height)
            canvas = pygame.Surface((canvas_rect.width, canvas_rect.height))

            # Draw the scaled background onto the canvas
            canvas.blit(scaled_background, (0, 0))

            scale_factor = canvas_rect.width / ASSET_RESOLUTION[0]
            scale_and_draw_buttons(canvas, canvas_rect.width / ASSET_RESOLUTION[0], elapsed_time)

            # Scale the logo according to the scale factor once
            logo_scaled_width = int(logo.get_width() * scale_factor)
            logo_scaled_height = int(logo.get_height() * scale_factor)
            scaled_logo = pygame.transform.smoothscale(logo, (logo_scaled_width, logo_scaled_height))  # Scale logo

            logo_rect = logo.get_rect()  # Update the rect with the new scaled size

            # Animate the logo to float up and down
            time_passed = pygame.time.get_ticks() / 1000  # Get the time in seconds
            logo_x = int(canvas_rect.width * 0.3932)  # 39.32% of the screen width (adjust as needed)
            logo_y_offset = math.sin(elapsed_time * FLOAT_SPEED) * (canvas_rect.height * FLOAT_AMPLITUDE)
            logo_y = int(canvas_rect.height * 0.1935 + logo_y_offset)  # Update Y-position
            logo_rect.topleft = (logo_x, logo_y + logo_y_offset)

            # Draw the scaled logo over the background and buttons
            canvas.blit(scaled_logo, (logo_x, logo_y + logo_y_offset))

            screen.fill(BLACK)
            screen.blit(canvas, canvas_rect.topleft)

            # Draw the confirm dialog if it's active
            if CONFIRM_STATE != ConfirmState.CLOSED:
                scale_and_draw_confirm_dialog(canvas, scale_factor, elapsed_time)
                screen.blit(canvas, canvas_rect.topleft)

            pygame.display.flip()
            clock.tick(60)

pygame.quit()
sys.exit()
