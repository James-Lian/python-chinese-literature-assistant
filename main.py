# Chinese Literature Learner Assistant
# !! GPU is recommended, otherwise loading times (especially for the OCR) may take a couple of seconds
# !! when working text files, only utf-8 is supported
# !! this program only handles simplified Chinese characters

# 1) scan an image to extract Chinese characters (optional)
# 2) the learning window opens, choose to translate your Chinese text to English, to Pinyin, or look them up in a dictionary!
# 3) if you want, you can save your Chinese text into a text file (utf-8)

from pathlib import Path

from tkinter import *
from tkinter import filedialog
from tkinter import scrolledtext
from PIL import Image, ImageTk, ImageOps

import easyocr
import cv2
import numpy as np

from hanzipy.dictionary import HanziDictionary
import pinyin
from deep_translator import *

from dragonmapper.transcriptions import numbered_to_accented

# global variables
filepath = "" # image filepath for OCR scanning
root = None # root Tkinter window
reader = easyocr.Reader(['ch_sim', 'en']) # OCR model
font_size = 16
dictionary = HanziDictionary() # search up Chinese characters, phrases, idioms, and more

# changing the font size in learning_window
def font_change(growth: bool, widgets: list):
    global font_size
    # increase font size
    if growth:
        font_size += 2
    # decrease font size
    else:
        font_size -= 2
    
    for widget in widgets:
        new_font = ("Calibri", font_size)
        widget.config(font=new_font)

# save your Chinese characters to a .txt file (utf-8)
def save_text(text):
    path = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[("Text files", ".txt")])
    if path == None:
        return
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    f.close()

# open a text file with Chinese characters (utf-8 only)
def open_text(widget, window, scroll_widget):
    text_path = filedialog.askopenfilename(initialdir = "/", title = "Upload a file", filetypes = [("Text file", ".txt")])
    window.title("Edit and lookup: " + str(text_path))

    # read and close the .txt file
    txt = Path(text_path).read_text(encoding='utf-8')
    widget.delete('1.0', END)
    widget.insert(INSERT, txt)

    scroll_widget.config(state='normal')
    scroll_widget.delete('1.0', END)
    scroll_widget.config(state='disabled')

# translate the user's Chinese text to English
def to_english(chinese, scroll_widget):
    translated = GoogleTranslator(source="zh-CN", target='english').translate(chinese)
    scroll_widget.config(state='normal')
    scroll_widget.delete('1.0', END)
    scroll_widget.insert(INSERT, translated + "\n\n(Translated with Google Translate)")
    scroll_widget.config(state='disabled')

# translate the user's Chinese text to Pinyin
def to_pinyin(chinese, scroll_widget):
    scroll_widget.config(state='normal')
    scroll_widget.delete('1.0', END)
    paragraph = chinese.split("\n")
    for line in paragraph:
        if line != "":
            scroll_widget.insert(INSERT, str(line) + "\n")
            scroll_widget.insert(INSERT, str(pinyin.get(line, delimiter=" ") + "\n"))
    scroll_widget.config(state='disabled')

# Retrieves the user's selected text, and looks up the text in a dictionary
def to_dictionary(edit_widget, scroll_widget):
    scroll_widget.config(state='normal')
    scroll_widget.delete('1.0', END)
    try:
        selected_txt = edit_widget.selection_get()
        # remove punctuation from the highlighted text
        punctuation = ['。', '，', '、', '‘', '’', '“', '”', '：', '；', '？', '！', '（', '）', '《', '》' ,'·']
        for mark in punctuation:
            selected_txt = selected_txt.replace(mark, "")

        # if the user only selected a single character, look up the character's definition in the dictionary
        if len(selected_txt) == 1:
            for dict in dictionary.definition_lookup(selected_txt):            
                scroll_widget.insert(INSERT, dict["simplified"] + " (" + dict["traditional"] +")\nPY " + numbered_to_accented(dict["pinyin"]) + "\n" + dict["definition"] + "\n\n")
        scroll_widget.insert(INSERT, "<Search>\n\n")
        # search the dictionary for instances when the selected text appears in a phrase, idiom, etc. 
        for dict in dictionary.dictionary_search(selected_txt, "only"):
            scroll_widget.insert(INSERT, dict["simplified"] + "\nPY " + numbered_to_accented(dict["pinyin"]) + "\n" + dict["definition"] + "\n\n")
    except:
        scroll_widget.insert(INSERT, "Please select some text in the left textbox to look it up in a dictionary.\n请在左边文本框中突出一些文本以在词典中查找。")
    scroll_widget.config(state='disabled')

# a window for editing the Chinese text, translating it, looking it up in a dictionary, saving it, etc.
def learning_window(text):
    global root
    global filepath

    try:
        root.destroy()
    except:
        pass

    parent = Tk()
    parent.title("Edit and lookup: " + str(filepath))
    parent.geometry("1000x600+100+200")

    # Config rows and columns
    parent.rowconfigure(1, weight=1)
    parent.columnconfigure(1, weight=1)
    parent.columnconfigure(2, weight=1)

    # top toolbar
    frame_t = Frame(parent, height=40, bg="#FFFFFF")
    frame_t.grid(row=0, column=0, sticky="NSEW", columnspan = 3, padx=2)

    # left scrollable text edit section
    frame_l = Frame(parent)
    frame_l.grid(row=1, column=1, sticky="NSEW")

    scroll_box = scrolledtext.ScrolledText(frame_l, wrap=WORD, undo=True, font = ("Calibri", 16))
    scroll_box.pack(fill=BOTH, expand=True, padx=8, pady=2)
    scroll_box.insert(INSERT, text)

    frame_r = Frame(parent, bg="#006dad")
    frame_r.grid(row=1, column=2, sticky="NSEW")

    scroll_box2 = scrolledtext.ScrolledText(frame_r, wrap=WORD, undo=True, font = ("Calibri", 16), background="#025d94", foreground="#FFFFFF")
    scroll_box2.pack(fill=BOTH, expand=True, padx=8, pady=2)
    scroll_box2.configure(state=DISABLED)
    to_english(text, scroll_box2)

    # side panel (on the left)
    panel = Frame(parent, width=60, bg="#1b7cb5")
    panel.grid(row=1, column=0, sticky="NSEW", padx=2)

    b_pinyin = Button(panel, text="Pinyin", relief="groove", height=3, font=("Calibri", 16), background="#1b7cb5", foreground="#FFFFFF", activebackground="#176fa3", activeforeground="#FFFFFF", command=lambda: to_pinyin(scroll_box.get("1.0", END), scroll_box2))
    b_pinyin.pack(fill=X)

    b_dict = Button(panel, text="Lookup", relief="groove", height=3, font=("Calibri", 16), background="#1b7cb5", foreground="#FFFFFF", activebackground="#176fa3", activeforeground="#FFFFFF", command=lambda: to_dictionary(scroll_box, scroll_box2))
    b_dict.pack(fill=X)

    b_translate = Button(panel, text="Translate", relief="groove", height=3, font=("Calibri", 16), background="#1b7cb5", foreground="#FFFFFF", activebackground="#176fa3", activeforeground="#FFFFFF", command=lambda: to_english(scroll_box.get("1.0", END), scroll_box2))
    b_translate.pack(fill=X)

    # add save function
    b_save = Button(frame_t, text="Save", relief="raised", width=10, font=("Calibri", 12), command=lambda: save_text(scroll_box.get("1.0", END)))
    b_save.pack(side=LEFT, fill=Y)
    b_open = Button(frame_t, text="Open", relief="raised", width=10, font=("Calibri", 12), command=lambda: open_text(scroll_box, parent, scroll_box2))
    b_open.pack(side=LEFT, fill=Y)
    b_lookup = Button(frame_t, text="Lookup", relief="raised", width=10, font=("Calibri", 12), command=lambda: to_dictionary(scroll_box, scroll_box2))
    b_lookup.pack(side=LEFT, fill=Y)
    b_font_increase = Button(frame_t, text="Aa⬆⬆", relief="raised", width=10, font=("Calibri", 12), command=lambda: font_change(True, [scroll_box, scroll_box2]))
    b_font_increase.pack(side=LEFT, fill=Y)
    b_font_decrease = Button(frame_t, text="Aa⬇⬇", relief="raised", width=10, font=("Calibri", 12), command=lambda: font_change(False, [scroll_box, scroll_box2]))
    b_font_decrease.pack(side=LEFT, fill=Y)

    parent.mainloop()

def confirm_scanned_image():
    global root
    global filepath
    global reader

    root.destroy()

    image = cv2.imread(filepath)

    if image.shape[2] == 3:
        # BGR image, convert to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        rgb_image = image

    result = reader.readtext(rgb_image, detail=0, paragraph=True)
    print(result)

    result_combined = ""
    for string in result:
        result_combined += string.replace(" ", "")
    
    result_combined = result_combined.split("。")
    
    final_str = ""
    for substring in result_combined:
        final_str += substring + "。\n"
    learning_window(final_str)

# prompt the user for an image file to scan Chinese characters from
def scan_image():
    global filepath
    filepath = filedialog.askopenfilename(initialdir = "/", title = "Upload a file", filetypes = [("Image files", ".png .jpg .tiff")])
    
    if filepath != "":
        i_viewer = Toplevel()
        i_viewer.title("Importing file: " + str(filepath))

        image = Image.open(filepath)
        image = ImageOps.exif_transpose(image)

        # resizing the image to a max of 600 by 600 pixels while keeping the aspect ratio
        width, height = image.size
        if width > height:
            size_factor = 600 / width
        else:
            size_factor = 600 / height
        width *= size_factor
        height *= size_factor
        image = image.resize((int(width), int(height)))
        
        image = ImageTk.PhotoImage(image)
        image_label = Label(i_viewer, image=image)
        image_label.pack()

        button = Button(i_viewer, text="Select this image", width=20, command=confirm_scanned_image)
        button.pack()

        label = Label(i_viewer, text="Note: scanning the image may take a few seconds... ")
        label.pack()

        i_viewer.geometry(str(int(width))+"x"+str(int(height)+38)+"+800+200")
        i_viewer.mainloop()

# Title screen
def root_window():
    global root
    root = Tk()

    root.title("Start / 开")
    root.geometry("600x500+100+200")

    spacer = Label(root, text="", height=8)
    spacer.pack()

    l_title = Label(root, text="\nChinese Language Learning Assistant / 汉语学习助手\nby James Lian")
    l_title.pack()

    spacer1 = Label(root, text="", height=1)
    spacer1.pack()

    b_scan = Button(root, text="Scan from image", width=30, height=3, command=scan_image)
    b_scan.pack()

    spacer2 = Label(root, text="", height=1)
    spacer2.pack()

    b_open = Button(root, text="Open text editor", width=30, height=3, command=lambda: learning_window("欢迎！"))
    b_open.pack()

    spacer3 = Label(root, text="", height=1)
    spacer3.pack()

    b_exit = Button(root, text="Exit", command=exit)
    b_exit.pack()

    root.mainloop()

root_window()