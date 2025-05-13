import os
import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D


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
    # 计算每个节点的度数
    compute_node_degrees(nodes)

    max_degree = -1
    potential_soma = None

    # 遍历节点，找到度数最大的节点作为潜在胞体
    for node in nodes.values():
        if node['degree'] > max_degree:
            max_degree = node['degree']
            potential_soma = node

    # 返回潜在胞体的坐标
    if potential_soma:
        return (potential_soma['x'], potential_soma['y'], potential_soma['z'])
    else:
        return None  # 如果没有找到，返回 None


def load_swc_to_undirected_graph(swc_file_path):
    """从SWC文件加载数据，构建无向图，并记录每个节点的parent信息"""
    df = pd.read_csv(swc_file_path, delim_whitespace=True, comment='#', header=None,
                     names=['id', 'type', 'x', 'y', 'z', 'radius', 'parent'])
    G = nx.Graph()

    for _, row in df.iterrows():
        # 添加节点，同时记录parent信息
        G.add_node(row['id'], pos=(row['x'], row['y'], row['z']), radius=row['radius'], type=row['type'],
                   parent=row['parent'])
        if row['parent'] != -1:
            G.add_edge(row['parent'], row['id'])

    return G


def apply_clustering(G, eps=1, min_samples=1):
    # 提取位置信息并应用DBSCAN聚类
    positions = np.array([G.nodes[n]['pos'] for n in G.nodes()])
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(positions)
    # 更新节点信息
    for node_id, cluster_id in zip(G.nodes, clustering.labels_):
        G.nodes[node_id]['cluster'] = cluster_id
    return clustering.labels_


def merge_clusters(G, labels):
    # 构建每个聚类的节点列表
    cluster_groups = {}
    for node_id, cluster_id in zip(G.nodes, labels):
        if cluster_id not in cluster_groups:
            cluster_groups[cluster_id] = []
        cluster_groups[cluster_id].append(node_id)

    new_G = nx.Graph()
    for cluster_id, nodes in cluster_groups.items():
        # 计算合并后的属性
        if cluster_id == -1:  # 跳过噪声点
            continue
        x, y, z, radius = zip(*[(G.nodes[n]['pos'][0], G.nodes[n]['pos'][1], G.nodes[n]['pos'][2], G.nodes[n]['radius']) for n in nodes])
        avg_pos = (np.mean(x), np.mean(y), np.mean(z))
        avg_radius = np.mean(radius)
        new_G.add_node(cluster_id, pos=avg_pos, radius=avg_radius)

    # 更新边，连接聚类中心
    for u, v, data in G.edges(data=True):
        cluster_u = G.nodes[u]['cluster']
        cluster_v = G.nodes[v]['cluster']
        if cluster_u != cluster_v and cluster_u != -1 and cluster_v != -1:
            new_G.add_edge(cluster_u, cluster_v)

    return new_G


def visualize_graph(G):
    # 可视化图
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for node, data in G.nodes(data=True):
        x, y, z = data['pos']
        ax.scatter(x, y, z, s=100 * data['radius'])
    for u, v in G.edges():
        x = [G.nodes[n]['pos'][0] for n in (u, v)]
        y = [G.nodes[n]['pos'][1] for n in (u, v)]
        z = [G.nodes[n]['pos'][2] for n in (u, v)]
        ax.plot(x, y, z, 'k-')
    plt.show()


def is_tree(G):
    # 检查图是否是连通的
    if not nx.is_connected(G.to_undirected()):
        return False

    # 检查图是否包含环
    if nx.is_tree(G):
        return True
    else:
        return False


def check_connectivity(G):
    # 对于无向图，直接检查连通性
    if nx.is_connected(G):
        return True
    else:
        return False


def find_nearest_node(G, target_pos):
    """在图中找到与给定坐标最近的节点"""
    nearest_node = None
    min_distance = float('inf')

    for node in G.nodes(data=True):
        pos = node[1]['pos']
        distance = np.linalg.norm(np.array(pos) - np.array(target_pos))
        if distance < min_distance:
            nearest_node = node[0]
            min_distance = distance

    return nearest_node


def export_to_swc_dfs(G, root_pos, output_filename):
    start_node = find_nearest_node(G, root_pos)

    # 打开文件进行写入
    with open(output_filename, 'w') as f:
        # 写入SWC文件的头部注释
        f.write("# SWC file generated from DFS traversal\n")
        f.write("# Columns: id type x y z radius parent\n")

        # 用于存储节点的新编号和访问状态
        new_id = 1
        visited = set()
        stack = [(start_node, -1)]  # (current_node, parent_id_in_new_swc)

        while stack:
            node, parent_id = stack.pop()
            if node not in visited:
                visited.add(node)
                node_data = G.nodes[node]
                pos = node_data['pos']
                radius = node_data.get('radius', 1.0)  # 默认半径为1.0
                node_type = node_data.get('type', 3)    # 默认类型为3

                # 写入当前节点数据
                f.write(f"{new_id} {node_type} {pos[0]} {pos[1]} {pos[2]} {radius} {parent_id}\n")

                # 更新父节点ID为当前节点的新ID
                current_parent_id = new_id
                new_id += 1

                # 将所有未访问的邻接节点添加到栈中
                for neighbor in G.neighbors(node):
                    if neighbor not in visited:
                        stack.append((neighbor, current_parent_id))


def transform_to_trees(G):
    # 新建一个图来存储结果
    tree_G = nx.Graph()

    # 获取G的所有连通分量
    components = nx.connected_components(G)

    # 对每个连通分量计算最小生成树
    for component in components:
        # 提取子图
        subgraph = G.subgraph(component)

        # 计算最小生成树
        if nx.is_connected(subgraph):
            mst = nx.minimum_spanning_tree(subgraph)
            # 添加最小生成树到结果图中
            tree_G = nx.compose(tree_G, mst)
        else:
            raise ValueError("子图不连通，出现了不应该发生的情况。")

    return tree_G


def connect_components(G):
    # 如果图已经是连通的，直接返回
    if nx.is_connected(G):
        return G

    # 新建图，包含所有原始图的节点和边
    new_G = G.copy()

    # 获得连通组件
    components = list(nx.connected_components(G))
    component_list = [comp for comp in components]

    while len(component_list) > 1:
        min_distance = float('inf')
        best_pair = None

        # 遍历所有组件对，寻找最短边
        for i in range(len(component_list)):
            for j in range(i + 1, len(component_list)):
                for u in component_list[i]:
                    for v in component_list[j]:
                        # 距离计算
                        if 'pos' in G.nodes[u] and 'pos' in G.nodes[v]:
                            distance = np.linalg.norm(np.array(G.nodes[u]['pos']) - np.array(G.nodes[v]['pos']))
                            if distance < min_distance:
                                min_distance = distance
                                best_pair = (u, v)

        # 添加最短边
        if best_pair:
            new_G.add_edge(best_pair[0], best_pair[1], weight=min_distance)
            # 更新连通组件
            component_list = list(nx.connected_components(new_G))

    return new_G


def sort_swc(swc_file, sorted_swc_file):
    G = load_swc_to_undirected_graph(swc_file)

    # 临近点聚类
    labels = apply_clustering(G)
    G = merge_clusters(G, labels)

    # 从原始 SWC 文件中读取节点信息，找到潜在的胞体位置
    nodes = read_swc(swc_file)
    potential_soma_pos = find_potential_soma(nodes)

    if potential_soma_pos is None:
        print("未能找到潜在的胞体节点，使用默认根节点位置 (0, 0, 0)")
        potential_soma_pos = (0, 0, 0)

    if not check_connectivity(G) or not is_tree(G):
        # 每个连通块生成最小生成树
        G = transform_to_trees(G)
        # 连接各个连通块
        G = connect_components(G)

    if os.path.exists(sorted_swc_file):
        os.remove(sorted_swc_file)

    # 使用找到的潜在胞体位置作为根节点位置
    export_to_swc_dfs(G, potential_soma_pos, sorted_swc_file)


if __name__ == '__main__':
    swc_file =r"D:\GXQ\cross_em_lm\test_data\data_confirmed\794820508_lcc.swc"
    sorted_swc_file = r"D:\GXQ\cross_em_lm\test_data\data_confirmed\kfc_794820508_lcc.swc"
    sort_swc(swc_file, sorted_swc_file)
