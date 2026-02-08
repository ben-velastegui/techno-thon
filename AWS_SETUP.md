# AWS Bedrock Setup Guide

This project uses **AWS Bedrock** to access Claude Sonnet 4.5 for LLM operations.

## 🔑 Prerequisites

1. **AWS Account** with Bedrock access
2. **Claude Sonnet 4.5 Model Access** enabled in your AWS region
3. **AWS Credentials** (access key or IAM role)

## 📍 Enable Bedrock Model Access

### Step 1: Navigate to Bedrock Console

1. Log into AWS Console
2. Navigate to **Amazon Bedrock** service
3. Select your preferred region (e.g., `us-east-1`)

### Step 2: Request Model Access

1. Go to **Model access** in the left sidebar
2. Click **Manage model access** or **Edit**
3. Find **Anthropic** section
4. Enable:
   - ✅ **Claude 3.5 Sonnet v2** (model ID: `us.anthropic.claude-sonnet-4-20250514-v1:0`)
5. Submit the request
6. Wait for approval (usually instant for existing accounts)

### Step 3: Verify Access

Once approved, the model status should show **Access granted** in green.

## 🔐 Authentication Options

### Option 1: Access Keys (Quick Start)

**For development/testing:**

1. Create IAM user with Bedrock permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream"
         ],
         "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
       }
     ]
   }
   ```

2. Generate access key for the user
3. Add to `.env`:
   ```bash
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=...
   AWS_REGION=us-east-1
   ```

### Option 2: IAM Roles (Recommended for Production)

**For EC2/ECS/Lambda deployments:**

1. Create IAM role with Bedrock permissions (same policy as above)
2. Attach role to your compute resource
3. **Remove** AWS credentials from `.env`:
   ```bash
   # AWS_ACCESS_KEY_ID=  # Not needed with IAM role
   # AWS_SECRET_ACCESS_KEY=  # Not needed with IAM role
   AWS_REGION=us-east-1
   ```

The boto3 SDK will automatically use the instance role.

### Option 3: AWS CLI Profile

**For local development with multiple AWS accounts:**

1. Configure AWS CLI profile:
   ```bash
   aws configure --profile task-extraction
   ```

2. Set environment variable:
   ```bash
   export AWS_PROFILE=task-extraction
   ```

3. Only set region in `.env`:
   ```bash
   AWS_REGION=us-east-1
   ```

## 🌍 Supported Regions

Claude Sonnet 4.5 is available in these regions (as of Feb 2026):

- ✅ `us-east-1` (US East - N. Virginia) - **Recommended**
- ✅ `us-west-2` (US West - Oregon)
- ✅ `eu-west-1` (Europe - Ireland)
- ✅ `ap-northeast-1` (Asia Pacific - Tokyo)

**Note**: Model availability may vary by region. Check the Bedrock console for your region.

## 🧪 Test Bedrock Access

Before running the full pipeline, test your Bedrock access:

```python
import boto3
import json

# Create Bedrock runtime client
bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

# Test invocation
response = bedrock.invoke_model(
    modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Say hello"}
        ]
    })
)

# Parse response
result = json.loads(response['body'].read())
print(result['content'][0]['text'])
```

If this works, your Bedrock access is configured correctly!

## 💰 Pricing

As of Feb 2026, Claude Sonnet 4.5 on Bedrock pricing (us-east-1):

- **Input tokens**: ~$3 per million tokens
- **Output tokens**: ~$15 per million tokens

**Estimated cost per task extraction**: $0.01 - $0.05 depending on transcript length

Use AWS Cost Explorer to monitor actual usage.

## 🐛 Troubleshooting

### "Access denied" errors

1. Verify model access is granted in Bedrock console
2. Check IAM permissions include `bedrock:InvokeModel`
3. Confirm you're using the correct region

### "Model not found" errors

1. Check model ID is correct: `us.anthropic.claude-sonnet-4-20250514-v1:0`
2. Verify region supports this model
3. Ensure model access request was approved

### "Invalid credentials" errors

1. Check AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
2. Verify credentials haven't expired
3. Test with AWS CLI: `aws bedrock list-foundation-models`

### "Rate limit exceeded" errors

Bedrock has rate limits:
- **Invocations**: 2,000 requests per minute (default)
- **Tokens**: 200,000 input tokens per minute

Request a quota increase if needed in the Service Quotas console.

## 📚 Additional Resources

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Anthropic Models on Bedrock](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [LangChain AWS Integration](https://python.langchain.com/docs/integrations/chat/bedrock)

## 🔄 Migration Notes

This project was updated from direct Anthropic API to AWS Bedrock:

**Changed:**
- ❌ `ANTHROPIC_API_KEY` → ✅ `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
- ❌ `langchain-anthropic` → ✅ `langchain-aws`
- ❌ `ChatAnthropic` → ✅ `ChatBedrock`

**Same model, different access method:**
- Model: Claude Sonnet 4.5 (same capabilities)
- Billing: Through AWS instead of Anthropic directly
- Region-specific deployment required
