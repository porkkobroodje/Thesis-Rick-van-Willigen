#Imports
import time

# Record the start time
start_time = time.time()


#Imports
import gurobipy as gp
from gurobipy import GRB
import pandas as pd
import random
import os
import numpy as np




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

results = 10
test = 0
for test in range(results):
    model = gp.Model("Facility_location")
    model.remove(model.getVars())
    model.remove(model.getConstrs())   
    start_time = time.time()
           
    #%% Data import
    excel_sheet = r"C:\Users\924351\Documents\Thesis\Data resutls\MediumSet5.xlsx"
    #excel_sheet = r"C:\Users\924351\Documents\Thesis\Data resutls\MediumSetOriginal.xlsx"
    
    
    #excel_sheet = r"C:\Users\924351\Documents\Thesis\Data resutls\LargeSet.xlsx"
 
    
    #excel_sheet =r"C:\Users\924351\Documents\Thesis\Data resutls\MediumSetOriginal - Copy.xlsx"
    
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
    M1 = 10 #big m constraint
    
    #Index creation
    I = int(I_df['I'].max()+1)
    J = int(J_df['J'].max()+1)
    K = int(K_df['K'].max()+1)
    L = int(L_df['L'].max()+1)
    
    
    #%% Model creating
    
    
    
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
    def create_constraints():
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
    create_constraints()
    #%% optimzing parameters
   
    def solution_limit_callback(model, where):
        if where == GRB.Callback.MIPNODE:
            if model.cbGet(GRB.Callback.MIPNODE_SOLCNT) >= 40: #10 for large 40 for medium
                model.terminate()
                    
    model.Params.TimeLimit =600
     #max time running
    model.params.PoolSolutions = 40#for large
    model.Params.PoolSearchMode = 1
    model.setParam('OutputFlag', 0) #console output
    model.optimize(solution_limit_callback)
    print("creating feasible solutions completed")
    print(model.SolCount, 'solutions created')
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.4f} seconds")
    #%% genetic algorithm
    genes_population_l = []
    score_population_l =[]
    
    def split_and_merge(arr1, arr2):
        # Ensure both arrays have the same shape
        assert arr1.shape == arr2.shape, "Input arrays must have the same shape."
    
        # Get the length of the arrays
        array_length = arr1.shape[0]
    
        # Choose a random split point (index) for the arrays
        split_point = random.randint(1, array_length - 1)
    
        # Split and merge the arrays
        new_array = np.concatenate((arr1[:split_point], arr2[split_point:]))
    
        return new_array
    
    
    
    def Create_new_chromosome_and_mutate(genes_population_a,fitness_population): ###DIT MOET NOG BETER WANT MUTEREN DOET EIGENLIJ NIKS OULE
    
    
            parent1 = genes_population_a[random.choices(np.arange(0,len(fitness_population)), weights=fitness_population)[0]]
            parent2 = genes_population_a[random.choices(np.arange(0,len(fitness_population)), weights=fitness_population)[0]]
            
            yyli_gene_1 = parent1[I:I+L*I]
            yyli_gene_2 = parent2[I:I+L*I]
            
            
            new_chromosome = split_and_merge(yyli_gene_1,yyli_gene_2)
            for i in new_chromosome:
                if random.random() < 0.1:
                            if i == 0:
                                new_chromosome[i] += random.randint(0,2)
                            else:
                                new_chromosome[i] += random.randint(-1, 1)
            return new_chromosome
    
    for solution_number in range(model.SolCount):
        model.setParam('SolutionNumber', solution_number)
        
        gene = model.getAttr('Xn')
        genes_population_l.append(gene[:(I+L*I+I*J)])#to only select till the last xij variable the rest will be filled by gurobi
        
        score = model.getAttr('PoolObjVal')
        score_population_l.append(score)
    
    
    
    print('Lowest found feasible solutions', min(score_population_l))
    generation = 0
    best_found = min(score_population_l)
    #model.setParam('OutputFlag', 1) #console output
    while generation < 5:  
        
        #print('total sum population', sum(score_population_l))
        
        
        
        new_genereation_objectivevalue = []
        new_generation_gene=[]
                
        #### using the new generation into the model ####
        model.Params.TimeLimit = 10 #60 large, 10 medium
        model.Params.MIPGap = 0.4
        model.params.PoolSolutions = 1
        model.Params.PoolSearchMode = 0
        new_generation_size = 15
        size_new_generation = 0
        model_status_list = []
        cyclecount = 0
        
        #while size_new_generation < new_generation_size:
        genes_population_a = np.array(genes_population_l,dtype='i')
        score_population_a = 1/np.array(score_population_l,dtype='f') #inverse because you want the lower values to have better fitness
        sum_score_generation = score_population_a.sum()
        fitness_population  = score_population_a/sum_score_generation 
        
        
        
        yyli_chromosome = Create_new_chromosome_and_mutate(genes_population_a, fitness_population)
        model.reset()
        
        
        #if production lines are at facility i 
        facilities_with_productionlines = []
        for facilities in range(I):
            current_sum= sum(yyli_chromosome[facilities::I])
            facilities_with_productionlines.append(current_sum)
        
        open_facilities = [1 if productionlines != 0 else 10000 for productionlines in facilities_with_productionlines]
        
        cij = cij_df.iloc[:,2]
    
        lowest_cost_list = []
    
        for client in range(J):
            costs_for_client = list(cij[client::J])
            adjusted_cost= []
            for location in range(len(open_facilities)):
                adjusted_cost.append(costs_for_client[location]*open_facilities[location])
            index_lowest_cost =costs_for_client.index(min(adjusted_cost))
            lowest_cost_list.append(index_lowest_cost)
        
        correct_index_list = []
        for facility in range(J):
            correct_index = J*lowest_cost_list[facility] + facility +I+L*I
            correct_index_list.append(correct_index)
        
        
        
        counteryyli = 0
        for i,v in enumerate(model.getVars()):
            if i < (I):
                if open_facilities[i] == 1:
                    v.Start =1 
                else:
                    model.addConstr(v == 0)
                
            elif i < (I+L*I):
                #if yyli_chromosome[counteryyli] == 0:
                #    model.addConstr(v == 0)
                #else:
                 #   v.Start = yyli_chromosome[counteryyli]
                
                model.addConstr(v == yyli_chromosome[counteryyli])
                counteryyli +=1
              
            elif i < (I+L*I+I*J):
                if i in correct_index_list:
                    v.Start = 1
                    #model.addConstr(v == 1)
                else:
                    v.Start = 0
                    #model.addConstr(v==0)
        
    
            
        
                 
        model.optimize()
        model_status_list.append(model.status)
        if model.status != 3 : #13 | 2:
            new_gene = model.getAttr('X')
            new_score = model.getAttr('ObjVal')
            print(new_score)
           
            if any(new_gene[:(I+L*I+I*J)] == old_genes for old_genes in genes_population_l)== False:
                genes_population_l.append(new_gene[:(I+L*I+I*J)])
                score_population_l.append(new_score)
                #new_generation_gene.append(model.getAttr('X'))
                #new_genereation_objectivevalue.append(model.getAttr('ObjVal'))
                size_new_generation +=1
            if min(score_population_l) < best_found:
                 best_found = min(score_population_l)
                 generation =0
                 best_gene = model.getAttr('X')
            else:
                 generation +=1 
        model.remove(model.getConstrs())
        
        create_constraints()
        
        #if cyclecount % 100 ==0 :
        #    print(cyclecount)
        #    cyclecount +=1
        #print('lowest found score',min(score_population_l))
        
        
        
        ###sorting genes to the scores####
        genes_score_combined = zip(genes_population_l,score_population_l)
        sorted_genes_score_combined = sorted(genes_score_combined,key=lambda x: x[1])
        genes_population_l, score_population_l = map(list,zip(*sorted_genes_score_combined)) #the *zip function retruns tuples with map and lists you can make it return lists, if not it errors at creating an array.
        genes_population_l = genes_population_l[:30]
        score_population_l= score_population_l[:30]
        
        
        #genes_population_l = new_generation_gene
        #score_population_l =new_genereation_objectivevalue
    
    print('lowest found score',min(score_population_l))
    
# =============================================================================
#     model.reset()
#     for i,v in enumerate(model.getVars()):  
#         v.Start = best_gene[i]
#     
#   
#     model.Params.TimeLimit =60
#      #max time running
#   
#     model.setParam('OutputFlag', 1)
#     model.optimize()
# =============================================================================
    #%% writin files 
    # =============================================================================
    # file_prefix = "testing feasible solutions"
    # map_name = "feasible_solutions"
    # # Loop over each solution in the pool
    # for solution_number in range(model.SolCount):
    # 
    #     # Get the variable values for the current solution
    #     model.setParam('SolutionNumber', solution_number)
    #    
    # 
    #     # Create a file name for the current solution
    #     file_name = os.path.join(map_name, f"{file_prefix}_{solution_number}.sol")
    #     model.write(file_name)
    #     # Write the variable values to the solution file
    #     #with open(file_name, 'w') as file:
    #       #  for var, value in zip(model.getVars(), variable_values):
    #        #     file.write(f"{var.VarName} = {value}\n")
    # 
    # =============================================================================
    
    
    #%% dit was een test om varaibles te fixen met de start functie. Maar is waarschijnlijk niet nodig omdat hij best moooie feasible solutions maakt.
                
    # =============================================================================
    # model.write('testing for feasible solutions2.sol')
    # 
    # model.reset()
    # 
    # 
    # for i, v in enumerate(model.getVars()):
    #     if i < I:
    #         v.Start = 1
    #     
    # model.optimize(mycallback)
    # model.write('testing for feasible solutions2.sol')
    # =============================================================================
    # Calculate the total time taken
    # Record the end time
    end_time = time.time()
    total_time = end_time - start_time
    print(f"Total time taken: {total_time:.4f} seconds")
    test +=1