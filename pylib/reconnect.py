import networkx as nx
import pandas as pd
import numpy as np


def load_swc(filename):
    """从SWC文件加载节点信息"""
    nodes = {}
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('#') or line.strip() == '':
                continue
            parts = line.split()
            if len(parts) == 7:
                node_id = int(parts[0])
                node_type = int(parts[1])
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
                radius = float(parts[5])
                parent_id = int(parts[6])
                nodes[node_id] = {'id': node_id, 'type': node_type, 'x': x, 'y': y, 'z': z,
                                  'radius': radius, 'parent': parent_id, 'children': []}
    return nodes

def read_swc(filename):
    nodes = {}
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            # 忽略空行和注释行
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
            radius = float(parts[5])  # 将R重命名为radius
            P = int(float(parts[6]))
            nodes[n] = {'n': n, 'T': T, 'x': x, 'y': y, 'z': z, 'radius': radius, 'P': P, 'children': []}
    # 构建子节点列表
    for node in nodes.values():
        P = node['P']
        if P != -1 and P in nodes:
            nodes[P]['children'].append(node['n'])
        elif P != -1:
            print(f"警告：父节点{P}不存在，节点{node['n']}的父节点设为-1")
            node['P'] = -1
    return nodes

def compute_node_degrees(nodes):
    # 计算每个节点的度（连接数）
    for node in nodes.values():
        degree = len(node['children'])
        if node['P'] != -1:
            degree += 1  # 加上父节点
        node['degree'] = degree

def find_potential_soma(nodes):
    # 计算质心
    x_avg = sum(node['x'] for node in nodes.values()) / len(nodes)
    y_avg = sum(node['y'] for node in nodes.values()) / len(nodes)
    z_avg = sum(node['z'] for node in nodes.values()) / len(nodes)
    # 计算节点度和与质心的距离
    for node in nodes.values():
        node['degree'] = len(node['children'])
        dx = node['x'] - x_avg
        dy = node['y'] - y_avg
        dz = node['z'] - z_avg
        node['distance'] = (dx**2 + dy**2 + dz**2) ** 0.5
    # 计算评分
    max_score = -1
    potential_soma = None
    for node in nodes.values():
        score = node['degree'] / (1 + node['distance'])
        if score > max_score:
            max_score = score
            potential_soma = node['n']
    return potential_soma

def build_tree(nodes, root_id):
    """从根节点构建树结构，修正无效连接并保证无环性"""
    G = nx.Graph()
    for node_id, node_data in nodes.items():
        G.add_node(node_id, pos=(node_data['x'], node_data['y'], node_data['z']), radius=node_data['radius'])

    stack = [(root_id, None)]
    visited = set()
    valid_edges = []

    while stack:
        current, parent = stack.pop()
        if current in visited:
            continue
        visited.add(current)
        if parent is not None:
            valid_edges.append((parent, current))

        for child in nodes[current]['children']:
            if child not in visited:
                stack.append((child, current))

    new_G = nx.Graph()
    new_G.add_edges_from(valid_edges)
    return new_G


def remove_disconnected_nodes(G, root_id):
    """保留与根节点连通的节点，删除其他未连接的节点"""
    # 检查图是否为空或没有节点
    if G.number_of_nodes() == 0:
        print("图为空，无需删除未连接节点")
        return G

    # 找出与根节点连通的节点
    connected_components = list(nx.connected_components(G))
    if not connected_components:
        print("无连通分量，返回空图")
        return nx.Graph()  # 返回空图

    # 找到最大连通分量并保留
    largest_component = max(connected_components, key=len)
    nodes_to_remove = [node for node in G if node not in largest_component]

    # 删除不在最大连通分量中的节点
    G.remove_nodes_from(nodes_to_remove)
    return G



def correct_leaf_nodes(G, nodes, root_id):
    """确保叶节点不直接连接到根节点"""
    leaves = [n for n in G.nodes if G.degree(n) == 1 and n != root_id]

    for leaf in leaves:
        parent = list(G.neighbors(leaf))[0]
        if parent == root_id:
            nearest_node = find_nearest_connected_node(nodes[leaf], nodes, root_id)
            if nearest_node:
                G.remove_edge(root_id, leaf)
                G.add_edge(nearest_node, leaf)

    return G


def find_nearest_connected_node(node, nodes, root_id):
    """查找与给定节点最近的非根节点已连接节点"""
    node_pos = np.array((node['x'], node['y'], node['z']))
    min_distance = float('inf')
    nearest_node = None

    for other in nodes.values():
        if other['id'] != node['id'] and other['id'] != root_id and other['parent'] != -1:
            other_pos = np.array((other['x'], other['y'], other['z']))
            distance = np.linalg.norm(node_pos - other_pos)
            if distance < min_distance:
                min_distance = distance
                nearest_node = other['id']
    return nearest_node


def save_swc(filename, G, nodes, root_id):
    """将修正后的树结构保存为SWC文件"""
    with open(filename, 'w') as f:
        f.write("# Corrected SWC file\n")
        for node_id in nx.dfs_preorder_nodes(G, source=root_id):
            node = nodes[node_id]
            parent = -1 if node_id == root_id else list(G.neighbors(node_id))[0]
            f.write(f"{node['id']} {node['type']} {node['x']} {node['y']} {node['z']} {node['radius']} {parent}\n")


# 使用示例
input_file =  r"D:\GXQ\cross_em_lm\test_data\em_h01\1333261412.swc"
output_file = r"D:\GXQ\cross_em_lm\test_data\em_h01\reconnect_1333261412.swc"

nodes=read_swc(input_file)
root_pos = find_potential_soma(nodes)
root_id = root_pos  # 根节点的编号
print(root_id)
nodes = load_swc(input_file)
G = build_tree(nodes, root_id)
G = remove_disconnected_nodes(G, root_id)  # 删除未连接的节点
G = correct_leaf_nodes(G, nodes, root_id)
save_swc(output_file, G, nodes, root_id)
