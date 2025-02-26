import json
import urllib3
import re
import os

# Initialize HTTP client
http = urllib3.PoolManager()

# Slack webhook URL
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def format_value(metric_name, value):
    """
    Converts bytes to GB, seconds to ms, and formats CPU utilization with %.
    """
    if metric_name in ["FreeableMemory", "FreeLocalStorage"]:
        return f"{value / (1024 ** 3):.2f} GB"
    elif metric_name in ["WriteLatency", "ReadLatency"]:
        return f"{value * 1000:.2f} ms"
    elif metric_name == "CPUUtilization":
        return f"{value:.2f} %"
    return f"{value:.2f}"

def extract_and_convert_value(reason_text):
    """
    Extracts the first numeric value from NewStateReason.
    Handles scientific notation by converting it correctly.
    """
    match = re.search(r"\[([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", reason_text)
    if not match:
        return None

    extracted_value = match.group(1)
    print(f"Extracted raw value: {extracted_value}")

    # Handle scientific notation
    if "e" in extracted_value or "E" in extracted_value:
        base, exponent = extracted_value.split("E") if "E" in extracted_value else extracted_value.split("e")
        base = float(base)
        exponent = int(exponent)

        if exponent >= 0:  # E+X → Multiply by 10^X
            converted_value = base * (10 ** exponent)
        else:  # E-X → Divide by 10^X
            converted_value = base / (10 ** abs(exponent))
    else:
        converted_value = float(extracted_value)

    print(f"Converted value: {converted_value}")
    return converted_value

def format_reason(sns_message):
    """
    Extracts the most recent value from NewStateReason and formats it as:
    "Current value X < threshold value Y"
    """
    reason_text = sns_message.get("NewStateReason", "No reason provided.")
    print(f"reason_text: {reason_text}")
    trigger = sns_message["Trigger"]
    metric_name = trigger.get("MetricName", "Unknown Metric")
    threshold = trigger["Threshold"]

    # Extract DB Instance Name
    db_instance = "Unknown"
    for dim in trigger.get("Dimensions", []):
        if dim["name"] == "DBInstanceIdentifier":
            db_instance = dim["value"]

    try:
        # Extract and convert the first numeric value
        current_value = extract_and_convert_value(reason_text)
        if current_value is None:
            return f"Could not parse reason: {reason_text}", db_instance

        # Format values
        formatted_current_value = format_value(metric_name, current_value)
        formatted_threshold = format_value(metric_name, threshold)

        # Determine comparison symbol (</>)
        comparison = "<" if current_value < threshold else ">"

        return f"Current value {formatted_current_value} {comparison} threshold value {formatted_threshold}", db_instance

    except Exception as e:
        return f"Error parsing reason: {str(e)}", db_instance

def lambda_handler(event, context):
    """
    AWS Lambda function to process CloudWatch alarms and send notifications to Slack.
    """
    try:
        sns_message = json.loads(event["Records"][0]["Sns"]["Message"])
        alarm_name = sns_message["AlarmName"].split(" DBInstanceIdentifier=")[0]
        reason, db_instance = format_reason(sns_message)

        # Construct Slack message
        slack_message = {
            "text": f"⚠️ *RDS Alert Triggered!* ⚠️\n"
                    f"*Alarm:* `{alarm_name}`\n"
                    f"*DB Instance:* `{db_instance}`\n"
                    f"*Reason:* `{reason}`"
        }

        # Send message to Slack
        encoded_message = json.dumps(slack_message).encode("utf-8")
        response = http.request("POST", SLACK_WEBHOOK_URL, body=encoded_message, headers={"Content-Type": "application/json"})

        return {"statusCode": response.status, "body": "Message sent to Slack"}

    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
