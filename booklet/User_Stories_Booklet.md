# User Stories Booklet

## Project
Mars Habitat Control

## Document Goal
Collect all user stories in one booklet, each including:
- user story text
- functional description
- specific LoFi mockup to produce

## Mockup Naming Convention
To keep references consistent, export each mockup in `booklet/mockups/` using the filename shown in each section.

---

## US-01 - Compact Rules View
**User story**  
As the User I want to see all the rules in a compact way.

**Description**  
The user needs a concise tabular view of rules, with essential columns (sensor, metric, condition, actuator, action, status), so they can quickly understand the current configuration.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-01_rules_compact_view_lofi.png`
- Content: Rules section header, compact table, status badges, row action buttons.

## US-02 - Add New Rule
**User story**  
As the User I want to add a new rule.

**Description**  
The user must be able to create a rule from a dedicated form by entering sensor, metric, operator, threshold, actuator, and action. After saving, they should receive clear feedback.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-02_add_rule_form_lofi.png`
- Content: Add Rule button, modal/form fields, Save/Cancel buttons.

## US-03 - Remove Existing Rule
**User story**  
As the User I want to remove an existing rule.

**Description**  
The user deletes a rule from the list using a dedicated action. Deletion should require confirmation, and the table should refresh immediately.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-03_delete_rule_lofi.png`
- Content: Table row with Delete button, confirmation dialog.

## US-04 - Edit Existing Rule
**User story**  
As the User I want to modify an existing rule.

**Description**  
The user can update an existing rule. Current values should be prefilled and editable before saving.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-04_edit_rule_lofi.png`
- Content: Rules table with Edit action, modal with current values.

## US-05 - Enable/Disable Rule
**User story**  
As the User I want to enable/disable an existing rule.

**Description**  
The user should be able to activate or deactivate a rule without deleting it. Status must be clearly visible.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-05_toggle_rule_lofi.png`
- Content: Status column, Enable/Disable button on each row.

## US-06 - Reset Rules
**User story**  
As the User I want to reset the rules.

**Description**  
The user restores the default rule set. The action should be protected by confirmation to prevent accidental resets.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-06_reset_rules_lofi.png`
- Content: Reset Rules button, confirmation modal, post-reset state.

## US-07 - Rule Persistence
**User story**  
As the User I want to save all rules persistently.

**Description**  
Created or updated rules must remain available after system restarts through database persistence.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-07_rules_persistence_lofi.png`
- Content: Rules view before/after restart, persistent save indicator.

## US-08 - Show Violated Rules
**User story**  
As the User I want to see which sensors violate the rules.

**Description**  
When a sensor value violates an active rule, the UI should highlight the case and clearly link it to the violated rule.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-08_rule_violation_lofi.png`
- Content: Highlighted metric, Rule Violated label, reference to related rule.

## US-09 - Show Active Actuators
**User story**  
As the User I want to see the current active actuators.

**Description**  
The user should see the actuator list with ON/OFF state in near real time and with immediate visual distinction.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-09_active_actuators_lofi.png`
- Content: Actuator cards/rows, ON/OFF state, state icons.

## US-10 - Show Active Sensors
**User story**  
As the User I want to see the current active sensors.

**Description**  
The user views sensors and current metrics with value, unit, source, and time since last update.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-10_active_sensors_lofi.png`
- Content: Sensor cards section, metric rows with metadata.

## US-11 - Manual Actuator Control
**User story**  
As the User I want to manually turn on/off a specific actuator.

**Description**  
The user must be able to send manual ON/OFF commands for a single actuator, with immediate UI state update.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-11_manual_actuator_control_lofi.png`
- Content: Toggle buttons on each actuator, command feedback.

## US-12 - Reset All Actuators to OFF
**User story**  
As the User I want to reset all actuators to off.

**Description**  
With one action, the user sets all actuators to OFF, with prior confirmation and state refresh.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-12_reset_actuators_lofi.png`
- Content: Reset Actuators button, confirmation dialog, OFF states.

## US-13 - Sensor Data Charts
**User story**  
As the User I want to visualize charts regarding current data from sensors.

**Description**  
The user selects a metric and visualizes its trend over time on a dynamically updated chart.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-13_sensor_charts_lofi.png`
- Content: Metric selector, chart area, minimal legend.

## US-14 - Group Related Sensors
**User story**  
As the User I want to visualize related sensors near to each other.

**Description**  
Metrics should be grouped by logical categories (for example air, power, priority) to improve operational readability.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-14_grouped_sensors_lofi.png`
- Content: Collapsible groups with related sensors.

## US-15 - Time Since Latest Update
**User story**  
As the User I want to see how much time has passed since the latest update.

**Description**  
Each metric should show relative time since last update (for example 00:12 ago), so data freshness is clear.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-15_last_update_time_lofi.png`
- Content: Updated field in each metric row with relative format.

## US-16 - Dangerous Conditions in Red
**User story**  
As the User I want to visualize dangerous conditions as red.

**Description**  
Critical conditions should use a consistent red color coding across cards, badges, or rows to emphasize urgency.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-16_danger_red_visual_lofi.png`
- Content: Normal vs danger state example with red highlight.

## US-17 - Dashboard KPI Counters
**User story**  
As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.

**Description**  
At the top of the dashboard, the user should always see four live counters: sensors, live telemetry, active rules, and actuators ON.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-17_dashboard_kpis_lofi.png`
- Content: Four KPI cards with label and numeric value.

## US-18 - Show Warning Sensors
**User story**  
As the User I want to see which sensors are in warning status.

**Description**  
Warning status must be visible with a dedicated badge and clearly distinct from ok/error to support preventive monitoring.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-18_warning_status_lofi.png`
- Content: Warning status badge on one or more metrics.

## US-19 - Quick Access to Alerts Section
**User story**  
As the User I want to directly access the alert section by clicking on a single button.

**Description**  
A dedicated button should take the user directly to the alerts section with automatic scrolling and visible focus.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-19_jump_to_alerts_lofi.png`
- Content: Jump to Alerts button and highlighted destination section.

## US-20 - Notification on Rule Violation
**User story**  
As the User I want to be notified when a rule has been broken.

**Description**  
When a new violation occurs, the user receives a clear notification (event log or toast) with essential information.

**Specific mockup (LoFi)**  
- File: `booklet/mockups/US-20_rule_broken_notification_lofi.png`
- Content: Notification/alert stream example with violation message.

---

## Operational Note
If you want, as next step I can create all 20 placeholder image files in `booklet/mockups/` (already with the correct names), so you only need to overwrite them with Figma/Balsamiq exports.
