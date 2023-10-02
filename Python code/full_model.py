#Imports
import gurobipy as gp
from gurobipy import GRB
import pandas as pd

#%% Functions creating dictionary for the parameters
def create_dictionary_from_dataframe_1index(df,a=0,b=1):
    dictionary = {}
    for x in df.itertuples(index=None):
        dictionary [(x[a])] = x[b]
    return dictionary

def create_dictionary_from_dataframe_2index(df,a=0,b=1,c=2):
    dictionary = {}
    for x in df.itertuples(index=None):
        dictionary[(x[a], x[b])] = x[c]
    return dictionary
#%% Data import
excel_sheet =... #Data set excel sheet
ajk_df = pd.read_excel(excel_sheet, sheet_name = 'ajk' )
bi_df =pd.read_excel(excel_sheet, sheet_name = 'bi')
bblk_df =pd.read_excel(excel_sheet, sheet_name = 'bblk')
cij_df =pd.read_excel(excel_sheet, sheet_name ='cij' )
ccqr_df =pd.read_excel(excel_sheet, sheet_name = 'ccqr')
fi_df =pd.read_excel(excel_sheet, sheet_name = 'fi')
ffl_df = pd.read_excel(excel_sheet, sheet_name = 'ffl')
dlk_df =pd.read_excel(excel_sheet, sheet_name ='dlk' )
el_df = pd.read_excel(excel_sheet, sheet_name = 'el')
J_df= pd.read_excel(excel_sheet, sheet_name ='clients' )
I_df =pd.read_excel(excel_sheet, sheet_name ='facilities' )
K_df =pd.read_excel(excel_sheet, sheet_name = 'products')
L_df =pd.read_excel(excel_sheet, sheet_name = 'productionlines')

#%% parameter creation
ajk = create_dictionary_from_dataframe_2index(ajk_df) #demand 
bi = create_dictionary_from_dataframe_1index(bi_df) #capacity facility i
bblk = create_dictionary_from_dataframe_2index(bblk_df) #capacity production line l
cij = create_dictionary_from_dataframe_2index(cij_df) #transport cost i to j
ccqr = create_dictionary_from_dataframe_2index(ccqr_df)# transport cost i to i
fi = create_dictionary_from_dataframe_1index(fi_df) #fixed cost facility i
ffl= create_dictionary_from_dataframe_1index(ffl_df) #fixed cost production line l
dlk = create_dictionary_from_dataframe_2index(dlk_df) #production cost k
el = create_dictionary_from_dataframe_1index(el_df) #size production line l
ee = 800     # Truck capacity 
M1 = 10    #big m 

#Index creation
I = int(I_df['I'].max()+1)
J = int(J_df['J'].max()+1)
K = int(K_df['K'].max()+1)
L = int(L_df['L'].max()+1)


#%% Model creating
model = gp.Model("Facility_location")


#%% Decision variables
yi = model.addVars(I,lb=0,vtype=GRB.BINARY,name="y_i",ub=1)
yyli = model.addVars(L,I,lb=0, vtype=GRB.INTEGER, name='yy_li')
xij = model.addVars(I,J,lb=0,vtype=GRB.BINARY, name="x_ij",ub=1)
xxqr = model.addVars(I,I,lb=0, vtype=GRB.INTEGER, name="x_qr")
zkli = model.addVars(K,L,I,lb=0,vtype=GRB.INTEGER, name= "z_kli")
wkqr = model.addVars(K,I,I,lb=0,vtype=GRB.INTEGER, name = "w_kqr")


#%% total facility cost + production cost
A1=gp.quicksum(fi[i]*yi[i] for i in range(I)) #fixed building cost
A2=gp.quicksum(ffl[l]*yyli[l,i]for l in range(L) for i in range(I)) #fixed productionline costs
A3=gp.quicksum(dlk[l,k]*zkli[k,l,i] for k in range(K) for l in range(L)for i in range (I)) #production cost
A = A1+A2+A3 


#%% transport costs
B=gp.quicksum(cij[i,j]*xij[i,j]for i in range(I) for j in range(J)) #client transport
C=gp.quicksum(ccqr[q,r]*xxqr[q,r] for q in range(I) for r in range(I)) #intern transport


#%% Objective function
model.setObjective(A+B+C,GRB.MINIMIZE)

#%% constraints
# single source constraint
for j in range(J):
    model.addConstr(gp.quicksum(xij[i,j] for i in range(I))==1)

#no production lines if yi is not open (big M constraint)
for i in range(I):
    model.addConstr(gp.quicksum(yyli[l,i] for l in range(L)) <= M1 * yi[i])
    #no transport if yi is not open
    for j in range (J):
        model.addConstr(xij[i,j]<=yi[i])

# flow constraint
for i in range(I):
    for k in range(K):
        model.addConstr(gp.quicksum(zkli[k,l,i]for l in range(L)) + gp.quicksum(wkqr[k,q,i] for q in range(I)) - gp.quicksum(wkqr[k,i,r] for r in range(I))- gp.quicksum(ajk[j,k]*xij[i,j] for j in range(J))>=0)

# capacity constraint facility
for i in range(I):
    model.addConstr(gp.quicksum(el[l]* yyli[l,i] for l in range(L))<=bi[i])

#capacity production line
for i in range(I):
    for k in range(K):
        for l in range(L):
            model.addConstr(zkli[k,l,i]<= bblk[l,k]*yyli[l,i])
            
#truck constraint
for q in range(I):
    for r in range(I):
        model.addConstr(gp.quicksum(wkqr[k,q,r]for k in range(K))/(ee) <= xxqr[q,r])


#%% optimzing parameters
model.setParam('OutputFlag', 1) #console output
model.Params.TimeLimit =... #setting time limit
model.Params.PoolSearchMode = 1

model.optimize()

#objective function printing
print(A.getValue())
print(B.getValue())
print(C.getValue()) 
print((B.getValue()+C.getValue())/(A.getValue()+B.getValue()+C.getValue()))

#model.write("namesolution.sol") used to write a sol/lp file.