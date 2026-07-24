# FiremeX Admin User Functional Test Cases

This document details the **Functional Test Cases** specifically for the **Administrator (Admin)** user role in FiremeX. These tests focus on business logic, backend/state data integrity, authorization controls, CRUD data flows, and state transition validation.

---

## 1. Organization Setup & Admin Registration

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FTC-ADM-01** | Unique Organization Code Generation | Admin is on `/FiremeX/register` step 'organization' | 1. Enter valid details for Acme Corp.<br>2. Submit the form.<br>3. Verify the generated Organization Code format in the alert. | 1. A unique code prefixed with `ORG-` and followed by 3 random digits is generated (e.g. `ORG-642`).<br>2. The format is alphanumeric and consistent. | High | REQ-ORG-01 |
| **FTC-ADM-02** | Local Storage Organization Persistence | Admin registers a new organization | 1. Fill and submit the Organization registration form.<br>2. Inspect browser's `localStorage` key `firemex_organizations`. | 1. The new organization object is successfully appended to the JSON array.<br>2. Keys include: `id`, `name`, `sector`, `email`, `adminName`, `phone`, and `date`. | Critical | REQ-ORG-02 |

---

## 2. Operator Management & Approvals Workflow

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FTC-ADM-03** | Approve Operator Request State Transition | Operator has submitted request using the Organization Code. Admin is logged in. | 1. Navigate to `/FiremeX/admin/users`.<br>2. Click the "Pending Requests" tab.<br>3. Select a request (e.g., Alice Williams) and click "Approve Access". | 1. The user request is removed from `localStorage.firemex_pending_users`.<br>2. The user object is added to `localStorage.firemex_active_users` with status set to `Active`. | Critical | REQ-USR-01 |
| **FTC-ADM-04** | Deny Operator Request Action | Pending request exists in queue | 1. Navigate to "Pending Requests" tab.<br>2. Select Bob Johnson's request and click "Deny Request". | 1. Request is permanently deleted from `localStorage.firemex_pending_users`.<br>2. User is NOT added to active operators and cannot access the admin space. | High | REQ-USR-02 |
| **FTC-ADM-05** | Active Operator Access Revocation | Operator exists in active users table | 1. Navigate to "Active Operators" tab.<br>2. Click "Revoke Access" next to John Doe.<br>3. Click "OK" in the confirmation prompt. | 1. The operator is deleted from `localStorage.firemex_active_users`.<br>2. Operator's email will no longer be authorized to access the layout dashboard. | Critical | REQ-USR-03 |
| **FTC-ADM-06** | State Count Indicators Sync | Pending and active operators exist | 1. View count indicators on the tabs.<br>2. Approve a pending operator. | 1. The count badge on "Pending Requests" decrements by 1.<br>2. The count badge on "Active Operators" increments by 1. | Medium | REQ-USR-04 |

---

## 3. Device Configuration & Network Streams (CRUD)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FTC-ADM-07** | Camera Dynamic ID Generation & Provisioning | Admin is on `/FiremeX/admin/livefeed/add-device` | 1. Input Name "Server Room L3", IP "192.168.1.189", select Zone, Resolution, FPS.<br>2. Click "Add Camera". | 1. The app parses existing camera lists and generates the next sequential ID (`CAM-05`).<br>2. The new camera is saved to `localStorage.firemex_cameras` with details formatted correctly (e.g. FPS lowercased, status defaults to `Normal`). | Critical | REQ-CAM-01 |
| **FTC-ADM-08** | Delete Camera Stream & Cache Purge | Camera CAM-04 exists in live streams | 1. Navigate to `/FiremeX/admin/livefeed`.<br>2. Click Delete/Trash icon for CAM-04. | 1. Camera CAM-04 is removed from the local state variable.<br>2. `localStorage.firemex_cameras` updates to exclude CAM-04. | High | REQ-CAM-02 |
| **FTC-ADM-09** | Connection Test Logic Verification | Admin is on Add Device form | 1. Fill details and click "Test Connection" button. | 1. App fires a mock network validation script returning a "Successful" connection message. | Medium | REQ-CAM-03 |

---

## 4. Incident Status & Resolution Workflow

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FTC-ADM-10** | Status Change: Unresolved to In Progress | Incident exists in Incidents log | 1. Navigate to `/FiremeX/admin/incidents`.<br>2. Locate an incident in "Unresolved" state.<br>3. Open Action dropdown and select "In Progress". | 1. Incident status state updates immediately to `In Progress`.<br>2. The status indicator text changes color to sky blue / amber (Warning). | Critical | REQ-INC-01 |
| **FTC-ADM-11** | Save Resolve Incident Note | Incident is marked "In Progress" | 1. In Action dropdown, select "Resolved".<br>2. In the modal, write note "Ventilation restored, fake alarm triggered by dust".<br>3. Click "Mark as Resolved". | 1. Modal closes.<br>2. Incident status is updated to `Resolved` (green).<br>3. The text note is saved inside the incident object and rendered on screen. | Critical | REQ-INC-02 |
| **FTC-ADM-12** | Save Blocker Reason (Unable to Resolve) | Incident is unresolved | 1. Open status dropdown and select "Resolved".<br>2. In modal, check "Unable to resolve this incident".<br>3. Enter blocker: "Sprinkler system valve jammed. Maintenance team dispatched".<br>4. Click "Save Note". | 1. Status remains "Unresolved" (red).<br>2. Blocker reason is appended to the incident object and rendered under the status. | High | REQ-INC-03 |

---

## 5. Alerts & Notification Dispatch Audit

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FTC-ADM-13** | Acknowledge Toggle Audit Update | Alerts exists on Alert history page | 1. Navigate to `/FiremeX/admin/alerts`.<br>2. Locate Alert ID 2 with Acknowledged: "No".<br>3. Click the "Yes" button under Acknowledged. | 1. Alert state `acknowledged` changes to `"Yes"`.<br>2. The counts of active alert indicators (Awaiting ack vs Acknowledged stats widgets) adjust dynamically. | High | REQ-ALT-01 |
| **FTC-ADM-14** | Filter/Search Compound Operations | Multiple alerts and incidents in logs | 1. Type "Kitchen" in search.<br>2. Filter by status "Resolved".<br>3. Select camera "Kitchen Cam 01". | 1. App applies AND filters across all parameters, showing matching datasets.<br>2. Displays empty placeholder message if no records intersect. | High | REQ-ALT-02 |
