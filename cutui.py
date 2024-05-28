
# 目录下要有 ffmpeg.exe
import random
import subprocess
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image

from tkinter import filedialog, messagebox
import os


def convert_to_png(image_path, output_path):
    with Image.open(image_path) as img:
        img = img.convert('RGBA')  # 确保图像转换为RGBA模式以兼容PNG格式
        img.save(output_path, 'PNG')

def process_directory(directory):
    temp_directory = os.path.join(directory, 'temp')
    os.makedirs(temp_directory, exist_ok=True)

    # 获取目录中的所有图片文件，排除01.png
    images = [f for f in os.listdir(directory) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')) and f != '01.png']
    
    # 打乱图片列表的顺序
    random.shuffle(images)
    
    converted_images = []

    # 将所有非PNG格式的图片转换为PNG，并移动到临时目录
    for filename in images:
        base, ext = os.path.splitext(filename)
        old_path = os.path.join(directory, filename)
        new_path = os.path.join(temp_directory, base + '.png')

        if ext.lower() != '.png':
            convert_to_png(old_path, new_path)
            os.remove(old_path)
        else:
            os.rename(old_path, new_path)

        converted_images.append(new_path)
    
    # 重命名临时目录中的图片文件，从02.png开始
    for index, temp_image_path in enumerate(converted_images):
        new_name = f"{index + 2:02}.png"  # 注意这里是从02.png开始
        new_path = os.path.join(directory, new_name)
        os.rename(temp_image_path, new_path)
        print(f"Processed {os.path.basename(temp_image_path)} to {new_name}")

    # 删除临时目录
    os.rmdir(temp_directory)

def rename_directories(root):
    # 获取子目录列表
    subdirs = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))]
    
    # 打乱子目录列表顺序
    random.shuffle(subdirs)
    
    # 临时重命名子目录以避免命名冲突
    temp_names = []
    for index, subdir in enumerate(subdirs):
        temp_name = f"temp_{index:02}"
        os.rename(os.path.join(root, subdir), os.path.join(root, temp_name))
        temp_names.append(temp_name)
    
    # 最终重命名子目录
    for index, temp_name in enumerate(temp_names):
        new_name = f"{index + 1:03}"
        os.rename(os.path.join(root, temp_name), os.path.join(root, new_name))
        print(f"Renamed {temp_name} to {new_name}")

def rename_images_in_directory(directory):
    for root, dirs, files in os.walk(directory):
        process_directory(root)
        if dirs:  # 仅在有子目录时才进行重命名
            rename_directories(root)

def select_directory():
    dir_path = filedialog.askdirectory()
    if dir_path:
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, dir_path)

def start_processing():
    dir_path = entry_dir.get()
    if not dir_path or not os.path.isdir(dir_path):
        messagebox.showerror("错误", "请选择有效的目录")
        return

    try:
        rename_images_in_directory(dir_path)
        messagebox.showinfo("完成", "处理完成")
    except Exception as e:
        messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")

# ====================================
def timeit(func):
    """
    装饰器，用于计算函数运行时间。
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"函数 {func.__name__} 的运行时间为 {duration} 秒。")
        return result
    return wrapper



@timeit
def cut_video_from_srt(input_video, srt_file_path, output_directory):
    """
    根据SRT文件的时间戳切割视频。

    参数:
    - input_video: 输入视频文件的路径。
    - srt_file_path: SRT字幕文件的路径。
    - output_directory: 输出视频文件的目录。
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    with open(srt_file_path, "r", encoding="utf-8") as file:
        srt_lines = file.readlines()

    for i in range(0, len(srt_lines), 4):  # SRT格式每4行为一组
        if "-->" in srt_lines[i+1]:
            start_time, end_time = srt_lines[i+1].split(" --> ")
            start_time = start_time.replace(",", ".")
            end_time = end_time.strip().replace(",", ".")  # Remove potential trailing newline characters
            
            output_video = os.path.join(output_directory, f"{i//4 + 1}.mp4")

            # Calculate duration
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            duration = end_seconds - start_seconds

            command = [
                'ffmpeg',
                '-ss', start_time,
                '-i', input_video,
                '-t', str(duration),
                '-c:v', 'libx264',  # 重新编码视频
                '-c:a', 'aac',      # 重新编码音频
                '-y',
                output_video
            ]
            print("Running command:", " ".join(command))
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                print(f"视频片段 {i//4 + 1} 已成功切割并保存到 {output_video}")
            else:
                print(f"切割视频片段 {i//4 + 1} 时出错: {stderr.decode('utf-8')}")

def time_to_seconds(time_str):
    """
    将时间字符串（格式为 HH:MM:SS,MMM）转换为秒。
    """
    h, m, s = time_str.split(':')
    s, ms = s.split('.')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def select_video_file():
    file_path = filedialog.askopenfilename(
        title="选择视频文件",
        filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
    )
    if file_path:
        video_entry.delete(0, tk.END)
        video_entry.insert(0, file_path)
        # 自动生成默认的 srt 文件路径
        srt_path = os.path.splitext(file_path)[0] + '.srt'
        srt_entry.delete(0, tk.END)
        srt_entry.insert(0, srt_path)

def select_srt_file():
    file_path = filedialog.askopenfilename(
        title="选择字幕文件",
        filetypes=[("SRT files", "*.srt"), ("All files", "*.*")]
    )
    if file_path:
        srt_entry.delete(0, tk.END)
        srt_entry.insert(0, file_path)
def select_output_directory():
    directory_path = filedialog.askdirectory(title="选择输出目录")
    if directory_path:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, directory_path)

def start_cutting():
    input_video = video_entry.get()
    srt_file_path = srt_entry.get()
    output_directory = output_entry.get()

    if not os.path.exists(input_video):
        messagebox.showerror("错误", "视频文件不存在")
        return

    if not os.path.exists(srt_file_path):
        messagebox.showerror("错误", "字幕文件不存在")
        return

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    cut_video_from_srt(input_video, srt_file_path, output_directory)
    messagebox.showinfo("完成", "视频剪辑完成")

# 创建主窗口
root = tk.Tk()
root.title("小红专用图片视频批量王 class111.com")

# 统一样式
style = ttk.Style()
style.configure("TFrame", padding=10)
style.configure("TLabel", padding=5)
style.configure("TButton", padding=5)

# 图片处理功能
image_frame = ttk.LabelFrame(root, text="图片处理", padding=10)
image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

ttk.Label(image_frame, text="选择目录:").grid(row=0, column=0, padx=5, pady=5)
entry_dir = ttk.Entry(image_frame, width=50)
entry_dir.grid(row=0, column=1, padx=5, pady=5)
ttk.Button(image_frame, text="浏览", command=select_directory).grid(row=0, column=2, padx=5, pady=5)
ttk.Button(image_frame, text="开始处理", command=start_processing).grid(row=1, column=0, columnspan=3, pady=10)

# 视频剪辑功能
video_frame = ttk.LabelFrame(root, text="视频剪辑", padding=10)
video_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

ttk.Label(video_frame, text="选择视频文件:").grid(row=0, column=0, padx=5, pady=5)
video_entry = ttk.Entry(video_frame, width=50)
video_entry.grid(row=0, column=1, padx=5, pady=5)
ttk.Button(video_frame, text="浏览", command=select_video_file).grid(row=0, column=2, padx=5, pady=5)

ttk.Label(video_frame, text="字幕文件路径:").grid(row=1, column=0, padx=5, pady=5)
srt_entry = ttk.Entry(video_frame, width=50)
srt_entry.grid(row=1, column=1, padx=5, pady=5)
ttk.Button(video_frame, text="浏览", command=select_srt_file).grid(row=1, column=2, padx=5, pady=5)

ttk.Label(video_frame, text="输出目录:").grid(row=2, column=0, padx=5, pady=5)
output_entry = ttk.Entry(video_frame, width=50)
output_entry.insert(0, "outputs")  # 默认输出目录
output_entry.grid(row=2, column=1, padx=5, pady=5)
ttk.Button(video_frame, text="浏览", command=select_output_directory).grid(row=2, column=2, padx=5, pady=5)

ttk.Button(video_frame, text="开始剪辑", command=start_cutting).grid(row=3, column=1, pady=20)

# 运行主循环
root.mainloop()
