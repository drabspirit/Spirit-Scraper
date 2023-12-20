import os
import tkinter as tk
from tkinter import filedialog
import subprocess
import sys
import threading
import atexit
import scraper
import re

def cleanup():
    # Clean up any resources or stop any processes here
    pass

atexit.register(cleanup)

processing_lock = threading.Lock()
stop_processing_event = threading.Event()

def stop_processing():
    stop_processing_event.set()  # Set the event to signal stop processing
    print("Processing stopped by user.")

def main():
    if len(sys.argv) > 1:
        input_method = sys.argv[1].strip().lower()

        if input_method == "manual":
            if len(sys.argv) > 2:
                game_name = sys.argv[2].strip()
                price = scraper.scrape_price(game_name)
                print(f"The price of {game_name} is: {price}")
            else:
                print("Usage: runt.exe manual <game_name>")
        elif input_method == "txt" or input_method == "json":
            if len(sys.argv) > 2:
                file_path = sys.argv[2].strip()
                output_file_path = os.path.join(os.path.dirname(file_path), "output.txt")
                retry_file_path = os.path.join(os.path.dirname(file_path), "retry.txt")
                scraper.scrape_prices_from_file(file_path, output_file_path, retry_file_path)
            else:
                print("Usage: runt.exe (txt|json) <file_path>")
        else:
            print("Invalid input method.")
    else:
        print("Usage: runt.exe (manual|txt|json) <args>")

if __name__ == "__main__":
    main()
def select_file():
    file_path = filedialog.askopenfilename(initialdir=os.path.dirname(__file__), title="Select File")
    if file_path:
        return file_path

def add_game(game_name):
    try:
        cleaned_game_name = scraper.clean_game_name(game_name)  # Clean the game name
        with open(file_path_entry.get(), "r+") as file:
            lines = [line.strip() for line in file]  # Read lines and remove leading/trailing whitespace
            if cleaned_game_name not in lines:  # Check if the game is already in the file
                lines.append(cleaned_game_name)  # Add the cleaned game name to the list
                lines.sort()  # Sort the list alphabetically
                file.seek(0)  # Move the cursor to the beginning of the file
                file.truncate()  # Clear the file contents
                file.write("\n".join(lines))  # Write the updated list to the file
                print(f"The game '{game_name}' was added.")
                output_text.insert(tk.END, f"The game '{game_name}' was added.\n")
            else:
                print(f"The game '{game_name}' already exists in the file.")
    except Exception as e:
        print(f"An error occurred while adding the game '{game_name}': {str(e)}")

def scrape_prices_from_file(input_file_path, output_file_path, retry_file_path):
    try:
        tf2_key_price = scraper.scrape_tf2_key_price()

        with open(input_file_path, "r") as file:
            with open(output_file_path, "w") as output_file, open(retry_file_path, "w") as retry_file:
                output_file.write(f"TF2 Key Price: ${tf2_key_price}\n\n")
                output_file.write("Game Name | Price | TF2 Key/Price\n\n")

                for line in file:
                    if stop_processing_event.is_set():  # Check if stop signal is set
                        print("Processing stopped by user.")
                        break  # Stop processing if the event is set

                    # Skip empty lines
                    if not line.strip():
                        continue

                    # Process each non-empty line here
                    cleaned_line = line.strip()  # Remove leading/trailing whitespace
                    game_price = scraper.scrape_price(cleaned_line)  # Scrape price for the game
                    if game_price:
                        # Remove non-numeric characters (e.g., '$') from the price before converting to float
                        cleaned_game_price = re.sub(r'[^\d.]', '', game_price)
                        ratio = round(float(cleaned_game_price) / float(tf2_key_price), 2)
                        output_line = f"{cleaned_line} | {game_price} | {ratio}\n"
                        output_file.write(output_line)
                        print(f"Processed: {output_line.strip()}")  # Print the processed line
                    else:
                        retry_file.write(f"{cleaned_line}\n")
                        print(f"Game not found: {cleaned_line}")  # Print a message for games not found

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        stop_processing_event.clear()  # Clear the event to reset for future use

def run_scraper():
    global processing_lock
    with processing_lock:
        try:
            file_path = file_path_entry.get()
            if not file_path:
                print("No file selected.")
                return

            _, file_extension = os.path.splitext(file_path)
            if file_extension.lower() not in ['.txt', '.json']:
                print("Unsupported file format.")
                return

            output_text.delete(1.0, tk.END)
            threading.Thread(target=scrape_and_update_ui, args=(file_path, file_extension)).start()
        except Exception as e:
            print(f"An error occurred while running the scraper: {str(e)}")

def scrape_and_update_ui(file_path, file_extension):
    global stop_processing_flag
    global processing_lock
    with processing_lock:
        try:
            if file_extension == ".txt":
                output_file_path = os.path.join(os.path.dirname(file_path), "output.txt")
                retry_file_path = os.path.join(os.path.dirname(file_path), "retry.txt")
                scrape_prices_from_file(file_path, output_file_path, retry_file_path)
                print("TXT processing completed.")
            elif file_extension == ".json":
                output_file_path = os.path.join(os.path.dirname(file_path), "output.json")
                scraper.scrape_prices_from_json(file_path, output_file_path)
                print("JSON processing completed.")
            else:
                print("Unsupported file format.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
def open_input_file():
    file_path = file_path_entry.get()
    if not file_path or not os.path.isfile(file_path):
        file_path = "list.txt"
        with open(file_path, "w"):
            pass
    subprocess.Popen(['notepad.exe', file_path])

def open_output_file():
    file_path = "output.txt"
    with open(file_path, "w"):
        pass
    subprocess.Popen(['notepad.exe', file_path])

def open_retry_file():
    file_path = os.path.join(os.path.dirname(file_path_entry.get()), "retry.txt")
    if os.path.isfile(file_path):
        subprocess.Popen(['notepad.exe', file_path])
    else:
        print("Retry file does not exist.")

class TextRedirector:
    def __init__(self, widget, tag):
        self.widget = widget
        self.tag = tag
        self.alive = True  # Flag to track if the widget is alive

    def write(self, message):
        if self.alive and self.widget and hasattr(self.widget, 'winfo_exists') and self.widget.winfo_exists():  
            self.widget.insert(tk.END, message, (self.tag,))
            self.widget.see(tk.END)  
        else:
            self.alive = False  # Set the flag to False if the widget is destroyed

    def close(self):
        self.alive = False  # Set the flag to False when closing the widget

# Create the main window
window = tk.Tk()
window.title("Spirit Key Pricer")

# Configure columns and rows to expand and shrink with window size
for i in range(6):
    window.columnconfigure(i, weight=1)
    window.rowconfigure(i, weight=1)

# Add a label and entry for the file path
file_path_label = tk.Label(window, text="File Path:")
file_path_label.grid(row=0, column=0, sticky="e")
file_path_entry = tk.Entry(window)
file_path_entry.grid(row=0, column=1, columnspan=2, sticky="ew")
file_path_entry.insert(0, "list.txt")  # Default file path

# Add a button to select the file
select_file_button = tk.Button(window, text="Select File", command=select_file)
select_file_button.grid(row=0, column=3, sticky="w")

# Add an entry for adding new games
game_entry_label = tk.Label(window, text="Add Game:")
game_entry_label.grid(row=1, column=0, sticky="e")
game_entry = tk.Entry(window)
game_entry.grid(row=1, column=1, columnspan=2, sticky="ew")

# Add a button to add the game to the file
add_game_button = tk.Button(window, text="Add Game", command=lambda: add_game(game_entry.get()))
add_game_button.grid(row=1, column=3, sticky="w")

# Add a button to run the scraper program
run_scraper_button = tk.Button(window, text="Run Scraper", command=run_scraper)
run_scraper_button.grid(row=2, column=1, columnspan=2, sticky="ew")

# Add a status label for displaying messages or errors
status_label = tk.Label(window, text="", fg="red")
status_label.grid(row=3, column=0, columnspan=4, sticky="ew")

# Add a text widget to display stdout and stderr
output_text = tk.Text(window, wrap=tk.WORD, height=10)
output_text.grid(row=4, column=0, columnspan=4, sticky="nsew")
output_text.tag_config("stdout", foreground="black")  # Style for stdout messages
output_text.tag_config("stderr", foreground="red")    # Style for stderr messages

# Create an instance of TextRedirector
text_redirector = TextRedirector(output_text, "stdout")

sys.stdout = text_redirector
sys.stderr = text_redirector

def on_closing():
    text_redirector.close()  # Close the TextRedirector
    window.destroy()

# Add buttons to open input and output files
open_input_button = tk.Button(window, text="Open Input File", command=open_input_file)
open_input_button.grid(row=5, column=0, sticky="ew")

open_output_button = tk.Button(window, text="Open Output File", command=open_output_file)
open_output_button.grid(row=5, column=1, sticky="ew")

# Add a button to open the retry file
open_retry_button = tk.Button(window, text="Open Retry File", command=open_retry_file)
open_retry_button.grid(row=5, column=2, sticky="ew")

# Add a button to stop processing and write the found and not found games to the appropriate files
stop_processing_button = tk.Button(window, text="Stop Processing", command=stop_processing, bg="red")
stop_processing_button.grid(row=5, column=3, sticky="ew")

# Bind the window closing event to the on_closing function
window.protocol("WM_DELETE_WINDOW", on_closing)

# Run the GUI
window.mainloop()

if __name__ == "__main__":
    main()
