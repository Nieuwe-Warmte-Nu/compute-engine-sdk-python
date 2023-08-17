--CREATE USER docker;
--CREATE DATABASE nieuwe;
--GRANT ALL PRIVILEGES ON DATABASE docker TO docker;

--CREATE DATABASE nieuwewarmtenu;

CREATE TYPE work_flow_type AS ENUM ('growth_optimizer');
CREATE TYPE job_status AS ENUM ('registered', 'running', 'finished', 'error');

CREATE TABLE job (
    job_id uuid PRIMARY KEY,
    job_name text NOT NULL,
    work_flow_type work_flow_type NOT NULL,
    map_editor_user text,
    status job_status NOT NULL,
    input_config text,
    input_esdl text NOT NULL,
    output_esdl text,
    added_at timestamp NOT NULL,
    running_at timestamp,
    stopped_at timestamp,
    error_logs text
);
