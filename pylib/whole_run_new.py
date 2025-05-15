import os
import subprocess
from collections import deque
from tqdm import tqdm  # 进度条库
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed


def read_swc(filename):
    nodes = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 7:
                print(f"警告：行格式不正确，已忽略：{line}")
                continue
            n = int(parts[0])
            T = int(parts[1])
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])
            radius = float(parts[5])
            P = int(float(parts[6]))
            nodes[n] = {'n': n, 'T': T, 'x': x, 'y': y, 'z': z, 'radius': radius, 'P': P, 'children': []}

    for node in nodes.values():
        P = node['P']
        if P != -1 and P in nodes:
            nodes[P]['children'].append(node['n'])
        elif P != -1:
            print(f"警告：父节点{P}不存在，节点{node['n']}的父节点设为-1")
            node['P'] = -1
    return nodes


def read_swc_with_stats_lcc(filename):
    nodes = {}
    max_radius = 0
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) != 7:
                print(f"警告：行格式不正确，已忽略：{line}")
                continue
            n = int(parts[0])
            T = int(parts[1])
            x = float(parts[2])
            y = float(parts[3])
            z = float(parts[4])
            radius = float(parts[5])
            P = int(float(parts[6]))
            nodes[n] = {'n': n, 'T': T, 'x': x, 'y': y, 'z': z, 'radius': radius, 'P': P, 'children': []}
            if radius > max_radius:
                max_radius = radius
    print(f"最大的半径（radius）：{max_radius}")

    for node in nodes.values():
        P = node['P']
        if P != -1 and P in nodes:
            nodes[P]['children'].append(node['n'])
        elif P != -1:
            print(f"警告：父节点{P}不存在，节点{node['n']}的父节点设为无效")

    root_nodes = [node_id for node_id, node in nodes.items() if node['P'] == -1]
    total_nodes = len(nodes)
    connected_components = []
    visited_nodes = set()

    def traverse_component(root_id, visited):
        stack = [root_id]
        component_nodes = set()
        while stack:
            current_id = stack.pop()
            if current_id not in visited:
                visited.add(current_id)
                component_nodes.add(current_id)
                stack.extend(nodes[current_id]['children'])
        return component_nodes

    for root_id in root_nodes:
        if root_id not in visited_nodes:
            component = traverse_component(root_id, visited_nodes)
            connected_components.append(component)

    largest_component = max(connected_components, key=len)
    num_nodes = len(largest_component)
    proportion = num_nodes / total_nodes * 100
    print(f"总节点数：{total_nodes}")
    print(f"最大的连通结构包含 {num_nodes} 个节点，占总节点数的 {proportion:.2f}%")

    nodes = {node_id: nodes[node_id] for node_id in largest_component}
    return nodes, proportion


def calculate_effective_center(nodes, distance_threshold=50000):
    # 计算有效几何中心，仅使用与根节点距离在一定范围内的节点
    root_node = min(nodes.values(), key=lambda node: node['n'])  # 假设根节点ID最小
    close_nodes = [node for node in nodes.values() if ((node['x'] - root_node['x']) ** 2 +
                                                       (node['y'] - root_node['y']) ** 2 +
                                                       (node['z'] - root_node['z']) ** 2) ** 0.5 < distance_threshold]
    x_avg = sum(node['x'] for node in close_nodes) / len(close_nodes)
    y_avg = sum(node['y'] for node in close_nodes) / len(close_nodes)
    z_avg = sum(node['z'] for node in close_nodes) / len(close_nodes)
    return x_avg, y_avg, z_avg
    # """
    # 计算距离指定中心节点一定范围内的局部几何中心。
    # 参数:
    # - nodes: 节点字典
    # - central_node: 预期胞体位置的中心节点
    # - radius_limit: 计算局部几何中心的距离阈值
    #
    # 返回:
    # - x_avg, y_avg, z_avg: 局部几何中心的坐标
    # """
    # x_center, y_center, z_center = nodes[central_node]['x'], nodes[central_node]['y'], nodes[central_node]['z']
    # close_nodes = []
    #
    # # 选择距离中心节点在radius_limit以内的所有节点
    # for node in nodes.values():
    #     dx = node['x'] - x_center
    #     dy = node['y'] - y_center
    #     dz = node['z'] - z_center
    #     distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #     if distance <= radius_limit:
    #         close_nodes.append(node)
    #
    # # 计算局部几何中心
    # x_avg = sum(node['x'] for node in close_nodes) / len(close_nodes)
    # y_avg = sum(node['y'] for node in close_nodes) / len(close_nodes)
    # z_avg = sum(node['z'] for node in close_nodes) / len(close_nodes)
    #
    # print(f"局部几何中心: ({x_avg:.2f}, {y_avg:.2f}, {z_avg:.2f})，节点数: {len(close_nodes)}")
    # return x_avg, y_avg, z_avg
    # # 计算局部几何中心
    # x_avg, y_avg, z_avg = calculate_local_center(nodes, central_node, radius_limit=100000)
    #
    # # 找到度数和半径的最小和最大值，用于归一化
    # max_degree = max(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    # min_degree = min(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    # max_radius = max(node['radius'] for node in nodes.values())
    # min_radius = min(node['radius'] for node in nodes.values())
    #
    # # 初始化最大评分
    # max_score = -1
    # potential_soma = None
    # node_scores = []
    #
    # for node in nodes.values():
    #     node['degree'] = len(node['children']) + (1 if node['P'] != -1 else 0)
    #
    #     # 归一化度数和半径
    #     normalized_degree = (node['degree'] - min_degree) / (max_degree - min_degree) if max_degree != min_degree else 1
    #     normalized_radius = (node['radius'] - min_radius) / (max_radius - min_radius) if max_radius != min_radius else 1
    #
    #     # 计算到局部几何中心的距离
    #     dx = node['x'] - x_avg
    #     dy = node['y'] - y_avg
    #     dz = node['z'] - z_avg
    #     distance_to_center = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #
    #     # 使用加权公式计算评分，包含局部几何中心的距离惩罚
    #     score = gamma * normalized_degree + beta * normalized_radius ** 2 - alpha * distance_to_center
    #     node['score'] = score
    #     node_scores.append((node, score))  # 将节点和评分添加到列表中
    #
    #     # 更新最高分的节点
    #     if score > max_score:
    #         max_score = score
    #         potential_soma = node['n']
    #
    # # 排序并打印评分排名前十的节点信息
    # top_ranked_nodes = sorted(node_scores, key=lambda x: x[1], reverse=True)[:10]
    # print("评分排名前十的节点参数值:")
    # for rank, (node, score) in enumerate(top_ranked_nodes, start=1):
    #     print(f"排名 {rank}: 节点 {node['n']}, 度数={node['degree']}, 半径={node['radius']}, "
    #           f"归一化度数={normalized_degree:.4f}, 归一化半径={normalized_radius:.4f}, 距离={distance_to_center:.2f}, 评分={score:.4f}")
    #
    # # 打印最终选择的胞体节点
    # print(f"最终选择的胞体节点: {potential_soma}，评分={max_score:.4f}")
    # return potential_soma
    #
    # # 计算有效几何中心
    # x_avg, y_avg, z_avg = calculate_effective_center(nodes, distance_threshold)
    #
    # # 找到度数的最小和最大值，用于归一化度数
    # max_degree = max(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    # min_degree = min(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    #
    # # 初始化最大评分
    # max_score = -1
    # potential_soma = None
    # tie_candidates = []
    # node_scores = []  # 用于存储节点及其评分信息
    #
    # for node in nodes.values():
    #     node['degree'] = len(node['children']) + (1 if node['P'] != -1 else 0)
    #
    #     # 跳过度数为1的节点，确保候选胞体节点至少有多个连接
    #     if node['degree'] <= 1:
    #         continue
    #
    #     # 归一化度数
    #     normalized_degree = (node['degree'] - min_degree) / (max_degree - min_degree) if max_degree != min_degree else 1
    #
    #     # 使用立方根缩放后的半径
    #     if use_cbrt_radius:
    #         scaled_radius = node['radius'] ** (1 / 3)  # 使用立方根缩放
    #     else:
    #         scaled_radius = node['radius']  # 使用原始半径
    #
    #     # 使用加权公式计算评分
    #     score = gamma * normalized_degree + beta * scaled_radius ** 2
    #     node['score'] = score
    #     node_scores.append((node, score))  # 将节点和评分添加到列表中
    #
    #     # 更新最高分的节点
    #     if score > max_score:
    #         max_score = score
    #         potential_soma = node['n']
    #         tie_candidates = [node]  # 重置候选节点
    #     elif score == max_score:
    #         tie_candidates.append(node)  # 如果评分相同，加入候选列表
    #
    # # 排序并打印评分排名前十的节点信息
    # top_ranked_nodes = sorted(node_scores, key=lambda x: x[1], reverse=True)[:10]
    # print("评分排名前十的节点参数值:")
    # for rank, (node, score) in enumerate(top_ranked_nodes, start=1):
    #     print(f"排名 {rank}: 节点 {node['n']}, 度数={node['degree']}, 半径={node['radius']}, "
    #           f"缩放半径={scaled_radius:.4f}, 归一化度数={normalized_degree:.4f}, 评分={score:.4f}")
    #
    # # 如果存在评分相同的多个候选节点，使用距离和密集度进行进一步筛选
    # if len(tie_candidates) > 1:
    #     max_density_score = -1
    #     for candidate in tie_candidates:
    #         # 计算候选节点到有效几何中心的距离
    #         dx = candidate['x'] - x_avg
    #         dy = candidate['y'] - y_avg
    #         dz = candidate['z'] - z_avg
    #         distance_to_center = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #
    #         # 计算候选节点的密集度（在指定半径内的邻居节点数）
    #         candidate_density = 0
    #         for other_node in nodes.values():
    #             if other_node['n'] != candidate['n']:
    #                 dx = candidate['x'] - other_node['x']
    #                 dy = candidate['y'] - other_node['y']
    #                 dz = candidate['z'] - other_node['z']
    #                 distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #                 if distance <= density_radius:
    #                     candidate_density += 1
    #
    #         # 综合距离和密集度得分
    #         density_score = candidate_density / (1 + 0.001 * distance_to_center)
    #
    #         # 更新密集度和距离得分最高的节点
    #         if density_score > max_density_score:
    #             max_density_score = density_score
    #             potential_soma = candidate['n']
    #
    # # 打印最终选择的胞体节点
    # print(f"最终选择的胞体节点: {potential_soma}，评分={max_score:.4f}")
    # return potential_soma

    # def find_potential_soma_with_adjusted_weights(nodes, density_radius=50000, distance_threshold=500000, gamma=5, beta=4.5):
    # 计算有效几何中心
    x_avg, y_avg, z_avg = calculate_effective_center(nodes, distance_threshold)

    # 找到度数和半径的最小和最大值，用于归一化
    # max_degree = max(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    # min_degree = min(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    # max_radius = max(node['radius'] for node in nodes.values())
    # min_radius = min(node['radius'] for node in nodes.values())
    #
    # # 初始化最大评分
    # max_score = -1
    # potential_soma = None
    # tie_candidates = []
    # node_scores = []  # 用于存储节点及其评分信息
    #
    # for node in nodes.values():
    #     node['degree'] = len(node['children']) + (1 if node['P'] != -1 else 0)
    #
    #     # 跳过度数为1的节点，确保候选胞体节点至少有多个连接
    #     if node['degree'] <= 1:
    #         continue
    #
    #     # 归一化后的度数和半径
    #     normalized_degree = (node['degree'] - min_degree) / (max_degree - min_degree) if max_degree != min_degree else 1
    #     normalized_radius = (node['radius'] - min_radius) / (max_radius - min_radius) if max_radius != min_radius else 1
    #
    #     # 使用加权公式计算评分
    #     # score = gamma * normalized_degree + beta * normalized_radius ** 2
    #     score = gamma * normalized_degree + beta * normalized_radius
    #     node['score'] = score
    #     node_scores.append((node, score))  # 将节点和评分添加到列表中
    #
    #     # 更新最高分的节点
    #     if score > max_score:
    #         max_score = score
    #         potential_soma = node['n']
    #         tie_candidates = [node]  # 重置候选节点
    #     elif score == max_score:
    #         tie_candidates.append(node)  # 如果评分相同，加入候选列表
    #
    # # 排序并打印评分排名前十的节点信息
    # top_ranked_nodes = sorted(node_scores, key=lambda x: x[1], reverse=True)[:10]
    # print("评分排名前十的节点参数值:")
    # for rank, (node, score) in enumerate(top_ranked_nodes, start=1):
    #     print(f"排名 {rank}: 节点 {node['n']}, 度数={node['degree']}, 半径={node['radius']}, "
    #           f"归一化度数={normalized_degree:.4f}, 归一化半径={normalized_radius:.4f}, 评分={score:.4f}")
    #
    # # 如果存在评分相同的多个候选节点，使用距离和密集度进行进一步筛选
    # if len(tie_candidates) > 1:
    #     max_density_score = -1
    #     for candidate in tie_candidates:
    #         # 计算候选节点到有效几何中心的距离
    #         dx = candidate['x'] - x_avg
    #         dy = candidate['y'] - y_avg
    #         dz = candidate['z'] - z_avg
    #         distance_to_center = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #
    #         # 计算候选节点的密集度（在指定半径内的邻居节点数）
    #         candidate_density = 0
    #         for other_node in nodes.values():
    #             if other_node['n'] != candidate['n']:
    #                 dx = candidate['x'] - other_node['x']
    #                 dy = candidate['y'] - other_node['y']
    #                 dz = candidate['z'] - other_node['z']
    #                 distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #                 if distance <= density_radius:
    #                     candidate_density += 1
    #
    #         # 综合距离和密集度得分
    #         density_score = candidate_density / (1 + 0.001 * distance_to_center)
    #
    #         # 更新密集度和距离得分最高的节点
    #         if density_score > max_density_score:
    #             max_density_score = density_score
    #             potential_soma = candidate['n']

    # 打印最终选择的胞体节点
    # print(f"最终选择的胞体节点: {potential_soma}，评分={max_score:.4f}")
    # return potential_soma
    # # def find_potential_soma_with_adjusted_weights(nodes, density_radius=50000, distance_threshold=500000, gamma=5, beta=4.5, use_sqrt_radius=True):
    # # 计算有效几何中心
    # x_avg, y_avg, z_avg = calculate_effective_center(nodes, distance_threshold)
    #
    # # 找到度数的最小和最大值，用于归一化度数
    # max_degree = max(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    # min_degree = min(len(node['children']) + (1 if node['P'] != -1 else 0) for node in nodes.values())
    #
    # # 初始化最大评分
    # max_score = -1
    # potential_soma = None
    # tie_candidates = []
    # node_scores = []  # 用于存储节点及其评分信息
    #
    # for node in nodes.values():
    #     node['degree'] = len(node['children']) + (1 if node['P'] != -1 else 0)
    #
    #     # 跳过度数为1的节点，确保候选胞体节点至少有多个连接
    #     if node['degree'] <= 1:
    #         continue
    #
    #     # 归一化度数
    #     normalized_degree = (node['degree'] - min_degree) / (max_degree - min_degree) if max_degree != min_degree else 1
    #
    #     # 使用原始半径或平方根缩放后的半径
    #     if use_sqrt_radius:
    #         scaled_radius = node['radius'] ** 0.5  # 使用平方根缩放
    #     else:
    #         scaled_radius = node['radius']  # 使用原始半径
    #
    #     # 使用加权公式计算评分
    #     score = gamma * normalized_degree + beta * scaled_radius ** 2
    #     node['score'] = score
    #     node_scores.append((node, score))  # 将节点和评分添加到列表中
    #
    #     # 更新最高分的节点
    #     if score > max_score:
    #         max_score = score
    #         potential_soma = node['n']
    #         tie_candidates = [node]  # 重置候选节点
    #     elif score == max_score:
    #         tie_candidates.append(node)  # 如果评分相同，加入候选列表
    #
    # # 排序并打印评分排名前十的节点信息
    # top_ranked_nodes = sorted(node_scores, key=lambda x: x[1], reverse=True)[:10]
    # print("评分排名前十的节点参数值:")
    # for rank, (node, score) in enumerate(top_ranked_nodes, start=1):
    #     print(f"排名 {rank}: 节点 {node['n']}, 度数={node['degree']}, 半径={node['radius']}, "
    #           f"缩放半径={scaled_radius:.4f}, 归一化度数={normalized_degree:.4f}, 评分={score:.4f}")
    #
    # # 如果存在评分相同的多个候选节点，使用距离和密集度进行进一步筛选
    # if len(tie_candidates) > 1:
    #     max_density_score = -1
    #     for candidate in tie_candidates:
    #         # 计算候选节点到有效几何中心的距离
    #         dx = candidate['x'] - x_avg
    #         dy = candidate['y'] - y_avg
    #         dz = candidate['z'] - z_avg
    #         distance_to_center = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #
    #         # 计算候选节点的密集度（在指定半径内的邻居节点数）
    #         candidate_density = 0
    #         for other_node in nodes.values():
    #             if other_node['n'] != candidate['n']:
    #                 dx = candidate['x'] - other_node['x']
    #                 dy = candidate['y'] - other_node['y']
    #                 dz = candidate['z'] - other_node['z']
    #                 distance = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
    #                 if distance <= density_radius:
    #                     candidate_density += 1
    #
    #         # 综合距离和密集度得分
    #         density_score = candidate_density / (1 + 0.001 * distance_to_center)
    #
    #         # 更新密集度和距离得分最高的节点
    #         if density_score > max_density_score:
    #             max_density_score = density_score
    #             potential_soma = candidate['n']
    #
    # # 打印最终选择的胞体节点
    # print(f"最终选择的胞体节点: {potential_soma}，评分={max_score:.4f}")
    # return potential_soma


def find_potential_soma_with_adjusted_weights(nodes, gamma=5, beta=4.5, percentile=0.005, use_cbrt_radius=True):
    # 计算有效几何中心
    x_avg, y_avg, z_avg = calculate_effective_center(nodes)

    # 找到所有节点的度数，并计算度数的最小和最大值
    for node in nodes.values():
        node['degree'] = len(node['children']) + (1 if node['P'] != -1 else 0)

    degree_list = sorted([node['degree'] for node in nodes.values()], reverse=True)

    # 确定度数前30%的阈值
    percentile_index = max(1, int(len(degree_list) * percentile))  # 保证至少选一个节点
    degree_threshold = degree_list[percentile_index - 1]  # 前30%的最低度数
    print(f"度数前 {percentile * 100}% 的阈值为: {degree_threshold}")

    # 初始化最大评分
    max_score = -1
    potential_soma = None
    node_scores = []  # 用于存储节点及其评分信息

    for node in nodes.values():
        # 仅考虑度数达到阈值的节点
        if node['degree'] < degree_threshold:
            continue

        # 归一化度数
        max_degree = max(degree_list)
        min_degree = min(degree_list)
        normalized_degree = (node['degree'] - min_degree) / (max_degree - min_degree) if max_degree != min_degree else 1

        # 使用立方根缩放后的半径
        scaled_radius = node['radius'] ** (1 / 3) if use_cbrt_radius else node['radius']
        node['scale_radius'] = scaled_radius
        node['normalized_degree'] = normalized_degree
        # 使用加权公式计算评分
        score = gamma * normalized_degree + beta * scaled_radius / 10
        # score1 = gamma * normalized_degree + beta * scaled_radius/10
        # score2 = gamma * normalized_degree + beta * scaled_radius/10
        node['score'] = score
        node_scores.append((node, score))  # 将节点和评分添加到列表中

        # 更新最高分的节点
        if score > max_score:
            max_score = score
            potential_soma = node['n']

    # 排序并打印评分排名前十的节点信息
    # top_ranked_nodes = sorted(node_scores, key=lambda x: x[1], reverse=True)[:10]
    # print("评分排名前十的节点参数值:")
    # for rank, (node, score) in enumerate(top_ranked_nodes, start=1):
    #     print(f"排名 {rank}: 节点 {node['n']}, 度数={node['degree']}, 半径={node['radius']}, "
    #           f"归一化度数={node['normalized_degree']}, 缩放半径={node['scale_radius']}, 评分={score:.4f}")

    print(f"最终选择的胞体节点: {potential_soma}，评分={max_score:.4f}")
    return potential_soma


def find_path(nodes, start_node, end_node):
    queue = deque([(start_node, [start_node])])
    visited = {start_node}
    while queue:
        current_node, path = queue.popleft()
        if current_node == end_node:
            return path
        for neighbor in nodes.get(current_node, {}).get('children', []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None


def reverse_path(nodes, path):
    path_len = len(path)
    for i in range(path_len - 1):
        child_id = path[i]
        parent_id = path[i + 1]
        nodes[child_id]['P'] = parent_id
    for node_id in path:
        nodes[node_id]['children'] = []
    for i in range(path_len - 1):
        parent_id = path[i + 1]
        child_id = path[i]
        nodes[parent_id]['children'].append(child_id)


def adjust_soma_and_roots(nodes):
    # 使用加权后的胞体检测方法
    soma_node = find_potential_soma_with_adjusted_weights(nodes)
    print(f"选择节点 {soma_node} 作为新的胞体节点")

    # 找到原始的 P=-1 节点（根节点）
    original_soma_nodes = [node['n'] for node in nodes.values() if node['P'] == -1 and node['n'] != soma_node]
    #print(f"原始 P=-1 节点: {original_soma_nodes}")

    # 处理每个原始根节点到新胞体节点的路径
    for old_soma_node in original_soma_nodes:
        path = find_path(nodes, old_soma_node, soma_node)
        if path:
            #print(f"从旧胞体节点 {old_soma_node} 到新胞体节点 {soma_node} 的路径: {path}")
            reverse_path(nodes, path)
        else:
            print(f"无法找到从旧胞体节点 {old_soma_node} 到新胞体节点 {soma_node} 的路径")

    # 设置新胞体节点的类型和父节点
    nodes[soma_node]['T'] = 1
    nodes[soma_node]['P'] = -1
    for node in nodes.values():
        if node['n'] != soma_node:
            node['T'] = 0  # 非胞体节点的类型设为1

    # 重建父子关系
    for node in nodes.values():
        node['children'] = []
    for node in nodes.values():
        P = node['P']
        if P != -1 and P in nodes:
            nodes[P]['children'].append(node['n'])
        elif P != -1:
            print(f"警告：父节点 {P} 不存在，节点 {node['n']} 的父节点设为 -1")
            node['P'] = -1
    return nodes, soma_node


def write_swc(nodes, filename):
    with open(filename, 'w') as f:
        f.write("# 标准化后的SWC文件\n")
        for n in sorted(nodes.keys()):
            node = nodes[n]
            f.write(f"{node['n']} {node['T']} {node['x']} {node['y']} {node['z']} {node['radius']} {node['P']}\n")


def sort_swc(v3d_path, swc_in, swc_out=None):
    cmd_args = [v3d_path, '/x', 'sort_neuron_swc', '/f', 'sort_swc', '/i', swc_in, '/o', swc_out]
    subprocess.run(cmd_args)


import os
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


# 定义处理文件的函数
def process_file(input_file, output_file, final_file, v3d_path, csv_file):
    print(f"\n处理文件：{input_file}")

    # 1. 读取SWC文件的所有节点并输出到crop目录
    # all_nodes = read_swc(input_file)
    # write_swc(all_nodes, crop_file)

    # 2. 识别最大连通分量（LCC）并输出结果
    lcc_nodes, lcc_proportion = read_swc_with_stats_lcc(input_file)
    output_lcc_file = f"{output_file.rstrip('.swc')}_lcc.swc"
    output_lcc_sort_file = f"{output_file.rstrip('.swc')}_sort_lcc.swc"
    write_swc(lcc_nodes, output_lcc_file)
    #
    # # 3. 对LCC结果排序并输出排序结果
    sort_swc(v3d_path, output_lcc_file, output_lcc_sort_file)
    lcc_nodes=read_swc(output_lcc_sort_file)
    # 4. 调整胞体节点，并获取调整后的节点信息
    nodes1, soma_node_id = adjust_soma_and_roots(lcc_nodes)
    output_file_1 = f"{output_file.rstrip('.swc')}_reverse.swc"
    #write_swc(nodes1, output_file_1)

    # 5. 对调整后的结果进行最终排序并存储到最终目录
    out_sort = f"{final_file.rstrip('.swc')}_sort.swc"
    sort_swc(v3d_path, output_file_1, out_sort)

    # 获取soma节点的坐标
    soma_x = nodes1[soma_node_id]['x']
    soma_y = nodes1[soma_node_id]['y']
    soma_z = nodes1[soma_node_id]['z']

    # 返回统计数据，供写入CSV使用
    return [os.path.basename(input_file), soma_x, soma_y, soma_z]


if __name__ == "__main__":
    # 定义输入和输出目录
    input_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\level3\final\weird_case\soma_error"
    final_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\level3\final\weird_case\soma_error\new"
    output_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\level3\final\weird_case\soma_error\new"
    #crop_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v1\crop_original"
    v3d_path = r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.exe"
    csv_file = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v2\level3\final\weird_case\soma_error\new\data.csv"

    # 初始化CSV文件，写入表头
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Soma_X", "Soma_Y", "Soma_Z", "LCC_Node_Proportion"])

    # 获取所有SWC文件
    files = [file for file in os.listdir(input_dir) if file.endswith(".swc")]

    # 使用多线程处理文件
    with ThreadPoolExecutor() as executor:
        futures = []
        for file in files:
            input_file = os.path.join(input_dir, file)
            #crop_file = os.path.join(crop_dir, file)
            final_file = os.path.join(final_dir, file)
            output_file = os.path.join(output_dir, file)

            # 提交任务给线程池
            futures.append(
                executor.submit(process_file, input_file,output_file, final_file, v3d_path, csv_file))

        # 收集并写入CSV数据
        with open(csv_file, mode='a', newline='') as f:
            writer = csv.writer(f)
            for future in tqdm(as_completed(futures), total=len(futures), desc="处理文件进度"):
                try:
                    result = future.result()  # 获取返回的统计数据
                    writer.writerow(result)  # 写入CSV文件
                except Exception as e:
                    print(f"处理文件时发生错误: {e}")

# def process_file(input_file, crop_file, output_file, final_file, v3d_path):
#     print(f"\n处理文件：{input_file}")
#
#     # 1. 读取SWC文件的所有节点并输出到crop目录
#     all_nodes = read_swc(input_file)
#     write_swc(all_nodes, crop_file)
#
#     # 2. 识别最大连通分量（LCC）并输出结果
#     lcc_nodes, lcc_proportion = read_swc_with_stats_lcc(input_file)
#     output_lcc_file = f"{output_file.rstrip('.swc')}_lcc.swc"
#     output_lcc_sort_file = f"{output_file.rstrip('.swc')}_sort_lcc.swc"
#     write_swc(lcc_nodes, output_lcc_file)
#
#     # 3. 对LCC结果排序并输出排序结果
#     sort_swc(v3d_path, output_lcc_file, output_lcc_sort_file)
#
#     # 4. 调整胞体节点，并获取调整后的节点信息
#     nodes1, soma_node_id = adjust_soma_and_roots(lcc_nodes)
#     output_file_1 = f"{output_file.rstrip('.swc')}_reverse.swc"
#     write_swc(nodes1, output_file_1)
#
#     # 5. 对调整后的结果进行最终排序并存储到最终目录
#     out_sort = f"{final_file.rstrip('.swc')}_sort.swc"
#     sort_swc(v3d_path, output_file_1, out_sort)
#
#     # 获取soma节点的坐标
#     soma_x = nodes1[soma_node_id]['x']
#     soma_y = nodes1[soma_node_id]['y']
#     soma_z = nodes1[soma_node_id]['z']
#
#     # 将统计数据写入CSV
#     with open(csv_file, mode='a', newline='') as f:
#         writer = csv.writer(f)
#         writer.writerow([os.path.basename(input_file), soma_x, soma_y, soma_z, lcc_proportion])
#
#     print('---------------------------------')
#
#
# if __name__ == "__main__":
#     # 定义输入和输出目录
#     input_dir = r"Z:\SEU-ALLEN\Users\ZhixiYun\data\H01\C3\C3_swc"
#     final_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v1\lcc_sort"
#     output_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v1\mid_data"
#     crop_dir = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\v1\crop_original"
#     v3d_path = v3d_path=r"C:\Users\SEU\Desktop\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.1.1.4_Windows_64bit_version\Vaa3D-x.exe"
#     csv_file = r"Z:\SEU-ALLEN\Users\XiaoqinGu\dataset\H01\data.csv"
#
#     # 初始化CSV文件，写入表头
#     with open(csv_file, mode='w', newline='') as f:
#         writer = csv.writer(f)
#         writer.writerow(["Filename", "Soma_X", "Soma_Y", "Soma_Z", "LCC_Node_Proportion"])
#
#     # 遍历输入目录中的所有SWC文件
#     files = [file for file in os.listdir(input_dir) if file.endswith(".swc")]
#     for file in tqdm(files, desc="处理文件进度"):
#         input_file = os.path.join(input_dir, file)
#         crop_file = os.path.join(crop_dir, file)
#         final_file = os.path.join(final_dir, file)
#         output_file = os.path.join(output_dir, file)
#
#         process_file(input_file, crop_file, output_file, final_file, v3d_path)
