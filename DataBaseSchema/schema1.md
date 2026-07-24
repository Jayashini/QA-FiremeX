//Registered Organizations
Organization(id, name, location, email, contact_number, is_deleted)

//Users & Roles
users(id, name, email, password_hash, organization, role_id, created_at, last_loging, is_active)
roles(id, name, permissions_json)

//Cameras & Zones
cameras(camera_id, name, rtsp_url, zone_id, location_lat, location_lng, status, last_seen, is_active)
zones(zone_id, name, criticality_level, facility_id)
facilities(facility_id, name, address)

//AI Detections
detections(id, camera_id, frame_ts, class, confidence, bbox_json, model_version)

//Risk & Incidents
risk_scores(id, detection_id_nullable, sensor_reading_id_nullable, zone_id,
            score, level, computed_at)
incidents(id, risk_score_id, camera_id, zone_id, screenshot_url, clip_url,
          status, assigned_to, created_at, resolved_at, notes)
resolve_incident(incident_id, resolve_at, resolve, resolved_by)

//Alerts
alerts(id, incident_id, channel, recipient_id, sent_at, delivered, acknowledged_by, acknoledged_stream, acknowledged_at)

//Audit
audit_logs(id, user_id, action, target_table, target_id, timestamp, ip_address)

//Reports
reports(id, type, generated_by, period_start, period_end, file_url, created_at)