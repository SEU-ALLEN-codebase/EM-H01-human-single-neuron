import os
import math

def read_swc_with_stats(filename):
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
            nodes[n] = {
                'n': n, 'original_id': n, 'T': T, 'x': x, 'y': y,
                'z': z, 'radius': radius, 'P': P, 'children': []
            }
            if radius > max_radius:
                max_radius = radius
    print(f"最大的半径（radius）：{max_radius}")

    # 建立父子关系
    for node in nodes.values():
        P = node['P']
        if P != -1 and P in nodes:
            nodes[P]['children'].append(node['n'])
        elif P != -1:
            print(f"警告：父节点{P}不存在，节点{node['n']}的父节点设为无效")

    # 查找所有的根节点（P == -1）
    root_nodes = [node_id for node_id, node in nodes.items() if node['P'] == -1]

    total_nodes = len(nodes)
    connected_components = []
    visited_nodes = set()

    # 统计连通结构
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

    # 找到最大连通结构并过滤
    largest_component = max(connected_components, key=len)
    filtered_components = []

    for idx, component in enumerate(connected_components, 1):
        component_size = len(component)
        proportion = (component_size / total_nodes) * 100

        # 仅保留比例超过5%的连通结构
        if proportion > 5:
            filtered_components.append(component)
            print(f"保留的连通结构 {idx} 包含 {component_size} 个节点，占总节点数的 {proportion:.2f}%")
        else:
            print(f"删除的连通结构 {idx} 包含 {component_size} 个节点，占总节点数的 {proportion:.2f}%")

    # 更新 nodes 仅保留符合条件的节点
    retained_nodes = set()
    for component in filtered_components:
        retained_nodes.update(component)

    # 删除不符合条件的节点
    nodes = {node_id: nodes[node_id] for node_id in retained_nodes}

    # 保存所有连通结构的信息
    components_info = {
        'largest_component': largest_component,
        'filtered_components': filtered_components,
        'total_nodes': total_nodes
    }

    return nodes, components_info

def find_potential_soma(nodes):
    x_avg = sum(node['x'] for node in nodes.values()) / len(nodes)
    y_avg = sum(node['y'] for node in nodes.values()) / len(nodes)
    z_avg = sum(node['z'] for node in nodes.values()) / len(nodes)

    max_score = -1
    potential_soma = None
    for node in nodes.values():
        node['degree'] = len(node['children']) + (1 if node['P'] != -1 else 0)
        dx = node['x'] - x_avg
        dy = node['y'] - y_avg
        dz = node['z'] - z_avg
        node['distance'] = (dx ** 2 + dy ** 2 + dz ** 2) ** 0.5
        score = (node['degree'] * node['radius']) / (1 + node['distance'])
        if score > max_score:
            max_score = score
            potential_soma = node['n']
    return potential_soma

def adjust_soma_and_roots(nodes):
    # 找到新的潜在胞体节点
    soma_node = find_potential_soma(nodes)
    print(f"选择节点 {soma_node} 作为新的胞体节点")

    # 调整节点信息
    nodes[soma_node]['T'] = 1
    nodes[soma_node]['P'] = -1
    nodes[soma_node]['children'] = []

    for node in nodes.values():
        if node['P'] == -1 and node['n'] != soma_node:
            node['P'] = soma_node
            nodes[soma_node]['children'].append(node['n'])
            # print(f"节点 {node['n']} 的父节点设为胞体节点 {soma_node}")

    # soma_children = nodes[soma_node]['children']
    # print(f"胞体节点 {soma_node} 的一级子节点为: {soma_children}")
    return nodes

def write_swc(filename, nodes):
    with open(filename, 'w') as f:
        f.write("# 标准化后的SWC文件\n")
        for n in sorted(nodes.keys()):
            node = nodes[n]
            f.write(f"{node['n']} {node['T']} {node['x']} {node['y']} {node['z']} {node['radius']} {node['P']}\n")

def calculate_min_distances(nodes, components_info):
    largest_component_nodes = [nodes[node_id] for node_id in components_info['largest_component']]
    filtered_components = components_info['filtered_components']
    total_nodes = components_info['total_nodes']

    # 获取最大连通结构中所有节点的坐标列表
    largest_coords = [(node['x'], node['y'], node['z']) for node in largest_component_nodes]

    # 计算每个其他连通结构到最大连通结构的最小距离
    for idx, component in enumerate(filtered_components, 1):
        if component == components_info['largest_component']:
            continue  # 跳过最大连通结构本身

        component_size = len(component)
        proportion = (component_size / total_nodes) * 100

        min_distance = float('inf')
        component_nodes = [nodes[node_id] for node_id in component]
        for node in component_nodes:
            x1, y1, z1 = node['x'], node['y'], node['z']
            for x2, y2, z2 in largest_coords:
                dx = x1 - x2
                dy = y1 - y2
                dz = z1 - z2
                distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if distance < min_distance:
                    min_distance = distance
        print(f"连通结构 {idx} 占总节点的 {proportion:.2f}%，到最大连通结构的最近距离为：{min_distance:.2f}")

if __name__ == "__main__":
    input_dir = r"D:\GXQ\cross_em_lm\test_data\crop_test"
    output_dir = r"D:\GXQ\cross_em_lm\test_data\output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for file in os.listdir(input_dir):
        if file.endswith("crop.swc"):
            input_file = os.path.join(input_dir, file)
            print(f"处理文件：{input_file}")
            nodes, components_info = read_swc_with_stats(input_file)

            if not nodes:
                print("没有符合条件的连通结构，跳过此文件。")
                print('---------------------------------')
                continue

            nodes = adjust_soma_and_roots(nodes)
            calculate_min_distances(nodes, components_info)

            # 写入新的 SWC 文件
            output_file = os.path.join(output_dir, f"{os.path.splitext(file)[0]}_filtered.swc")
            write_swc(output_file, nodes)
            print(f"已保存处理后的 SWC 文件：{output_file}")
            print('---------------------------------')
