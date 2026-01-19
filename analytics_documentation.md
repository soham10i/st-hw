
# Analytics Dashboard Documentation

This document provides a guide to understanding and using the Analytics Dashboard in the ST-HW system. The dashboard offers historical insights into the factory's performance, component health, and energy consumption.

## 1. Overview

The Analytics Dashboard is a powerful tool for visualizing time-series data, analyzing breakdown events, and gaining predictive insights into the health of the factory's components. It is designed to help maintenance teams, operations managers, and data analysts make informed decisions.

## 2. How to Read the Dashboard

The dashboard is organized into several sections, each providing a different perspective on the factory's performance.

### 2.1. Key Performance Indicators (KPIs)

The top of the dashboard displays a set of Key Performance Indicators (KPIs) that provide a high-level summary of the factory's performance over the selected time period.

| KPI | Description |
|---|---|
| **Total Energy (MJ)** | The total energy consumed by the factory in megajoules. |
| **Total Operations** | The total number of operations (store, retrieve, process) performed. |
| **Avg Uptime** | The average uptime of the factory as a percentage. |
| **Critical Alerts** | The number of critical alerts that have been triggered. |

### 2.2. Breakdown Scenario Summary

This section provides a summary of any simulated breakdown events that have occurred. It highlights the key details of each event, such as the component that failed, the impact on production, and the associated sensor readings.

### 2.3. Analytics Tabs

The main body of the dashboard is organized into a series of tabs, each focusing on a specific aspect of the factory's performance.

#### 2.3.1. Motor Health

This tab provides a detailed view of the health of the factory's motors. It includes a line chart showing the health score of each motor over time, with a threshold line indicating when maintenance is required. This allows for proactive maintenance and helps prevent unexpected failures.

#### 2.3.2. Energy Analysis

This tab visualizes the factory's energy consumption. It includes charts showing the total energy consumed per day and the average power consumption of each device. This information can be used to identify energy-intensive processes and opportunities for optimization.

#### 2.3.3. Production Metrics

This tab focuses on the factory's production throughput. It includes charts showing the number of operations performed per day, the average cycle time, and the overall equipment effectiveness (OEE). These metrics are essential for understanding the factory's productivity and identifying bottlenecks.

#### 2.3.4. Alerts & Events

This tab provides a log of all system alerts and events. It allows users to filter alerts by severity and device, making it easy to investigate specific issues. This is a critical tool for troubleshooting and root cause analysis.

#### 2.3.5. Predictive Insights

This tab offers predictive insights into the health of the factory's components. It uses historical data to forecast future health scores and estimate the remaining useful life (RUL) of each component. This enables predictive maintenance, which can significantly reduce downtime and maintenance costs.

## 3. How to Use the Dashboard

The Analytics Dashboard is designed to be interactive and easy to use.

### 3.1. Settings

The sidebar on the left of the dashboard provides a set of settings that allow you to customize the data being displayed.

-   **Date Range**: Select the time period for which you want to view data (e.g., Last 7 Days, Last 30 Days).
-   **Device Filter**: Filter the data to show only specific devices (e.g., HBW, VGR, Conveyor).
-   **Breakdown Scenarios**: Toggle the visibility of breakdown event highlights on the charts.

### 3.2. Interacting with Charts

The charts on the dashboard are interactive. You can:

-   **Hover**: Hover over data points to view detailed information.
-   **Zoom**: Zoom in on specific time periods to get a more granular view.
-   **Pan**: Pan across the charts to explore the data.
-   **Filter**: Click on items in the legend to toggle their visibility on the chart.

By using these interactive features, you can gain a deeper understanding of the factory's performance and identify trends and anomalies that may not be apparent at first glance.
