# Vulnerability Management Data Analysis Prompt

## Overview
You are analyzing Jira vulnerability management data to provide insights on security performance, SLA compliance, and process bottlenecks. Use this prompt to understand data format, calculation methods, and analysis requirements.

## Data Format Specification

### Expected CSV Structure
The vulnerability data will be in CSV format with these key columns:
- **Issue Type**: Always "Vulnerability" for security issues
- **Issue key**: Unique identifier (e.g., "PC-22264", "BILL-28826")
- **Issue id**: Numeric ID
- **Summary**: Description of the vulnerability
- **Project name**: Team/project responsible (e.g., "Integrations", "Hub Platform")
- **Status**: Current workflow state
- **Custom field (Security Impact)**: Criticality and SLA information
- **Custom field (Discovery Source:)**: How vulnerability was found
- **Created**: Creation date
- **Due date**: SLA deadline
- **Priority**: Jira priority field

### Date Format
Dates appear as: "DD/MMM/YY H:MM AM/PM" (e.g., "21/Feb/23 11:27 PM")

### Status Values
Key status values to analyze:
- **"Needs Risk Owner Triage"**: Awaiting initial assignment (primary bottleneck)
- **"In Progress"**: Actively being worked
- **"Due Date Extension Proposed"**: Encountering implementation delays  
- **"Done"**: Completed

### Security Impact Format
Criticality levels with embedded SLA information:
- **"P1: High - [15 Days SLA]"**: Most critical, 15-day deadline
- **"P2: Medium - [45 Days SLA]"**: Medium criticality, 45-day deadline
- **"P3: Low - [90 Days SLA]"**: Lower criticality, 90-day deadline

## SLA Calculation Methods

### SLA Compliance Determination
```
IF Due_Date < Current_Date THEN
    Status = "Past Due" (SLA Miss)
    Days_Past_Due = Current_Date - Due_Date
ELSE
    Status = "Within SLA"
    Days_Remaining = Due_Date - Current_Date
```

### Triage Time Analysis
```
Triage_Days = Current_Date - Created_Date (for items in "Needs Risk Owner Triage")
SLA_Consumption_Percentage = (Triage_Days / Total_SLA_Days) * 100
```

### Key Metrics to Calculate
1. **Overall SLA Miss Rate**: (Past_Due_Count / Total_With_Due_Dates) * 100
2. **Triage Percentage**: (Items_In_Triage / Total_Items) * 100
3. **Average Triage Time**: Mean days in "Needs Risk Owner Triage" status
4. **Team Performance**: SLA miss rates by "Project name"
5. **Impact Distribution**: Count/percentage by P1/P2/P3 levels

## Analysis Framework

### Required Analysis Sections

#### 1. Executive Summary
- Total vulnerability count
- Overall SLA miss rate
- Primary bottleneck identification

#### 2. Project Distribution (Teams)
- Vulnerability count by "Project name"
- Percentage distribution
- Top teams by volume

#### 3. Security Impact Analysis
- Distribution by P1/P2/P3 levels
- Status breakdown within each impact level
- Cross-reference impact vs. actual performance

#### 4. Discovery Source Analysis
- Vulnerability count by discovery method
- Effectiveness rates (which sources find high-impact issues)

#### 5. SLA Performance Analysis
- Past-due analysis by team, impact level, and time periods
- Monthly/quarterly trend analysis
- Most severe overdue cases

#### 6. Triage Performance Analysis
- Time spent in triage vs. total SLA
- Items past full SLA while still in triage
- Triage bottleneck quantification

#### 7. Root Cause & Remediation Insights
- Pattern analysis for process bottlenecks
- Team-specific performance variations
- Remediation opportunity identification

### Critical Analysis Rules

#### SLA Miss Calculation
- Only count items with due dates
- Use actual current date, not system date
- Consider timezone if specified

#### Percentage Calculations
- Always show both count and percentage: "X items (Y%)"
- Round percentages to 1 decimal place
- Include denominators for transparency

#### Time Calculations
- Calculate days using full date arithmetic
- For partial months, use actual days
- Handle missing dates gracefully

#### Data Quality Checks
- Identify items with missing due dates
- Flag inconsistencies between impact level and SLA days
- Note any unusual status values

### Trend Analysis Requirements

#### Monthly Analysis
- Group by due date month
- Calculate miss rate for each month
- Only include months where due dates have passed

#### Quarterly Analysis  
- Handle non-standard quarters if specified
- Calculate quarterly miss rates
- Show volume and percentage trends

### Output Format Guidelines

#### Tables
- Use clear headers with units
- Sort by relevance (highest impact first)
- Include both absolute numbers and percentages

#### Insights
- Present findings factually without emotional language
- Avoid prescriptive recommendations unless specifically requested
- Focus on data-driven observations

#### Charts (if creating)
- Line charts for time trends
- Tables for distributions
- Include data labels and clear legends

## Key Questions to Answer

1. **What percentage of vulnerabilities are past their SLA?**
2. **Where are the primary process bottlenecks?**
3. **Which teams have the highest SLA miss rates?**
4. **How long do vulnerabilities spend in triage vs. total SLA time?**
5. **Are high-priority items actually getting faster attention?**
6. **What discovery sources are most/least effective?**
7. **How has SLA performance changed over time?**
8. **What patterns suggest specific remediation opportunities?**

## Common Pitfalls to Avoid

- Don't forecast future performance unless explicitly requested
- Don't assume what constitutes "acceptable" performance levels
- Don't ignore data quality issues (missing dates, inconsistent formats)
- Don't mix different types of percentages without clear labeling
- Don't make assumptions about organizational priorities or risk tolerance

## Expected Deliverable

Provide a comprehensive vulnerability management analysis report that enables stakeholders to understand current performance, identify bottlenecks, and make data-driven decisions about security process improvements based on factual analysis rather than subjective assessments.
