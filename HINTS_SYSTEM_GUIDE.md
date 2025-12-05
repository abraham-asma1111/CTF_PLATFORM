# Challenge Hints System Guide

## Overview
The hints system allows admins to add helpful clues to challenges that users can reveal (with optional point deduction).

## Features Implemented

### 1. **Hint Model**
- Each challenge can have multiple hints
- Hints have:
  - Order (1, 2, 3...)
  - Content (the hint text)
  - Cost (points deducted when viewing, 0 for free)

### 2. **User Preference Integration**
- Users can enable/disable hints in Settings → Preferences
- If disabled, hints section shows a message with link to enable

### 3. **Point Deduction**
- When a user views a hint with cost > 0, points are deducted from their score
- Users must confirm before viewing paid hints
- Each hint can only be viewed once per user

### 4. **Admin Interface**
- Add hints directly when creating/editing challenges
- Inline hint editor in Django admin
- View hint statistics (how many users viewed each hint)

## How to Use

### For Admins: Adding Hints

**Method 1: Django Admin (Recommended)**
1. Go to Django Admin → Challenges
2. Click on a challenge or create new one
3. Scroll down to "Hints" section
4. Click "Add another Hint"
5. Fill in:
   - Order: 1, 2, 3... (display order)
   - Content: The hint text
   - Cost: Points to deduct (0 for free)
6. Save challenge

**Method 2: Hints Admin**
1. Go to Django Admin → Hints
2. Click "Add Hint"
3. Select challenge and fill in details

### For Users: Viewing Hints

1. Go to any challenge page
2. If hints are available, you'll see "💡 Hints Available" section
3. Click "🔓 Reveal Hint" button
4. If hint costs points, confirm the deduction
5. Hint content will be revealed
6. Once viewed, hint stays visible (no re-payment needed)

### Settings Control

Users can control hint visibility:
1. Go to Settings → Preferences
2. Toggle "Show Challenge Hints"
3. If disabled, hints section won't show on challenge pages

## Database Tables

### Hint
- `challenge` - Foreign key to Challenge
- `content` - The hint text
- `cost` - Points deducted (0 = free)
- `order` - Display order
- `created_at` - Timestamp

### HintView
- `user` - Who viewed the hint
- `hint` - Which hint was viewed
- `viewed_at` - When it was viewed
- `points_deducted` - How many points were deducted

## API Endpoint

**POST** `/challenges/hint/<hint_id>/view/`

Response:
```json
{
  "success": true,
  "hint": "The hint content",
  "cost": 5,
  "message": "Hint revealed! 5 points deducted.",
  "new_score": 95
}
```

## Testing

Run the test script:
```bash
python test_hints_system.py
```

This will:
- Add 3 sample hints to a challenge
- Show you the URL to test
- Display hint details

## Best Practices

### Hint Design
1. **Progressive Difficulty**: Make hints increasingly specific
   - Hint 1: General direction (free or cheap)
   - Hint 2: Specific technique (moderate cost)
   - Hint 3: Almost the answer (expensive)

2. **Cost Strategy**:
   - Free hints: General guidance, doesn't give away solution
   - 5-10 points: Specific technique or tool to use
   - 15-25 points: Very specific steps or partial solution

3. **Example Hint Progression**:
   ```
   Hint 1 (Free): "This challenge involves web exploitation"
   Hint 2 (5 pts): "Look for SQL injection vulnerabilities"
   Hint 3 (10 pts): "Try: ' OR '1'='1"
   ```

### Admin Tips
- Add hints after challenge is tested
- Monitor hint views in admin to see which challenges need better hints
- Update hint costs based on challenge difficulty
- Don't make hints too obvious - learning is the goal!

## Troubleshooting

**Hints not showing?**
- Check if user has hints enabled in settings
- Verify challenge has hints in admin
- Check browser console for JavaScript errors

**Points not deducting?**
- Verify hint has cost > 0
- Check user's current score
- Look at HintView table to confirm deduction

**Can't add hints in admin?**
- Make sure migrations are run: `python manage.py migrate`
- Check if HintInline is registered in admin.py

## Future Enhancements

Possible additions:
- Hint unlock requirements (e.g., must attempt 3 times first)
- Time-based hints (unlock after X minutes)
- Hint categories (technical, conceptual, tool-based)
- Hint ratings (users vote on helpfulness)
- Bulk hint import from CSV/JSON
