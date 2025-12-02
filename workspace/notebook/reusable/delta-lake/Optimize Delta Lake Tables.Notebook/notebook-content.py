# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "9402db12-a266-468c-96ed-54c44520e161",
# META       "default_lakehouse_name": "lh_silver",
# META       "default_lakehouse_workspace_id": "681534df-b5cf-44dc-9644-46312e52c461",
# META       "known_lakehouses": [
# META         {
# META           "id": "9402db12-a266-468c-96ed-54c44520e161"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

%run /DeltaLakeFunctions

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ### Iterate through all tables in lakehouse and run OPTIMIZE and VACCUM commands

# CELL ********************

df = spark.sql("show tables")
tableList = df.select("tableName").rdd.flatMap(lambda x:x).collect()
# print (tables)
for table in tableList:
    print ("optimizing",table)
    optimizeDelta(table)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
