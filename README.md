RDS CloudWatch Alert to Slack
This AWS Lambda function processes CloudWatch RDS alarms, formats the alert message into a human-readable format, and sends notifications to Slack via a webhook.

Setup Instructions
1. Create an AWS Lambda Function
- Go to ```AWS Lambda Console``` → Click ```Create Function```
- Select ```Author from Scratch```
- Runtime: ```Python 3.x```
- Create the function
2. Add Required Environment Variable
- In the ```Configuration``` tab, go to Environment Variables
- Key: SLACK_WEBHOOK_URL  
- Value: <Your Slack Webhook URL>
3. Add Required Permissions
- Attach the AWSLambdaBasicExecutionRole policy
4. Deploy the Code
- Copy and paste the code into the Lambda function editor
- Click ```Deploy```
5. Configure SNS Trigger
- Go to the ```Triggers``` tab → Click ```Add Trigger```
- Select ```SNS```
- Choose the SNS topic linked to your CloudWatch Alarms
6. Test the Setup

Expected Slack Message Format
```
:warning: RDS Alert Triggered! :warning:
Alarm: AWS/RDS FreeLocalStorage
DB Instance: staging-aurora-cluster-1
Reason: Current value 5.42 GB < threshold value 46.57 GB
```

Your Lambda function is now set up to monitor RDS metrics and send alerts to Slack.