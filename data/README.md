# Local Data Layout

This directory is for local development data.

- `config/` contains checked-in seed configuration for assets, clients, and market profiles.
- `raw/`, `processed/`, `outputs/`, and `db/` are runtime/local artifact locations created as needed.

Production deployments should move generated outputs to object storage and
database state to a managed database instead of treating these runtime folders
as source-controlled application state.
