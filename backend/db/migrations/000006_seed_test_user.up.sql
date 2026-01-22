INSERT INTO users (id, email, password_hash)
VALUES (
  '99999999-9999-9999-9999-999999999999',
  'admin@hellio.hr',
  '$2b$12$o7BDki1dO6kxJrwTNascbOfKx8z1bc9FUj3gDPFgTLM9I4aUyggoS'
);

INSERT INTO user_roles (user_id, role_id)
VALUES (
  '99999999-9999-9999-9999-999999999999',
  '00000000-0000-0000-0000-000000000003'
);
