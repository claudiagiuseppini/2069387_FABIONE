# User Stories Booklet

## US-01 - Compact Rules View
**User story**  
As the User I want to see all the rules in a compact way.

**Description**  
The user needs a concise tabular view of rules, with essential columns (sensor, metric, condition, actuator, action, status), so they can quickly understand the current configuration.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule1.png" alt="US-01 Compact Rules View LoFi" width="520" />
</p>

## US-02 - Add New Rule
**User story**  
As the User I want to add a new rule.

**Description**  
The user must be able to create a rule from a dedicated form by entering sensor, metric, operator, threshold, actuator, and action. After saving, they should receive clear feedback.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule2.png" alt="US-02 Add Rule Form LoFi - part 1" width="520" />
</p>
<p align="center">
	<img src="lo-fi%20mockup/rule2.1.png" alt="US-02 Add Rule Form LoFi - part 2" width="520" />
</p>

## US-03 - Remove Existing Rule
**User story**  
As the User I want to remove an existing rule.

**Description**  
The user deletes a rule from the list using a dedicated action. Deletion should require confirmation, and the table should refresh immediately.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule3.png" alt="US-03 Delete Rule LoFi" width="520" />
</p>

## US-04 - Edit Existing Rule
**User story**  
As the User I want to modify an existing rule.

**Description**  
The user can update an existing rule. Current values should be prefilled and editable before saving.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule4.png" alt="US-04 Edit Rule LoFi - part 1" width="520" />
</p>
<p align="center">
	<img src="lo-fi%20mockup/rule4.1.png" alt="US-04 Edit Rule LoFi - part 2" width="520" />
</p>

## US-05 - Enable/Disable Rule
**User story**  
As the User I want to enable/disable an existing rule.

**Description**  
The user should be able to activate or deactivate a rule without deleting it. Status must be clearly visible.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule5.png" alt="US-05 Toggle Rule LoFi" width="520" />
</p>

## US-06 - Reset Rules
**User story**  
As the User I want to reset the rules.

**Description**  
The user restores the default rule set. The action should be protected by confirmation to prevent accidental resets.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule6.png" alt="US-06 Reset Rules LoFi - part 1" width="520" />
</p>
<p align="center">
	<img src="lo-fi%20mockup/rule6.1.png" alt="US-06 Reset Rules LoFi - part 2" width="520" />
</p>

## US-07 - Rule Persistence
**User story**  
As the User I want to save all rules persistently.

**Description**  
Created or updated rules must remain available after system restarts through database persistence.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule7.png" alt="US-07 Rules Persistence LoFi" width="520" />
</p>

## US-08 - Show Violated Rules
**User story**  
As the User I want to see which sensors violate the rules.

**Description**  
When a sensor value violates an active rule, the UI should highlight the case and clearly link it to the violated rule.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule8.png" alt="US-08 Rule Violation LoFi" width="520" />
</p>

## US-09 - Show Active Actuators
**User story**  
As the User I want to see the current active actuators.

**Description**  
The user should see the actuator list with ON/OFF state in near real time and with immediate visual distinction.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule9.png" alt="US-09 Active Actuators LoFi" width="520" />
</p>

## US-10 - Show Active Sensors
**User story**  
As the User I want to see the current active sensors.

**Description**  
The user views sensors and current metrics with value, unit, source, and time since last update.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule10.png" alt="US-10 Active Sensors LoFi" width="520" />
</p>

## US-11 - Manual Actuator Control
**User story**  
As the User I want to manually turn on/off a specific actuator.

**Description**  
The user must be able to send manual ON/OFF commands for a single actuator, with immediate UI state update.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule11.png" alt="US-11 Manual Actuator Control LoFi" width="520" />
</p>

## US-12 - Reset All Actuators to OFF
**User story**  
As the User I want to reset all actuators to off.

**Description**  
With one action, the user sets all actuators to OFF, with prior confirmation and state refresh.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule12.png" alt="US-12 Reset Actuators LoFi - part 1" width="520" />
</p>
<p align="center">
	<img src="lo-fi%20mockup/rule12.1.png" alt="US-12 Reset Actuators LoFi - part 2" width="520" />
</p>

## US-13 - Sensor Data Charts
**User story**  
As the User I want to visualize charts regarding current data from sensors.

**Description**  
The user selects a metric and visualizes its trend over time on a dynamically updated chart.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule13.png" alt="US-13 Sensor Data Charts LoFi" width="520" />
</p>

## US-14 - Group Related Sensors
**User story**  
As the User I want to visualize related sensors near to each other.

**Description**  
Metrics should be grouped by logical categories (for example air, power, priority) to improve operational readability.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule14.png" alt="US-14 Group Related Sensors LoFi" width="520" />
</p>

## US-15 - Time Since Latest Update
**User story**  
As the User I want to see how much time has passed since the latest update.

**Description**  
Each metric should show relative time since last update (for example 00:12 ago), so data freshness is clear.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule15.png" alt="US-15 Time Since Latest Update LoFi" width="520" />
</p>

## US-16 - Dangerous Conditions in Red
**User story**  
As the User I want to visualize dangerous conditions as red.

**Description**  
Critical conditions should use a consistent red color coding across cards, badges, or rows to emphasize urgency.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule16.png" alt="US-16 Danger Red Visual LoFi" width="520" />
</p>

## US-17 - Dashboard KPI Counters
**User story**  
As the User I want to see the number of sensors, live telemetries, active rules and actuators currently on.

**Description**  
At the top of the dashboard, the user should always see four live counters: sensors, live telemetry, active rules, and actuators ON.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule17.png" alt="US-17 Dashboard KPI Counters LoFi" width="520" />
</p>

## US-18 - Show Warning Sensors
**User story**  
As the User I want to see which sensors are in warning status.

**Description**  
Warning status must be visible with a dedicated badge and clearly distinct from ok/error to support preventive monitoring.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule18.png" alt="US-18 Show Warning Sensors LoFi" width="520" />
</p>

## US-19 - Quick Access to Alerts Section
**User story**  
As the User I want to directly access the alert section by clicking on a single button.

**Description**  
A dedicated button should take the user directly to the alerts section with automatic scrolling and visible focus.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule19.1.png" alt="US-19.1 Quick Access to Alerts Section LoFi" width="520" />
</p>
<p align="center">
	<img src="lo-fi%20mockup/rule19.2.png" alt="US-19.2 Alerts Section Highlight LoFi" width="520" />
</p>

## US-20 - Notification on Rule Violation
**User story**  
As a User, I want to be notified when a rule has been broken, a violation has been resolved and when rules have been modified.

**Description**  
When a rule has been broken, a violation has been resolved and when rules have been modified, the user receives a clear notification (event log) with essential information.

**Specific mockup (LoFi)**  
<p align="center">
	<img src="lo-fi%20mockup/rule20.png" alt="US-20 Notification on Rule Violation LoFi" width="520" />
</p>
