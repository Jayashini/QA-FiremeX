//Registered Organizations
Organization(organization_id, ornagization_name, location, email, contact_number, is_deleted)

//Users & Roles
users(user_id, user_name, user_email, password_hash, organization_name, role_id, created_at, last_loging, is_active)
roles(role_id, user_role, permissions_json)

//Cameras & Zones
cameras(camera_id, ip, rtsp_url, zone_id, location_lat, location_lng, status, last_seen, is_active)
zones(zone_id, zone_name, criticality_level, facility_id)
facilities(facility_id, facility_name, address)

//AI Detections
detections(dectect_id, camera_id, frame_ts, class, confidence, bbox_json, model_version)

//Risk & Incidents
risk_scores(risk_id, detection_id_nullable, zone_id, score, level, computed_at)
incidents(incident_id, risk_id, camera_id, zone_id, screenshot_url, clip_url,
          status, created_at, resolved_at, notes)
resolve_incident(resolve_incident_id, incident_id, resolve_at, resolve, resolved_by)

//Alerts
alerts(alert_id, incident_id, channel, recipient_id, sent_at, delivered, acknowledged_by, acknoledged_stream, acknowledged_at)

//Audit
audit_logs(audit_id, user_id, action, target_table, target_id, timestamp, ip_address)

//Reports
reports(report_id, type, generated_by, period_start, period_end, file_url, created_at)