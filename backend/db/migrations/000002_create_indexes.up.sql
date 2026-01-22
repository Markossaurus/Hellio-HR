CREATE INDEX candidates_status_created_at_idx
  ON candidates (status, created_at DESC);

CREATE INDEX candidates_email_lower_idx
  ON candidates (lower(email));

CREATE INDEX positions_status_created_at_idx
  ON positions (status, created_at DESC);

CREATE INDEX candidate_positions_position_id_idx
  ON candidate_positions (position_id);

CREATE INDEX candidate_positions_candidate_id_idx
  ON candidate_positions (candidate_id);
