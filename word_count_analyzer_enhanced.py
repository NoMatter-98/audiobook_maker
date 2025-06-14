import os
import csv
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
from pathlib import Path
import sys
import re

class WordCountAnalyzer:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window initially
    
    def count_words_in_file(self, file_path):
        """
        Count words in a text file.
        
        Args:
            file_path (str): Path to the text file
            
        Returns:
            int: Number of words in the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                # Count Chinese characters and words
                # For Chinese text, we count characters as words
                # Remove whitespace and count non-space characters
                word_count = len([char for char in content if char.strip()])
                return word_count
        except Exception as e:
            print(f"Error reading {file_path}: {str(e)}")
            return 0
    
    def split_text_file(self, file_path, word_count):
        """
        Split a text file based on word count rules.
        
        Args:
            file_path (Path): Path to the text file
            word_count (int): Number of words in the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            lines = content.split('\n')
            
            # Calculate how many parts to split into
            if 4000 < word_count < 8000:
                parts = 2
                suffixes = ['《上》', '《下》']
            elif 8000 <= word_count < 12000:
                parts = 3
                suffixes = ['《上》', '《中》', '《下》']
            else:
                parts = (word_count - 1) // 4000 + 1
                suffixes = [f'<{i}>' for i in range(1, parts + 1)]
            
            # Find split positions based on word count
            current_word_count = 0
            split_positions = [0]
            
            for i, line in enumerate(lines):
                line_word_count = len([char for char in line if char.strip()])
                current_word_count += line_word_count
                
                # Check if we should split after this line
                expected_split_point = len(split_positions) * 4000
                if current_word_count >= expected_split_point and len(split_positions) < parts:
                    split_positions.append(i + 1)
            
            # Ensure we have the final position
            if len(split_positions) < parts + 1:
                split_positions.append(len(lines))
            
            # Create split files
            base_name = file_path.stem
            base_dir = file_path.parent
            
            created_files = []
            
            for i in range(parts):
                start_line = split_positions[i]
                end_line = split_positions[i + 1] if i + 1 < len(split_positions) else len(lines)
                
                split_content = '\n'.join(lines[start_line:end_line])
                new_filename = f"{base_name}{suffixes[i]}.txt"
                new_file_path = base_dir / new_filename
                
                with open(new_file_path, 'w', encoding='utf-8') as new_file:
                    new_file.write(split_content)
                
                created_files.append(new_file_path)
                print(f"Created: {new_filename}")
            
            # Delete original file
            file_path.unlink()
            print(f"Deleted original file: {file_path.name}")
            
            return created_files
            
        except Exception as e:
            print(f"Error splitting {file_path}: {str(e)}")
            return []
    
    def show_long_files_dialog(self, long_files, folder_path):
        """
        Show a dialog with all long files and options to split them.
        
        Args:
            long_files (list): List of tuples (filename, word_count, file_path)
            folder_path (Path): Path to the folder being analyzed
        """
        # Ensure root window exists and is properly configured
        self.root.deiconify()  # Show the root window
        self.root.geometry("1x1")  # Make it very small
        self.root.attributes('-topmost', True)  # Bring to front
        self.root.update()  # Process pending events
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Long Files Management")
        dialog.geometry("600x500")
        dialog.resizable(True, True)
        
        # Center the dialog on screen
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Make dialog modal and bring to front
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.attributes('-topmost', True)
        dialog.focus_force()
        
        # Header
        header_frame = tk.Frame(dialog)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(header_frame, text="⚠️ FILES OVER 4,000 WORDS DETECTED", 
                font=('Arial', 12, 'bold'), fg='red').pack()
        tk.Label(header_frame, text=f"Total files: {len(long_files)}", 
                font=('Arial', 10)).pack()
        tk.Label(header_frame, text="Select files to split automatically:", 
                font=('Arial', 10)).pack(pady=(10,0))
        
        # Create scrollable frame for file list
        canvas_frame = tk.Frame(dialog)
        canvas_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(canvas_frame)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # File checkboxes
        file_vars = {}
        for i, (filename, word_count, file_path) in enumerate(long_files):
            frame = tk.Frame(scrollable_frame)
            frame.pack(fill='x', padx=5, pady=2)
            
            var = tk.BooleanVar(value=True)  # Default selected
            file_vars[file_path] = var
            
            checkbox = tk.Checkbutton(frame, variable=var)
            checkbox.pack(side='left')
            
            # Determine split info
            if 4000 < word_count < 8000:
                split_info = "→ 2 parts (《上》, 《下》)"
            elif 8000 <= word_count < 12000:
                split_info = "→ 3 parts (《上》, 《中》, 《下》)"
            else:
                parts = (word_count - 1) // 4000 + 1
                split_info = f"→ {parts} parts (《1》, 《2》, ...)"
            
            label_text = f"{filename}: {word_count:,} words {split_info}"
            tk.Label(frame, text=label_text, anchor='w', justify='left').pack(side='left', fill='x', expand=True)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Control buttons frame
        button_frame = tk.Frame(dialog)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        # Select/Deselect all buttons
        control_frame = tk.Frame(button_frame)
        control_frame.pack(fill='x', pady=(0, 10))
        
        def select_all():
            for var in file_vars.values():
                var.set(True)
        
        def deselect_all():
            for var in file_vars.values():
                var.set(False)
        
        tk.Button(control_frame, text="Select All", command=select_all).pack(side='left', padx=5)
        tk.Button(control_frame, text="Deselect All", command=deselect_all).pack(side='left', padx=5)
        
        # Main action buttons
        action_frame = tk.Frame(button_frame)
        action_frame.pack(fill='x')
        
        def split_selected_files():
            selected_files = [(path, next(item for item in long_files if item[2] == path)) 
                            for path, var in file_vars.items() if var.get()]
            
            if not selected_files:
                messagebox.showinfo("No Selection", "No files selected for splitting.")
                return
            
            # Confirm action
            result = messagebox.askyesno(
                "Confirm Split", 
                f"Are you sure you want to split {len(selected_files)} files?\n\n"
                "⚠️ Original files will be deleted after splitting!"
            )
            
            if result:
                success_count = 0
                error_count = 0
                
                for file_path, (filename, word_count, _) in selected_files:
                    try:
                        created_files = self.split_text_file(Path(file_path), word_count)
                        if created_files:
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        print(f"Error splitting {filename}: {str(e)}")
                        error_count += 1
                
                # Show results
                if error_count == 0:
                    messagebox.showinfo(
                        "Split Complete", 
                        f"✅ Successfully split {success_count} files!\n\n"
                        "You can now re-analyze the folder to verify all files are within limits."
                    )
                else:
                    messagebox.showwarning(
                        "Split Completed with Errors", 
                        f"✅ Successfully split: {success_count} files\n"
                        f"❌ Failed to split: {error_count} files\n\n"
                        "Check console for error details."
                    )
                
                dialog.destroy()
                self.root.quit()  # Exit the mainloop
        
        def cancel_dialog():
            dialog.destroy()
            self.root.quit()  # Exit the mainloop
        
        tk.Button(action_frame, text="Split Selected Files", command=split_selected_files, 
                 bg='orange', fg='white', font=('Arial', 10, 'bold')).pack(side='right', padx=5)
        tk.Button(action_frame, text="Cancel", command=cancel_dialog).pack(side='right', padx=5)
        
        # Bind mouse wheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind("<MouseWheel>", on_mousewheel)
    
    def analyze_folder(self, folder_path):
        """
        Analyze all .txt files in a folder and generate word count report.
        
        Args:
            folder_path (str): Path to folder containing text files
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            messagebox.showerror("Error", f"Folder {folder_path} does not exist!")
            return
        
        # Find all .txt files
        txt_files = list(folder_path.glob("*.txt"))
        if not txt_files:
            messagebox.showwarning("Warning", "No .txt files found in the folder!")
            return
        
        print(f"Found {len(txt_files)} text files to analyze...")
        
        # Analyze each file
        file_data = []
        long_files = []
        
        for txt_file in txt_files:
            word_count = self.count_words_in_file(txt_file)
            file_data.append({
                'filename': txt_file.name,
                'word_count': word_count,
                'path': str(txt_file)
            })
            
            # Check if file is too long (>4000 words)
            if word_count > 4000:
                long_files.append((txt_file.name, word_count, str(txt_file)))
            
            print(f"Processed: {txt_file.name} - {word_count} words")
        
        # Sort by word count (descending)
        file_data.sort(key=lambda x: x['word_count'], reverse=True)
        
        # Generate CSV report
        folder_name = folder_path.name
        csv_filename = f"{folder_name}_words_count.csv"
        csv_path = folder_path / csv_filename
        
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            fieldnames = ['filename', 'word_count', 'status']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for data in file_data:
                status = "⚠️ Too Long" if data['word_count'] > 4000 else "✅ Safe"
                writer.writerow({
                    'filename': data['filename'],
                    'word_count': data['word_count'],
                    'status': status
                })
        
        print(f"✓ CSV report saved: {csv_path}")
        
        # Show results
        if not long_files:
            # Safe message
            message = (f"✅ ANALYSIS COMPLETE - ALL FILES SAFE ✅\n\n"
                      f"Folder: {folder_name}\n"
                      f"Total files analyzed: {len(txt_files)}\n"
                      f"Files over 4,000 words: 0\n\n"
                      f"All files are within the safe limit for Gemini 2.0 Flash processing.\n"
                      f"You can proceed with the conversion safely.\n\n"
                      f"📊 Detailed report saved to:\n{csv_path}")
            
            messagebox.showinfo("Word Count Analysis - Safe", message)
            # No need for mainloop here as messagebox handles it
        else:
            # Show long files management dialog
            print(f"Opening dialog for {len(long_files)} long files...")
            self.show_long_files_dialog(long_files, folder_path)
            # Keep the program running until dialog is closed
            self.root.mainloop()
    
    def run_gui(self):
        """Run the GUI version of the analyzer."""
        
        # Show folder selection dialog
        folder_path = filedialog.askdirectory(
            title="Select folder containing text files to analyze"
        )
        
        if folder_path:
            self.analyze_folder(folder_path)
        else:
            print("No folder selected.")
    
    def run_console(self):
        """Run the console version of the analyzer."""
        
        if len(sys.argv) > 1:
            folder_path = sys.argv[1]
        else:
            folder_path = input("Enter the path to the folder containing text files: ").strip().strip('"')
        
        if folder_path:
            self.analyze_folder(folder_path)
        else:
            print("No folder path provided.")

def main():
    """Main function to choose between GUI and console mode."""
    
    analyzer = WordCountAnalyzer()
    
    if len(sys.argv) > 1 or not sys.stdout.isatty():
        # Console mode if arguments provided or not in interactive terminal
        analyzer.run_console()
    else:
        # GUI mode for interactive use
        print("Opening folder selection dialog...")
        analyzer.run_gui()

if __name__ == "__main__":
    main()