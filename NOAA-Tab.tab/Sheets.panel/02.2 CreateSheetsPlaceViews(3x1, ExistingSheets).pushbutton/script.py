__title__="02.2 DuplicateView(3x1, Existing Sheet)"
__author__="Bogdan Popa"
__doc__="""Duplicates Views and creates corresponding Sheets. Places 3 x views per sheet. 
Places one View per corresponding Sheet

Sheet Number:   'XX - YYY' (displays 'NN - YYY')
Sheet Name:     SAME
View Names:     RENAMED

TEMPLATE 1:     1ST VIEW (L)
TEMPLATE 2:     2ND VIEW (C)
TEMPLATE 3:     3RD VIEW (R)
TEMPLATE 4:     KEY VIEW"""

import clr
import sys
import re
from pyrevit import forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, ElementId, ViewType, TextNoteType
import Autodesk.Revit.DB as DB


clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import TaskDialog

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
rvt_year = int(app.VersionNumber)
     


# Function to prompt user for sheet selection
def select_sheets():
    # Prompt the user to select sheets
    selected_sheets = forms.select_sheets(title='Select Sheets to Modify Title Block')
    # If user cancels selection, end script
    if not selected_sheets:
        forms.alert('No sheets selected. Exiting.', exitscript=True)
    # Return the list of selected sheet elements
    return selected_sheets


def prompt_for_view_name_suffix():
    return forms.ask_for_string("Enter view/sheet name suffix (e.g., '- AP TYPE'):")

def select_scope_box():
    scope_boxes = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_VolumeOfInterest).WhereElementIsNotElementType().ToElements()
    selected_name = forms.SelectFromList.show([sb.Name for sb in scope_boxes], title='Select a Scope Box', multiselect=False)
    return next((sb for sb in scope_boxes if sb.Name == selected_name), None)

def pick_title_block():
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
    title_blocks = {tb.FamilyName: tb.Id for tb in collector.ToElements()}
    selected = forms.SelectFromList.show(title_blocks.keys(), multiselect=False)
    if not selected:
        print("No title block selected.")
        return None
    return title_blocks[selected]       #THIS RETURNS ELEMENTID

def prompt_for_tamplate():
    all_views = FilteredElementCollector(doc).OfClass(View).ToElements()
    view_templates = [view for view in all_views if view.IsTemplate]
    view_templates_names = [template.Name for template in view_templates]
    # Prompt the user to select the template
    selected_template_name = forms.SelectFromList.show(view_templates_names, title='Select View Template', multiselect=False)
    selected_template_key = next(template for template in view_templates if template.Name == selected_template_name) # Stores the template
    return selected_template_key

def prompt_for_starting_sheet_number():
    while True:
        number = forms.ask_for_string("Enter starting sheet number (e.g., '35'):")
        if number:
            return number
        #if number and '-' in number and number.split('-')[-1].strip().isdigit():
        #    return number
        #print("Invalid format. Please enter a sheet number in the format '35 - 100'.")

def increment_sheet_number(start_number, increment):
    try:
        prefix, number_str = start_number.rsplit('-', 1)
        number = int(number_str.strip()) + increment
        new_number_str = str(number).zfill(len(number_str.strip()))
        return prefix.strip() + " - " + new_number_str
    except ValueError as e:
        print("Error incrementing sheet number:", e, "Input was:", start_number)
        return None

def is_sheet_number_in_use(number, doc):
    sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
    return any(sheet.SheetNumber == number for sheet in sheets)

def apply_templates_to_views(selected_views, selected_template_key):
    print("PLACING TEMPLATE ON THE KEY VIEW")
    t = Transaction(doc, 'Apply Templates to Views')
    t.Start()
    for view in selected_views:
        if selected_template_key:
            view.ViewTemplateId = selected_template_key.Id
    t.Commit()

def alphanumeric_sequence_match(str1, str2):
    # Remove all non-alphanumeric characters and convert to uppercase for case-insensitive comparison
    alphanumeric_str1 = re.sub(r'\W+', '', str1).upper()
    alphanumeric_str2 = re.sub(r'\W+', '', str2).upper()

    return alphanumeric_str1 == alphanumeric_str2


def prompt_user_to_select_fill_pattern_type(filled_region_types_dict):
    # Prompt user to pick a filled region type name from the list
    selected_type_name = forms.SelectFromList.show(
        sorted(filled_region_types_dict.keys()),
        title='Select Filled Region Type'
    )
    
    if selected_type_name is None:
        TaskDialog.Show('Selection', 'No filled region type was selected.')
        return None
    
    # Retrieve the FilledRegionType Id from the dictionary
    selected_type_id = filled_region_types_dict[selected_type_name]
    
    return selected_type_id

# Function to collect filled regions by type name
def collect_filled_region_types(doc):
    # Create a parameter value provider for the ALL_MODEL_TYPE_NAME parameter
    provider = ParameterValueProvider(ElementId(BuiltInParameter.ALL_MODEL_TYPE_NAME))
    
    # Create a filter to collect all filled region types
    filled_region_types = FilteredElementCollector(doc).OfClass(FilledRegionType).WhereElementIsElementType().ToElements()
    
    # Create a dictionary to hold the name and element id of each type
    filled_region_types_dict = {frt.LookupParameter('Type Name').AsString(): frt.Id for frt in filled_region_types}
    
    filled_region_types_dict = prompt_user_to_select_fill_pattern_type(filled_region_types_dict)

    return filled_region_types_dict


def create_filled_region_from_area_boundaries(doc, alphanumeric_sheet_title, target_view_id, collected_fill_pattern):
    print("FILLED REGION INITIATED")
    boundaryOptions = SpatialElementBoundaryOptions()
    areas = FilteredElementCollector(doc, target_view_id).OfCategory(BuiltInCategory.OST_Areas).WhereElementIsNotElementType().ToElements()
    print("Number of areas collected: ", len(areas))

    for area in areas:
        param = area.LookupParameter("Apartment Type")
        if param and param.HasValue:
            area_param = re.sub(r'\W+', '', param.AsString()).upper()
            print(area_param, type(area_param))
        else:
            # Handle the case where the parameter is not found or has no value
            area_param = None
            print("Parameter 'Apartment Type' not found or has no value.")

        #area_param = re.sub(r'\W+', '', (area.LookupParameter("Apartment Type")).AsString()).upper()
        if area_param and area_param and  area_param in alphanumeric_sheet_title:
            print("Area found: ", area.Id)
            boundary_segments = area.GetBoundarySegments(boundaryOptions)
            curves = []

            # Process each boundary segment to collect curves
            for boundaryList in boundary_segments:
                for segment in boundaryList:
                    curve = segment.GetCurve()
                    curves.append(curve)

            # Ensure continuity and create a CurveLoop for the Filled Region
            curve_loop = CurveLoop()
            for i, curve in enumerate(curves):
                next_curve = curves[(i + 1) % len(curves)]
                if not curve.GetEndPoint(1).IsAlmostEqualTo(next_curve.GetEndPoint(0)):
                    curve = Line.CreateBound(curve.GetEndPoint(0), next_curve.GetEndPoint(0))
                curve_loop.Append(curve)

            # Check for a valid FilledRegionType
            filledRegionTypes = FilteredElementCollector(doc).OfClass(FilledRegionType).ToElements()
            if not filledRegionTypes:
                print("No FilledRegionType found in the document.")
                return

            #filledRegionType = filledRegionTypes[0]  # Use the first available FilledRegionType
            filledRegionType = collected_fill_pattern

            with Transaction(doc, "Create Filled Region") as t:
                t.Start()
                try:
                    FilledRegion.Create(doc, filledRegionType.Id, target_view_id, [curve_loop])
                    print("Filled Region created successfully.")
                except Exception as e:
                    print("Failed to create Filled Region:", e)
                finally:
                    t.Commit()
        else:
            print("Apartment Type parameter not found or doesn't contain", area.Id, "in sheet:", alphanumeric_sheet_title)


def move_schedule_to_new_sheet(doc, original_sheet_id, new_sheet_id, new_location):
    """
    Moves a schedule from one sheet to another sheet at a specified location.

    Args:
    doc: The Revit document.
    original_sheet_id: The ElementId of the original sheet.
    new_sheet_id: The ElementId of the target (new) sheet.
    schedule_name: The name of the schedule to move.
    new_location: An XYZ object indicating the new location on the target sheet.
    """
    # Start a transaction
    t = Transaction(doc, "Move Schedule to New Sheet")
    t.Start()
    
    try:
        # Find the ScheduleSheetInstance on the original sheet
        original_schedules = FilteredElementCollector(doc, original_sheet_id).OfClass(ScheduleSheetInstance).ToElements()
        schedule_to_move = None
        for schedule in original_schedules:
            # Optionally filter by schedule name
            schedule_view = doc.GetElement(schedule.ScheduleId)
            if schedule_view.Name:
                schedule_to_move = schedule
                break
        
        if schedule_to_move is None:
            print("NO SCHEDULE FOUND.")
            t.RollBack()
            return

        # Create or find the target (new) sheet
        new_sheet = doc.GetElement(new_sheet_id)
        if new_sheet is None:
            print("New sheet not found.")
            t.RollBack()
            return
        
        # Place the schedule on the new sheet at the specified location
        # Note: ScheduleSheetInstance.Create method signature: (Document, ViewSheet, ElementId, XYZ)
        ScheduleSheetInstance.Create(doc, new_sheet.Id, schedule_to_move.ScheduleId, new_location)
        print("THE SCHEDULE {} MOVED ON NEW SHEET {} AT NEW LOCATION {}.".format(schedule_to_move.Name, new_sheet, new_location))

        t.Commit()
    except Exception as e:
        print("Failed to move schedule: {}".format(e))
        t.RollBack()

def duplicate_view(view):
    # Start the transaction
    with Transaction(doc, "Duplicate View and Apply Scope Box") as t:
        t.Start()
        try:
            # Duplicate view
            duplicated_view_id = view.Duplicate(ViewDuplicateOption.Duplicate)
            duplicated_view = doc.GetElement(duplicated_view_id)

        except Exception as e:
            print("Failed to duplicate view: {}".format(e))
            t.RollBack()
            return None
        else:
            t.Commit()
            return duplicated_view

def pick_text_style(doc):
    # Collect all TextNoteTypes in the document
    text_styles = FilteredElementCollector(doc).OfClass(TextNoteType).ToElements()

    # Prepare a dictionary with TextNoteType name and element ID, ensuring that each element has a Name attribute
    text_styles_dict = {style.LookupParameter("Type Name").AsString(): style.Id for style in text_styles}

    # Ask the user to pick a text style from the list
    picked_style_name = forms.SelectFromList.show(text_styles_dict.keys(),
                                                       message='Pick a text style:')

    # Return the selected TextNoteType element
    if picked_style_name:
        return text_styles_dict[picked_style_name]
    else:
        forms.alert('No text style selected.', exitscript=True)

def copy_text_annotations(source_view_id, target_view_id, selected_text_style, doc):
    # Begin a transaction to modify the document
    #t = Transaction(doc, "Copy Text Annotations")
    #t.Start()
    
    # Collect all text notes in the source view
    text_notes = FilteredElementCollector(doc, source_view_id).OfClass(TextNote).ToElements()
    for text_note in text_notes:
        text_type_id = text_note.TextNoteType.Id
        text = text_note.Text
        location = text_note.Coord

        # Verify the type ID
        print("Text Note Type ID:", text_type_id)

        options = TextNoteOptions(text_type_id)
        options.HorizontalAlignment = text_note.HorizontalAlignment
        #options.TypeId = text_note.GetTypeId()
        options.TypeId = selected_text_style
        new_text_note = TextNote.Create(doc, target_view_id, location, text, options)
    
    # Commit changes to the document
    #t.Commit()

def duplicate_sheets_and_place_views(selected_sheets, title_block_id, start_number_prefix, selected_template_1, selected_template_2, selected_template_3, selected_template_key, selected_text_style):
    
    count = 0
    number_views = 3

    # ========================================================================
    # LOOP THROUGH SHEETS
    # ========================================================================
    for sheet in selected_sheets:
        print("PROCESSING SHEET:{}".format(sheet.Name))
        # CREATE / DUPLICATE SHEET
        with Transaction(doc, "Create Sheet") as t:
                t.Start()

                # Get the view from the sheet
                original_sheet = doc.GetElement(sheet.Id)
                if not original_sheet:
                    print("Sheet not found")
                
                # Duplicate the sheett
                new_sheet = ViewSheet.Create(doc, title_block_id)
                if not new_sheet:
                            print("Failed to create new sheet.")
                            return None
                
                # Extract original sheet number and format the new one
                original_sheet_number = original_sheet.SheetNumber.split('-', 1)
                if len(original_sheet_number) > 1:
                    # If the original number follows the "XX - YYY" format
                    new_sheet_number = "{} - {}".format(start_number_prefix, original_sheet_number[1])
                else:
                    # Fallback in case the original number doesn't follow the expected format
                    new_sheet_number = "{} - {}".format(start_number_prefix, count)
                    count += 1

                # Apply the new sheet number and name with suffix
                new_sheet.SheetNumber = new_sheet_number
                new_sheet.Name = "{}".format(original_sheet.Name)
                
                # ========================================================================
                # SET SHEET PARAMETERS
                # ========================================================================
                # Get the title block for the new sheet
                title_blocks = FilteredElementCollector(doc, new_sheet.Id).OfCategory(BuiltInCategory.OST_TitleBlocks).WhereElementIsNotElementType().ToElements()
                if not title_blocks:
                    print("No title block found on the new sheet.")
                    continue
                title_block = title_blocks[0]  # Assuming there's only one title block per sheet

                # Check which "KEY CORE" parameter should be set to true based on the sheet name
                core_keys = {
                    "C1": "KEY CORE 1",
                    "C2": "KEY CORE 2",
                    "C3": "KEY CORE 3",
                    "C4": "KEY CORE 4",
                    "Void": "BUILDING KEY",
                    "VOid": "KEY PODIUM"
                }
                for core, core_key in core_keys.items():
                    param = title_block.LookupParameter(core_key)
                    if param:
                        # Set the corresponding parameter to true if core is in the sheet name,
                        # otherwise set it to false
                        param.Set(1 if core in new_sheet.Name else 0)
                        print("Parameter '{}' set to {}.".format(core_key, 'On' if core in new_sheet.Name else 'Off'))
                    else:
                        print("Parameter '{}' not found on title block.".format(core_key))

                t.Commit()

                # ========================================================================
                # CREATE & PLACE VIEWS
                # ========================================================================
                # Initial position for placing views
                x_offset = 157.5 / 304.8  # Convert from millimeters to feet
                initial_y_offset = 265 / 304.8 # Convert from millimeters to feet
                offset_x_increment = 265 / 304.8
                offset_y_increment = 182 / 304.8
                # Define suffixes for each duplicated view
                view_suffixes = [" - SETTING OUT", " - ELE LOW LEVEL", " - ELE HIGH LEVEL"]
                
                # Get all viewports on the sheet
                viewports = FilteredElementCollector(doc, sheet.Id).OfClass(Viewport).ToElements()
                schedule = FilteredElementCollector(doc, sheet.Id).OfClass(ViewSchedule).ToElements()
                print("Nuber of viewports:{}".format(len(viewports)))
                for v in viewports:
                    print("Name of Viewport{} is: {}".format(count, v.Name))
                    count += 1
                    # Get the view associated with each viewport
                    view_id = v.ViewId
                    view = doc.GetElement(view_id)
                    # Check if view is not None and perform operations on the view
                    if view:
                        print("PROCESSING VIEW: {0}".format(view.Name)) 
                        if 'FLAT TYPE' in view.Name:
                            # Duplicate and place the views on the sheet
                            for i in range(number_views):
                                view_to_place = duplicate_view(view)
                                if view_to_place:
                                    print("Duplicated view ID: {}".format(view_to_place.Id))
                                    # Rename the duplicated view
                                    new_view_name = "{0} {1}".format(view_to_place.Name.split(' Copy')[0], view_suffixes[i])
                                    # Assuming the duplicate_view function returns a View object
                                    # Start a transaction for renaming the view
                                    with Transaction(doc, "Rename Duplicated View") as rename_trans:
                                        rename_trans.Start()
                                        view_to_place.Name = new_view_name
                                        rename_trans.Commit()
                                    print("New view name: {0}".format(new_view_name))
                                else:
                                    print("Failed to duplicate view.")
                                pass
                                with Transaction(doc, "Place Views") as t:
                                    print("INITIATE SECOND TRANSACTION - TO POSITION VIEW: {0}".format(view_to_place.Name))
                                    t.Start()
                                    if i == 0:
                                        view_to_place.ViewTemplateId = selected_template_1.Id
                                    elif i==1:
                                        view_to_place.ViewTemplateId = selected_template_2.Id
                                    else:
                                        view_to_place.ViewTemplateId = selected_template_3.Id
                                    # Calculate the position for the current view
                                    x_position = x_offset + (i % 3) * offset_x_increment
                                    #y_position = y_offset - (i // 3) * offset_y_increment
                                    view_location = XYZ(x_position, initial_y_offset, 0)
                                    try:
                                        # Create the viewport for the current view
                                        # Use view_to_place.Id for the view's Id
                                        duplicated_view = Viewport.Create(doc, new_sheet.Id, view_to_place.Id, view_location)
                                        #apply_templates_to_views(duplicated_view, selected_template_key)
                                        print("SUCCESSFULLY ENDED SECOND TRANSACTION FOR {0}".format(view_to_place.Name))
                                    # Increment the count for the next sheet number  
                                    except Exception as e:
                                        print("Failed to place view on sheet. Error:", e)
                                    count += 1
                                    t.Commit()       

                        elif 'CORE' in view.Name:
                            key_to_place = duplicate_view(view)
                            if key_to_place:
                                print("Duplicated view: {}".format(key_to_place.Name))
                                # Rename duplicated view
                                new_key_name = "{0} {1}".format(key_to_place.Name.split(' Copy')[0], " - KEY PLAN")
                                with Transaction(doc, "Rename Duplicated Key") as rename_t:
                                    rename_t.Start()
                                    key_to_place.Name = new_key_name
                                    rename_t.Commit()
                                    print("New key name:",new_key_name)
                            else:
                                print("Failed to duplicate view.")
                            pass
                            with Transaction(doc, "Place Key View") as t:
                                    print("INITIATE SECOND TRANSACTION FOR KEY_VIEW: To duplicate {0}".format(key_to_place.Name))
                                    t.Start()
                                    # Calculate the position for the current view
                                    view_location = XYZ(728/304.8, ((initial_y_offset)*2)-10/304.8, 0)
                                    try:
                                        key_to_place.ViewTemplateId = selected_template_key.Id
                                        copy_text_annotations(view.Id, key_to_place.Id, selected_text_style, doc)
                                        # Create the viewport for the current view
                                        duplicated_view = Viewport.Create(doc, new_sheet.Id, key_to_place.Id, view_location)
                                        #apply_templates_to_views(duplicated_view, selected_template_key)
                                        print("SUCCESSFULLY ENDED SECOND TRANSACTION FOR {0}".format(key_to_place.Name))
                                    # Increment the count for the next sheet number  
                                    except Exception as e:
                                        print("Failed to place view on sheet. Error:", e)
                                    t.Commit()
                                    # Example usage
                                    sheet_title_contains = "C4 2B3PB"
                                    alphanumeric_sheet_title = re.sub(r'\W+', '', sheet.Name).upper()
                                    print("Alphanumeric_sheet_title:",alphanumeric_sheet_title)
                                    create_filled_region_from_area_boundaries(doc, alphanumeric_sheet_title, key_to_place.Id, collected_fill_pattern)

                                    
                # =====================================================================================
                #   SCHEDULE
                # =====================================================================================
                                                            
                # Assume you have the IDs of the original and new sheets and the new location
                original_sheet_id = sheet.Id  # Replace original_sheet_id_int with the actual original sheet ID integer
                new_sheet_id = new_sheet.Id  # Replace new_sheet_id_int with the actual new sheet ID integer
                new_schedule_location = XYZ(438/304.8, 565/304.8, 0)  # Replace with the desired new location (in feet)

                move_schedule_to_new_sheet(doc, original_sheet_id, new_sheet_id, new_schedule_location)
                
                    



if __name__ == "__main__":
    selected_sheets = select_sheets()
    print("Sheets slected:{}".format(selected_sheets))

    # Step 0: Prompt User for View Name Prefix
    #name_suffix = prompt_for_view_name_suffix()
    #if not name_suffix:
    #    print("No view name prefix provided. Exiting...")
    #    sys.exit()

    # Step 1: Select Title Block
    title_block_id = pick_title_block()
    if not title_block_id:
        print("No title block selected. Exiting...")
        sys.exit()

    # Step 2.0: Select Template
    selected_template_1 = prompt_for_tamplate()
    if not selected_template_1:
        print("Template not selected. Exiting...")
        sys.exit()

    # Step 2.1: Select Template
    selected_template_2 = prompt_for_tamplate()
    if not selected_template_2:
        print("Template not selected. Exiting...")
        sys.exit()

    # Step 2.2: Select Template
    selected_template_3 = prompt_for_tamplate()
    if not selected_template_2:
        print("Template not selected. Exiting...")
        sys.exit()

    # Step 2.3: Select Template
    selected_template_key = prompt_for_tamplate()
    if not selected_template_key:
        print("Template not selected. Exiting...")
        sys.exit()

    # Step 4: Prompt User for Starting Sheet Number
    starting_sheet_number = prompt_for_starting_sheet_number()
    if not starting_sheet_number:
        print("No starting sheet number provided. Exiting...")
        sys.exit()

    # Step 5: Select Fill Patterns
    collected_fill_pattern = doc.GetElement(collect_filled_region_types(doc))
    print(collected_fill_pattern, type(collected_fill_pattern))
    if not collected_fill_pattern:
        print("No fill pattern selected. Exiting...")
        sys.exit()

    # Step 6: Select Text Style for Key View
    selected_text_style = pick_text_style(doc)
    print(selected_text_style, type(selected_text_style))
    if not selected_text_style:
        print("No text style selected...")
        sys.exit()

    # Step 7: Create Sheets and Place Views
    duplicate_sheets_and_place_views(selected_sheets, title_block_id, starting_sheet_number, selected_template_1, selected_template_3, selected_template_2, selected_template_key, selected_text_style)
    print("Process completed successfully.")









