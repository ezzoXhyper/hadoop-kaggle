# Documentation technique

**Yasser Ezzonfari · Les transferts entre championnats de football**

Le projet utilise les cinq tables du jeu de données Soccer Player Transfer Dataset. L’ingestion se fait dans HDFS. Les notebooks utilisent PySpark et Delta Lake, puis Streamlit lit les tables Gold. [Source des données](https://www.kaggle.com/datasets/otaviofbrito/soccer-player-transfer-dataset)

| Notebook | Traitement |
| --- | --- |
| [J1](notebooks/J1_HDFS_Ingestion_Bronze.ipynb) | Ingestion des données et test de panne HDFS |
| [J2](notebooks/J2_Spark_Delta_Silver.ipynb) | Exploration, nettoyage et jointures |
| [J3](notebooks/J3_Analytics_SQL_Gold.ipynb) | Indemnités et flux entre championnats |
| [J4](notebooks/J4_Stats_Segmentation_Dashboard.ipynb) | Tests statistiques et profils de recrutement |

En J3, le championnat est attribué selon l’année du transfert. Quand l’affiliation du club est ambiguë, aucun championnat ne lui est attribué. Le graphique des flux couvre les **757 798 transferts** dont les deux championnats ont été identifiés.

Le test de J1 a confirmé que Spark pouvait lire les **858 947 lignes** du fichier des joueurs avec un DataNode arrêté. Après le redémarrage, HDFS indiquait trois DataNodes actifs et aucun bloc sous-répliqué.

Les quatre notebooks s’exécutent dans l’ordre J1 → J4 avec le cluster du fichier `docker-compose.yml`. Le [tableau de bord Streamlit](http://localhost:8501/) s’affiche sur la machine qui exécute le projet.
