import os, shutil, threading, time, subprocess, platform, sys
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
import tkinter.filedialog as filedialog
import webbrowser

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class ImageOptimizerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lysychka's Image Compressor")

        icon_path = os.path.join(sys.path[0], "icon.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)

        self.geometry("700x450")
        self.resizable(False, False)

        self.min_file_size_kb = ctk.IntVar(value=500)
        self.jpeg_quality = ctk.IntVar(value=85)
        self.saved_space = 0
        self.total_files = 0
        self.processed_files = 0

        self.create_widgets()

    def create_widgets(self):
        pad = 30

        fr = ctk.CTkFrame(self)
        fr.pack(fill="x", padx=pad, pady=(pad, 5))

        ctk.CTkLabel(fr, text="Input folder:").grid(row=0, column=0, sticky="w", pady=5)
        self.input_entry = ctk.CTkEntry(fr, placeholder_text="Choose folder with images to process...")
        self.input_entry.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkButton(fr, text="Select", command=self.browse_input).grid(row=0, column=2, padx=5)

        ctk.CTkLabel(fr, text="Output folder:").grid(row=1, column=0, sticky="w", pady=5)
        self.output_entry = ctk.CTkEntry(fr, placeholder_text="Choose folder to save compressed files, contents will be deleted...")
        self.output_entry.grid(row=1, column=1, sticky="ew", padx=5)
        ctk.CTkButton(fr, text="Select", command=self.browse_output).grid(row=1, column=2, padx=5)

        fr.grid_columnconfigure(1, weight=1)

        st = ctk.CTkFrame(self)
        st.pack(fill="x", padx=pad, pady=5)

        self.lbl_min = ctk.CTkLabel(st, text=f"Min JPEG file size to compress: {self.min_file_size_kb.get()} KB")
        self.lbl_min.pack(anchor="w", padx=5, pady=(5, 0))
        slider1 = ctk.CTkSlider(st, from_=100, to=5000, number_of_steps=500,
                                variable=self.min_file_size_kb, command=self.on_min_size_change)
        slider1.pack(fill="x", padx=5, pady=5)

        self.lbl_qual = ctk.CTkLabel(st, text=f"JPEG quality: {self.jpeg_quality.get()}")
        self.lbl_qual.pack(anchor="w", padx=5, pady=(5, 0))
        slider2 = ctk.CTkSlider(st, from_=10, to=100, variable=self.jpeg_quality, command=self.on_qua_change)
        slider2.pack(fill="x", padx=5, pady=5)

        pr = ctk.CTkFrame(self)
        pr.pack(fill="both", expand=False, padx=pad, pady=5)

        self.progressbar = ctk.CTkProgressBar(pr)
        self.progressbar.pack(fill="x", pady=(20, 5), padx=20)
        self.progressbar.set(0)

        self.progress_label = ctk.CTkLabel(pr, text="Progress: 0/0 — 00:00")
        self.progress_label.pack()
        self.saved_label = ctk.CTkLabel(pr, text="Saved: 0.00 MB")
        self.saved_label.pack(pady=(5, 0))

        bf = ctk.CTkFrame(self)
        bf.pack(fill="x", padx=pad, pady=10)

        self.start_btn = ctk.CTkButton(bf, text="🔁 Start", fg_color="#0078D7", command=self.start_conversion)
        self.start_btn.pack(side="left", expand=True, padx=5, pady=5)

        self.open_btn = ctk.CTkButton(bf, text="📂 Open output folder", command=self.open_output_dir)
        self.open_btn.pack(side="left", expand=True, padx=5, pady=5)

        self.donation_label = ctk.CTkLabel(
            self,
            text="🙏 Support me on Patreon",
            text_color="orange",
            cursor="hand2",
            font=ctk.CTkFont(underline=True)
        )
        self.donation_label.pack(pady=0)
        self.donation_label.bind("<Button-1>", lambda e: self.open_link("https://patreon.com/YadernaLysychka"))

    def on_min_size_change(self, val):
        self.lbl_min.configure(text=f"Min JPEG file size to compress: {int(float(val))} KB")

    def on_qua_change(self, val):
        self.lbl_qual.configure(text=f"JPEG quality: {int(float(val))}")

    def browse_input(self):
        folder = filedialog.askdirectory()
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, folder)

    def browse_output(self):
        folder = filedialog.askdirectory()
        self.output_entry.delete(0, "end")
        self.output_entry.insert(0, folder)

    def open_output_dir(self):
        p = os.path.join(self.output_entry.get(), "output")
        if os.path.exists(p):
            if platform.system() == "Windows":
                os.startfile(p)
            elif platform.system() == "Darwin":
                subprocess.run(["open", p])
            else:
                subprocess.run(["xdg-open", p])
        else:
            messagebox.showerror("Error", "No folder!")

    def start_conversion(self):
        input_path = self.input_entry.get()
        output_path = self.output_entry.get()

        if not os.path.isdir(input_path):
            messagebox.showerror("Error", "Incorrect input folder.")
            return
        if not os.path.isdir(output_path):
            messagebox.showerror("Error", "Incorrect output folder.")
            return

        self.donation_label.configure(text="🙏 If you like the app, support me: patreon.com/YadernaLysychka")
        threading.Thread(target=self.convert_files, daemon=True).start()

    def convert_files(self):
        self.saved_space = 0
        self.processed_files = 0

        input_path = self.input_entry.get()
        output_path = os.path.join(self.output_entry.get(), "output")
        if os.path.exists(output_path):
            shutil.rmtree(output_path)
        os.makedirs(output_path, exist_ok=True)

        all_files = []
        for root, _, files in os.walk(input_path):
            for name in files:
                all_files.append(os.path.join(root, name))

        self.total_files = len(all_files)
        self.progressbar.set(0)
        start_time = time.time()

        for path in all_files:
            rel_path = os.path.relpath(path, input_path)
            dest_folder = os.path.join(output_path, os.path.dirname(rel_path))
            os.makedirs(dest_folder, exist_ok=True)

            dest_file = os.path.join(dest_folder, os.path.basename(path))
            ext = os.path.splitext(path)[1].lower()
            is_image = ext in [".png", ".jpg", ".jpeg"]

            try:
                if is_image and (os.path.getsize(path) // 1024) >= self.min_file_size_kb.get():
                    dest_file = os.path.splitext(dest_file)[0] + ".jpg"
                    img = Image.open(path).convert("RGB")
                    img.save(dest_file, "JPEG", quality=self.jpeg_quality.get())
                    self.saved_space += max(0, os.path.getsize(path) - os.path.getsize(dest_file))
                else:
                    shutil.copy2(path, dest_file)
            except Exception as e:
                print("Error handling:", path, e)

            self.processed_files += 1
            elapsed = time.time() - start_time
            rem = int((elapsed / self.processed_files) * (self.total_files - self.processed_files)) if self.processed_files else 0
            mm, ss = divmod(rem, 60)
            self.progressbar.set(self.processed_files / self.total_files)
            self.progress_label.configure(text=f"Progress: {self.processed_files}/{self.total_files} — {mm:02d}:{ss:02d}")
            self.saved_label.configure(text=f"Saved: {self.saved_space / 1024 / 1024:.2f} MB")
            self.update()

        self.donation_label.configure(text="✅ Done. Thank you for using the app! Support me on Patreon")

    def open_link(self, url):
        webbrowser.open_new(url)


if __name__ == "__main__":
    app = ImageOptimizerApp()
    app.mainloop()
