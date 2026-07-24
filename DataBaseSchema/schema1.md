-- Users & Roles
users(id, name, email, password_hash, role_id, created_at, is_active)
roles(id, name, permissions_json)

-- Cameras & Zones
cameras(id, name, rtsp_url, zone_id, location_lat, location_lng, status, last_seen)
zones(id, name, criticality_level, facility_id)
facilities(id, name, address)

-- Sensors
sensors(id, type, camera_id_nullable, zone_id, calibration_offset, status)
sensor_readings(id, sensor_id, value, unit, recorded_at)   -- time-series table

-- AI Detections
detections(id, camera_id, frame_ts, class, confidence, bbox_json, model_version)

-- Risk & Incidents
risk_scores(id, detection_id_nullable, sensor_reading_id_nullable, zone_id,
            score, level, computed_at)
incidents(id, risk_score_id, camera_id, zone_id, screenshot_url, clip_url,
          status, assigned_to, created_at, resolved_at, notes)

-- Alerts
alerts(id, incident_id, channel, recipient_id, sent_at, delivered, acknowledged_at)

-- Audit
audit_logs(id, user_id, action, target_table, target_id, timestamp, ip_address)

-- Reports
reports(id, type, generated_by, period_start, period_end, file_url, created_at)