import numpy as np
import pandas as pd
import sqlite3 as sql

from sklearn import metrics
import matplotlib.pyplot as plt ### gráficos
from sklearn.model_selection import train_test_split

from sklearn.ensemble import RandomForestRegressor

from sklearn.feature_selection import VarianceThreshold

import _funciones as fn
from sklearn import tree
from sklearn.tree import export_text 
import openpyxl
from os import listdir ### para hacer lista de archivos en una ruta
from tqdm import tqdm  ### para crear contador en un for para ver evolución



###################Lista de nodos con mayor proporcion de fallos #############
#######################################################################
def prior_nodes ( mod, n_prior=10,):

    n_nod=mod.tree_.node_count ## número de nodos
    nodos=mod.tree_.value.reshape([n_nod,]) ###  observaciones categoria 0, obse cat 1
    nodos_mas_f=(-nodos).argsort()[0:n_prior] #### definir número de nodos a priorizar
    nodos[nodos_mas_f] ### para promar mayor en indicador

    nodos_prio= pd.DataFrame()

    nodos_prio['kpi']=nodos[nodos_mas_f]
    nodos_prio['ind_nodo']=nodos_mas_f
    nodos_prio['n'] = mod.tree_.n_node_samples[nodos_mas_f]

    #nodos_prio.to_excel('resultados\\nodos_prio.xlsx')

    return nodos_prio

    


#####################Extraer las interacciones ###############
def arcs_failed(nodo, mod, x_train):
    #x_train=X2 ## para pruebas
    #nodo=nodes_list[1] ### para pruebas
    dp=mod.decision_path(x_train) ### decision path 

    #dp.indices.shape ##el camino para llegar al nodo final de esa observacion, se repite la observacion por cada nodo en el que está
    #dp.indptr.shape ### el indice en el que arrancha el camino de cada observación 



    indice_fin=np.where(dp.indices==nodo)[0][0] ### en qué indice de nodos está el nodo seleccionado
  
    dif=[x for x in indice_fin-dp.indptr if x>0]

    pos_ini=np.argmin(dif) ### indica la posicion de indptr en la que está el indice inicial (el cero más cercano para determinar el path)
    indice_ini=dp.indptr[pos_ini] ## extraer el indice en el que arranca el path

    #dp.indices[indice_ini:(indice_fin+1)] ## para comprobar que el numero del nodo según el indice coincide con el seleccionado

    nodes_path=dp.indices[indice_ini:(indice_fin+1)] ## crea una lista con el camino desde 0 al nodo indicado

    l_ind_var=[] ## crear lista de variables para generar el nodo
   

    deep=len(nodes_path) -1 ### cuantos nodos para llegar al seleccionado

    for i in range(deep,-1,-1):  ## desde el nodo final hasta el raiz
        if mod.tree_.children_right[nodes_path[i-1]] == nodes_path[i]: ### para verificar si la variable si el arco falló
            ind_var=mod.tree_.feature[nodes_path[i-1]] ###guardar el número de la variable(arco)
            l_ind_var.append(ind_var) ### agregar arco a lista de arcos que fallaron
           
    if not l_ind_var: ## si ningun arco falló dejar interacción vacía
        inter=[] 
    else:
        rows=x_train.shape[0] ## número de filas para crear vector de 1
        inter=[1]*rows ## vector de 1 para agregar primera interacción con multiplicación
        name_inter="" ### inicalizar variable con nombre de interacciones
        
        for i in l_ind_var:
            inter=inter*x_train[x_train.columns[i]] ## crea interación multiplicando todos los arcos que fallaron
            name_inter+= x_train.columns[i]+"/" ### crea el nombre agregando los nombres de los arcos

    name_inter= name_inter[:-1]
    return l_ind_var, inter, name_inter



#### esta función aplica la extracción de todas las interacciones de los nodos priorizados
def inter_all_nodes(mod, x_train, n_prior=10 ):

    nodos_prior= prior_nodes(mod, n_prior)

    nodes_list= nodos_prior['ind_nodo'].values


    l_failed=[]
    l_inter=[]
    l_name=[]

    for i in nodes_list:
        
        failed, inter, name=arcs_failed(i, mod, x_train)
        l_failed.append(failed)
        l_inter.append(inter)
        l_name.append(name)
        
        interDF=pd.DataFrame(l_inter).T
        interDF.columns = l_name

        
        
        
    return l_failed, interDF , nodos_prior
        


 ####### evaluación de interacciones
 
 
def dif_prop(var_name, X2, y):
    
    
    ##var_name=X_intera.columns[140] ##para pruebas
    ##arcs=X_intera[var_name]
    arcs=X2[var_name]
    
    m_aok=np.mean(y[arcs==0])
    m_af=np.mean(y[arcs==1])
    sd_aok=np.std(y[arcs==0])
    sd_af=np.std(y[arcs==1])
    
    n_aok=np.count_nonzero(arcs==0)
    n_af=np.count_nonzero(arcs==1)
  
    dif_arc =m_af-m_aok



    
     
    return(dif_arc, m_aok ,m_af, sd_aok,sd_af,n_aok,n_af)


def todos_arcs(X2, y):
    
    dif_tot=pd.DataFrame()
    
    

    
    for var_n in X2.columns:
    
        dif_arc, m_aok ,m_af, sd_aok,sd_af,n_aok,n_af = dif_prop(var_n, X2, y)
        dif=pd.DataFrame([{'arc':var_n,
                          'dif_arc': dif_arc, 
                          'mean_aok':m_aok,
                          'mean_af': m_af, 
                          'sd_aok':sd_aok,
                          'sd_af':sd_af,
                          'n_aok':n_aok,
                          'n_af':n_af
                           }])
        dif_tot=pd.concat([dif_tot, dif])
        
    
    
    
    dif_tot.sort_values('dif_arc', ascending=False)
    dif_tot.iloc[:,1:]=dif_tot.iloc[:,1:].round()
            
    
    return dif_tot
        


#### filtrar arcos sin probabilidad de fallo

def analizar_comb(X, y):
    sel=VarianceThreshold()
    X2=sel.fit_transform(X)
    colum_out=sel.get_feature_names_out()
    X2=pd.DataFrame(X2, columns=colum_out)
    #X2.info(verbose=True)

    ### numero de escenarios que se consdiran significativos
    n_min_sce=30 ## param

    mod=tree.DecisionTreeRegressor( min_samples_leaf=n_min_sce)
    mod.fit(X2, y)

    y_arr=np.array(y)
    ###### evaluar modelo #########################
    #pred=mod.predict(X2)

    # metrics.mean_absolute_error(y, pred)
    # np.mean(y)

    # metrics.PredictionErrorDisplay.from_predictions(y_arr,pred, kind='residual_vs_predicted')
    # metrics.PredictionErrorDisplay.from_predictions(y_arr,pred, kind='actual_vs_predicted')

    # plt.figure(figsize=(100,100))
    # tree.plot_tree(mod,fontsize=10,impurity=False,filled=True,node_ids=True)
    # plt.show()


    ##### uso de las funciones

    l_failed, interDF, nodos_prior = inter_all_nodes(mod, X2, 10)
    X_intera=pd.concat([X2,interDF], axis=1)
    comp= todos_arcs(X_intera, y_arr)
    
    comp.sort_values('dif_arc', ascending=False, inplace=True)
    
    return comp

 


########### probar en escenarios #####


def main():
    dbs_path='data/db'
    results_path='resultados/subsets_escenarios1'

    dbs=listdir(dbs_path)

    # db=dbs[1] ### for debugging
    ### conectarse a bd
    for db in tqdm(dbs):
        esc=db[3:] ### extraer nombre del escenario 
        if os.path.exists(results_path + '/' + 'subsets_' + esc+ '.xlsx'):
            print(f"Escenario {esc} was already processed and output file exist in {results_path}")
            continue
        

        print(f"Processing scenario: {esc}")

        bd=dbs_path + '/' + db
    

        con=sql.connect(bd) 
        cur=con.cursor()
        #con.close()
        #cur.close()
        cur.execute("select name from sqlite_master where type='table'")
        cur.fetchall()

        pd.read_sql("select count(distinct arc) from df_arcsce_count limit 10", con)
    ##### cargar base de datos ####
        df=pd.read_sql(" select * from kpi_arc_ff", con)

        #### separar base de detos
        X=df.drop(['escenario','Costo','Ventas_perdidas','Arcos_faltantes','Costo_ventas_perdidas','Costo_real_de_la_CS',"Tiempo_tot_esc"],axis=1)
        y=df['Ventas_perdidas']

        

        try:
            comp_estFijo=analizar_comb(X,y)
            output_file = results_path + '/' + 'subsets_' + esc + '.xlsx'
            comp_estFijo.to_excel( output_file, index=False)
        except Exception as e:
            print(f"Error processing scenario {esc}: {e}")


main()







##### arbol imprimir

### numero de escenarios que se consdiran significativos
n_min_sce=30 ## param

mod=tree.DecisionTreeRegressor( min_samples_leaf=n_min_sce, max_depth=3)
mod.fit(X, y)



plt.figure(figsize=(18,18))
tree.plot_tree(mod,fontsize=10,impurity=False,filled=True,node_ids=True)
plt.show()
