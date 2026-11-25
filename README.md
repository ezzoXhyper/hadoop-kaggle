# Les transferts entre championnats de football

**Yasser Ezzonfari · TP Big Data Lakehouse**

J’ai voulu savoir d’où viennent les joueurs recrutés par les clubs et quels championnats concentrent les indemnités de transfert. Pour retrouver le championnat d’un club au moment d’un transfert, je croise les transferts avec les affiliations des clubs par saison. [Jeu de données Kaggle](https://www.kaggle.com/datasets/otaviofbrito/soccer-player-transfer-dataset)

## Notebooks

1. [J1 · Ingestion dans HDFS et test de panne](notebooks/J1_HDFS_Ingestion_Bronze.ipynb)
2. [J2 · Exploration, nettoyage et jointures](notebooks/J2_Spark_Delta_Silver.ipynb)
3. [J3 · Flux entre championnats et analyse des indemnités](notebooks/J3_Analytics_SQL_Gold.ipynb)
4. [J4 · Tests statistiques et profils de recrutement](notebooks/J4_Stats_Segmentation_Dashboard.ipynb)

Sur les 3,47 millions de transferts, j’ai pu rattacher environ 758 000 mouvements à un championnat de départ et à un championnat d’arrivée. Le graphique des flux porte sur ces mouvements. Parmi les indemnités strictement positives, la médiane est de 450 000 et la moyenne dépasse 2 millions.

## Exécution

Depuis le dossier du projet, avec Docker démarré, lancer `docker compose up -d --build`. Dans JupyterLab, exécuter les notebooks de J1 à J4 dans l’ordre. Streamlit affiche ensuite les résultats, avec des filtres par année et par championnat.

- [JupyterLab](http://localhost:8888/lab/tree/notebooks)
- [Tableau de bord Streamlit](http://localhost:8501/)

## Documentation technique

[Installation, commandes de vérification et procédure du test HDFS](GUIDE_TECHNIQUE.md)
