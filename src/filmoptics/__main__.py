'''
GUI figure plotter.
'''

from .tmm_utils import calculate_RAT
from functools import partial
from itertools import count, cycle
from pathlib import Path

import tkinter as tk
from tkinter.font import nametofont
from tkinter.filedialog import askopenfilename, asksaveasfilename
from tkinter.messagebox import showerror

from matplotlib.pyplot import Figure, colorbar
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np



NK_PATH = Path(__file__).parent.parent / "nk"

class Plot:
    def __init__(self, x, y, color=None, name=None):
        self.x = x
        self.y = y
        self.color = next(COLORS) if color is None else color
        self.name = name

class Layer:
    def __init__(self, name, indices, thickness, coherent):
        self.name = tk.StringVar(value=name)
        self.indices = tk.StringVar(value=indices)
        self.t = tk.StringVar(value=thickness)
        self.c = tk.IntVar(value=coherent)

class Wavelengths:
    def __init__(self, lmin, lmax, points):
        self.lmin = tk.StringVar(value=lmin)
        self.lmax = tk.StringVar(value=lmax)
        self.points = tk.StringVar(value=points)

    def get_vector(self):
        lmin = float(self.lmin.get())
        lmax = float(self.lmax.get())
        points = int(self.points.get())
        return np.linspace(lmin, lmax, points)

class MainWindow:
    """"""
    def __init__(self, root):
        self.root = root
        self.root.title("Optical")
        self.win_struct = tk.Toplevel(self.root)
        self.other = StructWindow(self.win_struct, self)

        self.n_loaded = count(1)
        self.plots = []
        self.choice = tk.StringVar(value="R")
        self.save_win = None

        # Matplotlib chart
        self.figure = Figure(figsize=(8,5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, self.root)
        self.fig_widget = self.canvas.get_tk_widget()
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root, pack_toolbar=False)
        self.toolbar.update()

        # Button panel
        self.frm_menu = tk.Frame(master=self.root, bd=1)
        self.btn_plot = self.make_button_panel()
        # Plots panel
        self.frm_plots = tk.Frame(master=self.root, bd=2, relief="groove", padx=10)
        self.make_plot_labels()

        # Aligment of main elements
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.columnconfigure(1, minsize=80)

        self.frm_menu.grid(row=0, column=0, padx=5, sticky="ns")
        self.frm_plots.grid(row=0, column=1, sticky="ns")
        self.fig_widget.grid(row=0, column=2, sticky="nswe")
        self.toolbar.grid(row=1, column=2, sticky="we")

    
    def plot(self):
        self.ax.clear()
        for p in self.plots:
            self.ax.plot(p.x, p.y, color=p.color)
        self.canvas.draw()
    
    def plot_rat(self):
        d = self.other.rat
        c = self.choice.get()
        self.plots.append(Plot(d["x"], d[c], name=f"Calculated {c}"))
        self.make_plot_labels()

    def remove(self, i):
        del self.plots[i]
        self.make_plot_labels()

    def clear_list(self):
        self.plots = []
        self.make_plot_labels()

    def make_plot_labels(self):
        frm = self.frm_plots
        # Clear frame
        for widget in frm.winfo_children():
            widget.destroy()
        # Title label and clear button
        lbl_frm_title = tk.Label(master=frm, text="Plot list")
        lbl_frm_title.grid(row=1, column=0, pady=10, sticky="ew")
        lbl_frm_title.configure(font=U_FONT)

        btn_clear = tk.Button(master=frm, text="Clear", command=self.clear_list)
        btn_clear.grid(row=0, column=0, pady=5, sticky="ew")

        # Redraw labels and button for all plots
        for i, p in enumerate(self.plots):
            lbl_line = tk.Label(master=frm, text='--', fg=p.color)
            lbl_line.configure(font=LINE_FONT)
            lbl_name = tk.Label(master=frm, text=p.name)
            btn_remove = tk.Button(master=frm, text='X', command=partial(self.remove, i))

            lbl_line.grid(row=i+2, column=0, sticky="w")
            lbl_name.grid(row=i+2, column=1, sticky="e")
            btn_remove.grid(row=i+2, column=2)
        # Redraw all plots
        self.plot()

    def make_button_panel(self):
        frm = self.frm_menu
        btn_open = tk.Button(master=frm, text="Load data", command=self.open_file)
        btn_edit = tk.Button(
            master=frm,
            text="Edit structure",
            command=self.win_struct.deiconify,
            )
        frm_plot = tk.Frame(master=frm)
        btn_plot = tk.Button(
            master=frm_plot, 
            text="Plot", 
            command=self.plot_rat, 
            state="disabled"
            )
        btn_plot.grid(row=0, column=0, sticky="ws")
        for i,s in enumerate("RTA"):
            sel_plt = tk.Radiobutton(
                    master=frm_plot,
                    value=s,
                    variable=self.choice,
                    text=s,
                    )
            sel_plt.grid(row=i, column=1, sticky="w")

        btn_save = tk.Button(master=frm, text="Save plot data", command=self.open_save_plots)

        btn_open.grid(row=0, column=0, pady=30, sticky="new")
        btn_edit.grid(row=1, column=0, pady=5, sticky="ew")
        frm_plot.grid(row=2, column=0, pady=5, sticky="nswe")
        btn_save.grid(row=3, column=0, pady=15, sticky="we")

        return btn_plot

    def open_file(self):
        """Open data file for plotting."""
        filepath = askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        
        x, y = np.loadtxt(filepath, skiprows = 1, unpack=True)
        self.plots.append(Plot(x, y, name= f"Plot {next(self.n_loaded)}"))
        self.make_plot_labels()

    def open_save_plots(self):
        if self.save_win: self.save_win.destroy()
        self.save_win = tk.Toplevel(master=self.root)
        sel_var = tk.IntVar(value=0)
        for i, p in enumerate(self.plots):
            sel = tk.Radiobutton(
                master=self.save_win,
                value=i,
                variable=sel_var,
                text=p.name,
                )
            sel.grid(row=i, column=0, pady=10, sticky="ew")
        btn_save = tk.Button(
            master=self.save_win,
            text="Save",
            command=partial(self.save_plot, sel_var.get())
            )
        btn_save.grid(row=len(self.plots), column=0, padx=10, pady=10, sticky="w")
    
    def save_plot(self, i):
        """Save text to file."""
        filepath = asksaveasfilename(
            defaultextension="txt",
            filetypes=[("Text files", "*.txt"), ("All Files", "*.*")]
        )
        if not filepath:
            return
        p = self.plots[i]
        data = np.c_[p.x, p.y]
        np.savetxt(filepath, data, fmt="%.8e", delimiter="\t", header=p.name)


class StructWindow:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.root.title("Edit Structure")
        self.root.protocol("WM_DELETE_WINDOW", self.root.withdraw)
        self.root.withdraw()   
        self.layers = [
            Layer("Air", NK_PATH / "air.nk", "inf", 0),
            Layer("Si", NK_PATH / "Si.nk", "inf", 0),
            ]
        self.active = tk.IntVar(value=0)
        self.lams = Wavelengths(200, 1000, 500)
        self.rat = None
       
        # Widgets
        self.lbl_str = tk.Label(master=self.root, text="Multilayer structure")

        self.frm_struct = tk.Frame(master=self.root, bd=2, relief="groove")
        self.make_struct_panel()

        self.frm_loadsave = tk.Frame(master=self.root, bd=2)
        btn_save = tk.Button(
            master=self.frm_loadsave, text="Save structure", command=self.save_struct
            )
        btn_load = tk.Button(
            master=self.frm_loadsave, text="Load structure", command=self.load_struct
            )
        btn_save.grid(row=0, column=0, pady=5, sticky="w")
        btn_load.grid(row=1, column=0, pady=5, sticky="w")

        self.frm_data = tk.Frame(master=self.root, bd=1)
        self.make_layer_panel()

        self.frm_lams = tk.Frame(master=self.root, bd=2, relief="groove")
        self.make_wv_panel()
        
        # Alignment of main elemnts
        self.root.columnconfigure(0, minsize=150)

        self.lbl_str.grid(row=0, column=0, pady=1)
        self.frm_struct.grid(row=1, column=0, padx=10, sticky="nsew")
        self.frm_data.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.frm_loadsave.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
        self.frm_lams.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

        
    def load_nk(self):
        """Chose nk data filepath"""
        filepath = askopenfilename(
            master=self.root,
            filetypes=[("NK files", "*.nk"), ("Text files", "*.txt"), ("All Files", "*.*")],
        )
        if not filepath:
            return
        layer = self.layers[self.active.get()]
        layer.indices.set(filepath)
    

    def calculate(self):
        x = self.lams.get_vector()
        try:
            r, t = calculate_RAT(self.layers, x)
        except (IOError, ValueError):
            showerror("File error", "Encountered a problem when loading nk file")
        else:
            self.rat =dict(x=x, R=r, T=t, A=1-r-t)
            self.parent.btn_plot.config(state="normal")

    def save_struct():
        pass

    def load_struct():
        pass


    def remove_layer(self,i):
        if len(self.layers) < 3: return
        if i == self.active.get(): self.active.set(0)
        del self.layers[i]
        self.make_struct_panel()

    def add_layer(self, i):
        new_layer = Layer("New Layer", "nkdata/air.nk", "100", 1)
        self.layers.insert(i+1, new_layer)
        self.make_struct_panel()

    def make_struct_panel(self):
        frm = self.frm_struct
        # Clear frame
        for widget in frm.winfo_children():
            widget.destroy()

        n = len(self.layers)
        for i, l in enumerate(self.layers):

            select_layer = tk.Radiobutton(
                master=frm,
                value=i,
                variable=self.active,
                textvariable=l.name,
                command=lambda: self.make_layer_panel(),
                )
            select_layer.grid(row=i, column=0, sticky="nw")

            if i != n-1:
                btn_add_layer = tk.Button(
                    master=frm,
                    text='+',
                    command=partial(self.add_layer, i),
                    )
                btn_add_layer.grid(row=i, column=2, sticky="nw")

                if i > 0:
                    btn_remove_layer = tk.Button(
                        master=frm,
                        text='X',
                        command=partial(self.remove_layer, i),
                        )
                    btn_remove_layer.grid(row=i, column=1, sticky="nw")

    def make_layer_panel(self):
        frm = self.frm_data
        # Clear frame
        for widget in frm.winfo_children():
            widget.destroy()
        i = self.active.get()
        n = len(self.layers)
        layer = self.layers[i]
        lbl_name = tk.Label(master=frm, text="Name")
        ent_name = tk.Entry(master=frm, textvariable=layer.name)

        lbl_thick = tk.Label(master=frm, text="Thickness (nm)")
        ent_thick = tk.Entry(master=frm, textvariable=layer.t, width=10)

        lbl_c = tk.Label(master=frm, text="Coherent?")
        chk_c = tk.Checkbutton(master=frm, variable=layer.c)

        lbl_nk = tk.Label(master=frm, text="Indices")
        ent_nk = tk.Entry(master=frm, textvariable=layer.indices, width=30)

        btn_load = tk.Button(master=frm, text="Load NK file", command=self.load_nk)

        if i in (0, n-1):
            ent_thick.configure(state="disabled")
            chk_c.configure(state="disabled")

        lbl_name.grid(row=0, column=0, sticky="w")
        ent_name.grid(row=1, column=0)
        lbl_thick.grid(row=2, column=0, sticky="w")
        ent_thick.grid(row=3, column=0, sticky="w")
        lbl_c.grid(row=2, column=1, sticky="w", padx=5)
        chk_c.grid(row=3, column=1, padx=5)
        lbl_nk.grid(row=4, column=0, sticky="w")
        ent_nk.grid(row=5, column=0)
        btn_load.grid(row=5, column=1, padx=5)
        
    def make_wv_panel(self):
        frm = self.frm_lams
        lbl_lmin = tk.Label(master=frm, text="Min wavelength (nm)")
        ent_lmin = tk.Entry(master=frm, textvariable=self.lams.lmin, width=15)
        lbl_lmax = tk.Label(master=frm, text="Max wavelength (nm)")
        ent_lmax = tk.Entry(master=frm, textvariable=self.lams.lmax, width=15)
        lbl_lnum = tk.Label(master=frm, text="Number of points")
        ent_lnum = tk.Entry(master=frm, textvariable=self.lams.points, width=15)
        btn_calc = tk.Button(master=frm, text="Calculate", command=self.calculate)
        
        lbl_lmin.grid(row=0, column=0, sticky="w", padx=5)
        ent_lmin.grid(row=1, column=0, sticky="w", padx=5)
        lbl_lmax.grid(row=0, column=1, sticky="w", padx=5)
        ent_lmax.grid(row=1, column=1, sticky="w", padx=5)
        lbl_lnum.grid(row=0, column=2, sticky="w", padx=5)
        ent_lnum.grid(row=1, column=2, sticky="w", padx=5)
        btn_calc.grid(row=2, column=2, sticky="e", padx=5, pady=10)


COLORS = cycle([
    'blue', 'green', 'red', 'cyan','magenta', 'yellow', 'black',
    ])

if __name__ == '__main__':  
     # Create window
    window = tk.Tk()
    # Make fonts
    default_font = nametofont("TkDefaultFont")
    U_FONT = default_font.copy()
    U_FONT.configure(underline=True)
    LINE_FONT = default_font.copy()
    LINE_FONT.configure(size=19, weight='bold')
    # Create app and run
    app = MainWindow(window)
    window.mainloop()
    
    
   
    

    