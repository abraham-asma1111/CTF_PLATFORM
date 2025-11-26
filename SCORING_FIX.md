# Leaderboard Scoring Fix

## Problem
The leaderboard was not correctly accumulating points and challenge counts when users solved multiple challenges. Points from previous challenges weren't being added together, and the challenges solved counter wasn't incrementing properly.

## Root Cause
The issue was in the `submit_flag` view in `challenges/views.py`. The logic for updating user profiles had a flaw:
- The condition `if not existing_submission or not existing_submission.is_correct:` was checking the wrong state
- This caused the profile update to be skipped in certain scenarios
- Additionally, the `was_previously_correct` variable wasn't being set correctly

## Solution Implemented

### 1. Fixed Flag Submission Logic (`challenges/views.py`)
- Simplified the submission handling logic
- Moved the "already solved" check to the beginning
- Properly track whether a submission was previously correct
- Only update the profile when a challenge is solved for the first time

### 2. Created Score Recalculation Command
- Created `users/management/commands/recalculate_scores.py`
- This command recalculates all user scores based on their correct submissions
- Fixes any existing data inconsistencies

### 3. Verified with Tests
- Created `test_scoring.py` to verify the scoring system works correctly
- Tests confirm that:
  - Points accumulate correctly when solving multiple challenges
  - Challenge count increments properly
  - Leaderboard displays correct data

## How It Works Now

When a user submits a flag:
1. Check if they already solved this challenge (if yes, reject)
2. Check if they have an existing submission for this challenge
3. If existing submission exists, update it; otherwise create new one
4. If the flag is correct:
   - Update user profile ONLY if this is the first time solving this challenge
   - Add challenge points to total_score
   - Increment challenges_solved counter
   - Update last_submission timestamp

## Testing
Run the test to verify scoring works:
```bash
python test_scoring.py
```

Run the recalculation command to fix existing data:
```bash
python manage.py recalculate_scores
```

## Files Modified
- `challenges/views.py` - Fixed submit_flag logic
- `users/management/commands/recalculate_scores.py` - New command for fixing existing data
- `test_scoring.py` - New test file for verification
