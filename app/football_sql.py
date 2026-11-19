DISTRIBUTION = """
SELECT COUNT(*) AS nb_indemnites_positives, AVG(fee) AS moyenne,
       STDDEV(fee) AS ecart_type, SKEWNESS(fee) AS asymetrie,
       PERCENTILE_APPROX(fee, 0.25) AS p25, PERCENTILE_APPROX(fee, 0.5) AS mediane,
       PERCENTILE_APPROX(fee, 0.75) AS p75, PERCENTILE_APPROX(fee, 0.9) AS p90,
       PERCENTILE_APPROX(fee, 0.95) AS p95, MAX(fee) AS maximum
FROM football_transfers_enriched WHERE fee > 0
"""

PARETO = """
WITH leagues AS (
    SELECT year, destination_league_id AS league_id,
           MIN(CONCAT_WS(' · ', destination_league, destination_country)) AS league,
           COUNT(*) AS transfers, COUNT(fee) AS known_fees, SUM(fee) AS total,
           PERCENTILE_APPROX(IF(fee > 0, fee, NULL), 0.50) AS median_fee,
           PERCENTILE_APPROX(IF(fee > 0, fee, NULL), 0.75)
             - PERCENTILE_APPROX(IF(fee > 0, fee, NULL), 0.25) AS iqr
    FROM football_transfers_enriched
    WHERE year IS NOT NULL AND destination_league_id IS NOT NULL
    GROUP BY year, destination_league_id
)
SELECT *, DENSE_RANK() OVER (PARTITION BY year ORDER BY total DESC NULLS LAST) AS spend_rank,
       ROW_NUMBER() OVER (PARTITION BY year ORDER BY total DESC NULLS LAST, league_id) AS pareto_order,
       TRY_DIVIDE(SUM(total) OVER (PARTITION BY year ORDER BY total DESC NULLS LAST, league_id
         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW),
         SUM(total) OVER (PARTITION BY year)) AS cumulative_share
FROM leagues
"""

TIME = """
WITH annual AS (
    SELECT year,
           CASE WHEN origin_league_id = destination_league_id THEN 'Même championnat'
                ELSE 'Entre championnats' END AS scope,
           COUNT(*) AS transfers, COUNT(fee) AS known_fees,
           AVG(IF(fee > 0, fee, NULL)) AS mean_fee,
           PERCENTILE_APPROX(IF(fee > 0, fee, NULL), 0.50) AS median_fee
    FROM football_transfers_enriched
    WHERE year IS NOT NULL AND origin_league_id IS NOT NULL AND destination_league_id IS NOT NULL
    GROUP BY 1, 2
), history AS (
    SELECT *, LAG(year) OVER (PARTITION BY scope ORDER BY year) AS previous_year,
           LAG(transfers) OVER (PARTITION BY scope ORDER BY year) AS previous_transfers
    FROM annual
)
SELECT *, IF(year = previous_year + 1,
           TRY_DIVIDE(transfers - previous_transfers, previous_transfers), NULL) AS growth
FROM history
"""

FLOWS = """
WITH pairs AS (
    SELECT year, origin_league_id, destination_league_id,
           MIN(origin_league) AS origin_league, MIN(origin_country) AS origin_country,
           MIN(destination_league) AS destination_league, MIN(destination_country) AS destination_country,
           COUNT(*) AS transfers, COUNT(fee) AS known_fees,
           COUNT_IF(fee > 0) AS positive_fees, SUM(fee) AS known_total,
           AVG(IF(fee > 0, fee, NULL)) AS mean_positive_fee,
           PERCENTILE_APPROX(IF(fee > 0, fee, NULL), 0.50) AS median_positive_fee
    FROM football_transfers_enriched
    WHERE year IS NOT NULL AND origin_league_id IS NOT NULL AND destination_league_id IS NOT NULL
    GROUP BY year, origin_league_id, destination_league_id
)
SELECT *, ROW_NUMBER() OVER (PARTITION BY year, destination_league_id
                             ORDER BY transfers DESC, origin_league_id) AS origin_rank
FROM pairs
"""

COVERAGE = """
SELECT year, origin_status, destination_status, COUNT(*) AS count
FROM football_transfers_enriched GROUP BY year, origin_status, destination_status
"""

DETAILS = """
SELECT year, origin_league_id, destination_league_id, player_name,
       origin_club, destination_club, transfer_type, fee
FROM football_transfers_enriched
WHERE year IS NOT NULL AND origin_league_id IS NOT NULL AND destination_league_id IS NOT NULL
"""

FEATURES = """
SELECT destination_club_id AS club_id, MIN(destination_club) AS club,
       COUNT(*) AS arrivals, COUNT(DISTINCT origin_club_id) AS origin_clubs,
       COUNT_IF(fee > 0) AS known_positive_fees,
       PERCENTILE_APPROX(IF(fee > 0, fee, NULL), 0.50) AS median_fee,
       AVG(CAST(origin_league_id <> destination_league_id AS DOUBLE)) AS cross_share
FROM football_transfers_enriched
WHERE year BETWEEN {first_year} AND {last_year}
  AND origin_league_id IS NOT NULL AND destination_league_id IS NOT NULL
  AND destination_club_id IS NOT NULL AND destination_club IS NOT NULL
GROUP BY destination_club_id
HAVING COUNT(*) >= 10 AND COUNT_IF(fee > 0) >= 5
"""
