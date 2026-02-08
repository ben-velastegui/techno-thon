# ☁️ AWS Bedrock Version - Quick Start

This version of the Task Extraction System uses **AWS Bedrock** to access Claude Sonnet 4.5.

Perfect for users with **AWS promotional credits** or existing AWS infrastructure.

## 🎯 Why AWS Bedrock?

- ✅ **Use AWS Credits**: Leverage your AWS promotional or organizational credits
- ✅ **IAM Integration**: Secure access via AWS IAM roles (no API keys needed)
- ✅ **Regional Deployment**: Deploy in your preferred AWS region
- ✅ **Unified Billing**: Everything on one AWS bill
- ✅ **AWS Ecosystem**: Easy integration with S3, Lambda, ECS, etc.

## 🚀 Quick Start (5 Steps)

### 1. Enable Bedrock Model Access

**Before anything else**, enable Claude Sonnet 4.5 in AWS Bedrock:

1. Log into AWS Console
2. Navigate to **Amazon Bedrock** service
3. Go to **Model access** → **Manage model access**
4. Enable **Anthropic > Claude 3.5 Sonnet v2**
5. Submit (usually approved instantly)

### 2. Get AWS Credentials

**Option A: Access Keys (Quick)**
```bash
# Create IAM user with Bedrock permissions
# Generate access key
# Add to .env:
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
```

**Option B: IAM Role (Recommended)**
```bash
# If running on EC2/ECS/Lambda
# Attach IAM role with Bedrock permissions
# No credentials needed in .env!
AWS_REGION=us-east-1
```

See **`AWS_SETUP.md`** for detailed setup instructions.

### 3. Install & Setup

```bash
# Extract and setup
unzip task_extraction_poc.zip
cd task_extraction_poc
./setup.sh

# Edit .env with AWS credentials
nano .env
```

### 4. Test AWS Connection

```bash
# Activate environment
source venv/bin/activate

# Test Bedrock connectivity
python test_aws_bedrock.py
```

You should see:
```
🎉 ALL TESTS PASSED!
```

### 5. Run the System

```bash
# Test the pipeline
python test_pipeline.py

# Start the API
cd api && uvicorn main:app --reload

# Visit http://localhost:8000/docs
```

## 📊 Supported Regions

Claude Sonnet 4.5 is available in:

- ✅ **us-east-1** (N. Virginia) - Recommended
- ✅ **us-west-2** (Oregon)
- ✅ **eu-west-1** (Ireland)
- ✅ **ap-northeast-1** (Tokyo)

Choose the region closest to your users or data.

## 💰 Pricing

Same model, same pricing as Anthropic API:

- **Input**: ~$3 per million tokens
- **Output**: ~$15 per million tokens
- **Per task**: $0.01 - $0.05 typical

**Bonus**: Use your AWS credits!

## 📚 Documentation Files

- **`AWS_SETUP.md`** - Detailed AWS configuration guide
- **`README.md`** - Complete system documentation
- **`QUICKREF.md`** - Quick reference for common tasks
- **`MIGRATION.md`** - Migrating from Anthropic API
- **`VERIFICATION.md`** - Completeness checklist

## 🔧 IAM Permissions Required

Minimal IAM policy needed:

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

## 🐛 Common Issues

### "Access denied"
→ Enable model access in Bedrock console (see Step 1 above)

### "Model not found"
→ Check region supports Claude Sonnet 4.5 (see Supported Regions)

### "Invalid credentials"
→ Verify AWS credentials in .env or IAM role attached

**Full troubleshooting**: See `AWS_SETUP.md`

## 🎓 What You Get

Same powerful system as the Anthropic API version:

- ✅ LangGraph stateful pipeline
- ✅ Strict database grounding (no hallucination)
- ✅ Policy-driven validation
- ✅ Deterministic priority scoring
- ✅ Complete audit trail
- ✅ FastAPI REST endpoints

**Only difference**: Uses AWS Bedrock instead of Anthropic API

## 📞 Need Help?

1. **Setup Issues**: See `AWS_SETUP.md`
2. **Pipeline Questions**: See `README.md`
3. **Quick Commands**: See `QUICKREF.md`

## 🔄 Switching Back to Anthropic API?

See `MIGRATION.md` for rollback instructions (though you probably won't need to!)

---

**Ready to start?** Run `python test_aws_bedrock.py` to verify your setup! 🚀
