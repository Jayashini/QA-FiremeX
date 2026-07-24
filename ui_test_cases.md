# FiremeX UI Test Cases

This document outlines the comprehensive UI test suite for all pages, layouts, and components in the **FiremeX Fire & Security Monitoring System**.

---

## 1. Authentication (Login & Gateway)

### Pages under Test:
*   [Login.tsx](file:///d:/FiremeX/src/pages/auth/Login.tsx)
*   [RegisterGateway.tsx](file:///d:/FiremeX/src/pages/auth/RegisterGateway.tsx)
*   [AuthLayout.tsx](file:///d:/FiremeX/src/layouts/AuthLayout.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-AUTH-01** | Verify Login Form Display & Defaults | App is open and user is on `/FiremeX/login` or `/` | 1. Observe the email and password fields.<br>2. Observe the brand branding logo and headers. | 1. Email field defaults to `operator@gmail.com`.<br>2. Password field defaults to `operator12345`.<br>3. Brand title says "FiremeX" and slogan is present. | High | REQ-AUTH-01 |
| **TC-AUTH-02** | Toggle Password Visibility | Password field contains text | 1. Click on the Eye icon in the password field.<br>2. Click it again. | 1. Clicking the Eye once changes input `type` to `text`, revealing characters.<br>2. Clicking again changes type back to `password`. | High | REQ-AUTH-01 |
| **TC-AUTH-03** | Submit Valid Login | Default operator credentials populated | 1. Click the "Sign in" button. | 1. Layout redirects to the Admin Dashboard (`/FiremeX/admin/dashboard`). | Critical | REQ-AUTH-01 |
| **TC-AUTH-04** | Forgot Password Click Action | Login view active | 1. Click on the "Forgot password?" link next to the Password label. | 1. Browser shows a window alert stating: "Reset password link sent to email." | Medium | REQ-AUTH-01 |
| **TC-AUTH-05** | Navigate to Registration Gateway Selection | User is on Login page | 1. Click the toggle link: "Don't have an account? Request access..." | 1. Browser redirects to the `/FiremeX/register` page. | High | REQ-AUTH-02 |
| **TC-REG-01** | Registration Type Cards Interaction | User is on registration selection step | 1. Hover over "Register as an Organization".<br>2. Hover over "Register as an Operator".<br>3. Click "Select Organization". | 1. Cards should hover-transform with border styling changes (accent/40).<br>2. Clicking "Select Organization" loads Step 2 (Organization Profile form). | High | REQ-AUTH-02 |
| **TC-REG-02** | Submit Organization Registration Form | Step is 'organization' | 1. Populate Org Name, Email, Phone, Admin Name, and Password.<br>2. Select Sector from dropdown.<br>3. Click "Complete Registration". | 1. Success alert shows: `Organization "[Name]" registered successfully!...`<br>2. A unique code is generated and shown in the alert (e.g. `ORG-XYZ`).<br>3. Organization details are written into `localStorage.firemex_organizations`. | Critical | REQ-AUTH-02 |
| **TC-REG-03** | Submit Operator Registration Request | Step is 'operator' | 1. Populate Organization Code, Operator Name, Email, Password, and Reason.<br>2. Click "Request Operators Access". | 1. Alert shows operator access request submitted successfully.<br>2. Operator request is logged into `localStorage.firemex_pending_users`. | Critical | REQ-AUTH-03 |
| **TC-REG-04** | Back to Selection Flow | User is in Step 2 of either registration view | 1. Click the back arrow button next to the form header. | 1. Step transitions back to selection screen (`select`). | Medium | REQ-AUTH-02 |

---

## 2. Dashboard Component

### Pages under Test:
*   [Dashboard.tsx](file:///d:/FiremeX/src/pages/admin/Dashboard.tsx)
*   [AdminLayout.tsx](file:///d:/FiremeX/src/layouts/AdminLayout.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-DASH-01** | Real-time Clock updates every second | User is on Dashboard page | 1. Verify the LIVE ticker clock is active in the top-right header. | 1. Clock hours, minutes, and seconds increment in real-time.<br>2. The green "LIVE" circular indicator badge is pulsing. | High | REQ-DASH-01 |
| **TC-DASH-02** | Cameras Online Stats Redirection | User is on Dashboard page | 1. Click the "Cameras Online" card widget. | 1. Redirects page route to Live Feed screen (`/FiremeX/admin/livefeed`). | High | REQ-DASH-02 |
| **TC-DASH-03** | Current Risk Level Stats Redirection | User is on Dashboard page | 1. Click the "Current Risk Level" card widget. | 1. Redirects page route to Incidents log (`/FiremeX/admin/incidents`). | High | REQ-DASH-02 |
| **TC-DASH-04** | Active Alerts Redirection | User is on Dashboard page | 1. Click the "Active Alerts" card widget, or the Header Notification Bell. | 1. Redirects page route to Alert History (`/FiremeX/admin/alerts`). | High | REQ-DASH-02 |
| **TC-DASH-05** | Recent Incident Table Rows Navigation | User is on Dashboard page | 1. Click the "View all" link in the Recent Incidents panel. | 1. Redirects page route to Incidents log page. | Medium | REQ-DASH-03 |
| **TC-DASH-06** | Real-time CCTV Stream & AI Overlay Rendering | User is on Dashboard page | 1. Observe the "Recent Alert Camera Preview" video container. | 1. Image feed `/warehouse_fire.png` is displayed.<br>2. Red bounding box is drawn at bottom center around the fire region.<br>3. Red blinking badge "LIVE" and "REC" are visible.<br>4. Floating tag text "FIRE - 0.94" is highlighted on screen. | High | REQ-DASH-04 |

---

## 3. Live Feed Page

### Pages under Test:
*   [Livefeed.tsx](file:///d:/FiremeX/src/pages/admin/Livefeed.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-FEED-01** | Grid Layout Switcher Execution | User is on Live Feed page | 1. Click the Layout "1 x 2" button.<br>2. Click the Layout "2 x 2" button. | 1. Layout switches grid layout immediately.<br>2. Active camera stream cards shift columns to fill space. | High | REQ-LIV-01 |
| **TC-FEED-02** | Critical vs Normal Alert Badges | Active camera feeds present | 1. Observe CAM-02 status badge.<br>2. Observe CAM-01 status badge. | 1. CAM-02 has border-red styling and blinking ring anim (`Critical`).<br>2. CAM-01 has green normal status badge (`Normal`). | High | REQ-LIV-02 |
| **TC-FEED-03** | Delete Camera Stream action | User is on Live Feed page | 1. Click the Trash Can icon on any camera stream card (e.g. CAM-04). | 1. Camera is removed from the DOM list.<br>2. Stream settings are deleted from `localStorage.firemex_cameras`. | Critical | REQ-LIV-03 |
| **TC-FEED-04** | Edit Configuration Action | User is on Live Feed page | 1. Click the Pencil/Edit icon next to any camera name. | 1. Shows a window alert stating: "Edit config for [CAM-ID]". | Medium | REQ-LIV-03 |
| **TC-FEED-05** | Redirect to Add Device Page | User is on Live Feed page | 1. Click "Add Camera" in the header control or the dotted add card. | 1. Redirects page to `/FiremeX/admin/livefeed/add-device`. | High | REQ-LIV-03 |

---

## 4. Add Device Component

### Pages under Test:
*   [AddDevice.tsx](file:///d:/FiremeX/src/pages/admin/AddDevice.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-ADD-01** | IP Address Stream Validation | User is on Add Device page | 1. Leave "Camera Name" and "IP Address" empty and press submit.<br>2. Fill invalid values. | 1. Form triggers HTML native validation warnings for mandatory inputs. | High | REQ-ADD-01 |
| **TC-ADD-02** | Toggle Enable AI Tracking | User is on Add Device page | 1. Click on the "Enable AI Tracking" toggle switch button. | 1. Switch slider animations translate left/right, and background color switches. | Medium | REQ-ADD-02 |
| **TC-ADD-03** | Simulation Connection Test | User is on Add Device page | 1. Click "Test Connection". | 1. Alerts: "Testing stream connection... Successful." | Medium | REQ-ADD-03 |
| **TC-ADD-04** | Provision Camera Stream Submission | User is on Add Device page | 1. Populate all inputs.<br>2. Click the "Add Camera" button. | 1. Stream is appended to the camera config list in `localStorage.firemex_cameras`.<br>2. Redirects back to Live Feed stream overview. | Critical | REQ-ADD-01 |
| **TC-ADD-05** | Cancel Provisioning Flow | User is on Add Device page | 1. Click the "Cancel" link button. | 1. Page discards inputs and redirects to `/FiremeX/admin/livefeed`. | Medium | REQ-ADD-01 |

---

## 5. Incidents Log

### Pages under Test:
*   [Incidents.tsx](file:///d:/FiremeX/src/pages/admin/Incidents.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-INC-01** | Search Filtering Input Query | Multiple incident items loaded | 1. Input "Cam 03" into Search field.<br>2. Input "Warehouse A" into search. | 1. Filters table rows to match camera IDs or zone names immediately. | High | REQ-INC-01 |
| **TC-INC-02** | Filter Dropdowns Manipulation | Dropdowns exist in header | 1. Choose "Unresolved" from Status dropdown.<br>2. Choose "Cam 07" from Camera dropdown. | 1. Table matches selected query combinations. | High | REQ-INC-01 |
| **TC-INC-03** | Switch State status to Unresolved / In Progress | User is in Incidents log | 1. Choose "In Progress" or "Unresolved" from a row's dropdown. | 1. Updates state status tag colors dynamically without popup modal. | Critical | REQ-INC-02 |
| **TC-INC-04** | Resolve Incident with Notes Modal Flow | User is in Incidents log | 1. Select "Resolved" status dropdown.<br>2. Fill "Resolve Note" text area.<br>3. Click "Mark as Resolved". | 1. Opens Resolution Modal popup.<br>2. Close button updates target row action status to "Resolved" (green).<br>3. Notes display below the status. | High | REQ-INC-03 |
| **TC-INC-05** | Resolution Blocked Note validation | Resolution Modal is open | 1. Check the box "Unable to resolve this incident".<br>2. Populate "blocker reason" textarea.<br>3. Click "Save Note". | 1. Resolve note textarea is swapped with Blocker reason textarea.<br>2. Status updates to Unresolved (red) with Blocker alert note displayed on list page. | High | REQ-INC-03 |

---

## 6. Alerts History Log

### Pages under Test:
*   [Alerts.tsx](file:///d:/FiremeX/src/pages/admin/Alerts.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-ALT-01** | Direct Acknowledge Yes / No action buttons | User is on Alerts page | 1. Locate row with Acknowledged: "No".<br>2. Click the "Yes" button in that row. | 1. Active button toggles layout immediately.<br>2. Status pill changes to green and states "Yes". | Critical | REQ-ALT-02 |
| **TC-ALT-02** | Filter by Alert Channel | Alerts list populated | 1. Select "SMS" filter from dropdown in header. | 1. Table rows display only notifications sent over SMS channels. | High | REQ-ALT-01 |
| **TC-ALT-03** | Detail Button Trigger | Alerts page active | 1. Click the chevron arrow next to any alert entry row. | 1. System displays alert notification detail (e.g. window alert message). | Low | REQ-ALT-01 |

---

## 7. User Management Page

### Pages under Test:
*   [User.tsx](file:///d:/FiremeX/src/pages/admin/User.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-USR-01** | Active Operators vs Pending Requests Navigation Tabs | User is on User Management page | 1. Click the "Pending Requests" tab.<br>2. Click the "Active Operators" tab. | 1. Active tab displays count matching pending/active operator quantities.<br>2. Grid shifts items dynamically when tabs are switched. | High | REQ-USR-01 |
| **TC-USR-02** | Revoke Active Operator Access flow | "Active Operators" view active | 1. Click "Revoke Access" link under any active operator profile.<br>2. Click "Cancel" in browser confirmation dialog.<br>3. Click "OK" on confirmation. | 1. Clicking Cancel stops process.<br>2. Clicking OK deletes user from active list, updates `localStorage.firemex_active_users` dynamically. | Critical | REQ-USR-02 |
| **TC-USR-03** | Approve Operator Access request | "Pending Requests" tab active | 1. Locate pending user and click "Approve Access". | 1. Request is deleted from pending.<br>2. User is added to Active list.<br>3. Status writes to localStorage. | Critical | REQ-USR-03 |
| **TC-USR-04** | Deny Operator Access request | "Pending Requests" tab active | 1. Locate pending user and click "Deny Request". | 1. Access request is permanently rejected and removed from DOM/state. | High | REQ-USR-03 |

---

## 8. Sidebar Shell Navigation

### Pages under Test:
*   [AdminSidebar.tsx](file:///d:/FiremeX/src/components/sidebar/AdminSidebar.tsx)
*   [AdminLayout.tsx](file:///d:/FiremeX/src/layouts/AdminLayout.tsx)

| Test Case ID | Title | Precondition | Test Steps | Expected Result | Priority | Req ID |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-NAV-01** | Highlight active sidebar menu | User shifts pages | 1. Navigate to `/FiremeX/admin/livefeed`. | 1. Live Feed navigation button in sidebar highlights with accent color border (border-l-4). | High | REQ-NAV-01 |
| **TC-NAV-02** | User Profile footer data rendering | User is inside admin dashboard layout | 1. Verify user profile card details in bottom-left footer. | 1. Displays correct user name initials "JS".<br>2. Status indicator is green (online). | Medium | REQ-NAV-02 |
