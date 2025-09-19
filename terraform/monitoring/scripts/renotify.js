"use strict";

const AWS = require('aws-sdk');
const cloudwatch = new AWS.CloudWatch();
const sns = new AWS.SNS();

exports.handler = async () => {
  const alarms = await cloudwatch.describeAlarms({ StateValue: 'ALARM' }).promise();
  const names = (alarms.MetricAlarms || []).map(a => a.AlarmName);
  if (!names.length) return;
  const message = `Still ALARM after 1h: ${names.join(', ')}`;
  await sns.publish({ TopicArn: process.env.SNS_TOPIC_ARN, Message: message, Subject: 'Monitoring re-notify' }).promise();
};
