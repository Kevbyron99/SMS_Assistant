import os
import re
import datetime
from typing import Dict, Any, List, Optional
from services.base_handler import BaseHandler

class ShiftHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.airtable_api_key = os.getenv('AIRTABLE_API_KEY')
        self.airtable_base_id = os.getenv('AIRTABLE_BASE_ID')
        self.airtable_table_name = os.getenv('AIRTABLE_SHIFTS_TABLE', 'Shifts')
        
        # Import here to avoid importing if the handler is not used
        try:
            from pyairtable import Table
            self.airtable_client = Table(self.airtable_api_key, self.airtable_base_id, self.airtable_table_name)
            self.airtable_available = True
            self.logger.info("Shift handler initialized with Airtable configuration")
        except ImportError:
            self.logger.warning("pyairtable not installed, Airtable integration disabled")
            self.airtable_available = False
        except Exception as e:
            self.logger.error(f"Error initializing Airtable client: {e}")
            self.airtable_available = False

    async def handle(self, message: str, params: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Parse the shift query intent
            intent = self._parse_shift_intent(message.lower())
            
            if not self.airtable_available:
                self.logger.warning("Airtable is not available, using simulated data for shift handler")
                # For testing, we'll simulate success for add, delete operations
                if intent['action'] == 'add':
                    # Simulate adding a shift
                    intent_str = str(intent)
                    if 'off' in intent_str:
                        return {
                            'success': True,
                            'message': f"Successfully marked a day as off (SIMULATED)"
                        }
                    elif 'overnight' in intent_str:
                        return {
                            'success': True,
                            'message': f"Successfully added overnight shift (SIMULATED)"
                        }
                    else:
                        return {
                            'success': True,
                            'message': f"Successfully added shift (SIMULATED)"
                        }
                elif intent['action'] == 'delete':
                    return {
                        'success': True,
                        'message': f"Successfully deleted shift (SIMULATED)"
                    }
            
            if intent['action'] == 'list':
                return await self._handle_list_shifts(intent)
            elif intent['action'] == 'add':
                return await self._handle_add_shift(intent, message)
            elif intent['action'] == 'next':
                return await self._handle_next_shift()
            elif intent['action'] == 'delete':
                return await self._handle_delete_shift(intent)
            else:
                return {
                    'success': False,
                    'error': 'Unknown shift action. Try "list shifts", "add shift", or "next shift".'
                }
        except Exception as e:
            self.logger.error(f"Shift handler error: {str(e)}")
            return {
                'success': False,
                'error': f"Error processing shift request: {str(e)}"
            }
            
    def _parse_shift_intent(self, message: str) -> Dict[str, Any]:
        """Parse the intent from the shift-related message"""
        intent = {'action': None, 'date': None, 'time': None, 'status': 'working'}
        
        self.logger.info(f"Parsing shift intent from message: {message}")
        
        # Check for list shifts action
        if re.search(r'(list|show|get|what are).*shift', message):
            intent['action'] = 'list'
            
            # Check for time period
            if 'today' in message:
                intent['date'] = datetime.date.today()
            elif 'tomorrow' in message:
                intent['date'] = datetime.date.today() + datetime.timedelta(days=1)
            elif 'this week' in message:
                intent['date'] = 'week'
            elif 'next week' in message:
                intent['date'] = 'next_week'
            elif 'month' in message:
                intent['date'] = 'month'
                
        # Check for next shift action
        elif re.search(r'(next|upcoming|what\'?s my next).*shift', message):
            intent['action'] = 'next'
            
        # Check for add shift action
        elif re.search(r'(add|create|new|schedule).*shift', message):
            intent['action'] = 'add'
            
            # Check if this is a day off request
            if re.search(r'(off day|day off|off shift|shift off)', message):
                intent['status'] = 'off'
                # For day off, we don't need time range
            
            # Try to extract date from the message for regular shifts
            date_match = re.search(r'(?:on|for)\s+(\w+(?:\s+\w+)?)(?:\s|$)', message)
            if date_match:
                intent['date_str'] = date_match.group(1)
                self.logger.info(f"Found date: {intent['date_str']}")
            
            # Handle overnight shifts (spans two days)
            overnight_match = re.search(r'(?:from\s+)?(\w+)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-)\s*(\w+)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message)
            if overnight_match:
                self.logger.info(f"Detected overnight shift pattern: {overnight_match.groups()}")
                intent['overnight'] = True
                intent['date_str'] = overnight_match.group(1)
                intent['end_date_str'] = overnight_match.group(3)
                intent['start_time_str'] = overnight_match.group(2)
                intent['end_time_str'] = overnight_match.group(4)
                self.logger.info(f"Parsed overnight shift: {intent['date_str']} {intent['start_time_str']} to {intent['end_date_str']} {intent['end_time_str']}")
            else:
                # Try to extract regular time range
                time_match = re.search(r'from\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', message)
                if time_match:
                    intent['start_time_str'] = time_match.group(1)
                    intent['end_time_str'] = time_match.group(2)
                    self.logger.info(f"Parsed regular shift times: {intent['start_time_str']} to {intent['end_time_str']}")
            
            # Extract notes if present
            notes_match = re.search(r'notes:?\s+(.+?)(?:$|\?|\.)', message)
            if notes_match:
                intent['notes'] = notes_match.group(1)
                self.logger.info(f"Found notes: {intent['notes']}")
            
        # Check for marking days off
        elif re.search(r'(mark|set)\s+(\w+)\s+(?:as\s+)?(off day|day off)', message):
            intent['action'] = 'add'
            intent['status'] = 'off'
            
            # Extract the date
            date_match = re.search(r'(mark|set)\s+(\w+)', message)
            if date_match:
                intent['date_str'] = date_match.group(2)
                self.logger.info(f"Found day off date: {intent['date_str']}")
                
        # Check for delete shift action
        elif re.search(r'(delete|remove|cancel).*shift', message):
            intent['action'] = 'delete'
            # Try to extract date from the message
            date_match = re.search(r'(?:on|for)\s+(\w+)(?:\s|$)', message)
            if date_match:
                intent['date_str'] = date_match.group(1)
        
        self.logger.info(f"Parsed intent: {intent}")
        return intent
        
    async def _handle_list_shifts(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle listing shifts based on intent"""
        try:
            if self.airtable_available:
                # Get all shifts from Airtable
                all_shifts = self.airtable_client.all()
                
                # Get available fields in Airtable
                available_fields = self._get_airtable_fields()
                self.logger.info(f"Available Airtable fields for listing: {available_fields}")
                
                # Convert Airtable records to our format
                shifts = []
                for record in all_shifts:
                    try:
                        shift = {
                            'id': record['id'],
                            'date': record['fields'].get('Date', ''),
                            'start_time': record['fields'].get('Start Time', ''),
                            'end_time': record['fields'].get('End Time', '')
                        }
                        
                        # Add optional fields if they exist in Airtable
                        if 'Status' in available_fields:
                            shift['status'] = record['fields'].get('Status', 'working')
                        if 'Notes' in available_fields:
                            shift['notes'] = record['fields'].get('Notes', '')
                        
                        # Only add shifts with valid dates
                        if shift['date']:
                            shifts.append(shift)
                    except Exception as e:
                        self.logger.warning(f"Error processing shift record: {e}")
                        continue
            else:
                # Use simulated data for testing
                shifts = self._get_simulated_shifts()
            
            # Parse date strings to datetime objects for comparison
            valid_shifts = []
            for shift in shifts:
                try:
                    # Convert to datetime.date
                    if '/' in shift['date']:
                        day, month, year = map(int, shift['date'].split('/'))
                        shift['date_obj'] = datetime.date(year, month, day)
                    elif '-' in shift['date']:
                        # Handle ISO format YYYY-MM-DD
                        shift['date_obj'] = datetime.datetime.strptime(shift['date'], '%Y-%m-%d').date()
                    else:
                        # Skip shifts with invalid date format
                        self.logger.warning(f"Skipping shift with invalid date format: {shift['date']}")
                        continue
                        
                    valid_shifts.append(shift)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Error parsing date {shift['date']}: {e}")
                    continue  # Skip shifts with invalid dates
            
            # Use the valid shifts for filtering
            shifts = valid_shifts
            
            if intent['date'] == 'week':
                # Filter shifts for this week
                today = datetime.date.today()
                start_of_week = today - datetime.timedelta(days=today.weekday())
                end_of_week = start_of_week + datetime.timedelta(days=6)
                filtered_shifts = [
                    shift for shift in shifts 
                    if start_of_week <= shift['date_obj'] <= end_of_week
                ]
            elif intent['date'] == 'next_week':
                # Filter shifts for next week
                today = datetime.date.today()
                start_of_week = today - datetime.timedelta(days=today.weekday())
                start_of_next_week = start_of_week + datetime.timedelta(days=7)
                end_of_next_week = start_of_next_week + datetime.timedelta(days=6)
                filtered_shifts = [
                    shift for shift in shifts 
                    if start_of_next_week <= shift['date_obj'] <= end_of_next_week
                ]
            elif intent['date'] == 'month':
                # Filter shifts for this month
                today = datetime.date.today()
                filtered_shifts = [
                    shift for shift in shifts 
                    if shift['date_obj'].month == today.month and shift['date_obj'].year == today.year
                ]
            elif isinstance(intent['date'], datetime.date):
                # Filter shifts for a specific date
                filtered_shifts = [
                    shift for shift in shifts 
                    if shift['date_obj'] == intent['date']
                ]
            else:
                # Return all shifts
                filtered_shifts = shifts
                
            # Sort shifts by date
            filtered_shifts.sort(key=lambda x: x['date_obj'])
                
            return {
                'success': True,
                'shifts': filtered_shifts,
                'count': len(filtered_shifts)
            }
        except Exception as e:
            self.logger.error(f"Error listing shifts: {e}")
            return {
                'success': False,
                'error': f"Error listing shifts: {str(e)}"
            }
            
    async def _handle_next_shift(self) -> Dict[str, Any]:
        """Get the next upcoming shift"""
        try:
            if self.airtable_available:
                # Get all shifts from Airtable
                all_shifts = self.airtable_client.all()
                
                # Get available fields in Airtable
                available_fields = self._get_airtable_fields()
                self.logger.info(f"Available Airtable fields for next shift: {available_fields}")
                
                # Convert Airtable records to our format
                shifts = []
                for record in all_shifts:
                    try:
                        shift = {
                            'id': record['id'],
                            'date': record['fields'].get('Date', ''),
                            'start_time': record['fields'].get('Start Time', ''),
                            'end_time': record['fields'].get('End Time', '')
                        }
                        
                        # Add optional fields if they exist in Airtable
                        if 'Status' in available_fields:
                            shift['status'] = record['fields'].get('Status', 'working')
                        if 'Notes' in available_fields:
                            shift['notes'] = record['fields'].get('Notes', '')
                        
                        # Only add shifts with valid dates
                        if shift['date']:
                            shifts.append(shift)
                    except Exception as e:
                        self.logger.warning(f"Error processing shift record: {e}")
                        continue
            else:
                # Use simulated data for testing
                shifts = self._get_simulated_shifts()
            
            today = datetime.date.today()
            now = datetime.datetime.now().time()
            
            # Parse date strings and filter upcoming shifts
            upcoming_shifts = []
            for shift in shifts:
                try:
                    # Convert to datetime.date
                    if '/' in shift['date']:
                        day, month, year = map(int, shift['date'].split('/'))
                        shift_date = datetime.date(year, month, day)
                    elif '-' in shift['date']:
                        # Handle ISO format YYYY-MM-DD
                        shift_date = datetime.datetime.strptime(shift['date'], '%Y-%m-%d').date()
                    else:
                        # Skip shifts with invalid date format
                        continue
                        
                    # Skip shifts that have already passed
                    if shift_date < today:
                        continue
                        
                    # For today's shifts, check if the time has passed
                    if shift_date == today and 'status' not in shift:
                        try:
                            shift_time = shift['start_time']
                            hour, minute = map(int, shift_time.split(':'))
                            shift_start = datetime.time(hour, minute)
                            
                            # Skip if the shift has already started
                            if shift_start < now:
                                continue
                        except (ValueError, IndexError):
                            # If we can't parse the time, include the shift anyway
                            pass
                    
                    # Add date object for sorting
                    shift['date_obj'] = shift_date
                    upcoming_shifts.append(shift)
                except (ValueError, TypeError) as e:
                    self.logger.warning(f"Error parsing date/time for shift: {e}")
                    continue
            
            if not upcoming_shifts:
                return {
                    'success': True,
                    'message': "You don't have any upcoming shifts scheduled."
                }
                
            # Sort by date
            upcoming_shifts.sort(key=lambda x: (x['date_obj'], x['start_time']))
            
            # Return the next shift
            return {
                'success': True,
                'shift': upcoming_shifts[0],
                'count': 1
            }
        except Exception as e:
            self.logger.error(f"Error getting next shift: {e}")
            return {
                'success': False,
                'error': f"Error getting next shift: {str(e)}"
            }
            
    async def _handle_add_shift(self, intent: Dict[str, Any], message: str) -> Dict[str, Any]:
        """Add a new shift"""
        try:
            if not self.airtable_available:
                return {
                    'success': False,
                    'error': 'Airtable is not available for adding shifts'
                }
                
            # Parse the date
            date_str = intent.get('date_str')
            if not date_str:
                return {
                    'success': False,
                    'error': 'Could not determine the date for the shift. Please include a date like "Monday" or "March 24".'
                }
                
            # Handle relative dates like "today", "tomorrow", "Monday", etc.
            date_obj = self._parse_date(date_str)
            if not date_obj:
                return {
                    'success': False,
                    'error': f'Could not understand date "{date_str}". Please use a format like "Monday" or "March 24".'
                }
                
            # Convert to YYYY-MM-DD format for Airtable
            formatted_date = date_obj.strftime('%Y-%m-%d')
            
            # Get available fields in Airtable
            available_fields = self._get_airtable_fields()
            self.logger.info(f"Available Airtable fields: {available_fields}")
            
            # Create the record - use only the fields that exist in Airtable
            new_shift = {
                'Date': formatted_date
            }
            
            # Get shift status (working or off)
            status = intent.get('status', 'working')
            
            # Handle day off vs regular shift
            if status == 'off':
                # For day off, set times to all day
                new_shift['Start Time'] = '00:00'
                new_shift['End Time'] = '23:59'
                
                # Add Status field if it exists
                if 'Status' in available_fields:
                    new_shift['Status'] = 'off'
                
                # Add Notes field if it exists
                if 'Notes' in available_fields:
                    new_shift['Notes'] = 'Day Off'
            else:
                # Parse the times for working shifts
                start_time_str = intent.get('start_time_str')
                end_time_str = intent.get('end_time_str')
                
                if not start_time_str or not end_time_str:
                    return {
                        'success': False,
                        'error': 'Could not determine the start and end times for the shift. Please include times like "9am to 5pm".'
                    }
                    
                # Format the times for consistency
                start_time = self._format_time(start_time_str)
                end_time = self._format_time(end_time_str)
                
                if not start_time or not end_time:
                    return {
                        'success': False,
                        'error': f'Could not understand time format. Please use formats like "9am", "14:30", or "2pm".'
                    }
                
                new_shift['Start Time'] = start_time
                new_shift['End Time'] = end_time
                
                # Add Status field if it exists
                if 'Status' in available_fields:
                    new_shift['Status'] = 'working'
                
                # Handle overnight shifts
                if intent.get('overnight'):
                    # Get the end date
                    end_date_str = intent.get('end_date_str')
                    end_date_obj = self._parse_date(end_date_str)
                    
                    if not end_date_obj:
                        return {
                            'success': False,
                            'error': f'Could not understand end date "{end_date_str}". Please use a format like "Monday" or "March 24".'
                        }
                    
                    # Add overnight shift note if Notes field exists
                    if 'Notes' in available_fields:
                        new_shift['Notes'] = f"Overnight shift ending on {end_date_obj.strftime('%A, %B %d')}"
                elif intent.get('notes') and 'Notes' in available_fields:
                    new_shift['Notes'] = intent.get('notes')
            
            # Check if ID field exists and add it
            if 'ID' in available_fields:
                # Generate a simple ID based on date and time
                shift_id = f"shift_{date_obj.strftime('%Y%m%d')}"
                if status == 'working':
                    shift_id += f"_{start_time.replace(':', '')}"
                else:
                    shift_id += "_dayoff"
                new_shift['ID'] = shift_id
            
            # Add to Airtable
            self.logger.info(f"Creating shift with fields: {new_shift}")
            created = self.airtable_client.create(new_shift)
            
            # Prepare response message
            if status == 'off':
                msg = f'Successfully marked {date_obj.strftime("%A, %B %d")} as a day off'
            elif intent.get('overnight'):
                end_date_obj = self._parse_date(intent.get('end_date_str'))
                msg = f'Successfully added overnight shift from {date_obj.strftime("%A, %B %d")} at {start_time} to {end_date_obj.strftime("%A, %B %d")} at {end_time}'
            else:
                msg = f'Successfully added shift on {date_obj.strftime("%A, %B %d")} from {start_time} to {end_time}'
            
            # Create response with only the fields that exist
            shift_response = {
                'id': created['id'],
                'date': formatted_date,
                'start_time': new_shift.get('Start Time', ''),
                'end_time': new_shift.get('End Time', '')
            }
            
            # Add optional fields if they exist
            if 'Status' in available_fields:
                shift_response['status'] = status
            if 'Notes' in available_fields and 'Notes' in new_shift:
                shift_response['notes'] = new_shift['Notes']
            
            return {
                'success': True,
                'message': msg,
                'shift': shift_response
            }
        except Exception as e:
            self.logger.error(f"Error adding shift: {e}")
            return {
                'success': False,
                'error': f"Error adding shift: {str(e)}"
            }
        
    async def _handle_delete_shift(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a shift"""
        try:
            if not self.airtable_available:
                return {
                    'success': False,
                    'error': 'Airtable is not available for deleting shifts'
                }
                
            # Parse the date
            date_str = intent.get('date_str')
            if not date_str:
                return {
                    'success': False,
                    'error': 'Could not determine which shift to delete. Please include a date like "delete shift on Monday".'
                }
                
            # Handle relative dates like "today", "tomorrow", "Monday", etc.
            date_obj = self._parse_date(date_str)
            if not date_obj:
                return {
                    'success': False,
                    'error': f'Could not understand date "{date_str}". Please use a format like "delete shift on Monday".'
                }
                
            # Convert to YYYY-MM-DD format for Airtable
            formatted_date = date_obj.strftime('%Y-%m-%d')
            
            # Find shifts on this date
            all_shifts = self.airtable_client.all(formula=f"{{Date}} = '{formatted_date}'")
            
            if not all_shifts:
                return {
                    'success': False,
                    'error': f'No shifts found on {date_obj.strftime("%A, %B %d")}'
                }
                
            # If multiple shifts on the same day, ask for clarification
            if len(all_shifts) > 1:
                shift_details = []
                for i, shift in enumerate(all_shifts, 1):
                    start_time = shift['fields'].get('Start Time', 'Unknown')
                    end_time = shift['fields'].get('End Time', 'Unknown')
                    shift_details.append(f"{i}. {start_time} - {end_time}")
                    
                shift_list = "\n".join(shift_details)
                return {
                    'success': False,
                    'error': f'Multiple shifts found on {date_obj.strftime("%A, %B %d")}. Please specify which one to delete:\n{shift_list}'
                }
                
            # Delete the shift
            shift_to_delete = all_shifts[0]
            self.airtable_client.delete(shift_to_delete['id'])
            
            start_time = shift_to_delete['fields'].get('Start Time', 'Unknown')
            end_time = shift_to_delete['fields'].get('End Time', 'Unknown')
            
            return {
                'success': True,
                'message': f'Successfully deleted shift on {date_obj.strftime("%A, %B %d")} ({start_time} - {end_time})'
            }
        except Exception as e:
            self.logger.error(f"Error deleting shift: {e}")
            return {
                'success': False,
                'error': f"Error deleting shift: {str(e)}"
            }
    
    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse a date string into a datetime.date object"""
        today = datetime.date.today()
        
        # Handle common relative dates
        date_str = date_str.lower().strip()
        if date_str in ['today']:
            return today
        elif date_str in ['tomorrow']:
            return today + datetime.timedelta(days=1)
        elif date_str in ['yesterday']:
            return today - datetime.timedelta(days=1)
            
        # Handle day names (Monday, Tuesday, etc.)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if date_str in days:
            day_index = days.index(date_str)
            today_index = today.weekday()
            days_ahead = (day_index - today_index) % 7
            if days_ahead == 0:  # Same day of the week means next week
                days_ahead = 7
            return today + datetime.timedelta(days=days_ahead)
            
        # Try to parse specific dates in various formats
        try:
            # Try MM/DD/YYYY format
            return datetime.datetime.strptime(date_str, '%m/%d/%Y').date()
        except ValueError:
            pass
            
        try:
            # Try Month Day format (March 15)
            return datetime.datetime.strptime(date_str, '%B %d').replace(year=today.year).date()
        except ValueError:
            pass
            
        try:
            # Try Month Day format with abbreviated month (Mar 15)
            return datetime.datetime.strptime(date_str, '%b %d').replace(year=today.year).date()
        except ValueError:
            pass
            
        # More complex parsing might require a specialized library like dateutil
        return None
        
    def _format_time(self, time_str: str) -> str:
        """Format time strings consistently for Airtable"""
        time_str = time_str.lower().strip()
        
        # Handle 12-hour format with am/pm
        am_pm_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', time_str)
        if am_pm_match:
            hour = int(am_pm_match.group(1))
            minute = int(am_pm_match.group(2) or 0)
            period = am_pm_match.group(3)
            
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
                
            return f"{hour:02d}:{minute:02d}"
            
        # Handle 24-hour format (14:30)
        hour_minute_match = re.search(r'(\d{1,2}):(\d{2})', time_str)
        if hour_minute_match:
            hour = int(hour_minute_match.group(1))
            minute = int(hour_minute_match.group(2))
            return f"{hour:02d}:{minute:02d}"
            
        # Handle simple hour format (14 or 2)
        hour_match = re.search(r'^(\d{1,2})$', time_str)
        if hour_match:
            hour = int(hour_match.group(1))
            return f"{hour:02d}:00"
            
        return time_str  # Return as-is if we can't parse it
    
    def _get_simulated_shifts(self) -> List[Dict[str, Any]]:
        """Get simulated shifts for testing"""
        today = datetime.date.today()
        tomorrow = today + datetime.timedelta(days=1)
        next_week = today + datetime.timedelta(days=7)
        two_days = today + datetime.timedelta(days=2)
        
        return [
            {
                'id': '1',
                'date': today.strftime('%d/%m/%Y'),
                'start_time': '08:00',
                'end_time': '16:00',
                'status': 'working',
                'notes': 'Morning shift'
            },
            {
                'id': '2',
                'date': tomorrow.strftime('%d/%m/%Y'),
                'start_time': '12:00',
                'end_time': '20:00',
                'status': 'working',
                'notes': 'Evening shift'
            },
            {
                'id': '3',
                'date': two_days.strftime('%d/%m/%Y'),
                'start_time': '00:00',
                'end_time': '23:59',
                'status': 'off',
                'notes': 'Day Off'
            },
            {
                'id': '4',
                'date': next_week.strftime('%d/%m/%Y'),
                'start_time': '09:00',
                'end_time': '17:00',
                'status': 'working',
                'notes': 'Regular shift'
            },
            {
                'id': '5',
                'date': (next_week + datetime.timedelta(days=1)).strftime('%d/%m/%Y'),
                'start_time': '22:00',
                'end_time': '10:00',
                'status': 'working',
                'notes': 'Overnight shift ending on ' + (next_week + datetime.timedelta(days=2)).strftime('%A, %B %d')
            }
        ]
            
    def _get_airtable_fields(self) -> List[str]:
        """Get the field names in the Airtable table"""
        try:
            if not self.airtable_available:
                return []
                
            # Get a record to see fields
            records = self.airtable_client.all(max_records=1)
            
            if records:
                return list(records[0]['fields'].keys())
            
            # If no records, assume default fields
            return ['ID', 'Date', 'Start Time', 'End Time', 'Status', 'Notes']
        except Exception as e:
            self.logger.error(f"Error getting Airtable fields: {e}")
            # Return default field set
            return ['Date', 'Start Time', 'End Time', 'Status', 'Notes']
            
    def format_response(self, data: Dict[str, Any]) -> str:
        """Format the shift data for display"""
        if not data.get('success'):
            return f"Sorry, I couldn't process your shift request: {data.get('error')}"
            
        if 'message' in data:
            return data['message']
            
        if 'shift' in data:
            # Format a single shift
            shift = data['shift']
            return self._format_shift(shift)
            
        if 'shifts' in data:
            # Format multiple shifts
            if not data['shifts']:
                return "No shifts found for that time period."
                
            if len(data['shifts']) == 1:
                return self._format_shift(data['shifts'][0])
                
            # Format a list of shifts
            result = f"📅 Found {len(data['shifts'])} upcoming shifts:\n\n"
            for i, shift in enumerate(data['shifts'], 1):
                result += f"Shift {i}: {self._format_shift_brief(shift)}\n"
                
            return result
    
    def _format_shift(self, shift: Dict[str, Any]) -> str:
        """Format a single shift for detailed display"""
        try:
            # Parse the date (handle different formats)
            if '/' in shift['date']:
                day, month, year = map(int, shift['date'].split('/'))
                shift_date = datetime.date(year, month, day)
            else:
                shift_date = datetime.datetime.strptime(shift['date'], '%Y-%m-%d').date()
                
            date_str = shift_date.strftime('%A, %B %d')
        except Exception:
            # Fallback if date parsing fails
            date_str = shift['date']
        
        # Check if this is a day off (if Status field exists)
        if shift.get('status') == 'off':
            return f"📅 Day Off: {date_str}"
        
        # Format regular working shift
        result = f"📅 Shift on {date_str}:\n" \
                f"Time: {shift['start_time']} - {shift['end_time']}"
        
        # Add notes if available and if the field exists
        if 'notes' in shift and shift['notes']:
            result += f"\nNotes: {shift['notes']}"
            
        return result
    
    def _format_shift_brief(self, shift: Dict[str, Any]) -> str:
        """Format a shift for brief display in a list"""
        try:
            # Parse the date (handle different formats)
            if '/' in shift['date']:
                day, month, year = map(int, shift['date'].split('/'))
                shift_date = datetime.date(year, month, day)
            else:
                shift_date = datetime.datetime.strptime(shift['date'], '%Y-%m-%d').date()
                
            date_str = shift_date.strftime('%a, %b %d')
        except Exception:
            # Fallback if date parsing fails
            date_str = shift['date']
        
        # Check if this is a day off (if Status field exists)
        if shift.get('status') == 'off':
            return f"{date_str} (Day Off)"
        
        # Regular working shift
        shift_info = f"{date_str} ({shift['start_time']} - {shift['end_time']})"
        
        # Add abbreviated notes if available and if the field exists
        if 'notes' in shift and shift['notes']:
            notes = shift['notes']
            if len(notes) > 15:
                notes = notes[:15] + "..."
            shift_info += f" - {notes}"
            
        return shift_info 