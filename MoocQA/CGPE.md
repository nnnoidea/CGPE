# MOOC Q&A
can be downloaded from http://moocdata.cn/data/MOOCCube
We imported the files under MOOCCube/MOOCQA/tuples into Neo4j as a knowledge base.

# codes
## main.py
the **data_path** on line 6 and the **file path** on line 160 need to be modified to your own.

## utils.py
**use_model** in line 9 decides the base model
**base_url** in line 12 is the url of your own ChatGLM.
**graph** in line 15 is used to connect with neo4j.

