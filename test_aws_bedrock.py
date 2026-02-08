#!/usr/bin/env python3
"""
Test AWS Bedrock connectivity before running the full pipeline.
This ensures your AWS credentials and Bedrock access are configured correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_aws_credentials():
    """Check if AWS credentials are configured"""
    print("=" * 80)
    print("AWS CREDENTIALS CHECK")
    print("=" * 80)
    
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    if not access_key and not secret_key:
        print("ℹ️  No AWS credentials in .env")
        print("   Checking for IAM role or AWS CLI profile...")
        # boto3 will auto-detect credentials
    elif access_key and secret_key:
        print(f"✅ AWS credentials found in .env")
        print(f"   Access Key: {access_key[:10]}...")
        print(f"   Region: {region}")
    else:
        print("⚠️  Incomplete AWS credentials in .env")
        print(f"   AWS_ACCESS_KEY_ID: {'✅' if access_key else '❌'}")
        print(f"   AWS_SECRET_ACCESS_KEY: {'✅' if secret_key else '❌'}")
        return False
    
    return True


def test_boto3():
    """Test boto3 can create a client"""
    print("\n" + "=" * 80)
    print("BOTO3 CLIENT TEST")
    print("=" * 80)
    
    try:
        import boto3
        
        # Try to create Bedrock client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION", "us-east-1")
        )
        
        print("✅ Successfully created Bedrock runtime client")
        print(f"   Region: {bedrock.meta.region_name}")
        
        return True, bedrock
        
    except Exception as e:
        print(f"❌ Failed to create Bedrock client: {str(e)}")
        return False, None


def test_bedrock_access(bedrock):
    """Test actual Bedrock API access"""
    print("\n" + "=" * 80)
    print("BEDROCK API TEST")
    print("=" * 80)
    
    import json
    
    try:
        # Simple test invocation
        response = bedrock.invoke_model(
            modelId='us.anthropic.claude-sonnet-4-20250514-v1:0',
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 50,
                "messages": [
                    {"role": "user", "content": "Say 'AWS Bedrock connection successful' and nothing else."}
                ]
            })
        )
        
        # Parse response
        result = json.loads(response['body'].read())
        response_text = result['content'][0]['text']
        
        print("✅ Successfully invoked Claude Sonnet 4.5 via Bedrock")
        print(f"   Model response: {response_text}")
        print(f"   Tokens used: {result.get('usage', {}).get('input_tokens', 0)} input, {result.get('usage', {}).get('output_tokens', 0)} output")
        
        return True
        
    except bedrock.exceptions.AccessDeniedException:
        print("❌ Access Denied")
        print("   Solution: Enable Claude Sonnet 4.5 model access in AWS Bedrock console")
        print("   Steps:")
        print("   1. Go to AWS Bedrock console")
        print("   2. Navigate to 'Model access'")
        print("   3. Click 'Manage model access'")
        print("   4. Enable 'Anthropic > Claude 3.5 Sonnet v2'")
        print("   5. Submit and wait for approval")
        return False
        
    except bedrock.exceptions.ResourceNotFoundException:
        print("❌ Model Not Found")
        print("   Solution: Check your AWS region supports Claude Sonnet 4.5")
        print("   Supported regions: us-east-1, us-west-2, eu-west-1, ap-northeast-1")
        print(f"   Current region: {os.getenv('AWS_REGION', 'us-east-1')}")
        return False
        
    except Exception as e:
        print(f"❌ Bedrock API error: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        return False


def test_langchain_integration():
    """Test LangChain AWS integration"""
    print("\n" + "=" * 80)
    print("LANGCHAIN INTEGRATION TEST")
    print("=" * 80)
    
    try:
        from langchain_aws import ChatBedrock
        from langchain_core.messages import HumanMessage
        
        # Create LangChain Bedrock chat
        llm = ChatBedrock(
            model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            model_kwargs={
                "temperature": 0,
                "max_tokens": 50
            }
        )
        
        # Test invocation
        messages = [HumanMessage(content="Say 'LangChain integration working' and nothing else.")]
        response = llm.invoke(messages)
        
        print("✅ LangChain AWS integration working")
        print(f"   Response: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ LangChain integration failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("AWS BEDROCK CONNECTIVITY TEST")
    print("=" * 80)
    print("\nThis script tests your AWS Bedrock setup before running the task extraction pipeline.\n")
    
    # Test 1: Credentials
    if not test_aws_credentials():
        print("\n❌ FAILED: AWS credentials not properly configured")
        print("\nSee AWS_SETUP.md for detailed setup instructions.")
        return 1
    
    # Test 2: Boto3
    boto3_ok, bedrock = test_boto3()
    if not boto3_ok:
        print("\n❌ FAILED: Cannot create Bedrock client")
        print("\nCheck your AWS credentials and region configuration.")
        return 1
    
    # Test 3: Bedrock API
    if not test_bedrock_access(bedrock):
        print("\n❌ FAILED: Bedrock API access denied or model not available")
        print("\nSee AWS_SETUP.md for troubleshooting steps.")
        return 1
    
    # Test 4: LangChain
    if not test_langchain_integration():
        print("\n❌ FAILED: LangChain integration issue")
        print("\nEnsure langchain-aws is installed: pip install langchain-aws")
        return 1
    
    # All tests passed
    print("\n" + "=" * 80)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 80)
    print("\nYour AWS Bedrock setup is working correctly.")
    print("You can now run the task extraction pipeline:")
    print("  python test_pipeline.py")
    print("  cd api && uvicorn main:app --reload")
    print("")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
