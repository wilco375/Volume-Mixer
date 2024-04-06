import tkinter as tk
from tkinter.font import Font

show_vars = None
priority_vars = None

def get_applications():
    # Sample data, replace this with your actual data source
    return [
        # {"name": "App 1", "show": True, "priority": 1},
        # {"name": "App 2", "show": False, "priority": 2},
        # {"name": "App 3", "show": True, "priority": 3},
        # Add more sample data here to test scroll functionality
        {"name": f"App {i}", "show": True, "priority": i} for i in range(4, 21)
    ]

def update_application(index, show, priority):
    # Sample function to update application data
    print(f"Updating application at index {index}: Show={show}, Priority={priority}")

def update_show(index):
    show = show_vars[index].get()
    update_application(index, show, priority_vars[index].get())

def update_priority(index):
    priority = priority_vars[index].get()
    update_application(index, show_vars[index].get(), priority)

def validate_priority(new_value):
    if new_value.isdigit() or new_value == "":
        return True
    else:
        return False

def create_table(canvas_frame, applications):
    num_apps = len(applications)
    labels = [None] * num_apps
    show_vars = [None] * num_apps
    priority_vars = [None] * num_apps

    for i, app in enumerate(applications):
        labels[i] = tk.Label(canvas_frame, text=app["name"], padx=10, pady=5, width=30, anchor='w')
        labels[i].grid(row=i+1, column=0, sticky='w')

        show_vars[i] = tk.BooleanVar(value=app["show"])
        show_check = tk.Checkbutton(canvas_frame, variable=show_vars[i], command=lambda idx=i: update_show(idx))
        show_check.grid(row=i+1, column=1)

        priority_vars[i] = tk.StringVar(value=str(app["priority"]))
        priority_entry = tk.Entry(canvas_frame, textvariable=priority_vars[i], width=5)
        priority_entry.grid(row=i+1, column=2, padx=10, pady=5)
        priority_entry.config(validate="key", validatecommand=(canvas_frame.register(validate_priority), '%P'))
        priority_entry.bind('<FocusOut>', lambda event, idx=i: update_priority(idx))

    return show_vars, priority_vars

root = None
def show(_):
    global root
    if root:
        # UI already open
        return

    root = tk.Tk()
    root.title("Volume Mixer Settings")
    root.configure(padx=20, pady=20)

    # Title label
    title_label = tk.Label(root, text="Volume Mixer Settings", font=("Arial", 14, "bold"), anchor='w')
    title_label.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))

    # Create a canvas and attach scrollbar
    canvas = tk.Canvas(root)
    canvas.grid(row=2, column=0, columnspan=3)
    canvas_frame = tk.Frame(canvas)
    scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
    scrollbar.grid(row=2, column=3, sticky='ns')
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.create_window((0, 0), window=canvas_frame, anchor='nw')

    # Add header labels with bold font
    bold_font = Font(weight="bold")
    bold_font.configure(size=10)  # Set the font size to match the default size
    tk.Label(canvas_frame, text="Name", padx=10, pady=5, width=30, anchor='w', font=bold_font).grid(row=0, column=0, sticky='w')
    tk.Label(canvas_frame, text="Show", padx=10, pady=5, font=bold_font, anchor='w').grid(row=0, column=1, sticky='w')
    tk.Label(canvas_frame, text="Priority", padx=10, pady=5, font=bold_font, anchor='w').grid(row=0, column=2, sticky='w')

    applications = get_applications()
    global show_vars, priority_vars
    show_vars, priority_vars = create_table(canvas_frame, applications)

    # Update scroll region after widget is placed in canvas
    canvas_frame.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

    root.mainloop()
    
    root = None

def quit():
    if root is not None: 
        root.destroy()