__title__="CreateSheetsForDuplicatedViews"
__author__="Bogdan Popa"
__doc__="""Duplicates Views places on Sheets.
Sheet Name - Prefix - 

View Name = Sheet Name( - Level XX)"""

import clr
import sys
from pyrevit import forms
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, ElementId, ViewType
import Autodesk.Revit.DB as DB

clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *

app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document
     

def get_view_category():
    from System import Enum
    category_options = [category.ToString() for category in Enum.GetValues(ViewType)]
    category_name = forms.SelectFromList.show(category_options, title='Select View Category')
    if not category_name:
        sys.exit(0)
    return Enum.Parse(ViewType, category_name)

def get_views_by_type(view_type):
    all_views = FilteredElementCollector(doc).OfClass(View).ToElements()
    filtered_views = [v for v in all_views if v.ViewType == view_type]

    # Get names of selected views from the user
    selected_view_names = forms.SelectFromList.show([v.Name for v in filtered_views], title='Select {} Views'.format(view_type), multiselect=True)

    if not selected_view_names:
        print("No views selected.")
        return []

    # Find and return the View objects corresponding to the selected names
    return [v for v in filtered_views if v.Name in selected_view_names]

def prompt_for_view_name_prefix():
    return forms.ask_for_string("Enter view/sheet name prefix (e.g., 'RCP -'):")

def select_scope_box():
    scope_boxes = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_VolumeOfInterest).WhereElementIsNotElementType().ToElements()
    selected_name = forms.SelectFromList.show([sb.Name for sb in scope_boxes], title='Select a Scope Box', multiselect=False)
    return next((sb for sb in scope_boxes if sb.Name == selected_name), None)

def pick_title_block():
    collector = FilteredElementCollector(doc).OfClass(FamilySymbol).OfCategory(BuiltInCategory.OST_TitleBlocks)
    title_blocks = {tb.FamilyName: tb.Id for tb in collector.ToElements()}
    selected = forms.SelectFromList.show(title_blocks.keys(), title='Select Titleblock', multiselect=False)
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
    selected_template = next(template for template in view_templates if template.Name == selected_template_name) # Stores the template
    return selected_template

def prompt_for_starting_sheet_number():
    while True:
        number = forms.ask_for_string("Enter starting sheet number (e.g., '35 - 100'):")
        if number and '-' in number and number.split('-')[-1].strip().isdigit():
            return number
        print("Invalid format. Please enter a sheet number in the format '35 - 100'.")

def duplicate_views_and_apply_scope_box(views, scope_box):
    duplicated_views = []
    with Transaction(doc, "Duplicate Views and Apply Scope Box") as t:
        t.Start()
        for view in views:
            # Duplicate view
            # Assuming 'view' is a Revit View object
            duplicated_view_ids = ElementTransformUtils.CopyElement(doc, view.Id, XYZ(0, 0, 0))

            # Check if we have received any IDs back
            if duplicated_view_ids and len(duplicated_view_ids) > 0:
                duplicated_view_id = duplicated_view_ids[0]
                duplicated_view = doc.GetElement(duplicated_view_id)
            else:
                print("No view was duplicated.")
            # Apply scope box
            duplicated_view.get_Parameter(BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP).Set(scope_box.Id)
            duplicated_views.append(duplicated_view)
        t.Commit()
    return duplicated_views

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

def apply_templates_to_views(selected_views, selected_template):
    t = Transaction(doc, 'Apply Templates to Views')
    t.Start()
    for view in selected_views:
        if selected_template:
            view.ViewTemplateId = selected_template.Id
    t.Commit()

def create_sheets_and_place_views(views, title_block_id, start_number_prefix, name_prefix, selected_template):
    apply_templates_to_views(views, selected_template)

    # Split the prefix and base number
    prefix, base_number = start_number_prefix.rsplit('-', 1)
    prefix = prefix.strip()
    base_number = base_number.strip()

    with Transaction(doc, "Create Sheets and Place Views") as t:
        t.Start()
        for view in views:
            if isinstance(view, ViewPlan):  # Ensure the view is a plan view
                level = view.GenLevel
                if level:
                    level_number = ''.join(c for c in level.Name if c.isdigit())
                    level_number_int = int(level_number)

                    # Format sheet number based on level
                    if level_number_int < 10:
                        new_sheet_number = "{} - {}{}".format(prefix, base_number[:-1], level_number)
                        new_sheet_name = "{} - LEVEL 0{}".format(name_prefix,level_number_int)
                        new_view_name = "{} - LEVEL 0{}".format(name_prefix,level_number_int)
                    else:
                        new_sheet_number = "{} - {}{}".format(prefix, base_number[:-2], level_number)
                        new_sheet_name = "{} - LEVEL {}".format(name_prefix,level_number_int)
                        new_view_name = "{} - LEVEL {}".format(name_prefix,level_number_int)

                    if not is_sheet_number_in_use(new_sheet_number, doc):
                        sheet = ViewSheet.Create(doc, title_block_id)
                        sheet.SheetNumber = new_sheet_number
                        sheet.Name = new_sheet_name

                        # Define the location to place the view on the sheet
                        sheet_width = sheet.Outline.Max.U - sheet.Outline.Min.U
                        sheet_height = sheet.Outline.Max.V - sheet.Outline.Min.V
                        view_location = XYZ((sheet_width-(102.5/304.8)) / 2, sheet_height / 2, 0)

                        view.Name = new_sheet_name

                        # Place view on sheet
                        try:
                            Viewport.Create(doc, sheet.Id, view.Id, view_location)
                        except Exception as e:
                            print("Failed to place view on sheet. Error:", e)
                    else:
                        print("Sheet number", new_sheet_number, "is already in use.")
                else:
                    print("No associated level found for the plan view.")
            else:
                print("The view is not a plan view.")
        t.Commit()






if __name__ == "__main__":
    # Step 0: Select View Type
    select_plan_view = get_view_category()

    # Step 1: Collect Ceiling Plan Views
    plan_views = get_views_by_type(select_plan_view)
    if not plan_views:
        print("No ceiling plan views selected. Exiting...")
        sys.exit()

    # Step 2: Prompt User for View Name Prefix
    name_prefix = prompt_for_view_name_prefix()
    if not name_prefix:
        print("No view name prefix provided. Exiting...")
        sys.exit()

    # Step 3: Select Scope Box
    selected_scope_box = select_scope_box()
    if not selected_scope_box:
        print("No scope box selected. Exiting...")
        sys.exit()

    # Step 4: Select Title Block
    title_block_id = pick_title_block()
    if not title_block_id:
        print("No title block selected. Exiting...")
        sys.exit()

    # Step 5: Select Template
    selected_template = prompt_for_tamplate()
    if not selected_template:
        print("Template not selected. Eiting...")
        sys.exit()

    # Step 6: Prompt User for Starting Sheet Number
    starting_sheet_number = prompt_for_starting_sheet_number()
    if not starting_sheet_number:
        print("No starting sheet number provided. Exiting...")
        sys.exit()

    # Step 7: Duplicate Views and Apply Scope Box
    duplicated_views = duplicate_views_and_apply_scope_box(plan_views, selected_scope_box)
    if not duplicated_views:
        print("Failed to duplicate views. Exiting...")
        sys.exit()

    # Step 8: Create Sheets and Place Views
    create_sheets_and_place_views(duplicated_views, title_block_id, starting_sheet_number, name_prefix, selected_template)
    print("Process completed successfully.")
















