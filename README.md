# Marché des transferts de football

**Yasser Ezzonfari**

J’analyse les transferts de joueurs pour voir quels championnats recrutent les uns chez les autres et comment se répartissent les indemnités. [Données sur Kaggle](https://www.kaggle.com/datasets/otaviofbrito/soccer-player-transfer-dataset)

## Tester le projet

Si Docker tourne déjà, ouvre JupyterLab. Pour un premier démarrage, lance cette commande depuis le dossier du projet dans ton terminal Linux ou WSL.

```bash
docker compose up -d --build
```

Dans JupyterLab, ouvre le dossier `notebooks`. Clique sur une cellule Python, puis appuie sur **Maj + Entrée** pour l’exécuter et voir le résultat juste en dessous. Pour reconstruire les données, lance toutes les cellules de chaque notebook dans l’ordre. [Ouvrir JupyterLab](http://localhost:8888/lab/tree/notebooks)

1. [J1 · Charger les données](notebooks/J1_HDFS_Ingestion_Bronze.ipynb)
2. [J2 · Explorer et préparer les transferts](notebooks/J2_Spark_Delta_Silver.ipynb)
3. [J3 · Analyser les transferts en SQL](notebooks/J3_Analytics_SQL_Gold.ipynb)
4. [J4 · Tester les hypothèses et comparer les clubs](notebooks/J4_Stats_Segmentation_Dashboard.ipynb)

Après J4, les graphiques sont disponibles dans le [tableau de bord Streamlit](http://localhost:8501).

## Documentation technique

Les commandes détaillées et le test de panne HDFS sont dans le [guide technique](GUIDE_TECHNIQUE.md).
