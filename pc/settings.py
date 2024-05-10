import tkinter as tk
from tkinter.font import Font
from communication import Communicator

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
        for app in self.comm.volume_provider.get_applications():
            applications.append({
                "name": app.get_display_name(),
                "binary": app.get_binary(),
                "show": app.get_binary() not in self.comm.volume_provider.config["blacklist"],
                "priority": i
            })
            i += 1

        return applications

    def update_application(self, index, name, show, priority):
        print(f"Updating application at index {index}: Name={name}, Show={show}, Priority={priority}")

    def update_show(self, index):
        show = self.show_vars[index].get()
        self.applications[index]["show"] = show
        binary = self.applications[index]["binary"]
        blacklist = self.comm.volume_provider.config["blacklist"]
        if show:
            blacklist.remove(binary)
        else:
            blacklist.append(binary)
        self.comm.volume_provider.update_config()
        self.comm.send_applications()

    def update_priority(self, index):
        priority = self.priority_vars[index].get()
        if not priority:
            priority = 99999
        self.applications[index]["priority"] = int(priority)
        sorted_applications = sorted(self.applications, key=lambda x: int(x['priority']))
        self.comm.volume_provider.config["priority"] = [app["binary"] for app in sorted_applications]
        self.comm.volume_provider.update_config()
        self.comm.send_applications()

    def update_name(self, index):
        name = self.name_vars[index].get()
        if not name:
            return
        self.comm.volume_provider.config["display_names"][self.applications[index]["binary"]] = name
        self.comm.volume_provider.update_config()
        self.comm.send_applications()

    def validate_priority(self, new_value):
        return new_value.isdigit() or new_value == ""

    def validate_name(self, new_value):
        return "," not in new_value

    def create_table(self, canvas_frame, applications):
        num_apps = len(applications)
        self.show_vars = [None] * num_apps
        self.priority_vars = [None] * num_apps
        self.name_vars = [None] * num_apps

        for i, app in enumerate(applications):
            self.name_vars[i] = tk.StringVar(value=app["name"])
            name_entry = tk.Entry(canvas_frame, textvariable=self.name_vars[i], width=30)
            name_entry.grid(row=i+1, column=0, sticky='w')
            name_entry.config(validate="key", validatecommand=(canvas_frame.register(self.validate_name), '%P'))
            name_entry.bind('<FocusOut>', lambda event, idx=i: self.update_name(idx))

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
        self.root.iconbitmap("icon.ico")
        self.root.configure(padx=20, pady=20)

        self.root.minsize(450, 200)

        # Title label
        title_label = tk.Label(self.root, text="Volume Mixer Settings", font=("Arial", 14, "bold"), anchor='w')
        title_label.grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 10))

        # Create a canvas and attach scrollbar
        canvas = tk.Canvas(self.root, highlightthickness=0)
        canvas.grid(row=2, column=0, columnspan=3, sticky='nsew')
        canvas_frame = tk.Frame(canvas)
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollbar.grid(row=2, column=3, sticky='ns')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.create_window((0, 0), window=canvas_frame, anchor='nw')
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)  

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