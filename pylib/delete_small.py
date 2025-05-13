import os

def read_swc_with_stats(filename):
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
            nodes[n] = {
                'n': n, 'original_id': n, 'T': T, 'x': x, 'y': y,
                'z': z, 'radius': radius, 'P': P, 'children': []
            }
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

    # 找到最大连通结构
    largest_component = max(connected_components, key=len)
    num_nodes = len(largest_component)
    proportion = num_nodes / total_nodes * 100

    print(f"总节点数：{total_nodes}")
    print(f"最大的连通结构包含 {num_nodes} 个节点，占总节点数的 {proportion:.2f}%")

    # 仅保留最大连通结构中的节点
    nodes = {node_id: nodes[node_id] for node_id in largest_component}

    return nodes

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
    # 获取原始的 P=-1 节点
    original_soma_nodes = [node['n'] for node in nodes.values() if node['P'] == -1]
    print(f"原始 P=-1 节点: {original_soma_nodes}")
    #nodes[original_soma_nodes]['T']=4

    # 找到新的潜在胞体节点
    soma_node = find_potential_soma(nodes)
    print(f"选择节点 {soma_node} 作为新的胞体节点")

    # 对比原始 P=-1 节点和新的胞体节点
    if soma_node in original_soma_nodes:
        print(f"新胞体节点 {soma_node} 与原始的 P=-1 节点一致。")
    else:
        print(f"新胞体节点 {soma_node} 与原始的 P=-1 节点不一致。")
        print(f"原始的 P=-1 节点为: {original_soma_nodes}，新的胞体节点为: {soma_node}")
    nodes[soma_node]['T'] = 1
    nodes[soma_node]['P'] = -1
    nodes[soma_node]['children'] = []

    for node in nodes.values():
        if node['P'] == -1 and node['n'] != soma_node:
            node['P'] = soma_node
            nodes[soma_node]['children'].append(node['n'])
            print(f"节点 {node['n']} 的父节点设为胞体节点 {soma_node}")

    soma_children = nodes[soma_node]['children']
    print(f"胞体节点 {soma_node} 的一级子节点为: {soma_children}")
    return nodes

def write_swc(filename, nodes):
    with open(filename, 'w') as f:
        f.write("# 标准化后的SWC文件\n")
        for n in sorted(nodes.keys()):
            node = nodes[n]
            f.write(f"{node['n']} {node['T']} {node['x']} {node['y']} {node['z']} {node['radius']} {node['P']}\n")



if __name__ == "__main__":
    input_dir = r"D:\GXQ\cross_em_lm\test_data\crop_test"
    input_file="D:\GXQ\cross_em_lm\test_data\crop_test\1099456691.swc"
    nodes = read_swc_with_stats(input_file)
    new_node = adjust_soma_and_roots(nodes)
    # for file in os.listdir(input_dir):
    #     if str(os.path.basename(file)).endswith("crop.swc"):
    #         input_file = os.path.join(input_dir, os.path.basename(file))
    #         cc = str(input_file).rstrip(".swc")
    #         output_file = f"{cc}_lcc.swc"
    #         print(cc)
    #         nodes = read_swc_with_stats(input_file)
    #         new_node=adjust_soma_and_roots(nodes)
    #         #write_swc(output_file,adjust_soma_and_roots(nodes))
