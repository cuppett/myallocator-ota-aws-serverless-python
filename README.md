MyAllocator OTA AWS Lambda API
==============================

Python web service using AWS Lambda and Amazon API Gateway. This implements the 
[OTA Build-To-Us API](https://myallocator.github.io/build2us-apidocs/index.html) from 
[myallocator](https://myallocator.com) and [cloudbeds](http://cloudbeds.com). This minimal 
sample (paired with an AWS Multi-AZ RDS instance) allows creating an HA API endpoint to 
service the integration between your OTA channel and cloudbeds. 

## Pre-requisites for building

1) Python 3.6
2) [AWS CLI](https://aws.amazon.com/cli/) installed and configured
3) S3 bucket for deployment package

## Building the package

Using the steps in buidspec.yml, you can run similar commands on a Linux system to create the
 environment, run the tests & generate the deployment package.

## Pre-requisites for deployment

1) AWS Account with VPC
2) MySQL database deployed with schema from schema.sql

## Deploying

Using the generated template-export.yml, you can use AWS CloudFormation to create the
stack. The stack will generate the Lambda function, the API Gateway and wire it all up.
