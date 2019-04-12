import os
import shutil
import tkinter as tk
import tkinter.filedialog
import re

class MyCheckBox:
    def __init__(self, parent, text, chosen_dict, row, column):
        self.var = tk.IntVar()
        self.text = text
        self.button = tk.Checkbutton(parent, text=self.text, variable=self.var)
        self.button.grid(row=row, column=column)
        self.chosen_dict = chosen_dict
        
        def change_checked(*args):
            print (self.text)
            if self.var.get() == 1:
                self.chosen_dict[self.text] = None
            else:
                self.chosen_dict.pop(self.text)
        
        self.var.trace('w', change_checked)

class FileChooser:
    def __init__(self, pattern, exclusive=True):
        self.filenames = []
        self.pattern_string = pattern
        self.pattern = re.compile(pattern)
        self.exclusive = exclusive
        self.chosen = {}
    
    def offer_file(self, filename, full_filename):
        if self.pattern.match(filename):
            self.filenames.append(full_filename)
    
    def make_widgets(self, root, column):
        label = tk.Label(root, text=self.pattern_string)
        label.grid(row=0, column=column)
        if len(self.filenames) == 0:
            return
        if self.exclusive:
            choice_var = tk.StringVar()
            option_menu = tk.OptionMenu(root, choice_var, *self.filenames)
            option_menu.grid(row=1, column=column)
            
            def change_dropdown(*args):
                self.chosen = {choice_var.get(): None}
            
            choice_var.trace('w', change_dropdown)
        else:
            frame = tk.Frame(root)
            frame.grid(row=1, column=column)
            
            for i, filename in enumerate(self.filenames):
                check_box = MyCheckBox(frame, filename, self.chosen, i, 0)
                        
    
    def copy_to(self, directory):
        for chosen in self.chosen:
            shutil.copy(chosen, directory)

window = tk.Tk()

artist_chooser = FileChooser('.+_artist\.py', False)

choosers = [
    FileChooser('gui\.py'),
    FileChooser('camera\.py'),
    FileChooser('renderer\.py'),
    artist_chooser,
    FileChooser('location_filter\.py'),
    FileChooser('osm_helper\.py'),
    FileChooser('geometry\.py')
    ]

code_dir = '.'
for person_dir in os.listdir(code_dir):
    full_dir = os.path.join(code_dir, person_dir)
    if os.path.isdir(full_dir):
        for code_file in os.listdir(full_dir):
            full_file = os.path.join(full_dir, code_file)
            if os.path.isfile(full_file):
                for chooser in choosers:
                    chooser.offer_file(code_file, full_file)

for i, chooser in enumerate(choosers):
    chooser.make_widgets(window, i)


save_button = tk.Button(window, text='Save')
save_button.grid(row=2, column=0)

def save(event):
    save_dir = tk.filedialog.asksaveasfilename()
    os.mkdir(save_dir)
    if os.path.isdir(save_dir):
        for chooser in choosers:
            chooser.copy_to(save_dir)
        
        with open(os.path.join(save_dir, 'artists.py'), 'w') as file:
            modules = []
            for filename in artist_chooser.chosen:
                basename = os.path.basename(filename)
                module = os.path.splitext(basename)[0]
                modules.append(module)
            class_names = []
            for module in modules:
                class_names.append(module[0].upper() + module[1:-7] + "Artist")
            
            for module in modules:
                file.write('import {}\n'.format(module))
            
            file.write('\ndef get_artists():\n    artists = []\n')
            for module, class_name in zip(modules, class_names):
                file.write('    artists.append({}.{}())\n'.format(module, class_name))
            
            file.write('    return artists\n')

save_button.bind('<Button-1>', save)

window.mainloop()
