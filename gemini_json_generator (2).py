#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini 2.0 Flash Lite JSON Generator for Audiobook Format
Converts text files to JSON format for audiobook production
With GUI interface and batch processing support
"""

import os
import json
import argparse
from google import genai
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading

# Configuration - Add your API key here
GEMINI_API_KEY = ""  # Replace with your actual API key

class GeminiJSONGenerator:
    def __init__(self, api_key):
        """Initialize the Gemini client with API key"""
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash-lite"
        
    def read_text_file(self, file_path):
        """Read content from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            print(f"错误：找不到文件 {file_path}")
            return None
        except Exception as e:
            print(f"读取文件时出错：{e}")
            return None
    
    def create_prompt(self, custom_prompt, text_content):
        """Create the full prompt for Gemini API"""
        full_prompt = f"""
{custom_prompt}

以下是需要处理的小说文本：
{text_content}

请严格按照上述要求处理，输出完整的JSON格式。
"""
        return full_prompt
    
    def generate_json_for_file(self, prompt, text_file_path, output_file=None, progress_callback=None):
        """Generate JSON for a single file"""
        # Read the text file
        text_content = self.read_text_file(text_file_path)
        if text_content is None:
            return None
        
        # Set default output path if not provided
        if output_file is None:
            output_file = os.path.splitext(text_file_path)[0] + '.json'
        
        # Create full prompt
        full_prompt = self.create_prompt(prompt, text_content)
        
        try:
            if progress_callback:
                progress_callback(f"正在处理: {os.path.basename(text_file_path)}")
            
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            
            # Extract the response text
            response_text = response.text
            
            # Try to extract JSON from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end]
            else:
                json_text = response_text
            
            # Validate JSON
            try:
                parsed_json = json.loads(json_text)
            except json.JSONDecodeError as e:
                if progress_callback:
                    progress_callback(f"JSON 格式验证失败: {os.path.basename(text_file_path)}")
                return None
            
            # Save to file
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(parsed_json, f, ensure_ascii=False, indent=2)
            
            if progress_callback:
                progress_callback(f"完成: {os.path.basename(text_file_path)} -> {os.path.basename(output_file)}")
            
            return parsed_json
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"处理失败: {os.path.basename(text_file_path)} - {str(e)}")
            return None
    
    def batch_process_folder(self, folder_path, prompt, progress_callback=None):
        """Batch process all txt files in a folder"""
        # Create output folder
        output_folder = folder_path + "_json"
        os.makedirs(output_folder, exist_ok=True)
        
        # Find all txt files
        txt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.txt')]
        
        if not txt_files:
            if progress_callback:
                progress_callback("错误：文件夹中没有找到 .txt 文件")
            return []
        
        results = []
        total_files = len(txt_files)
        
        for i, txt_file in enumerate(txt_files, 1):
            input_path = os.path.join(folder_path, txt_file)
            output_file = os.path.splitext(txt_file)[0] + '.json'
            output_path = os.path.join(output_folder, output_file)
            
            if progress_callback:
                progress_callback(f"进度 {i}/{total_files}: {txt_file}")
            
            result = self.generate_json_for_file(prompt, input_path, output_path, progress_callback)
            results.append((txt_file, result is not None))
            
            # Rate limiting - wait between requests
            if i < total_files:
                time.sleep(2)  # 2 second delay between requests
        
        return results

class GeminiGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Gemini 2.0 Flash Lite JSON 生成器")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # Variables
        self.api_key_var = tk.StringVar(value=GEMINI_API_KEY)
        self.input_path_var = tk.StringVar()
        self.processing_mode = tk.StringVar(value="single")  # single or batch
        self.generator = None
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # API Key section
        api_frame = ttk.LabelFrame(main_frame, text="API 配置", padding="10")
        api_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        api_frame.columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="API Key:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=50)
        api_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        ttk.Button(api_frame, text="测试", command=self.test_api_key).grid(row=0, column=2)
        
        # Processing mode section
        mode_frame = ttk.LabelFrame(main_frame, text="处理模式", padding="10")
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="单个文件", variable=self.processing_mode, 
                       value="single", command=self.on_mode_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="批量处理文件夹", variable=self.processing_mode, 
                       value="batch", command=self.on_mode_change).grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Input selection section
        input_frame = ttk.LabelFrame(main_frame, text="输入选择", padding="10")
        input_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_frame.columnconfigure(1, weight=1)
        
        self.input_label = ttk.Label(input_frame, text="文件路径:")
        self.input_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        ttk.Entry(input_frame, textvariable=self.input_path_var, width=60).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.browse_button = ttk.Button(input_frame, text="浏览文件", command=self.browse_file)
        self.browse_button.grid(row=0, column=2)
        
        # Prompt section
        prompt_frame = ttk.LabelFrame(main_frame, text="提示词设置", padding="10")
        prompt_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        prompt_frame.columnconfigure(0, weight=1)
        prompt_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        ttk.Label(prompt_frame, text="提示词内容:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.prompt_text = scrolledtext.ScrolledText(prompt_frame, height=8, wrap=tk.WORD)
        self.prompt_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Set default prompt
        default_prompt = """请将我提供的 （小说文本） （1）所有的英文和数字都必须改写成谐音的中文（但是中文不要再改成谐音中文了），比如第2章改成“第二章”（但是第10章改成“十”而不是“一零”），java改成“加瓦”，unicode改成“油泥扣”，“C++”改成西加加，json改成接省。但是不要把"1933年"擅自添加成"1933年轻"。 （2）最重要的，是把原本我输入的txt文件，转换为有声书JSON格式输出，需要严格按照以下要求进行转换： 1. 输出格式必须是有效的JSON数组，每个对话或旁白为一个对象 2. 每个对象必须包含以下字段： - speaker: 说话者姓名（如"旁白"、角色名等） - content: 对话或旁白内容 - tone: 语气描述（如"neutral"表示中性，或其他情感描述） - intensity: 语气强度，范围1-10的整数值 - delay: 语音之间的停顿时间（毫秒） 3. 旁白部分： - speaker设置为"旁白" - tone通常设置为"neutral" - intensity通常设置为5（中等强度） - delay根据内容长度和情境设置，通常在300-800毫秒之间 4. 角色对话部分： - speaker设置为角色名称 - tone需要根据对话内容和情境描述具体情感（如"愤怒"、"惊讶"、"低声念叨"等） - intensity根据情感强度设置，范围1-10 - delay根据对话节奏设置，通常在400-1500毫秒之间 5. 长段落处理规则： - 超过100个字的段落应拆分为多个对象 - 拆分时保持同一个speaker - 拆分时保持相同的tone和intensity - 拆分点应选择在自然停顿处（如句号、逗号后） - 每个拆分后的片段不应超过80-100个字 6. 特殊要求： - 所有引号必须正确转义 - 不要添加额外的字段 - 保持原文的语意完整性 - 内容中除了，。！？和... 不要有其它的标点符号，但是一行字里不要用空格空开，要用标点符号表示间隔和结束。 - 对于情感强烈的对话，适当提高intensity值 - 对于重要或情感转折的对话，适当增加delay值 请确保输出的JSON格式完全符合上述规范，可以直接用于有声书制作系统。"""
        
        self.prompt_text.insert(tk.END, default_prompt)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="10")
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=6, wrap=tk.WORD, state='disabled')
        self.progress_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        
        self.start_button = ttk.Button(button_frame, text="开始处理", command=self.start_processing)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        ttk.Button(button_frame, text="清除日志", command=self.clear_log).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="退出", command=self.root.quit).grid(row=0, column=2)
    
    def on_mode_change(self):
        """Handle processing mode change"""
        if self.processing_mode.get() == "single":
            self.input_label.config(text="文件路径:")
            self.browse_button.config(text="浏览文件", command=self.browse_file)
        else:
            self.input_label.config(text="文件夹路径:")
            self.browse_button.config(text="浏览文件夹", command=self.browse_folder)
        
        # Clear current path
        self.input_path_var.set("")
    
    def browse_file(self):
        """Browse for a single text file"""
        filename = filedialog.askopenfilename(
            title="选择文本文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.input_path_var.set(filename)
    
    def browse_folder(self):
        """Browse for a folder"""
        folder = filedialog.askdirectory(title="选择包含文本文件的文件夹")
        if folder:
            self.input_path_var.set(folder)
    
    def test_api_key(self):
        """Test the API key"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先输入 API Key")
            return
        
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents="Test"
            )
            messagebox.showinfo("成功", "API Key 测试成功！")
        except Exception as e:
            messagebox.showerror("错误", f"API Key 测试失败：{str(e)}")
    
    def log_message(self, message):
        """Add message to progress log"""
        self.progress_text.config(state='normal')
        self.progress_text.insert(tk.END, message + "\n")
        self.progress_text.see(tk.END)
        self.progress_text.config(state='disabled')
        self.root.update()
    
    def clear_log(self):
        """Clear the progress log"""
        self.progress_text.config(state='normal')
        self.progress_text.delete(1.0, tk.END)
        self.progress_text.config(state='disabled')
    
    def start_processing(self):
        """Start the processing in a separate thread"""
        # Validate inputs
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请输入 API Key")
            return
        
        input_path = self.input_path_var.get().strip()
        if not input_path:
            messagebox.showerror("错误", "请选择输入文件或文件夹")
            return
        
        if not os.path.exists(input_path):
            messagebox.showerror("错误", "输入路径不存在")
            return
        
        prompt = self.prompt_text.get(1.0, tk.END).strip()
        if not prompt:
            messagebox.showerror("错误", "请输入提示词")
            return
        
        # Disable start button
        self.start_button.config(state='disabled')
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_files, args=(api_key, input_path, prompt))
        thread.daemon = True
        thread.start()
    
    def process_files(self, api_key, input_path, prompt):
        """Process files (runs in separate thread)"""
        try:
            self.generator = GeminiJSONGenerator(api_key)
            
            if self.processing_mode.get() == "single":
                # Single file processing
                self.log_message(f"开始处理单个文件: {os.path.basename(input_path)}")
                result = self.generator.generate_json_for_file(prompt, input_path, progress_callback=self.log_message)
                if result:
                    output_path = os.path.splitext(input_path)[0] + '.json'
                    self.log_message(f"处理完成！输出文件: {output_path}")
                else:
                    self.log_message("处理失败！")
            else:
                # Batch processing
                self.log_message(f"开始批量处理文件夹: {input_path}")
                results = self.generator.batch_process_folder(input_path, prompt, progress_callback=self.log_message)
                
                success_count = sum(1 for _, success in results if success)
                total_count = len(results)
                
                self.log_message(f"\n批量处理完成！")
                self.log_message(f"总文件数: {total_count}")
                self.log_message(f"成功处理: {success_count}")
                self.log_message(f"失败数量: {total_count - success_count}")
                self.log_message(f"输出文件夹: {input_path}_json")
        
        except Exception as e:
            self.log_message(f"处理过程中出现错误: {str(e)}")
        
        finally:
            # Re-enable start button
            self.root.after(0, lambda: self.start_button.config(state='normal'))
    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

def main():
    # Default prompt
    default_prompt = """请将我提供的 （小说文本） （1）所有的英文和数字都必须改写成谐音的中文，比如1改成一（但是10要改成十而不是一零），java改成加瓦，unicode改成油泥扣，C++改成西加加，json改成接省。但是不要把"1933年"擅自添加成"1933年轻"。 （2）最重要的，是把原本我输入的txt文件，转换为有声书JSON格式输出，需要严格按照以下要求进行转换： 1. 输出格式必须是有效的JSON数组，每个对话或旁白为一个对象 2. 每个对象必须包含以下字段： - speaker: 说话者姓名（如"旁白"、角色名等） - content: 对话或旁白内容 - tone: 语气描述（如"neutral"表示中性，或其他情感描述） - intensity: 语气强度，范围1-10的整数值 - delay: 语音之间的停顿时间（毫秒） 3. 旁白部分： - speaker设置为"旁白" - tone通常设置为"neutral" - intensity通常设置为5（中等强度） - delay根据内容长度和情境设置，通常在300-800毫秒之间 4. 角色对话部分： - speaker设置为角色名称 - tone需要根据对话内容和情境描述具体情感（如"愤怒"、"惊讶"、"低声念叨"等） - intensity根据情感强度设置，范围1-10 - delay根据对话节奏设置，通常在400-1500毫秒之间 5. 长段落处理规则： - 超过100个字的段落应拆分为多个对象 - 拆分时保持同一个speaker - 拆分时保持相同的tone和intensity - 拆分点应选择在自然停顿处（如句号、逗号后） - 每个拆分后的片段不应超过80-100个字 6. 特殊要求： - 所有引号必须正确转义 - 不要添加额外的字段 - 保持原文的语意完整性 - 内容中除了，。！？和... 不要有其它的标点符号，但是一行字里不要用空格空开，要用标点符号表示间隔和结束。 - 对于情感强烈的对话，适当提高intensity值 - 对于重要或情感转折的对话，适当增加delay值 请确保输出的JSON格式完全符合上述规范，可以直接用于有声书制作系统。模板示例如下： [ { "speaker": "旁白", "content": "章节标题", "tone": "neutral", "intensity": 3, "delay": 500 }, { "speaker": "旁白", "content": "场景描述文本", "tone": "neutral", "intensity": 5, "delay": 500 }, { "speaker": "角色名", "content": "角色对话内容", "tone": "具体情感描述", "intensity": 7, "delay": 800 } ]"""
    
    # Set up argument parser for command line usage
    parser = argparse.ArgumentParser(description='Generate JSON using Gemini 2.0 Flash Lite')
    parser.add_argument('--api-key', help='Gemini API key (overrides stored key)')
    parser.add_argument('--text-file', help='Path to input text file')
    parser.add_argument('--folder', help='Path to folder containing text files')
    parser.add_argument('--output', help='Output JSON file path (for single file) or folder path (for batch)')
    parser.add_argument('--prompt', help='Custom prompt (optional)', default=default_prompt)
    parser.add_argument('--gui', action='store_true', help='Launch GUI interface')
    
    args = parser.parse_args()
    
    # Launch GUI if requested or no command line arguments
    if args.gui or (not args.text_file and not args.folder):
        gui = GeminiGUI()
        gui.run()
        return
    
    # Command line processing
    api_key = args.api_key or GEMINI_API_KEY
    if not api_key:
        print("错误：未找到 API Key。请在脚本中设置 GEMINI_API_KEY 或使用 --api-key 参数")
        exit(1)
    
    generator = GeminiJSONGenerator(api_key)
    
    if args.text_file:
        # Single file processing
        output_file = args.output or (os.path.splitext(args.text_file)[0] + '.json')
        result = generator.generate_json_for_file(args.prompt, args.text_file, output_file)
        if result:
            print(f"处理完成：{output_file}")
        else:
            print("处理失败")
    
    elif args.folder:
        # Batch processing
        results = generator.batch_process_folder(args.folder, args.prompt)
        success_count = sum(1 for _, success in results if success)
        print(f"批量处理完成：{success_count}/{len(results)} 个文件成功处理")

if __name__ == "__main__":
    main()
