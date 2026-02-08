# Migration Guide: Anthropic API → AWS Bedrock

This guide helps you migrate from the Anthropic API version to the AWS Bedrock version of this project.

## 🔄 What Changed

### Dependencies
```diff
# requirements.txt
- langchain-anthropic==0.3.8
+ langchain-aws==0.2.6
- anthropic==0.43.0
+ boto3==1.35.93
```

### Environment Variables
```diff
# .env
- ANTHROPIC_API_KEY=sk-ant-...
+ AWS_ACCESS_KEY_ID=AKIA...
+ AWS_SECRET_ACCESS_KEY=...
+ AWS_REGION=us-east-1
```

### Code Changes
```diff
# orchestration/pipeline.py
- from langchain_anthropic import ChatAnthropic
+ from langchain_aws import ChatBedrock

- llm = ChatAnthropic(
-     model="claude-sonnet-4-5-20250929",
-     temperature=0,
-     max_tokens=4000
- )
+ llm = ChatBedrock(
+     model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
+     region_name=os.getenv("AWS_REGION", "us-east-1"),
+     model_kwargs={
+         "temperature": 0,
+         "max_tokens": 4000
+     }
+ )
```

## 📋 Migration Steps

### 1. Update Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Uninstall old packages
pip uninstall langchain-anthropic anthropic -y

# Install new packages
pip install langchain-aws boto3
```

### 2. Update Environment Variables

```bash
# Edit .env file
nano .env

# Remove:
# ANTHROPIC_API_KEY=...

# Add:
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
```

### 3. Enable Bedrock Model Access

See `AWS_SETUP.md` for detailed instructions:

1. Log into AWS Console
2. Navigate to Amazon Bedrock
3. Go to "Model access"
4. Enable "Claude 3.5 Sonnet v2"
5. Wait for approval

### 4. Test the Migration

```bash
# Test AWS Bedrock connectivity
python test_aws_bedrock.py

# If successful, run the pipeline test
python test_pipeline.py
```

## 🆚 Feature Comparison

| Feature | Anthropic API | AWS Bedrock |
|---------|---------------|-------------|
| Model | Claude Sonnet 4.5 | Claude Sonnet 4.5 |
| Capabilities | Same | Same |
| Pricing | Direct billing | AWS billing |
| Rate Limits | Anthropic limits | AWS Bedrock limits |
| Regions | Global | Region-specific |
| Authentication | API key | AWS credentials/IAM |
| Credits | Anthropic credits | AWS credits ✅ |

## ✅ Advantages of AWS Bedrock

1. **Use AWS Credits**: Perfect if you have AWS promotional credits
2. **IAM Integration**: Use AWS IAM roles instead of managing API keys
3. **Regional Deployment**: Deploy close to your data
4. **Unified Billing**: Everything on one AWS bill
5. **AWS Ecosystem**: Integrate with other AWS services (S3, Lambda, etc.)

## ⚠️ Considerations

1. **Model Access Required**: You must request and receive model access in Bedrock
2. **Region Availability**: Claude Sonnet 4.5 not available in all AWS regions
3. **Rate Limits**: Different from Anthropic API (check AWS quotas)
4. **Pricing**: May differ slightly from direct Anthropic pricing

## 🔍 Verification

After migration, verify everything works:

```bash
# 1. AWS connectivity
python test_aws_bedrock.py
# Should show: "ALL TESTS PASSED!"

# 2. Pipeline execution
python test_pipeline.py
# Should process sample transcripts successfully

# 3. API server
cd api && uvicorn main:app --reload
# Test at http://localhost:8000/docs
```

## 💰 Cost Comparison

Both use the same Claude Sonnet 4.5 model, so costs are similar:

- **Anthropic API**: ~$3/M input tokens, ~$15/M output tokens
- **AWS Bedrock**: ~$3/M input tokens, ~$15/M output tokens

However:
- AWS may offer volume discounts
- AWS credits can offset costs
- Check current pricing: https://aws.amazon.com/bedrock/pricing/

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'langchain_aws'"

```bash
pip install langchain-aws boto3
```

### "Access Denied" errors

1. Check AWS credentials are correct
2. Verify IAM permissions include `bedrock:InvokeModel`
3. Ensure model access is granted in Bedrock console

### "Model not found"

1. Check you're using the right region
2. Verify model ID: `us.anthropic.claude-sonnet-4-20250514-v1:0`
3. Confirm region supports this model

See `AWS_SETUP.md` for more troubleshooting tips.

## 🔙 Rollback (If Needed)

To revert to Anthropic API:

```bash
# 1. Reinstall old dependencies
pip uninstall langchain-aws boto3 -y
pip install langchain-anthropic anthropic

# 2. Update .env
# Remove AWS credentials
# Add ANTHROPIC_API_KEY=...

# 3. Update orchestration/pipeline.py
# Change ChatBedrock back to ChatAnthropic
# (See git diff or previous version)
```

## 📚 Additional Resources

- AWS Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
- LangChain AWS: https://python.langchain.com/docs/integrations/chat/bedrock
- Model Access Guide: See `AWS_SETUP.md`
