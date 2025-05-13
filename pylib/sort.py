import subprocess
import sys
import os
import pandas as pd
v3d_path=r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.2_Windows_64bit\Vaa3D-x.exe"
def sort_swc(swc_in, swc_out=None):
    if sys.platform.startswith('linux'):
        cmd_args = [v3d_path, '-x', 'sort_neuron_swc', '-f', 'sort_swc', '-i', swc_in, '-o', swc_out]
    else:
        cmd_args = [v3d_path, "/x", "sort_neuron_swc", "/f", "sort_swc", "/i", swc_in, "/o", swc_out]
    subprocess.run(cmd_args)

# 定义主目录路径和Vaa3D路径
# base_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted"
# # 遍历主目录下的每个子文件夹
# for cell_type in os.listdir(base_dir):
#     cell_type_dir = os.path.join(base_dir, cell_type)
#     if not cell_type =='spiny_stellate_neuron':
#         outpath = os.path.join(cell_type_dir, f"{cell_type}_fea.csv")
#     # 检查输出文件是否存在，决定是否跳过或覆盖
#     # if os.path.exists(outpath):
#     #     print(f"{outpath} 已存在，跳过该文件的处理。")
#     #     continue  # 若存在，跳过该文件的处理（或者可以选择覆盖）
#     # else:
#     #     pd.DataFrame().to_csv(outpath, index=False)
#     #     print(f"已创建空白文件: {outpath}")
#         # 定义插件的参数
#         args = [v3d_path,'/x',"global_neuron_feature",'/f', "compute_feature_in_folder","/i", cell_type_dir, '/o', outpath]
#         # 运行插件
#         print(f"正在处理: {cell_type}，输出到 {outpath}")
#         subprocess.run(args)

import os
import shutil
import subprocess

import os
import shutil
import subprocess
import pandas as pd

#
# def batch_process_files(v3d_path, cell_type_dir, output_dir, final_output_path, batch_size=1000):
#     """
#     对文件夹内的 SWC 文件进行分批处理并合并所有生成的表格。
#
#     参数：
#         v3d_path (str): Vaa3D 可执行文件路径。
#         cell_type_dir (str): 输入的文件夹路径。
#         output_dir (str): 输出文件存放的文件夹路径。
#         final_output_path (str): 最终合并的总表路径。
#         batch_size (int): 每批处理的文件数。
#     """
#     # 获取所有文件列表
#     files = [file for file in os.listdir(cell_type_dir) if file.endswith('.swc')]
#     total_files = len(files)
#     print(f"总文件数: {total_files}")
#
#     # 确保输出目录存在
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir)
#
#     # 临时目录
#     temp_dir = os.path.join(cell_type_dir, "temp_batch")
#     if not os.path.exists(temp_dir):
#         os.makedirs(temp_dir)
#
#     # 存储所有批次的输出路径
#     output_files = []
#
#     # 分批处理
#     for i in range(0, total_files, batch_size):
#         outpath = os.path.join(output_dir, f"result_fea_{i}.csv")
#         batch_files = files[i:i + batch_size]
#         print(f"正在处理第 {i // batch_size + 1} 批，共 {len(batch_files)} 个文件")
#
#         # 将当前批次文件复制到临时目录
#         for file in batch_files:
#             src = os.path.join(cell_type_dir, file)
#             dst = os.path.join(temp_dir, file)
#             shutil.copy(src, dst)
#
#         # 调用插件处理当前批次
#         args = [
#             v3d_path, '/x', "global_neuron_feature", '/f', "compute_feature_in_folder",
#             "/i", temp_dir, '/o', outpath
#         ]
#         try:
#             subprocess.run(args, check=True)
#             print(f"第 {i // batch_size + 1} 批处理完成，输出: {outpath}")
#             output_files.append(outpath)  # 记录输出文件路径
#         except subprocess.CalledProcessError as e:
#             print(f"处理第 {i // batch_size + 1} 批时发生错误: {e}")
#         finally:
#             # 清空临时目录
#             for file in os.listdir(temp_dir):
#                 os.remove(os.path.join(temp_dir, file))
#
#     # 删除临时目录
#     shutil.rmtree(temp_dir)
#     print("所有批次处理完成")
#
#     # 合并所有批次生成的 CSV 文件
#     print("开始合并所有批次文件...")
#     combined_df = pd.concat([pd.read_csv(f) for f in output_files], ignore_index=True)
#     combined_df.to_csv(final_output_path, index=False)
#     print(f"合并完成，最终总表保存至: {final_output_path}")
# import subprocess
# v3d_path=r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.4\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.exe"
# # cell_type_dir=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\excitatory_spiny_neuron_with_atypical_tree"
# # outpath=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\excitatory_spiny_neuron_with_atypical_tree\excitatory_spiny_neuron_with_atypical_tree_fea.csv"
# cell_type_dir=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\level2\merge"
# outpath=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\level2\merge\l_fea.csv"
#         # 运行插件
# print(f"正在处理: {cell_type_dir}，输出到 {outpath}")
# args = [v3d_path, '/x', "global_neuron_feature", '/f', "compute_feature_in_folder","/i",cell_type_dir, '/o', outpath]
# subprocess.run(args)
#
# print("所有神经元类型特征已计算完成并保存。")
#
# # 参数设置
# v3d_path = r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.4\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.exe"
# # cell_type_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\2radius\pyramidal_neuron"
# # output_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\2radius\pyramidal_neuron\output_batches"
# #final_output_path = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\2radius\pyramidal_neuron\final_combined_features.csv"
# cell_type_dir=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\pyramidal_neuron"
# output_dir=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\pyramidal_neuron"
# final_output_path=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\pyramidal_neuron\all_pyramidal_neuron_fea.csv"
# # 调用函数进行分批处理并合并
# batch_process_files(v3d_path, cell_type_dir, output_dir, final_output_path, batch_size=500)

# 参数设置
# v3d_path = r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.4\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.exe"
# cell_type_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\2radius\pyramidal_neuron"
# outpath = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\2radius\pyramidal_neuron\pyramidal_neuron_l_fea.csv"
#
# # 调用函数进行分批处理
# batch_process_files(v3d_path, cell_type_dir, outpath, batch_size=1000)

# v3d_path=r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.4\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.exe"
# cell_type_dir=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\pyramidal_neuron"
# outpath=r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\cell_type_sorted\soma_merge\pyramidal_neuron\pyramidal_neuron_fea.csv"
# args = [v3d_path,'/x',"global_neuron_feature",'/f', "compute_feature_in_folder","/i", cell_type_dir, '/o', outpath]
#         # 运行插件
# print(f"正在处理: {cell_type_dir}，输出到 {outpath}")
# subprocess.run(args)
#
# print("所有神经元类型特征已计算完成并保存。")

# input=r"D:\GXQ\cross_em_lm\test_data\data_confirmed\1099456691_l_sorted_reverse.swc"
# output=r"D:\GXQ\cross_em_lm\test_data\data_confirmed\1099456691_l_sorted_reverse_sort.swc"
# sort_swc(input,output)
if __name__ == "__main__":
    input_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\classify_branch\apical_verify\eswc\sort"

    for file in os.listdir(input_dir):
        if file.endswith(".swc"):
            input_file = os.path.join(input_dir, file)
            print(f"处理文件：{input_file}")
            # nodes = read_swc_with_stats(input_file)
            # #nodes = adjust_soma_and_roots(nodes)
            output_file = f"{input_file.rstrip('.swc')}_sorted.swc"
            sort_swc(input_file, output_file)
           # write_swc(output_file, nodes)
            print('---------------------------------')