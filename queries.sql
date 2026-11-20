-- queries.sql
-- Example SQL queries used in the project, runnable against elections.db
-- (for example:  sqlite3 elections.db < queries.sql ).
-- They show the kind of joins and aggregation the project relies on.

-- 1. How many seats and candidates are in the database?
SELECT (SELECT COUNT(*) FROM constituencies) AS seats,
       (SELECT COUNT(*) FROM candidates)     AS candidates;

-- 2. Winner of each constituency (candidate with the most votes).
SELECT con.const_name,
       s.state_name,
       c.cand_name,
       p.abbr      AS party,
       c.votes
FROM candidates c
JOIN constituencies con ON c.const_id = con.const_id
JOIN states        s   ON con.state_id = s.state_id
JOIN parties       p   ON c.party_id = p.party_id
WHERE c.votes = (SELECT MAX(c2.votes)
                 FROM candidates c2
                 WHERE c2.const_id = c.const_id)
ORDER BY s.state_name, con.const_name;

-- 3. Seats won per party (headline result).
WITH seat_winners AS (
    SELECT c.const_id, c.party_id
    FROM candidates c
    WHERE c.votes = (SELECT MAX(c2.votes)
                     FROM candidates c2
                     WHERE c2.const_id = c.const_id)
)
SELECT p.abbr AS party, COUNT(*) AS seats
FROM seat_winners w
JOIN parties p ON w.party_id = p.party_id
GROUP BY p.abbr
ORDER BY seats DESC;

-- 4. Total votes and vote share per party.
SELECT p.abbr AS party,
       SUM(c.votes) AS total_votes,
       ROUND(100.0 * SUM(c.votes) /
             (SELECT SUM(votes) FROM candidates), 2) AS vote_share_pct
FROM candidates c
JOIN parties p ON c.party_id = p.party_id
GROUP BY p.abbr
ORDER BY total_votes DESC
LIMIT 15;

-- 5. Turnout per state (votes polled over electors).
SELECT s.state_name,
       ROUND(100.0 * SUM(con.total_polled) / SUM(con.total_electors), 2)
           AS turnout_pct
FROM constituencies con
JOIN states s ON con.state_id = s.state_id
GROUP BY s.state_name
ORDER BY turnout_pct DESC;
