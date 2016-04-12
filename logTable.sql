-- Table: web_services.geoserver_log

-- DROP TABLE web_services.geoserver_log;

CREATE TABLE web_services.geoserver_log
(
  vhost text, -- Apache virtual server name
  ip inet, -- IP of client
  date timestamp with time zone, -- date and time of request
  request text, -- URL of request
  agent text, -- Agent used ot make request
  status smallint, -- HTTP response status from server
  bytes bigint -- Foreign key that refers to table "profile"
)
WITH (
  OIDS=FALSE
);

COMMENT ON TABLE web_services.geoserver_log
  IS 'Geoserver log table mainly for web services';
COMMENT ON COLUMN web_services.geoserver_log.vhost IS 'Apache virtual server name';
COMMENT ON COLUMN web_services.geoserver_log.ip IS 'IP of client';
COMMENT ON COLUMN web_services.geoserver_log.date IS 'date and time of request';
COMMENT ON COLUMN web_services.geoserver_log.request IS 'URL of request';
COMMENT ON COLUMN web_services.geoserver_log.agent IS 'Agent used ot make request';
COMMENT ON COLUMN web_services.geoserver_log.status IS 'HTTP response status from server';
COMMENT ON COLUMN web_services.geoserver_log.bytes IS 'Foreign key that refers to table "profile"';

