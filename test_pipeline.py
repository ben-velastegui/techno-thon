#!/usr/bin/env python3
"""
Quick test script for Task Extraction Pipeline
Run this to verify the system works end-to-end
"""

import json
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestration.pipeline import run_pipeline


def test_extraction():
    """Test the extraction pipeline with sample transcripts"""
    
    test_cases = [
        {
            "name": "Urgent Medication Review",
            "transcript": "Dr. Chen here. I need to review Maria Garcia's medications ASAP. Her MRN is MRN005678. She mentioned some side effects during her last visit. This is urgent and should be done by tomorrow."
        },
        {
            "name": "Lab Follow-up",
            "transcript": "Mike Johnson speaking. We need to follow up on Robert Smith's lab results from yesterday. MRN009012. His potassium levels were critical. Please call him today."
        },
        {
            "name": "Patient Call",
            "transcript": "This is Emily Rodriguez. Can someone schedule a call with Jennifer Lee, MRN003456, to discuss her discharge plan? No rush, sometime this week is fine."
        },
        {
            "name": "Administrative Task",
            "transcript": "Administrative note: We need to update the patient intake forms. This should be done by end of month."
        },
        {
            "name": "Ambiguous Task (should reject)",
            "transcript": "Someone needs to do something about that patient. You know who I mean."
        }
    ]
    
    print("=" * 80)
    print("TASK EXTRACTION PIPELINE - TEST SUITE")
    print("=" * 80)
    print()
    
    results = {
        "passed": 0,
        "failed": 0,
        "rejected": 0
    }
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'=' * 80}")
        print(f"Transcript: {test['transcript'][:100]}...")
        print()
        
        try:
            result = run_pipeline(test['transcript'])
            
            if result['status'] == 'rejected':
                print(f"❌ REJECTED: {result['rejection_reason']}")
                print(f"   Category: {result['rejection_category']}")
                results['rejected'] += 1
            elif result['status'] == 'completed':
                print(f"✅ COMPLETED")
                print(f"   Task ID: {result['task_id']}")
                print(f"   Priority: {result['task']['priority_level']} ({result['task']['priority_score']:.2f})")
                print(f"   Category: {result['task'].get('enriched_fields', {}).get('category_name', 'N/A')}")
                results['passed'] += 1
            
        except Exception as e:
            print(f"💥 FAILED: {str(e)}")
            results['failed'] += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"✅ Passed:   {results['passed']}")
    print(f"❌ Rejected: {results['rejected']}")
    print(f"💥 Failed:   {results['failed']}")
    print(f"📊 Total:    {sum(results.values())}")
    print()
    
    if results['failed'] == 0:
        print("🎉 All tests completed successfully!")
        return 0
    else:
        print("⚠️  Some tests failed - check errors above")
        return 1


if __name__ == "__main__":
    sys.exit(test_extraction())
