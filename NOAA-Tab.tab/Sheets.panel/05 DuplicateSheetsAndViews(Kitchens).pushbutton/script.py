__title__="05 DuplicateSheetsAndViews(Kitchens)"
__author__="Bogdan Popa"
__doc__="""Duplicates and renames the selected Sheets along with associated Views.
Enter the Name prefix as 'Name[space]-[space] '"""


# Import necessary modules
import clr
import System
import Autodesk.Revit.DB as DB
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
from pyrevit import revit, DB


app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document



# Collect all View Templates
all_views = FilteredElementCollector(doc).OfClass(View).ToElements()
view_templates = [view for view in all_views if view.IsTemplate]
view_templates_names = [template.Name for template in view_templates]

# Prompt the user to select the template
selected_template_name = forms.SelectFromList.show(view_templates_names, title='Select View Template', multiselect=False)
selected_template = next(template for template in view_templates if template.Name == selected_template_name)  # Stores the template

def pick_title_block():
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
    title_blocks = {tb.FamilyName: tb.Id for tb in collector.ToElements()}
    selected = forms.SelectFromList.show(title_blocks.keys(), multiselect=False)
    if not selected:
        print("No title block selected.")
        return None
    return title_blocks[selected]  # THIS RETURNS ELEMENTID

def collect_and_select_plumbing_fixtures_multiple(doc):
    # Collect all plumbing fixtures
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()
    fixtures = list(collector)

    # Prepare fixture names for selection, sorted alphabetically
    fixture_names = [f.Name for f in fixtures]
    unique_fixture_names = sorted(list(set(fixture_names)))

    # User selection with multi-selection enabled, presented alphabetically
    selected_names = forms.SelectFromList.show(unique_fixture_names, 
                                               title="Select Fixture Families", 
                                               button_name="Select", 
                                               multiselect=True)

    return selected_names

# Define the update_schedule_field function with the correct handling for field index
def update_schedule_field(schedule, field_name, new_value):
    for field_index, fieldId in enumerate(schedule.Definition.GetFieldOrder()):
        field = schedule.Definition.GetField(fieldId)
        if field.GetName() == field_name:
            # Use field_index to set the cell text
            tableData = schedule.GetTableData()
            sectionData = tableData.GetSectionData(SectionType.Body)
            for rowIndex in range(sectionData.NumberOfRows):
                schedule.SetCellText(SectionType.Body, rowIndex, field_index, new_value)
            break
    else:
        print("Field", field_name, "not found in schedule", schedule.Name)

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
    
def add_filter_to_schedule(schedule, field_id, filter_type, filter_value):
    try:
        sched_def = schedule.Definition
        new_filter = ScheduleFilter(field_id, filter_type, filter_value)
        sched_def.AddFilter(new_filter)
        print("Filter added using field ID: {}".format(field_id))
    except Exception as e:
        print('Error adding filter to schedule: {0}'.format(str(e)))

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


# Collect selected names
selected_names = collect_and_select_plumbing_fixtures_multiple(doc)
# Prompt the user to select sheets
sheet_to_duplicate = forms.select_sheets(title='Select Sheet to Duplicate')

# Prompt the user for the new sheet number prefix and name prefix
starting_number = forms.ask_for_string(default="",
                                       prompt="Enter starting sheet number:",
                                       title="Starting Number")
name_prefix = forms.ask_for_string(default="",
                                   prompt="Enter name prefix for new sheets:",
                                   title="Name Prefix")
title_block = pick_title_block()

# Ensure that the returned value is a single sheet, not a list
if sheet_to_duplicate and len(sheet_to_duplicate) == 1:
    sheet_to_duplicate = sheet_to_duplicate[0]
else:
    TaskDialog.Show('Error', 'Please select exactly one sheet.')

# Make sure the user has selected at least one sheet and entered all required inputs
if not sheet_to_duplicate or not starting_number or not title_block or not selected_names:
    TaskDialog.Show("Error", "Please select at least one sheet and enter all required inputs.")
else:
    for i, selected_name in enumerate(selected_names):
        print("PROCESSING FOR:", selected_name)
        with revit.Transaction("Duplicate Sheets") as t:
            # Create a new sheet
            new_sheet = DB.ViewSheet.Create(revit.doc, title_block)

            # Split the starting number into prefix and suffix
            starting_number_prefix = starting_number[:-3]
            starting_number_suffix = int(starting_number[-3:])

            # Generate the new number and name
            new_sheet_number = starting_number_prefix + str(starting_number_suffix + i).zfill(3)
            new_sheet_name = name_prefix + selected_name # Keep the original sheet name

            # Set the new number and name
            new_sheet.SheetNumber = new_sheet_number
            new_sheet.Name = new_sheet_name

            # First, collect all schedule sheet instances in the document
            all_schedule_instances = FilteredElementCollector(revit.doc).OfClass(ScheduleSheetInstance).ToElements()

            # Filter schedule instances that are on the original sheet
            schedules_on_sheet = [s for s in all_schedule_instances if s.OwnerViewId == sheet_to_duplicate.Id]
            print("SCHEDULES ON SHEET:",len(schedules_on_sheet))

            # Iterate through all viewports on the original sheet
            for viewport_id in sheet_to_duplicate.GetAllViewports():
                viewport = revit.doc.GetElement(viewport_id)
                view = revit.doc.GetElement(viewport.ViewId)

                if view.ViewType != ViewType.Legend:
                    # Duplicate the view for non-legend views
                    new_view_id = view.Duplicate(ViewDuplicateOption.WithDetailing)
                    
                    # Keep the original view name and set the view template if required
                    new_view = revit.doc.GetElement(new_view_id)
                    new_view.ViewTemplateId = selected_template.Id

                    # Create a new viewport on the new sheet with the duplicated view
                    Viewport.Create(revit.doc, new_sheet.Id, new_view_id, viewport.GetBoxCenter())
                else:
                    # Directly place the legend view on the new sheet
                    Viewport.Create(revit.doc, new_sheet.Id, view.Id, viewport.GetBoxCenter())

            # Now handle the schedule instances
            for schedule_instance in schedules_on_sheet:
                schedule = doc.GetElement(schedule_instance.ScheduleId)

                # Continue if the schedule is None or if it's a type that cannot be duplicated/placed on sheets
                if schedule is None or not isinstance(schedule, ViewSchedule):
                    continue

                # Additional checks can be added here based on the properties of non-duplicable schedules

                # Attempt to create a new schedule instance on the new sheet
                try:
                    new_schedule_instance = ScheduleSheetInstance.Create(doc, new_sheet.Id, schedule_instance.ScheduleId, schedule_instance.Point)
                    new_schedule = doc.GetElement(new_schedule_instance.ScheduleId)
                    
                    if isinstance(new_schedule, ViewSchedule):
                        #update_schedule_field(schedule, "Kitchen Type", selected_name)
                        # Remove existing filter
                        remove_filter(schedule, "Kitchen Type", 4)
                        # Add new filter
                        new_field_id = get_field_id_from_schedule(schedule, "Kitchen Type")
                        if new_field_id is not None:
                            add_filter_to_schedule(new_schedule, new_field_id, ScheduleFilterType.Equal, selected_name)
                        else:
                            print("Field 'Number' not found in the schedule.")
                        
                except Exception as e:
                    # Handle cases where the schedule cannot be added to the sheet
                    print("Could not duplicate schedule", schedule.Name, "on the new sheet:", e)
                
    TaskDialog.Show("Success", "Sheets have been duplicated.")
































