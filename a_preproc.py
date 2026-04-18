      
      
      
      
import pandas as pd
import sqlite3 as sql
import openpyxl
from os import listdir
from tqdm import tqdm  ### para crear contador en un for para ver evolución



def arc_clas(con,url_arc='data/raw/arcsData.txt'):
    ####Leer info de arcos
    df_arc_ff=pd.read_table(url_arc, header=None,sep=" ")
    df_arc_ff.columns=['origen','destino','demanda','prob_fallo']
    df_arc_ff["arc"]=df_arc_ff['origen'] + ' - ' +df_arc_ff['destino']
    
   
    df_arc_ff.to_sql('info_arc', con, if_exists='replace')
    
    
    return(df_arc_ff)

def set_node_df(con, url_nodes='data/raw/nodesData.txt',url_nodeclas='data/raw/clasificacionArcos.txt'):  
    
    #### leer nombre nodos

    df_nodes=pd.read_table(url_nodes, header=None,sep=" ")
    df_nodes['cod_node']=df_nodes.index
    df_nodes.columns=['name_node','code_node']

    ### leer características nodos

    df_nodes_carc=pd.read_table(url_nodeclas, header=None,sep='&')

    x=df_nodes_carc[0].str.split("/",expand=True)
    x.columns=["Supplier","Plant","CD","Customer"]
    x['Supplier']=x['Supplier'].str.split("[",expand=True)[1]
    x["Supplier"]=x["Supplier"].str.strip()

    y=df_nodes_carc[1].str.split("]",expand=True)
    y1=y[0].str.split("/",expand=True)
    y1.columns=["Supplier","Plant","CD","Customer"]
    y1['Customer']=y1['Customer'].str.strip()
    nodes=y[1].str.split("-",expand=True)
    x_node =nodes[0].str.split("(",expand=True)
    x_node=x_node[1]
    x_node.column=["name_node"]
    y_node=nodes[1].str.split(")", expand=True)[0]

    x["name_node"]=x_node
    y1['name_node']=y_node

    x_y=pd.concat([x,y1], axis=0 )
  

    x_y.replace(['-',' -','-  '],0, inplace=True)
    x_y.replace(['Supplier','Plant','CD','Customer', ' Supplier', 'Customer '],1, inplace=True)
    x_y.drop_duplicates(inplace=True)

    df_nodes= df_nodes.merge(x_y, how='inner')

    df_nodes=df_nodes[['code_node','name_node','Supplier','Plant','CD','Customer']]

    df_nodes.to_sql('info_nodes', con, if_exists='replace')

    return()

def set_arcsce_df(con, url_arcsce='data/3. fullFlexArcos.txt', ):


    # Efficiently parse and store data using lists, avoid repeated DataFrame concatenation
    data = []
    with open(url_arcsce) as f:
        sce = None
        for line in tqdm(f):
            fila = line.split('[')
            if len(fila) == 3:
                sce = fila[0].strip()
                arc_fail = fila[2].replace(']\n', '').strip()
                data.append((sce, arc_fail))
            elif len(fila) == 2 and sce is not None:
                arc_fail = fila[1].replace(']\n', '').strip()
                data.append((sce, arc_fail))
    df_sce = pd.DataFrame(data, columns=["escenario", "arc_fail"])
    df_sce.to_sql("df_arcsce", con, if_exists="replace", index=False)

    return(df_sce)            


def prepro_kpi(url_kpi='data/4. fullFlexKPI.txt'):

    df_ffkpi=pd.read_table(url_kpi, header=None) #leer los datos
    
    df_ffkpi = df_ffkpi[0].str.split('-', expand=True)
    #Funcion lambda funciona como un for que itera y elimina en cada registro o fila los caracteres que le indique
    df_ffkpi[0] = df_ffkpi[0].apply(lambda x : (x[:-1])) #quité escenario
    df_ffkpi[1] = df_ffkpi[1].apply(lambda x : (x[9:]))
    df_ffkpi[1] = df_ffkpi[1].apply(lambda x : (x[:-1]))
    df_ffkpi[2] = df_ffkpi[2].apply(lambda x : (x[28:-1]))
    df_ffkpi[3] = df_ffkpi[3].apply(lambda x : (x[23:-1]))
    df_ffkpi[4] = df_ffkpi[4].apply(lambda x : (x[17:-1]))
    df_ffkpi[5] = df_ffkpi[5].apply(lambda x : (x[21:-1]))
    df_ffkpi[6] = df_ffkpi[6].apply(lambda x : (x[35:])) #no sigue un guón

    #df_ffkpi.set_index(0, inplace = True)
    df_ffkpi = df_ffkpi.rename(columns={0:'escenario',1:'Costo', 2:'Arcos_faltantes',3:'Costo_ventas_perdidas',4:'Ventas_perdidas',5:'Costo_real_de_la_CS',6:'Tiempo_tot_esc'})
    df_ffkpi=df_ffkpi.astype({'Costo':'float','Arcos_faltantes':'int','Costo_ventas_perdidas':'float','Ventas_perdidas':'float','Costo_real_de_la_CS':'float','Tiempo_tot_esc':'int'})
    df_ffkpi.info(verbose=True)
        
    return(df_ffkpi)

              
def set_df_full_arc_sce(con, cur, df_kpi):
     
    cur.execute('''drop table if exists df_all_sce ''')
    cur.execute('''
                create table df_all_sce as
                select distinct escenario
                from df_arcsce
                
                ''')

    cur.execute('''drop table if exists  df_all_arcsce ''')
    cur.execute('''
                create table df_all_arcsce as
                select arc,  escenario
                from info_arc join df_all_sce
                
                ''')   

    cur.execute('''drop table if exists  df_arcsce_count ''')
    
    cur.execute('''
                create table df_arcsce_count as
                select a.arc,  a.escenario, iif(arc_fail is null, 0,1) as arc_fail
                from df_all_arcsce a left join 
                df_arcsce b on a.escenario=b.escenario and a.arc=b.arc_fail         
                ''')        

    #### convertir a wide ####

    df_long_arcsce=pd.read_sql("select * from df_arcsce_count", con)
    df_wide_arcsce=df_long_arcsce.pivot(index='escenario',columns='arc', values='arc_fail')
    df_wide_arcsce.reset_index(inplace=True)
    
    
    df=df_kpi.merge(df_wide_arcsce,how='inner', on="escenario") ### cruzar KPI con arcos fallaron
    
    df.to_sql('kpi_arc_ff', con, if_exists="replace", index=False)


def main():
    
    ##### tablas ####
    #### se demora 20  minutos la función set_arcsce_df 

    ####df_arcsce:  los escenarios con las arcos que fallaron (solo los que fallaron)
    ##### info_arc:  lista de todos los arcos (144) con información origen destino separa, demanda y prob fallo
    #####df_all_sce: lista de todos los escenarios (10080) sin información adicional
    #### df_all_arc_sce:  lista de todos los escenarios y todos los arcosa para cada escenario 
    ####df_arcsce_count: lista de todos los arcos y escenarios con un 1 en los arcos que fallaron y 0 en los que no. (formatto long)
    ##### df_wide_arcsce Una columna por cada arco, 1 si fallo 0 si no y una fila para cada escenario formato wide
    #### Kpi_ff: Kpi escenario fullflex
    #### kpi_arc_ff: unión de kpi_ff con df_wide_arc_sce  es la que queda en base de datos
    
    ## archivos genéricos de la red

    url_arc='data/raw/arcsData.txt'
    url_nodes='data/raw/nodesData.txt'
    url_nodeclas='data/raw/clasificacionArcos.txt'


    path_fail='data/raw'
    path_kpi='data/raw'


    files_in_kpi = sorted(listdir(path_kpi))
    
    
    #kpi=files_in_kpi[0] #para debugging
    for kpi in tqdm(files_in_kpi):
        
        print(f"Procesando escenario: {kpi}")
        arc_reinforced = kpi[4:-4]
        db='data/db/db_'+arc_reinforced.replace('-','_')
        url_kpi=path_kpi + '/' + kpi                    
        url_arcsce=path_fail + '/' + 'fallos_' + arc_reinforced + '.txt'
       
        #print(arc_reinforced, url_kpi, url_arcsce) 
        
        con=sql.connect(db)
        cur= sql.Cursor(con)
        
        count_dbs=pd.read_sql("select name from sqlite_master where type='table'", con).shape[0]
        if count_dbs >  0: 
            continue
        
        arc_clas(con,url_arc)
        set_node_df(con,url_nodes,url_nodeclas)
        set_arcsce_df(con, url_arcsce)
        df_kpi=prepro_kpi(url_kpi) ## generar kpi organizado
        set_df_full_arc_sce(con, cur, df_kpi)
        
        #### depurar base ###
        cur.execute("drop table if exists df_arcsce ")
        cur.execute("drop table if exists df_all_sce ")
        cur.execute("drop table if exists df_all_arcsce ")

        cur.execute("vacuum")
        con.close()
        print(f"Escenario {arc_reinforced} procesado y guardado en {db}")
        
    
main()




### convertir esto a función para que se pueda aplicar para cada escenario
###############  agregar coordenadas y enumerar ########################

db="data/db/db_EstFija10"
con=sql.connect(db)
cur= sql.Cursor(con)

cur.execute("select name from sqlite_master where type='table'")
cur.fetchall()


coord=pd.read_csv('data/processed/Coordenadas.csv')
coord.to_sql('coordenadas', con, if_exists="replace")
pd.read_sql('select*, i as dos from info_nodes', con)
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
                        on a.name_node =b.Name order by Latitude asc""", con)



info_nodes.drop(columns=['code_node'], inplace =True)

info_nodes2.drop('i')

info_nodes2=info_nodes.drop_duplicates(subset="name_node",keep='first')

info_nodes2.reset_index(inplace=True)

info_nodes2['index']+=1

info_nodes2.rename(columns={'index': 'i'}, inplace=True)

info_nodes2.to_sql('info_nodes', con, if_exists='replace', index=False)
cur.execute('drop table if exists info_node2')
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
                        arc 
                        from info_arc)
                        select
                        '(' || b.i || ',' || c.i || ')' AS arc_i_j, 
                        a.*,
                        b.Latitude as latitud_o,
                        b.Longitude as longitud_o,
                        c.Latitude as latitud_d,
                        c.Longitude as longitude_d,
                        b.i as i_o,
                        c.i as i_d
                        from t1 a left join info_nodes b on a.origen=b.name_node left join
                       info_nodes c on a.destino=c.name_node
                        """, con).sort_values(by='prob_fallo')

info_arc=info_arc.drop_duplicates(subset='arc_i_j',keep='first')
info_arc.sort_values('arc_i_j')
info_arc.to_csv('data/processed/info_arc.csv')


info_nodes2.to_csv('data/processed/info_nodes.csv')
info_arc.to_sql('info_arc', con, if_exists='replace')

####

index_node=info_nodes2[['name_node','i']]

index_node.columns=['Node name','index']

index_node=index_node.replace('_', ' ', regex=True)
index_node.to_csv('data/processed/node_index_long.csv', index=False)



n = len(index_node)  # Number of rows
num_parts = 3
rows_per_part = (n + num_parts - 1) // num_parts  # Ceiling division for rows per part

# Reshape into three columns
reshaped_data = []
for i in range(num_parts):
    start_idx = i * rows_per_part
    end_idx = min(start_idx + rows_per_part, n)
    reshaped_data.append(index_node.iloc[start_idx:end_idx].reset_index(drop=True))

# Combine into a single DataFrame with new columns
final_table = pd.concat(reshaped_data, axis=1, keys=[f'Part{i+1}' for i in range(num_parts)])

final_table.to_csv('data/processed/node_index.csv', index=False)
