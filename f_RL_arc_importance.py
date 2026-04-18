
from pathlib import Path
### paquetes con operaciones básicas y sql
import pandas as pd
import sqlite3 as sql ##para conectarse a bd, traer y manipular info con sql
import numpy as np
import itertools

BASE = Path(__file__).parent

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score



cons=sql.connect(BASE / 'data/db/db_EstFija10')
curs=cons.cursor()

curs.execute("select name from sqlite_master where type='table'")
curs.fetchall()



df=pd.read_sql(" select * from kpi_arc_ff", cons)

X=df.drop(['escenario','Costo','Ventas_perdidas','Arcos_faltantes','Costo_ventas_perdidas','Costo_real_de_la_CS',"Tiempo_tot_esc"],axis=1)
y=df['Ventas_perdidas']


model = LinearRegression(fit_intercept=False)
model.fit(X,y)  


y_pred = model.predict(X)
mse = mean_squared_error(y, y_pred)
rmse=np.sqrt(mse)
np.mean(y)
# Create a DataFrame with feature names and coefficients, sorted descending by coefficient value
coef_df = pd.DataFrame({
    'feature': model.feature_names_in_,
    'coefficient': model.coef_
}).sort_values(by='coefficient', ascending=False).reset_index(drop=True)

coef_df.to_excel(BASE / "output/post_processing/rl_arc_importance.xlsx", index=False)


coef_10=coef_df.head(10)
# For combinations of 3 and 4 features
combinations = []

for subset in itertools.combinations(coef_10['feature'], 3):
    sum_coefficients = coef_10[coef_10['feature'].isin(subset)]['coefficient'].sum()
    combinations.append({
        'subset': ', '.join(subset),
        'sum_coefficients': sum_coefficients
    })

comb_df = pd.DataFrame(combinations)
comb_df = comb_df.sort_values(by='sum_coefficients', ascending=False).reset_index(drop=True)
comb_df.to_excel(BASE / "output/post_processing/rl_arc_importance_combinations.xlsx", index=False)
