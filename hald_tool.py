import numpy as np
from PIL import Image
import sys
import os

def generate_neutral():
    size = 64
    img = np.zeros((size*8, size*8, 3), dtype=np.uint8)
    for b in range(size):
        by = b // 8
        bx = b % 8
        for g in range(size):
            for r in range(size):
                x = bx * size + r
                y = by * size + g
                img[y, x, 0] = int(r * 255.0 / 63.0)
                img[y, x, 1] = int(g * 255.0 / 63.0)
                img[y, x, 2] = int(b * 255.0 / 63.0)
    
    Image.fromarray(img).save("neutral_lut_64.png")
    print("==================================================")
    print("✅ 成功生成【标准中性彩色图】：neutral_lut_64.png")
    print("==================================================")
    print("【接下来需要做的】：")
    print("1. 用 Photoshop 打开这件 neutral_lut_64.png 文件。")
    print("2. 选中图层，选择菜单栏：滤镜 -> Camera Raw 滤镜。")
    print("3. 应用你的预设（比如【滨田英明调色】），点击确定。")
    print("4. 把调完色的图片，导出/另存为一个新文件，命名为：modified_lut_64.png，保存在本目录。")
    print("5. 存好后，再次运行这个脚本，我就会自动帮你抽出完美的 .cube 啦！\n")

def convert_to_cube(image_path, output_path):
    img = np.array(Image.open(image_path).convert('RGB'))
    size = 64
    
    with open(output_path, 'w') as f:
        f.write("# Extract by ComfyUI-LUT Tools\n")
        f.write(f"LUT_3D_SIZE {size}\n")
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        
        # CUBE format asks for R fastest, then G, then B
        for b in range(size):
            by = b // 8
            bx = b % 8
            for g in range(size):
                for r in range(size):
                    x = bx * size + r
                    y = by * size + g
                    rv, gv, bv = img[y, x]
                    f.write(f"{rv/255.0:.6f} {gv/255.0:.6f} {bv/255.0:.6f}\n")
                    
    print("==================================================")
    print(f"🎉 成功将 {image_path} 转换为 CUBE 文件：{output_path} !")
    print("==================================================")
    print("现在你可以把这个 .cube 文件放进 ComfyUI-lut 里跑跑看啦！")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        if os.path.exists("modified_lut_64.png"):
            convert_to_cube("modified_lut_64.png", "my_extracted_color.cube")
        else:
            generate_neutral()
    elif len(sys.argv) == 3:
        convert_to_cube(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python hald_tool.py")
