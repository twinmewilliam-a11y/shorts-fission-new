"""
生成 3 种字幕方案样图
"""
import subprocess
import os

# 创建 3 种 ASS 字幕文件
styles = {
    "A_classic": {
        "name": "经典 - 黑底白字+黄色描边",
        "style": "Style: Default, Arial, 48, &H00FFFFFF, &H000000FF, &H0000FFFF, &H00000000, 1, 0, 0, 0, 100, 100, 0, 0, 1, 3, 0, 2, 10, 10, 10, 1"
    },
    "B_modern": {
        "name": "现代 - 渐变背景+白字",
        "style": "Style: Default, Arial, 48, &H00FFFFFF, &H000000FF, &H00000000, &H009933FF, 1, 0, 0, 0, 100, 100, 0, 0, 3, 2, 1, 2, 10, 10, 10, 1"
    },
    "C_minimal": {
        "name": "简约 - 透明底+白字黑边",
        "style": "Style: Default, Arial, 48, &H00FFFFFF, &H000000FF, &H00000000, &H00000000, 0, 0, 0, 0, 100, 100, 0, 0, 1, 4, 0, 2, 10, 10, 10, 1"
    }
}

sample_text = "THIS IS UNBELIEVABLE! 🏆"

output_dir = "/root/.openclaw/workspace/projects/shorts-fission/data/subtitle_samples"

for key, info in styles.items():
    ass_path = os.path.join(output_dir, f"subtitle_{key}.ass")
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write("[Script Info]\n")
        f.write("ScriptType: v4.00+\n")
        f.write("PlayResX: 1080\n")
        f.write("PlayResY: 1920\n")
        f.write("\n")
        f.write("[V4+ Styles]\n")
        f.write("Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
        f.write(info['style'] + "\n")
        f.write("\n")
        f.write("[Events]\n")
        f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        f.write(f"Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{sample_text}\n")
    
    print(f"✅ {info['name']} → {ass_path}")

print("\n字幕文件生成完成！")
