from pathlib import Path
from geopy.geocoders import Nominatim

BASE = Path(__file__).parent


### paquetes con operaciones básicas y sql 
import pandas as pd
import sqlite3 as sql ##para conectarse a bd, traer y manipular info con sql
import numpy as np
import math ### para floor y ceil

#### para hacer gráficas

import plotly.express as px

import seaborn as sns

import matplotlib.pyplot as plt

from statistics import linear_regression
from tabnanny import verbose
#import streamlit as st


import plotly.graph_objects as go
import matplotlib
import matplotlib.ticker as ticker

#### para mapas

import folium as fo



bds=[BASE / "data/db/db_EstFija10"]

con=sql.connect(bds[0]) 
cur=con.cursor()

cur.execute("select name from sqlite_master where type='table'")
cur.fetchall()

##################Cargar coordenadas

coord=pd.read_csv(BASE / 'data/processed/Coordenadas.csv')
coord.to_sql('coordenadas', con, if_exists="replace")
####### información de nods y arcos es igual para todos los escenarios

info_nodes=pd.read_sql("""with t1 as ( 
                       select 
                       code_node,
                       case when name_node = 'Bogota1' then 'Bogota'
                        when name_node = 'Bogota2' then 'Bogota'
                        when name_node = 'Barranquilla1' then 'Barranquilla'
                        when name_node = 'Ibague1' then 'Ibague'
                        when name_node = 'Medellin1' then 'Medellin'
                        when name_node = 'Pereira1' then 'Pereira' else name_node
                        end as name_node,
                        Supplier,
                        Plant,
                        CD,
                        Customer
                        from info_nodes)
                        select 
                        a.*, b.Latitude as latitude, 
                        b.Longitude as longitude  
                        from t1 a left join 
                        coordenadas b 
                        on a.name_node =b.Name """, con)



#################info arcos

info_arc=pd.read_sql(""" with t1 as( 
                     select 
                     case when origen = 'Bogota1' then 'Bogota'
                        when origen = 'Bogota2' then 'Bogota'
                        when origen = 'Barranquilla1' then 'Barranquilla'
                        when origen = 'Ibague1' then 'Ibague'
                        when origen = 'Medellin1' then 'Medellin'
                        when origen = 'Pereira1' then 'Pereira' else origen
                        end as origen,
                        case when destino = 'Bogota1' then 'Bogota'
                        when destino = 'Bogota2' then 'Bogota'
                        when destino = 'Barranquilla1' then 'Barranquilla'
                        when destino = 'Ibague1' then 'Ibague'
                        when destino = 'Medellin1' then 'Medellin'
                        when destino = 'Pereira1' then 'Pereira' else destino
                        end as destino,
                        demanda,
                        prob_fallo,
                        arc from info_arc)
                        select  
                        a.*,
                        b.Latitude as latitud_o,
                        b.Longitude as longitud_o,
                        c.Latitude as latitud_d,
                        c.Longitude as longitude_d
                                                from t1 a left join coordenadas b on a.origen=b.Name left join
                        coordenadas c on a.destino=c.Name
                        """, con).sort_values(by='prob_fallo')


info_arc.to_csv(BASE / 'data/processed/info_arc.csv')
info_nodes.to_csv(BASE / 'data/processed/info_nodes.csv')

info_arc.isna().sum()



###############################



# Create a base map
my_map = fo.Map(location=[info_nodes.iloc[2,6], info_nodes.iloc[2,7]], zoom_start=4)

# Add markers for each location
for location in info_nodes.index:
    fo.CircleMarker([info_nodes.iloc[location,6], info_nodes.iloc[location,7]], popup=info_nodes.iloc[location,2],
             radius=5).add_to(my_map)
    


for location in range(len(info_arc)):
    coord_o = [info_arc.iloc[location,5],info_arc.iloc[location,6] ]
    coord_d = [info_arc.iloc[location,7],info_arc.iloc[location,8] ]
    fo.PolyLine(
                [coord_o, coord_d],
                color="green",
                weight=1,
                opacity=1).add_to(my_map)
    

    
    


# Save the map as an HTML file or display it
my_map.save("map_with_points.html")



#####


# Create a base map
my_map2 = fo.Map(location=[info_nodes.iloc[2,6], info_nodes.iloc[2,7]], zoom_start=4)

# Add markers for each location
for location in info_nodes.index:
    fo.CircleMarker([info_nodes.iloc[location,6], info_nodes.iloc[location,7]], popup=info_nodes.iloc[location,2],
             radius=5, color='green').add_to(my_map2)
    
location=1

for location in range(len(info_arc)):
    coord_o = [info_arc.iloc[location,5],info_arc.iloc[location,6] ]
    coord_d = [info_arc.iloc[location,7],info_arc.iloc[location,8] ]
    
    if ((info_arc.iloc[location,0] == 'Girardot' and  info_arc.iloc[location,1] == 'Espinal') or
        (info_arc.iloc[location,0] == 'Honda' and  info_arc.iloc[location,1] == 'Mariquita') or
        (info_arc.iloc[location,0] == 'Itagui' and info_arc.iloc[location,1] == 'La_Felisa')   
    ):
        fo.PolyLine(
                [coord_o, coord_d],
                color="red",
                weight=3,
                opacity=1).add_to(my_map2)
    else:
    
        fo.PolyLine(
                    [coord_o, coord_d],
                    color="black",
                    weight=1,
                    opacity=1).add_to(my_map2)
    
    
    

    
    


# Save the map as an HTML file or display it
my_map2.save("map_with_pointsset1.html")





# Create a base map
my_map2 = fo.Map(location=[info_nodes.iloc[2,6], info_nodes.iloc[2,7]], zoom_start=4)

# Add markers for each location
for location in info_nodes.index:
    fo.CircleMarker([info_nodes.iloc[location,6], info_nodes.iloc[location,7]], popup=info_nodes.iloc[location,2],
             radius=5, color='green').add_to(my_map2)
    
location=1

for location in range(len(info_arc)):
    coord_o = [info_arc.iloc[location,5],info_arc.iloc[location,6] ]
    coord_d = [info_arc.iloc[location,7],info_arc.iloc[location,8] ]
    
    if ((info_arc.iloc[location,0] == 'Caloto' and  info_arc.iloc[location,1] == 'Popayan') or
        (info_arc.iloc[location,0] == 'Mariquita' and  info_arc.iloc[location,1] == 'Manizales') or
        (info_arc.iloc[location,0] == 'Ibague' and info_arc.iloc[location,1] == 'Armenia') or
        (info_arc.iloc[location,0] == 'Itagui' and info_arc.iloc[location,1] == 'La_Felisa')    
    ):
        fo.PolyLine(
                [coord_o, coord_d],
                color="red",
                weight=3,
                opacity=1).add_to(my_map2)
    else:
    
        fo.PolyLine(
                    [coord_o, coord_d],
                    color="black",
                    weight=1,
                    opacity=1).add_to(my_map2)
    
    
    

    
    


# Save the map as an HTML file or display it
my_map2.save("map_with_points_set2.html")



# Create a base map
my_map2 = fo.Map(location=[info_nodes.iloc[2,6], info_nodes.iloc[2,7]], zoom_start=4)

# Add markers for each location
for location in info_nodes.index:
    fo.CircleMarker([info_nodes.iloc[location,6], info_nodes.iloc[location,7]], popup=info_nodes.iloc[location,2],
             radius=5, color='green').add_to(my_map2)
    
location=1

for location in range(len(info_arc)):
    coord_o = [info_arc.iloc[location,5],info_arc.iloc[location,6] ]
    coord_d = [info_arc.iloc[location,7],info_arc.iloc[location,8] ]
    
    if ((info_arc.iloc[location,0] == 'Caloto' and  info_arc.iloc[location,1] == 'Popayan') or
        (info_arc.iloc[location,0] == 'Manizales' and  info_arc.iloc[location,1] == 'Pereira') or
        (info_arc.iloc[location,0] == 'Ibague' and info_arc.iloc[location,1] == 'Armenia') or
        (info_arc.iloc[location,0] == 'La_Felisa' and info_arc.iloc[location,1] == 'Cartago')    
    ):
        fo.PolyLine(
                [coord_o, coord_d],
                color="red",
                weight=3,
                opacity=1).add_to(my_map2)
    else:
    
        fo.PolyLine(
                    [coord_o, coord_d],
                    color="black",
                    weight=1,
                    opacity=1).add_to(my_map2)
    
    
    

    
    


# Save the map as an HTML file or display it
my_map2.save("map_with_points_set3.html")









# Create a base map
my_map2 = fo.Map(location=[info_nodes.iloc[2,6], info_nodes.iloc[2,7]], zoom_start=4)

# Add markers for each location
for location in info_nodes.index:
    fo.CircleMarker([info_nodes.iloc[location,6], info_nodes.iloc[location,7]], popup=info_nodes.iloc[location,2],
             radius=5).add_to(my_map2)
    
location=1

for location in range(len(info_arc)):
    coord_o = [info_arc.iloc[location,5],info_arc.iloc[location,6] ]
    coord_d = [info_arc.iloc[location,7],info_arc.iloc[location,8] ]
    
    if ((info_arc.iloc[location,0] == 'Bogota' and  info_arc.iloc[location,1] == 'Fusa') or
        (info_arc.iloc[location,0] == 'Madrid' and  info_arc.iloc[location,1] == 'Girardot') or
        (info_arc.iloc[location,0] == 'Itagui' and info_arc.iloc[location,1] == 'La_Felisa') or
        (info_arc.iloc[location,0] == 'Honda' and info_arc.iloc[location,1] == 'Mariquita')    
    ):
        fo.PolyLine(
                [coord_o, coord_d],
                color="red",
                weight=3,
                opacity=1).add_to(my_map2)
    else:
    
        fo.PolyLine(
                    [coord_o, coord_d],
                    color="green",
                    weight=1,
                    opacity=1).add_to(my_map2)
    
    
    

    
    


# Save the map as an HTML file or display it
my_map2.save("map_with_points_set4.html")
