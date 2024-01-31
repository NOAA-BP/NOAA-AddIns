__title__="03 ScheduleReplaceFilters(SchedulePerSheet)"
__author__="Bogdan Popa"
__doc__="""It removes one filter at index and name, it adds a new filter at the end of the list"""

import clr
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import FilteredElementCollector, ViewSchedule, ScheduleFilter, ScheduleFilterType, Transaction, BuiltInCategory

clr.AddReference('RevitServices')
from pyrevit import forms

# Access the current document
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document




def get_field_id_from_schedule(schedule, field_name):
    """
    Gets the field ID for a given field name in a schedule.

    :param schedule: The ViewSchedule object.
    :param field_name: The name of the field to find.
    :return: The ElementId of the field, or None if not found.
    """
    try:
        sched_def = schedule.Definition
        for field_index in range(sched_def.GetFieldCount()):
            field = sched_def.GetField(field_index)
            if field.GetName() == field_name:
                return field.FieldId
        print("Field '{}' not found in schedule.".format(field_name))
        return None
    except Exception as e:
        print('Error getting field ID: {0}'.format(str(e)))
        return None

def remove_filter(schedule, field_name, filter_index):
    try:
        sched_def = schedule.Definition
        filters = sched_def.GetFilters()

        if filters.Count > filter_index:
            field_id = filters[filter_index].FieldId
            field = sched_def.GetField(field_id)
            if field.GetName() == field_name:
                sched_def.RemoveFilter(filter_index)
                print("Filter for field '{}' removed at index {}".format(field_name, filter_index))
            else:
                print("No matching filter found for field '{}' at index {}".format(field_name, filter_index))
        else:
            print("Filter index {} out of range. Total filters: {}.".format(filter_index, filters.Count))
    except Exception as e:
        print('Error removing filter: {0}'.format(str(e)))

def add_filter_to_schedule(schedule, field_id, filter_type, filter_value):
    try:
        sched_def = schedule.Definition
        new_filter = ScheduleFilter(field_id, filter_type, filter_value)
        sched_def.AddFilter(new_filter)
        print("Filter added using field ID: {}".format(field_id))
    except Exception as e:
        print('Error adding filter to schedule: {0}'.format(str(e)))

# Function to prompt user for sheet selection
def select_sheets():
    try:
        selected_sheets = forms.select_sheets(title='Select Sheets to Modify Title Block')
        if not selected_sheets:
            forms.alert('No sheets selected. Exiting.', exitscript=True)
        return selected_sheets
    except Exception as e:
        print('Error during sheet selection: {0}'.format(str(e)))
        return []




sheets = select_sheets()

with Transaction(doc, "Apply schedule changes") as t:
    t.Start()
    for sheet in sheets:
        try:
            print("Looping at Sheet ID: {}".format(sheet.Id))
            # Collect ScheduleSheetInstance elements on the sheet
            scheduleInstances = FilteredElementCollector(doc, sheet.Id).OfCategory(BuiltInCategory.OST_ScheduleGraphics).ToElements()
            print(scheduleInstances)
            if not scheduleInstances:
                print("No schedule instances found on sheet ID: {}".format(sheet.Id))
                continue

            for instance in scheduleInstances:
                print("Instance schedule found {} for sheet {}".format(instance, sheet.Id))
                # Get the ViewSchedule associated with the ScheduleSheetInstance
                scheduleId = instance.ScheduleId
                schedule = doc.GetElement(scheduleId)  # This should be a ViewSchedule
                if isinstance(schedule, ViewSchedule):
                    
                    # Remove existing filter
                    remove_filter(schedule, "Accommodation", 5)

                    # Add new filter
                    new_field_id = get_field_id_from_schedule(schedule, "Number")
                    if new_field_id is not None:
                        add_filter_to_schedule(schedule, new_field_id, ScheduleFilterType.NotContains, "B")
                    else:
                        print("Field 'Number' not found in the schedule.")

                    print("Processed schedule ID: {}".format(schedule.Id))
                else:
                    print("Element is not a ViewSchedule: ID {}".format(scheduleId))
        except Exception as e:
            print('Error processing sheet ID {0}: {1}'.format(sheet.Id, str(e)))
    t.Commit()









