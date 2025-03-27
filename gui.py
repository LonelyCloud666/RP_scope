import tkinter as tk
import matplotlib # type: ignore
matplotlib.use("Agg")
from matplotlib.figure import Figure # type: ignore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # type: ignore
from matplotlib.animation import FuncAnimation  # type: ignore
from scope_update import PlotUpdater
from tkinter import filedialog
import os
from tkinter import messagebox

class App(tk.Tk):

    def __init__(self, data, sine_wave_data, ch_time, data_processor):
        super().__init__()
        self.data = data
        self.sine_wave_data = sine_wave_data
        self.ch_time = ch_time
        self.data_processor = data_processor
        self.ch_toggle = [True, True, True, True]
        self.state = 0
        self.active_channel = 0

        self.zoom_up_ico = tk.PhotoImage(file=r"./img/zoom_up.png") 
        self.zoom_down_ico = tk.PhotoImage(file=r"./img/zoom_down.png")
        self.settings_ico = tk.PhotoImage(file=r"./img/settings.png")
        self.eye_ico = tk.PhotoImage(file=r"./img/eye.png")
        self.photo_ico = tk.PhotoImage(file=r"./img/photo.png")
        self.sine_ico = tk.PhotoImage(file=r"./img/sine.png")

        self.ch_units = self.data_processor.unit
        self.ch_ratio = self.data_processor.ratio

        self.title("Scope")
        self.geometry("1024x600")
        self.config(cursor="none")

        self.setup_grid()
        self.create_widgets()
        self.update_display()
        self.plot_updater = PlotUpdater(self.fig, self.ax, self.data, self.sine_wave_data, self.ch_toggle, self.state, self.ch_time)
        self.animation = FuncAnimation(self.fig, self.plot_updater.update_plot, interval=800, blit=True)

    def setup_grid(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, minsize=150, weight=1)

    def create_widgets(self):
        self.create_left_frame()
        self.create_center_frame()
        self.create_right_frame()

    def create_left_frame(self):
        self.left_frame = tk.Frame(self, bg="lightgray", width=150)
        self.left_frame.grid(row=0, column=0, sticky="nswe")

        buttons = [
            (self.photo_ico, self.save_plot),
            (self.zoom_up_ico, self.zoom_up),
            (self.zoom_down_ico, self.zoom_down),
            (self.eye_ico, self.ch_toggle_fnc),
            (self.sine_ico, self.main_ch_set),
            (self.settings_ico, self.settings)
        ]

        for image, command in buttons:
            button = tk.Button(self.left_frame, image=image, width=50, command=command, bg="lightgray", activebackground="lightgray", activeforeground="black")
            button.pack(fill=tk.BOTH, expand=True)

    def create_center_frame(self):
        self.center_frame = tk.Frame(self, bg="white")
        self.center_frame.grid(row=0, column=1, sticky="nswe")
        self.center_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.center_frame.grid_rowconfigure(0, weight=0)
        self.center_frame.grid_rowconfigure(1, weight=1)
        self.center_frame.grid_rowconfigure(2, weight=0)

        self.labels = [tk.Label(self.center_frame, text="Loading...", font=("Arial", 10)) for _ in range(4)]
        for i, label in enumerate(self.labels):
            label.grid(row=0, column=i, padx=10, pady=10, sticky="nsew")

        self.fig = Figure(figsize=(5, 3), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.center_frame)
        self.canvas.get_tk_widget().grid(row=1, column=0, columnspan=4, pady=10, sticky="nsew")

        self.label4 = tk.Label(self.center_frame, text="Loading...", font=("Arial", 14))
        self.label4.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

    def create_right_frame(self):
        self.right_frame = tk.Frame(self, bg="lightgray", width=150)
        self.right_frame.grid(row=0, column=2, sticky="nswe")
        self.exit_button = tk.Button(
            self.right_frame, text="Exit", width=5, command=self.close_window, 
            bg="red", activebackground="red", activeforeground="black"
        )
        self.exit_button.pack(fill=tk.BOTH, expand=True)

        self.ch_buttons = []
        for i in range(4):
            button = tk.Button(
                self.right_frame, text=f"Ch{i}", width=5, 
                command=lambda i=i: self.active_channel_fnc(i), 
                bg="darkgray", activebackground="lightblue", 
                activeforeground="black"
            )
            button.pack(fill=tk.BOTH, expand=True)
            self.ch_buttons.append(button)

        self.state_button_right = tk.Button(
            self.right_frame, text="mode:\nsine", width=5, 
            command=self.cycle_state_right, bg="lightgray", 
            activebackground="lightgray", activeforeground="black"
        )
        self.state_button_right.pack(fill=tk.BOTH, expand=True)

    def cycle_state_right(self):
        self.state = (int(self.state) + 1) % 3
        new_text = ["sine", "raw", "both"][self.state]
        new_text = "mode:\n" + new_text
        self.state_button_right.config(text=new_text)
        self.plot_updater.state = self.state

    def description(self, index):
        _, (amplitude, frequency, phase) = self.sine_wave_data[index]
        amplitude = amplitude * self.ch_ratio[index] / self.data_processor.ch_zoom[index]
        unit = self.ch_units[index]
        ratio = self.ch_ratio[index] / self.data_processor.ch_zoom[index]
        rms = amplitude / 2 ** 0.5
        if frequency > 0:
            phase_shift_ms = (phase / (2 * 3.141592653589793)) * (1 / frequency) * 1000
        else:
            phase_shift_ms = 0
        return (f"Ch{index}   {ratio:.1f} {unit} / 1\n Amp={amplitude:.2f} {unit}     Rms={rms:.2f} {unit}\n "
                f"Freq={frequency:.0f}Hz,\n Phase Shift={phase_shift_ms:.3f}ms")

    def update_display(self):
        self.ch_units = self.data_processor.unit
        self.ch_ratio = self.data_processor.ratio
        if not self.attributes("-fullscreen"):
            self.attributes("-fullscreen", True)
        local_data = self.data.copy()
        local_sine_wave_data = self.sine_wave_data.copy()
        if local_data[4]:
            for index, label in enumerate(self.labels):
                label.config(text=self.description(index))
            self.label4.config(text=f"Sample rate: {local_data[5]:.0f} Hz")

        for i, button in enumerate(self.ch_buttons):
            button.config(bg="lightskyblue" if i == self.active_channel else "darkgray")
            button.config(activebackground="lightskyblue" if i == self.active_channel else "darkgray")

        self.after(100, self.update_display)

    def set_ylim(self, ymin, ymax):
        self.ax.set_ylim(ymin, ymax)

    def zoom_up(self):
        _, (amplitude, frequency, phase) = self.sine_wave_data[self.active_channel]
        if amplitude < 0.1:
            self.data_processor.ch_zoom[self.active_channel] += 5
        else:
            self.data_processor.ch_zoom[self.active_channel] += 0.2

    def zoom_down(self):
        self.data_processor.ch_zoom[self.active_channel] -= 0.2

    def main_ch_set(self):
        self.data_processor.main_channel = self.active_channel

    def ch_toggle_fnc(self):
        self.ch_toggle[self.active_channel] = not self.ch_toggle[self.active_channel]

    def active_channel_fnc(self, i):
        self.active_channel = i

    def settings(self):
        settings_window = SettingsWindow(self, self.data_processor)

    def save_plot(self):
        self.animation.event_source.stop()

        usb_drives = [f"/media/student/{d}" for d in os.listdir("/media/student") if os.path.isdir(f"/media/student/{d}")]
        if not usb_drives:
            messagebox.showerror("Error", "No USB detected!")
            self.animation.event_source.start()
            return

        usb_path = usb_drives[0]
        results_folder = os.path.join(usb_path, "CT Test Results")
        os.makedirs(results_folder, exist_ok=True)

        index = 0
        while os.path.exists(os.path.join(results_folder, f"plot{index}.png")):
            index += 1
        file_path = os.path.join(results_folder, f"plot{index}.png")

        # Show "Saving" popup
        saving_popup = tk.Toplevel(self)
        saving_popup.title("Saving")
        saving_popup.geometry("200x100")
        saving_popup.transient(self)
        saving_popup.grab_set()
        tk.Label(saving_popup, text="Saving...", font=("Arial", 12)).pack(expand=True, pady=20)

        self.update_idletasks()  # Ensure the popup is displayed before saving

        try:
            spacing = 1/(self.ch_toggle.count(True)+1)
            count = 1
            for i in range(4):
                if self.ch_toggle[i]:
                    self.ax.text(
                        spacing * count, 1.03,
                        self.description(i),
                        fontsize=6, ha="center", transform=self.ax.transAxes
                    )
                    count += 1
            self.fig.savefig(file_path, format='png', dpi=300)
        except Exception as e:
            print(f"Error saving plot: {e}")
        finally:
            saving_popup.destroy()  # Close the "Saving" popup
            self.animation.event_source.start()

        # Show success popup
        messagebox.showinfo("Success", f"Plot saved to:\n{file_path}")

    def close_window(self):
        self.quit()
        self.destroy()

class SettingsWindow:
    def __init__(self, master, data_processor):
        self.data_processor = data_processor
        self.master = master
        self.window = tk.Toplevel(master)
        self.window.title("Settings")
        self.window.config(cursor="none")

        self.window.focus_force()
        self.window.grab_set()

        # Unit
        tk.Label(self.window, text="Unit", font=("Arial", 14)).pack(pady=10)
        self.unit_inputs = []
        unit_frame = tk.Frame(self.window)
        unit_frame.pack(pady=5)
        for i in range(4):
            entry = tk.Entry(unit_frame, width=10)
            entry.insert(0, data_processor.unit[i])
            entry.pack(side=tk.LEFT, padx=10)
            self.unit_inputs.append(entry)

        # Ratio
        tk.Label(self.window, text="Ratio", font=("Arial", 14)).pack(pady=10)
        self.ratio_inputs = []
        ratio_frame = tk.Frame(self.window)
        ratio_frame.pack(pady=5)
        for i in range(4):
            entry = tk.Entry(ratio_frame, width=10)
            entry.insert(0, f"{data_processor.ratio[i]}")
            entry.pack(side=tk.LEFT, padx=10)
            self.ratio_inputs.append(entry)

        # Buttons
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)
        tk.Button(button_frame, text="Save", height=3, width=6, command=self.save).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Sync", height=3, width=6, command=self.sync_phase).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Sync\nClear", height=3, width=6, command=self.sync_clear).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Exit", height=3, width=6, command=self.close_window).pack(side=tk.LEFT, padx=10)

    def save(self):
        try:
            units = [entry.get() for entry in self.unit_inputs]
            ratios = [float(entry.get()) for entry in self.ratio_inputs]
            self.data_processor.update_unit_ratio(units, ratios)
        except ValueError:
            pass

    def sync_phase(self):
        self.data_processor.sync_phase_offset()

    def sync_clear(self):
        self.data_processor.update_phase_offset([0, 0, 0, 0])

    def close_window(self):
        self.window.destroy()