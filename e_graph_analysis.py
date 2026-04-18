from pathlib import Path
import sqlite3 as sql
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

BASE = Path(__file__).parent


con=sql.connect(BASE / "data/db/db_EstFija10")
cur=con.cursor()

cur.execute("select name from sqlite_master where type='table'")
cur.fetchall()


info_arc=pd.read_sql("select* from info_arc", con)
info_nodes=pd.read_sql("select* from info_nodes", con)
info_node=pd.read_sql("""
                      select a.*, b.Supplier, b.Plant, b.CD,b.Customer 
                      from coordenadas a left join info_nodes b on
                      b.name_node=a.Name """, con)

#pd.read_sql("select * from info_nodes where name_node like '%Bogota%' ", con)


info_node.drop(columns=['Group','index'], inplace =True)

info_nodes2=info_node.drop_duplicates(keep='first')

info_nodes2.reset_index(inplace=True, drop=True)

info_arc[info_arc['destino'].str.contains('2', regex=False)]

info_arc['destino']=info_arc['destino'].str.replace('2', '', regex=False)


G = nx.from_pandas_edgelist(info_arc, source='origen', target='destino', edge_attr='demanda', create_using=nx.Graph())

#G.nodes['Caucasia']['Longitude']

#node='Caucasia'

for _, row in info_nodes2.iterrows():

    G.nodes[row['Name']]['Latitude'] = row['Latitude']  
    G.nodes[row['Name']]['Longitude'] = row['Longitude']
    G.nodes[row['Name']]['Supplier'] = row['Supplier']
    G.nodes[row['Name']]['Plant'] = row['Plant']
    G.nodes[row['Name']]['CD'] = row['CD']
    G.nodes[row['Name']]['Customer'] = row['Customer']
    print(row)
    

### general metrics
edge_betweenness_centrality = nx.edge_betweenness_centrality(G, normalized=True)

# Edge Load number of shortest path
edge_load = nx.edge_load_centrality(G)


# Combine into a DataFrame for easy viewing
edge_metrics_df = pd.DataFrame({
    'Source': [edge[0] for edge in G.edges()],
    'Target': [edge[1] for edge in G.edges()],
    'Betweenness Centrality': [edge_betweenness_centrality[edge] for edge in G.edges()],
    'Load Centrality': [edge_load[edge] for edge in G.edges()]
    #'Current Flow Betweenes Centrality': [cf_bc[edge] for edge in G.edges()]
    
})



#############


 ##############metrics by echelon ##########

# subset1:  source Supplier == 1) and target nodes (Plant == 1)
source_supplier_nodes = [node for node, data in G.nodes(data=True) if data.get('Supplier') == 1]
target_plant_nodes = [node for node, data in G.nodes(data=True) if data.get('Plant') == 1]

# Calculate edge betweenness centrality using the source and target nodes
edge_betweenness_supplier_plant = nx.edge_betweenness_centrality_subset(G, sources=target_plant_nodes, targets=target_plant_nodes, normalized=True)


# Subset 2: Source = Plant, Target = CD
source_plant_nodes = [node for node, data in G.nodes(data=True) if data.get('Plant') == 1]
target_cd_nodes = [node for node, data in G.nodes(data=True) if data.get('CD') == 1]

# Calculate edge betweenness centrality for Source = Plant and Target = CD
edge_betweenness_plant_cd = nx.edge_betweenness_centrality_subset(G, sources=source_plant_nodes, targets=target_cd_nodes,normalized=True)

# Subset 2: Source = CD, Target = Customer
source_cd_nodes = [node for node, data in G.nodes(data=True) if data.get('CD') == 1]
target_customer_nodes = [node for node, data in G.nodes(data=True) if data.get('Customer') == 1]

# Calculate edge betweenness centrality for Source = CD and Target = Customer
edge_betweenness_cd_customer = nx.edge_betweenness_centrality_subset(G, sources=source_cd_nodes, targets=target_customer_nodes, normalized=True)



betweenness_data = [
    (edge_betweenness_supplier_plant, 'Supplier-Plant'),
    (edge_betweenness_plant_cd, 'Plant-CD'),
    (edge_betweenness_cd_customer, 'CD-Customer')
]

# Create a single DataFrame for all edges by iterating over the data
df_all_edges = pd.concat(
    [pd.DataFrame([(src, tgt, bet, subset) for (src, tgt), bet in data.items()],
                  columns=['Source', 'Target', 'Betweenness_Centrality', 'Subset'])
     for data, subset in betweenness_data],
    ignore_index=True
)







import openpyxl

edge_metrics_df.to_excel(BASE / 'output/graph_metrics_graph.xlsx')
df_all_edges.to_excel(BASE / 'output/graphs_metrics_echelon.xlsx')



################ min_cut


from networkx.algorithms.connectivity import minimum_st_edge_cut

### to try out

source= "Bogota"
target="Medellin"


def compute_minimum_cut_subset(G, source_subset, target_subset):
    min_cut_data = []
    
    # Loop over each pair of source and target nodes
    for source in source_subset:
        for target in target_subset:
            try:
                # Compute the minimum cut between each source-target pair
                cut_set = minimum_st_edge_cut(G, source, target)
                
                # Sort each edge in the cut set alphabetically by the nodes
                sorted_cut_set = sorted([tuple(sorted(edge)) for edge in cut_set])
                
                # Convert the cut set to a string of sorted edges
                sorted_cut_set_str = ', '.join([f"{u}-{v}" for u, v in sorted_cut_set])
                
                # Sort source and target alphabetically
                #sorted_source_target = tuple(sorted([source, target]))
                
                # Store data: source, target, and the sorted cut set
                min_cut_data.append({
                    'Source': source,
                    'Target': target,
                    'Cut_Set': sorted_cut_set_str  # Ordered cut set as a string
                })
            except Exception as e:
                # Handle the error, for example by printing a message and continuing
                print(f"Error computing minimum cut between {source} and {target}: {e}")
    
    # Convert the results to a DataFrame
    df_min_cut = pd.DataFrame(min_cut_data, columns=['Source', 'Target', 'Cut_Set'])
    
    return df_min_cut


min_cut_supplier_plant = compute_minimum_cut_subset(G, source_supplier_nodes, target_plant_nodes)
min_cut_plant_cd = compute_minimum_cut_subset(G, source_plant_nodes, target_cd_nodes)
min_cut_cd_customer = compute_minimum_cut_subset(G, source_cd_nodes, target_customer_nodes)

min_cut_supplier_plant['Subset'] = 'Supplier-Plant'
min_cut_plant_cd['Subset'] = 'Plant-CD'
min_cut_cd_customer['Subset'] = 'CD-Customer'

# Concatenate the DataFrames
df_all_min_cuts = pd.concat([min_cut_supplier_plant, min_cut_plant_cd, min_cut_cd_customer], ignore_index=True)


df_all_min_cuts.to_excel(BASE / "output/all_cutsets.xlsx")

info_nodes['Plant'].sum()
4*25

from collections import defaultdict

def count_edges_in_min_cut_sets(G, source_subset, target_subset):
    # Dictionary to count how many times each edge appears in cut sets
    edge_count = defaultdict(int)
    
    # Loop over each pair of source and target nodes
    for source in source_subset:
        for target in target_subset:
            try:
                # Compute the minimum cut between each source-target pair
                cut_set = minimum_st_edge_cut(G, source, target)
                
                # Increment the count for each edge in the cut set (unordered)
                for edge in cut_set:
                    # Sort the nodes in the edge to make it order-independent
                    u, v = sorted(edge)
                    edge_count[(u, v)] += 1
            except Exception as e:
                # Handle the error and continue
                print(f"Error computing minimum cut between {source} and {target}: {e}")
    
    return edge_count


cunt_s_plant=count_edges_in_min_cut_sets(G, source_supplier_nodes, target_plant_nodes)

df_cunt_s_plant = pd.DataFrame(
    [(u, v, count) for (u, v), count in cunt_s_plant.items()],
    columns=['Source', 'Target', 'Count']
)


cunt_s_plant_cd = count_edges_in_min_cut_sets(G, source_plant_nodes, target_cd_nodes)

df_cunt_s_plant_cd = pd.DataFrame(
    [(u, v, count) for (u, v), count in cunt_s_plant_cd.items()],
    columns=['Source', 'Target', 'Count']
)

# Count edges in minimum cut sets for CD - Customer subset
cunt_s_cd_customer = count_edges_in_min_cut_sets(G, source_cd_nodes, target_customer_nodes)

# Create DataFrame for CD - Customer
df_cunt_s_cd_customer = pd.DataFrame(
    [(u, v, count) for (u, v), count in cunt_s_cd_customer.items()],
    columns=['Source', 'Target', 'Count']
)


# Add a column for the subset to each DataFrame
df_cunt_s_plant['Subset'] = 'Supplier-Plant'
df_cunt_s_plant_cd['Subset'] = 'Plant-CD'
df_cunt_s_cd_customer['Subset'] = 'CD-Customer'

# Concatenate the DataFrames
df_all_edges = pd.concat([df_cunt_s_plant, df_cunt_s_plant_cd, df_cunt_s_cd_customer], ignore_index=True)

df_all_edges.to_excel(BASE / 'output/min_cut_count.xlsx')