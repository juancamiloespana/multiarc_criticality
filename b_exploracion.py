
##################################################################
##################################################################
##################Cargar paquetes ################################
##################################################################

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



import os

os.getcwd()

##################################################################
##################################################################
##################Conectarse BD y revisar tablas##################
##################################################################

### conectarse a bds y unir bases

# bds=["data\\DB1\\db_estFija10"]

# cons=[]
# curs=[]


# for i in range(len(bds)):
#     print(i)
#     print(bds[i])
#     con=sql.connect(bds[i]) 
#     cur=con.cursor()
#     cons.append(con)
#     curs.append(cur)


cons=sql.connect('data/db/db_EstFija10')
curs=cons.cursor()

curs.execute("select name from sqlite_master where type='table'")
curs.fetchall()


####### información de nods y arcos es igual para todos los escenarios

info_arc=pd.read_sql("select * from info_arc", cons).sort_values(by='prob_fallo')
info_nodes=pd.read_sql("select * from info_nodes", cons)
info_arc['demanda'].sum()
info_arc.info()

pd.read_sql(""" select * from info_nodes where Supplier =1 """, cons)
pd.read_sql(""" select * from info_nodes where Plant =1 """, cons)
pd.read_sql(""" select * from info_nodes where CD =1 """, cons)
pd.read_sql(""" select * from info_nodes where Customer =1 """, cons)
pd.read_sql(""" select * from info_arc order by prob_fallo desc """, cons).head(20)


info_arc.query('prob_fallo==0')
info_arc.columns
info_arc['arc']
#####Tabla con informacion de arcos y kpis


df=pd.read_sql(" select * from kpi_arc_ff", cons)

# df['esce_prob'] = 'τ =1'
# df1=pd.read_sql(" select * from kpi_arc_ff", cons[1])
# df1['esce_prob'] = 'τ =2'
# df2=pd.read_sql(" select * from kpi_arc_ff", cons[2])
# df2['esce_prob'] = 'τ =3'

df_cum=df.copy()


###validar probabilidades para un arco

arco='Pinchote - Barbosa_Boy'
info_arc[info_arc['arc']==arco]
df[arco].sum()/len(df)
# df1[arco].sum()/len(df1)
# df2[arco].sum()/len(df2)


df_cum['Arcos_faltantes']
########## explorar numero de fallos################


# 1. Set global academic style

matplotlib.rcParams['font.family'] = 'serif'
# Note: Ensure your system has the 'serif' font; otherwise use 'DejaVu Serif'

# 2. Define figure size for a one-column layout
# A standard column width is approx 3.5 inches
plt.figure(figsize=(3.5, 4.5))

# 3. Univariate Boxplot (Y-axis only)
# - color: A single muted blue (#4C72B0) or gray (#7F7F7F) is standard.
# - fliersize: Set to 3 to keep outlier points sharp but not overwhelming.
# - width: Reduced to 0.5 so the box isn't unnaturally wide.
ax = sns.boxplot(
    y='Arcos_faltantes', 
    data=df_cum, 
    showmeans=True,
    color="#4C72B0", 
    width=0.5,
    fliersize=3,
    linewidth=1.2,
    meanprops={
        "marker":"o", 
        "markerfacecolor":"white", 
        "markeredgecolor":"black", 
        "markersize":"5"
    }
)

# 4. Refine Axis and Labels
plt.ylabel('Number of failing arcs', fontsize=10)
plt.yticks(fontsize=9)

# 5. Clean layout
sns.despine(left=True) # Removes the outer frame for a modern journal look
 
# 6. High-Resolution Export (CRITICAL for the "Blurred" comment)
# Save as PDF for LaTeX or 600 DPI PNG for Word.
plt.savefig('imagenes/round_3/closed_arcs.pdf', bbox_inches='tight')
plt.savefig('imagenes/round_3/closed_arcs.png', dpi=600, bbox_inches='tight')

plt.show() 

###########################################

group_data=df_cum['Arcos_faltantes'].agg(['mean', 'max', 'min']).reset_index()
group_data['Arcos_faltantes']=group_data['Arcos_faltantes'].round()


# #######Explorar variable respuesta ########
# sns.set_theme(style="ticks")
# f, ax = plt.subplots(figsize=(6, 4))
# sns.boxplot(x ='Ventas_perdidas', data=df_cum,showmeans=True, whis=[0, 100], width=.6, meanprops={'marker':'o', 'markerfacecolor':'black'} )
# formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M')
# ax.xaxis.set_major_formatter(formatter)
# sns.stripplot( x ='Ventas_perdidas', data=df_cum,size=4, color=".3", alpha=.25, palette='dark')
# # plt.ylabel('Scenario')
# plt.xlabel('Lost sales units')
# plt.show()



#################

sns.set_theme(style="whitegrid", rc={"font.family": "serif"})
fig, ax = plt.subplots(figsize=(6, 4))

# 2. Create the Raincloud Effect
# Note: We use 'cut=0' to keep it clean and 'alpha' to keep it light
# If your seaborn version is older, you can simulate this with 'split=True' in violinplot
sns.violinplot(x='Ventas_perdidas', data=df_cum, inner=None, color="#D9EAD3", 
               alpha=0.3, cut=0, ax=ax, width=0.6)

# Overlay a very thin boxplot
sns.boxplot(
    x='Ventas_perdidas', 
    data=df_cum, 
    showmeans=True, 
    whis=[0, 100], 
    width=0.18, 
    color="#55A868", 
    linewidth=1.2,
    fliersize=2, 
    meanprops={
        "marker":"o", 
        "markerfacecolor":"white", 
        "markeredgecolor":"black", 
        "markersize":"4"
    },
    ax=ax
)

# Add a light strip plot underneath (the "rain")
sns.stripplot(x='Ventas_perdidas', data=df_cum, size=2, color=".3", 
              alpha=0.1, jitter=True, ax=ax)

# 3. Polish
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}M')
ax.xaxis.set_major_formatter(formatter)
plt.xlabel('Lost sales units', fontsize=10)
sns.despine(left=True)
plt.savefig('imagenes/round_3/ventas_perd.png', dpi=600, bbox_inches='tight')
plt.savefig('imagenes/round_3/ventas_perd.pdf', bbox_inches='tight')

plt.show()




################################################################################




group_data=df_cum.groupby('esce_prob')['Ventas_perdidas'].agg(['mean', 'max', 'min']).reset_index()
group_data2=group_data[['mean','max', 'min']]/1000000
group_data2["porc_prom_vp"]= group_data2['mean']/group_data2['max']
group_data2[['mean','min','max','porc_prom_vp']]=group_data2[['mean','min','max','porc_prom_vp']].round(2)



####Escenarios de colapos######


max=np.floor(group_data['max'].max())
df_cum['Ventas_perdidas'].value_counts().sort_index()

s_vp=df_cum[df_cum['Ventas_perdidas']==0].groupby('esce_prob')['escenario'].count() ### 626 escenario sin ventas perdidas
colap=df_cum[df_cum['Ventas_perdidas']>=max].groupby('esce_prob')['escenario'].count()### 591 escenarios con colapso de demanda

n_esce=len(df)

df_colapsos= pd.DataFrame({'n_colapsos':colap, 'n_sin_vp': s_vp}).reset_index()
df_colapsos=df_colapsos.fillna(0)
df_colapsos['porc_colpasos']= (df_colapsos['n_colapsos']/n_esce).round(1)
df_colapsos= df_colapsos[['esce_prob', 'n_colapsos', 'porc_colpasos', 'n_sin_vp']]


df_colapsos['Red']=df_colapsos['esce_prob'] +' ('+df_colapsos['porc_colpasos'].astype(str)+')'
ax=sns.barplot(x='Red', y='n_colapsos', data=df_colapsos, color='green')
ax.bar_label(ax.containers[0])
plt.title('Número de colapsos')


###################


X=df_cum.drop(['escenario','Costo','Ventas_perdidas','Arcos_faltantes','Costo_ventas_perdidas','Costo_real_de_la_CS',"Tiempo_tot_esc"],axis=1)
y=df_cum['Ventas_perdidas']


prob_fallo_sim=X.groupby("esce_prob").sum()/n_esce
prob_fallo_sim=prob_fallo_sim.T
prob_fallo_sim.reset_index(inplace=True)
prob_fallo_sim=prob_fallo_sim.rename(columns={'index':'arc'})
prob_fallo_sim.columns.name = None



prob_fallos=prob_fallo_sim.merge(info_arc[['arc','prob_fallo']], how='inner', on= 'arc' ).sort_values('prob_fallo', ascending=False)
prob_fallos[['estFija10','estFija20', 'estFija30']]=prob_fallos[['estFija10','estFija20', 'estFija30']].round(2)
prob_fallos= prob_fallos[['arc','prob_fallo','estFija10','estFija20', 'estFija30']]


prob_fallos2=prob_fallos.query('prob_fallo >0')
np.mean(prob_fallos2['estFija10'])
np.mean(prob_fallos2['estFija20'])
np.mean(prob_fallos2['estFija30'])

0.24*1.2

##################################################################
##################################################################
##################Explorar Datos################################
##################################################################


##### correlaciones de costos #####



df['Ventas_perdidas'].corr(df['Arcos_faltantes']) ## Las ventas perdidas tienen mayor peso sobre el costo
#df1['Ventas_perdidas'].corr(df1['Arcos_faltantes']) ## Las ventas perdidas tienen mayor peso sobre el costo
#df2['Ventas_perdidas'].corr(df2['Arcos_faltantes']) ## Las ventas perdidas tienen mayor peso sobre el costo

######################################################################

# fig,axes = plt.subplots( figsize=(6, 4))

# ax=sns.scatterplot(x='Arcos_faltantes', y='Ventas_perdidas', palette='viridis',data=df, ax=axes)
# formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M')
# axes.set_xlabel("Number of failing arcs")
# axes.set_ylabel("Lost sales units")
# ax.yaxis.set_major_formatter(formatter)

sns.set_theme(style="ticks", rc={"font.family": "serif"})

fig, ax = plt.subplots(figsize=(4, 4)) # Square aspect ratio is often better for correlations

# 2. Optimized Scatter Plot
# - color='#4C72B0': Matches your previous boxplots/violins
# - alpha=0.3: Solves "difficult to observe points" by showing density through overlap
# - s=15: Smaller point size reduces clutter
# - linewidth=0: Removes point borders to prevent a "blurred" or "heavy" look
sns.scatterplot(
    x='Arcos_faltantes', 
    y='Ventas_perdidas', 
    data=df, 
    color="#55A868", 
    alpha=0.3, 
    s=15, 
    linewidth=0,
    ax=ax
)

# 3. Axis Formatting (Millions for Y-axis)
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}M')
ax.yaxis.set_major_formatter(formatter)

# 4. Clean Labels and Aesthetics
ax.set_xlabel("Number of failing arcs", fontsize=10)
ax.set_ylabel("Lost sales units", fontsize=10)
ax.tick_params(labelsize=9)
sns.despine() # Removes top and right spines for a clean academic look

# 5. High-Resolution Export
# PDF for LaTeX (vector) or 600 DPI PNG

plt.savefig('imagenes/round_3/corr.png', dpi=600, bbox_inches='tight')
plt.savefig('imagenes/round_3/corr.pdf', bbox_inches='tight')

plt.show()



# --- PANEL B: FIGURE 6 (Scatter Plot) ---
sns.scatterplot(
    x='Arcos_faltantes', 
    y='Ventas_perdidas', 
    data=df, 
    color="#55A868", # Emerald Green to match Panel A
    alpha=0.3, 
    s=15, 
    linewidth=0
)

# 3. Unified Formatting
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}M')

# Apply formatting to both Y-axes
for ax in [ax1, ax2]:
    ax.yaxis.set_major_formatter(formatter)
    ax.set_ylabel("Lost sales units", fontsize=10)
    ax.tick_params(labelsize=9)

# Individual X-labels
ax1.set_xlabel("Distribution", fontsize=10)
ax2.set_xlabel("Number of failing arcs", fontsize=10)

# Labeling subfigures (Standard for Journal Papers)
ax1.set_title("(a)", loc='left', fontweight='bold', fontsize=11)
ax2.set_title("(b)", loc='left', fontweight='bold', fontsize=11)

# 4. Final Polish and Spacing
plt.tight_layout(pad=3.0) # Addresses reviewer's comment on 'spacing'
sns.despine(ax=ax1, left=True)
sns.despine(ax=ax2)

# 5. High-Resolution Export

plt.savefig('imagenes/round_3/lost_sales.png', dpi=600, bbox_inches='tight')

plt.show()









######################################################################



ax=sns.scatterplot(x='Arcos_faltantes', y='Ventas_perdidas', color='black',data=df1, ax=axes[1])
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M')
ax.yaxis.set_major_formatter(formatter)
axes[1].set_ylabel("")
axes[1].set_xlabel("τ=2 Number of closed arc")




ax=sns.scatterplot(x='Arcos_faltantes', y='Ventas_perdidas', color='grey',data=df2,ax=axes[2])
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M')
ax.yaxis.set_major_formatter(formatter)
axes[2].set_xlabel("τ=3 Number of closed arc")
axes[2].set_ylabel("")




####### analisis de arcos individuales
## probar nombre de arcos
df_cum["Barranquilla - Barranquilla1"]
df_cum["Girardot - Espinal"]
df_cum["Itagui - La_Felisa"]


# curs.execute(""" create table df_subset1 as 
#                 select *, 
#                 case when "Honda - Mariquita" + "Girardot - Espinal" + "Itagui - La_Felisa" =0 then 1 else 0 end as reinforce_subset1
#                 from kpi_arc_ff """)

pd.read_sql("""select reinforce_subset1,  
            sum(iif(Ventas_perdidas>=36366780,1.0,0.0))/count(*)  as prop_collapse,
            sum(iif(Ventas_perdidas>=36366780,1.0,0.0)) as n_collapse,
            count(*) as n_escenarios,
            avg(Ventas_perdidas) as avg_ventas_perdidas
            from df_subset1 group by reinforce_subset1""", cons)
## tabla con campo para separar 
df_subset1=pd.read_sql("select * from df_subset1", cons)
df_subset1['reinforce_subset1']=df_subset1['reinforce_subset1'].map({0:'Non Reinforced', 1:'Reinforced'})

df_subset1['reinforce_subset1'].value_counts()



############################ new version of subsets with combinaciones de arcos

sns.set_theme(style="whitegrid", rc={"font.family": "serif"})

# 2. Setup Figure - slightly wider to accommodate category labels
fig, ax = plt.subplots(figsize=(6, 4))

# 3. The "Raincloud" Style Components
# Color: Muted Amethyst (#8172B3)
main_color = "#8172B3"
bg_color = "#E6E1F1" # Very light amethyst for the violin background

# LAYER 1: The Violin (Frequency Density)
# Using 'split=True' or 'inner=None' for a clean density shape
sns.violinplot(
    x='Ventas_perdidas', 
    y='reinforce_subset1', 
    data=df_subset1, 
    inner=None, 
    color=bg_color, 
    linewidth=0, 
    cut=0, 
    width=0.7,
    ax=ax
)

# LAYER 2: The Boxplot (Summary)
sns.boxplot(
    x='Ventas_perdidas', 
    y='reinforce_subset1', 
    data=df_subset1, 
    showmeans=True, 
    whis=[0, 100], 
    width=0.15, 
    color=main_color, 
    linewidth=1.2,
    fliersize=0, # Hide outliers because stripplot shows them
    meanprops={"marker":"o", "markerfacecolor":"white", "markeredgecolor":"black", "markersize":"4"},
    ax=ax
)

# LAYER 3: The Stripplot (Raw Points / "Rain")
sns.stripplot(
    x='Ventas_perdidas', 
    y='reinforce_subset1', 
    data=df_subset1, 
    size=3, 
    color=".3", 
    alpha=0.2, 
    jitter=True, 
    ax=ax
)

# 4. Axis Formatting (Millions)
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.1f}M')
ax.xaxis.set_major_formatter(formatter)

# 5. Clean Aesthetics
plt.xlabel('Lost sales units', fontsize=10) # Adjust based on your subset meaning
plt.ylabel('', fontsize=10)
plt.xticks(fontsize=9)
plt.yticks(fontsize=9)
sns.despine(left=True)

# 6. High-Resolution Save
plt.savefig('imagenes/round_3/reinforced.png', dpi=600, bbox_inches='tight')
plt.savefig('imagenes/round_3/reinforced.pdf', bbox_inches='tight')

plt.show()




################################################

#### combinaciones 1

curs.execute("drop table if exists df_subset2")
curs.execute(""" create table df_subset2 as 
                select *, 
                case when "Itagui - La_Felisa"+"Cartago - Buga"+"Palmira - Caloto" =3 then 'Fallaron' else 'No fallaron' end as reinforce_subset2
                from kpi_arc_ff """)


fallas=pd.read_sql("""select reinforce_subset2,  
            sum(iif(Ventas_perdidas>=36366780,1.0,0.0))/count(*)  as prop_collapse,
            sum(iif(Ventas_perdidas>=36366780,1.0,0.0)) as n_collapse,
            count(*) as n_escenarios,
            avg(Ventas_perdidas) as avg_ventas_perdidas
            from df_subset2 group by reinforce_subset2""", cons)

fallas.iloc[0,4] -fallas.iloc[1,4]



#### combinaciones 2

curs.execute("drop table if exists df_subset2")
curs.execute(""" create table df_subset2 as 
                select *, 
                case when "Itagui - La_Felisa"+"Caloto - Popayan" =0 then 'No Fallaron' else 'Fallaron' end as reinforce_subset2
                from kpi_arc_ff """)


fallas=pd.read_sql("""select reinforce_subset2,  
            sum(iif(Ventas_perdidas>=36366780,1.0,0.0))/count(*)  as prop_collapse,
            sum(iif(Ventas_perdidas>=36366780,1.0,0.0)) as n_collapse,
            count(*) as n_escenarios,
            avg(Ventas_perdidas) as avg_ventas_perdidas
            from df_subset2 group by reinforce_subset2""", cons)



para_median = pd.read_sql("select * from df_subset2 ", cons)

para_median.groupby('reinforce_subset2')['Ventas_perdidas'].median()

fallas.iloc[0,4] -fallas.iloc[1,4]




## tabla con campo para separar 
df_subset2=pd.read_sql("select * from df_subset1", cons)
df_subset2['reinforce_subset2']=df_subset1['reinforce_subset1'].map({0:'Non Fortified', 1:'Fortified'})

df_subset2['reinforce_subset2'].value_counts()

sns.set_theme(style="ticks")
f, ax = plt.subplots(figsize=(6, 4))
sns.boxplot(x ='Ventas_perdidas', y='reinforce_subset2', data=df_subset2,showmeans=True, whis=[0, 100], width=.6, meanprops={'marker':'o', 'markerfacecolor':'black'} )
formatter = ticker.FuncFormatter(lambda x, pos: f'{x/1e6:.0f}M')
ax.xaxis.set_major_formatter(formatter)
sns.stripplot( x ='Ventas_perdidas', y='reinforce_subset2', data=df_subset2,size=4, color=".3", alpha=.25, hue='reinforce_subset1', legend=False, palette='dark')
# plt.ylabel('Scenario')
plt.xlabel('Lost sales units')
plt.show()


arcos=df_cum.columns.drop(['escenario','Costo','Ventas_perdidas','Arcos_faltantes','Costo_ventas_perdidas','Costo_real_de_la_CS',"Tiempo_tot_esc"])

df_tot=pd.DataFrame()

for i, arco in enumerate(arcos):
    print(arco)
    print(i)
    df_arco=pd.read_sql(f"""with t1 as (select avg(iif("{arco}" = 1, Ventas_perdidas, null)) as avg_arc_fail,
                avg(iif("{arco}" = 0, Ventas_perdidas, null)) as avg_arc_no_fail,
                sum(iif("{arco}" = 1,1,0 )) as n_arc,
                sum(iif("{arco}" = 0,1,0 )) as n_no_arc
                from kpi_arc_ff )
                select 
                "{arco}" as arc,
                avg_arc_fail - avg_arc_no_fail as impact,
                avg_arc_no_fail as mean_aok,
                avg_arc_fail as mean_af,
                n_no_arc as n_aok, 
                n_arc as n_af 
                from t1""", cons)

    df_tot=pd.concat([df_tot, df_arco], axis=0)

df_tot=df_tot.sort_values(by='impact', ascending=False)
df_tot.to_excel('resultados/subsets_escenarios1/indivEstFija10.xlsx', index=False)
