import tkinter as tk
from tkinter.font import Font
from communication import Communicator
import yaml

class Settings():
    show_vars = None
    priority_vars = None
    name_vars = None
    root = None

    def __init__(self, comm: Communicator) -> None:
        self.comm = comm

    def get_applications(self):
        applications = []
        i = 0
        for app in self.comm.volume_provider.get_applications(False, True):
            applications.append({
                "name": app.get_display_name(),
                "binary": app.get_binary(),
                "show": app.get_binary() not in self.comm.volume_provider.config["blacklist"],
                "priority": i
            })
            i += 1

        return applications

    def update_show(self, index):
        show = self.show_vars[index].get()
        if show:
            self.comm.volume_provider.config["blacklist"].remove(self.applications[index]["binary"])
        else:
            self.comm.volume_provider.config["blacklist"].append(self.applications[index]["binary"])

        self.comm.volume_provider.update_config()

    def update_priority(self, index):
        priorities = [i for (i, priority) in sorted(enumerate(self.priority_vars), key=lambda x: int(x[1].get()))]
        priorities_binaries = [self.applications[i]["binary"] for i in priorities]
        self.comm.volume_provider.config["priority"] = priorities_binaries
        self.comm.volume_provider.update_config()

    def update_name(self, index):
        name = self.name_vars[index].get()
        self.comm.volume_provider.config["display_names"][self.applications[index]["binary"]] = name
        self.comm.volume_provider.update_config()

    def validate_priority(self, new_value):
        return new_value.isdigit() or new_value == ""

    def create_table(self, canvas_frame, applications):
        num_apps = len(applications)
        labels = [None] * num_apps
        self.show_vars = [None] * num_apps
        self.priority_vars = [None] * num_apps
        self.name_vars = [None] * num_apps

        for i, app in enumerate(applications):
            self.name_vars[i] = tk.StringVar(value=app["name"])
            labels[i] = tk.Entry(canvas_frame, textvariable=self.name_vars[i], width=30)
            labels[i].grid(row=i+1, column=0, sticky='w')
            labels[i].bind('<FocusOut>', lambda event, idx=i: self.update_name(idx))

            self.show_vars[i] = tk.BooleanVar(value=app["show"])
            show_check = tk.Checkbutton(canvas_frame, variable=self.show_vars[i], command=lambda idx=i: self.update_show(idx))
            show_check.grid(row=i+1, column=1)

            self.priority_vars[i] = tk.StringVar(value=str(app["priority"]))
            priority_entry = tk.Entry(canvas_frame, textvariable=self.priority_vars[i], width=5)
            priority_entry.grid(row=i+1, column=2, padx=10, pady=5)
            priority_entry.config(validate="key", validatecommand=(canvas_frame.register(self.validate_priority), '%P'))
            priority_entry.bind('<FocusOut>', lambda event, idx=i: self.update_priority(idx))

    def show(self, _):
        if self.root:
            # UI already open
            return

        self.root = tk.Tk()
        self.root.title("Volume Mixer Settings")
        self.root.configure(padx=20, pady=20)

        # Title label
        title_label = tk.Label(self.root, text="Volume Mixer Settings", font=("Arial", 14, "bold"), anchor='w')
        title_label.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))

        # Create a canvas and attach scrollbar
        canvas = tk.Canvas(self.root, highlightthickness=0)
        canvas.grid(row=2, column=0, columnspan=3)
        canvas_frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=2, column=3, sticky='ns')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.create_window((0, 0), window=canvas_frame, anchor='nw')

        # Add header labels with bold font
        bold_font = Font(weight="bold")
        bold_font.configure(size=10)  # Set the font size to match the default size
        tk.Label(canvas_frame, text="Name", padx=10, pady=5, width=30, anchor='w', font=bold_font).grid(row=0, column=0, sticky='w')
        tk.Label(canvas_frame, text="Show", padx=10, pady=5, font=bold_font, anchor='w').grid(row=0, column=1, sticky='w')
        tk.Label(canvas_frame, text="Priority", padx=10, pady=5, font=bold_font, anchor='w').grid(row=0, column=2, sticky='w')

        self.applications = self.get_applications()
        self.create_table(canvas_frame, self.applications)

        # Update scroll region after widget is placed in canvas
        canvas_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        self.root.mainloop()
        
        self.root = None

    def quit(self):
        if self.root is not None: 
            self.root.destroy()
