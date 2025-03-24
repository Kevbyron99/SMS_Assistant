# Shift Tracking System - User Guide

Your personal assistant now includes a shift tracking system that integrates with Airtable to store and manage your work schedule. This guide explains how to use the shift tracking features.

## Setting Up

The system uses Airtable as the database for storing your shifts. You should have:

1. An Airtable account
2. A base with a "Shifts" table with these required fields:
   - Date (Date)
   - Start Time (Text)
   - End Time (Text)

Optional fields to enhance functionality:
   - ID (Text) - Generated automatically if it exists
   - Status (Text) - For marking days as "working" or "off"
   - Notes (Text) - For additional information about shifts

The system will work even without the optional fields, but with slightly limited functionality.

Your `.env` file should contain:
```
AIRTABLE_API_KEY=your_airtable_api_key
AIRTABLE_BASE_ID=your_base_id
AIRTABLE_SHIFTS_TABLE=Shifts
```

## SMS Commands

### Adding Regular Shifts

To add a new shift to your schedule, use a command like:

```
add shift on Monday from 9am to 5pm
```

Other examples:
```
add shift on tomorrow from 12pm to 8pm
add shift on March 30 from 10:30am to 6:30pm
add shift on Friday from 9:00 to 17:00
```

### Adding Overnight Shifts (24-Hour Shifts)

For shifts that span across two days, specify both days:

```
add shift from Monday 10pm to Tuesday 10am
```

The system will record this as an overnight shift correctly. If you have a Notes field in your Airtable, it will include information about the end date.

### Adding Shifts with Notes

If you have a Notes field in your Airtable, you can add notes to any shift:

```
add shift on Saturday from 12pm to 8pm notes: Special event coverage
```

### Marking Days Off

To mark a day as off (no work):

```
mark Friday as day off
```

Alternative formats:
```
set Monday as off day
mark tomorrow as day off
```

This will create a shift for the entire day (00:00 to 23:59). If you have a Status field in your Airtable, it will be marked as "off".

### Viewing Shifts

To see your shifts, use commands like:

**List all shifts**:
```
list all shifts
list my shifts
show my schedule
```

**List specific time periods**:
```
list shifts this week
list shifts next week
list shifts for today
list shifts for tomorrow
```

**See your next shift**:
```
what's my next shift
next shift
upcoming shift
```

### Deleting Shifts

To remove a shift from your schedule:

```
delete shift on Monday
remove shift tomorrow
cancel shift on Friday
```

If you have multiple shifts on the same day, the system will ask you to specify which one to delete.

## Tips

1. The system understands various time formats (9am, 09:00, 9:00am, etc.)
2. For dates, you can use day names (Monday, Tuesday), relative terms (today, tomorrow), or specific dates (March 24)
3. The system will automatically sort shifts by date and time when showing your schedule
4. If you have the Status field, days off are marked with a special status and displayed differently
5. Overnight shifts spanning multiple days are supported and clearly marked in the Notes field (if available)
6. You can manually add/edit shifts directly in Airtable if needed

## Troubleshooting

If you encounter issues with the shift tracking system:

1. Check that your Airtable base and table are correctly set up with at least the required fields
2. Verify your API key and base ID in the `.env` file
3. Make sure your message format is clear - specify the date and time range
4. If the assistant doesn't understand your command, try rephrasing it

For common date and time formats, use:
- Days: Monday, Tuesday, today, tomorrow
- Times: 9am, 3pm, 14:30, 9:45am 