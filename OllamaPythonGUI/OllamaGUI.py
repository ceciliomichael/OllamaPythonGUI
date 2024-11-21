import customtkinter as ctk
import requests
import threading
import json
import os

# Initialize context for conversation memory
context = None

# Load context from file if it exists
try:
    with open("context.json", "r") as file:
        context = json.load(file)
except FileNotFoundError:
    context = None

# Load instruction from file if it exists
try:
    with open("instruction.json", "r") as file:
        instruction = json.load(file)
except FileNotFoundError:
    instruction = ""

# Load model from file if it exists
try:
    with open("model.json", "r") as file:
        model = json.load(file)
except FileNotFoundError:
    model = "mistral-nemo:12b-instruct-2407-q2_K"  # Default model

# Load conversation from file if it exists, otherwise create an empty file
if not os.path.exists("conversation.txt"):
    with open("conversation.txt", "w") as file:
        pass

# Function to send prompt to Ollama API and get response
def get_response(event=None):  # Add event parameter with default None
    global context
    prompt = large_text_entry.get("1.0", ctk.END).strip()  # Specify required arguments
    if not prompt:
        return

    # Clear the message box
    large_text_entry.delete("1.0", ctk.END)

    # Append user message to the large text box
    large_text.configure(state=ctk.NORMAL)
    large_text.insert(ctk.END, f"You: {prompt}\n")
    large_text.configure(state=ctk.DISABLED)
    large_text.yview(ctk.END)  # Scroll to the bottom

    # Append user message to conversation file
    with open("conversation.txt", "a", encoding="utf-8") as file:
        file.write(f"You: {prompt}\n")

    def fetch_response():
        global context
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "context": context
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            response_text = response_data.get("response", "No response received.")
            context = response_data.get("context", None)
        else:
            response_text = f"Error: {response.status_code}"

        # Append bot response to the large text box
        large_text.configure(state=ctk.NORMAL)
        large_text.insert(ctk.END, f"Model: {response_text}\n")
        large_text.configure(state=ctk.DISABLED)
        large_text.yview(ctk.END)  # Scroll to the bottom

        # Append bot response to conversation file
        with open("conversation.txt", "a", encoding="utf-8") as file:
            file.write(f"Model: {response_text}\n")

        # Save context to file
        with open("context.json", "w") as file:
            json.dump(context, file)

    # Run the fetch_response function in a separate thread
    threading.Thread(target=fetch_response).start()

# Function to clear conversation memory
def clear_memory():
    global context
    context = None  # Clear the context
    large_text.configure(state=ctk.NORMAL)
    large_text.delete("1.0", ctk.END)
    large_text.configure(state=ctk.DISABLED)

    # Remove context file
    try:
        os.remove("context.json")
    except FileNotFoundError:
        pass

    # Clear conversation file
    with open("conversation.txt", "w") as file:
        pass

    # Send the instruction to the AI as a prompt
    send_instruction_as_prompt(instruction)

    # Echo "Memory cleared." in the small echo box
    echo_text.configure(state=ctk.NORMAL)
    echo_text.delete("1.0", ctk.END)
    echo_text.insert(ctk.END, "Memory cleared.")
    echo_text.configure(state=ctk.DISABLED)

# Function to save instruction to file and send it to the AI
def save_instruction():
    instruction_text = small_text.get("1.0", ctk.END).strip()
    with open("instruction.json", "w") as file:
        json.dump(instruction_text, file)
    
    # Clear memory before applying new instructions
    clear_memory()
    
    # Send the instruction to the AI as a prompt
    send_instruction_as_prompt(instruction_text)
    
    # Echo "Instructions applied." in the small echo box
    echo_text.configure(state=ctk.NORMAL)
    echo_text.delete("1.0", ctk.END)
    echo_text.insert(ctk.END, "Instructions applied.")
    echo_text.configure(state=ctk.DISABLED)

# Function to send instruction as a prompt to the AI
def send_instruction_as_prompt(instruction):
    global context
    prompt = instruction

    def fetch_response():
        global context
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "context": context
        }

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            response_data = response.json()
            context = response_data.get("context", None)

        # Save context to file
        with open("context.json", "w") as file:
            json.dump(context, file)

    # Run the fetch_response function in a separate thread
    threading.Thread(target=fetch_response).start()

# Function to swap models
def swap_model():
    global context, model
    new_model = model_text.get("1.0", ctk.END).strip()
    if not new_model:
        return

    def unload_model():
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": model,
            "prompt": "",
            "keep_alive": 0
        }
        requests.post(url, headers=headers, json=data)

    def load_model():
        url = "http://localhost:11434/api/generate"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": new_model,
            "prompt": ""
        }
        requests.post(url, headers=headers, json=data)

    # Unload the current model and load the new model
    threading.Thread(target=unload_model).start()
    threading.Thread(target=load_model).start()

    # Update the model and save it to file
    model = new_model
    with open("model.json", "w") as file:
        json.dump(model, file)

    # Clear the context and update the UI
    context = None
    large_text.configure(state=ctk.NORMAL)
    large_text.delete("1.0", ctk.END)
    large_text.insert(ctk.END, f"Model swapped to {new_model}.")
    large_text.configure(state=ctk.DISABLED)

# Function to unload the current model
def unload_model():
    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": model,
        "prompt": "",
        "keep_alive": 0
    }
    requests.post(url, headers=headers, json=data)

# Function to load a new model
def load_model():
    global context, model
    new_model = model_text.get("1.0", ctk.END).strip()
    if not new_model:
        return

    url = "http://localhost:11434/api/generate"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": new_model,
        "prompt": ""
    }
    requests.post(url, headers=headers, json=data)

    # Update the model and save it to file
    model = new_model
    with open("model.json", "w") as file:
        json.dump(model, file)

    # Clear the context and update the UI
    context = None
    large_text.configure(state=ctk.NORMAL)
    large_text.delete("1.0", ctk.END)
    large_text.insert(ctk.END, f"Model loaded: {new_model}.")
    large_text.configure(state=ctk.DISABLED)

# Function to clear the instruction text box
def clear_instruction():
    small_text.delete("1.0", ctk.END)
    large_text.configure(state=ctk.NORMAL)
    large_text.delete("1.0", ctk.END)
    large_text.insert(ctk.END, "Instruction cleared.")
    large_text.configure(state=ctk.DISABLED)

# Function to copy large text content to clipboard
def copy_large_text():
    root.clipboard_clear()
    root.clipboard_append(large_text.get("1.0", ctk.END).strip())
    root.update()  # Now it stays on the clipboard after the window is closed

# Create the main window
root = ctk.CTk()

# Set the window title
root.title("OllamaGUI")

# Set the window size
root.geometry("1000x600")

# Set the font to support colorful emojis
emoji_font = ("Segoe UI Emoji", 12)

# Create a frame for the left side
left_frame = ctk.CTkFrame(root)
left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

# Create a large text area in the left frame
large_text = ctk.CTkTextbox(left_frame, width=50, height=20, font=emoji_font)
large_text.pack(fill="both", expand=True, padx=10, pady=10)

# Load conversation into the large text box if it exists
with open("conversation.txt", "r", encoding="utf-8") as file:
    conversation = file.read()
    large_text.insert("1.0", conversation)
large_text.configure(state=ctk.DISABLED)

# Add a copy button above the large text area
copy_button = ctk.CTkButton(left_frame, text="Copy", command=copy_large_text)
copy_button.pack(pady=(0, 10))  # Apply padding only to the bottom

# Add an entry text box below the large text area
large_text_entry = ctk.CTkTextbox(left_frame, width=200,height=75, font=emoji_font)  # Adjusted width
large_text_entry.pack(fill="both", padx=10)
large_text_entry.bind("<Control-Return>", get_response)  # Bind Ctrl+Enter key to get_response function

# Add a button under the entry text box
large_text_button = ctk.CTkButton(left_frame, text="Send Message", command=get_response)
large_text_button.pack(pady=10)

# Create a frame for the right side
right_frame = ctk.CTkFrame(root)
right_frame.pack(side="right", fill="y", padx=10, pady=10)

# Create a small text box in the right frame for custom instructions
small_text = ctk.CTkTextbox(right_frame, width=350, height=200, font=emoji_font)
small_text.pack(padx=10, pady=10)

# Load instruction into the small text box if it exists
if instruction:
    small_text.insert("1.0", instruction)

# Add a frame for the instruction buttons
instruction_button_frame = ctk.CTkFrame(right_frame)
instruction_button_frame.pack(pady=10)

# Add a button under the small text box to save instruction
small_text_button = ctk.CTkButton(instruction_button_frame, text="Save Instruction", command=save_instruction)
small_text_button.pack(side="left", padx=5)

# Add a button to clear instruction next to the save instruction button
clear_instruction_button = ctk.CTkButton(instruction_button_frame, text="Clear Instruction", command=clear_instruction)
clear_instruction_button.pack(side="left", padx=5)

# Create a small text box in the right frame for model input
model_text = ctk.CTkTextbox(right_frame, width=300, height=25, font=emoji_font)
model_text.pack(padx=10, pady=10)

# Load model into the model text box if it exists
model_text.insert("1.0", model)

# Create a frame for the model buttons
model_button_frame = ctk.CTkFrame(right_frame)
model_button_frame.pack(padx=10, pady=10)

# Add buttons to load and unload models side by side
unload_model_button = ctk.CTkButton(model_button_frame, text="Unload Model", command=unload_model)
unload_model_button.pack(side="left", padx=5)

load_model_button = ctk.CTkButton(model_button_frame, text="Load Model", command=load_model)
load_model_button.pack(side="left", padx=5)

# Create a small text box in the right frame for echo messages
echo_text = ctk.CTkTextbox(right_frame, width=350, height=50, font=emoji_font)
echo_text.pack(padx=10, pady=10)
echo_text.configure(state=ctk.DISABLED)

# Add a button to clear memory at the bottom right
clear_button = ctk.CTkButton(right_frame, text="Clear Memory", command=clear_memory)
clear_button.pack(side="bottom", pady=10)

# Run the application
root.mainloop()