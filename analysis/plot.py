
import matplotlib.pyplot as plt
import pandas as pd
import os
import mplcursors

# 文件路径定义
swc_folder = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\2radius\excitatory_spiny_neuron_with_atypical_tree"
red_points_file = r"D:\GXQ\cross_em_lm\test_script\reassigned_labels3.csv"

# 加载数据
red_points_df = pd.read_csv(red_points_file)
red_points_df['Filename'] = red_points_df['Filename'].astype(str)

# 确保输出文件夹存在
output_folder = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\combined_plot"
os.makedirs(output_folder, exist_ok=True)

# 遍历 SWC 文件夹并去掉 '_sort.swc' 后缀
swc_files = [f for f in os.listdir(swc_folder) if f.endswith("_sort.swc")]
filenames = [f.replace('_sort.swc', '') for f in swc_files]
print(f"Found {len(filenames)} SWC files in the folder.")

# 初始化绘图
plt.figure(figsize=(12, 12))

# 获取唯一的 Layer 值并为其分配颜色
layers = red_points_df['Cell body layer'].unique()
layer_color_map = {layer: plt.cm.tab10(idx % 10) for idx, layer in enumerate(layers)}

# 创建空的列表，用于存储红点的悬停信息
annotations = []

for idx, neuron_id in enumerate(filenames):
    # 查找对应表格数据
    neuron_data = red_points_df[red_points_df['Filename'] == neuron_id]

    if neuron_data.empty:
        print(f"SWC 文件 {neuron_id} 没有在表格中找到对应的数据")
        continue

    # 获取红点坐标和对应的 Layer
    red_point_x = neuron_data['Soma_X'].values[0]
    red_point_y = neuron_data['Soma_Y'].values[0]
    neuron_layer = neuron_data['Cell body layer'].values[0]
    color = layer_color_map[neuron_layer]  # 根据 Layer 分配颜色

    # 读取 SWC 文件数据
    swc_path = os.path.join(swc_folder, f"{neuron_id}_sort.swc")
    df_swc = pd.read_csv(swc_path, index_col=None, header=None, skiprows=15, sep=' ')

    # 绘制 SWC 数据（用对应 Layer 的颜色）
    plt.plot(df_swc.iloc[:, 2].values, df_swc.iloc[:, 3].values, color=color, linewidth=0.5)

    # 绘制红点并保存悬停信息
    scatter = plt.scatter(red_point_x, red_point_y, color='red', s=25, marker='o')
    annotations.append((scatter, f"Neuron ID: {neuron_id}"))

# 设置图形属性
plt.title("Spiny Stellate Neuron")
plt.axis('equal')
plt.axis('off')

# 使用 mplcursors 绑定悬停事件，仅绑定 scatter 对象
cursor = mplcursors.cursor([scatter[0] for scatter in annotations], highlight=True)


# 为每个红点添加自定义注释
@cursor.connect("add")
def on_add(sel):
    for scatter, text in annotations:
        if sel.artist == scatter:
            sel.annotation.set_text(text)
            sel.annotation.set_fontsize(8)
            break


# 显示图形
plt.tight_layout()
plt.show()
