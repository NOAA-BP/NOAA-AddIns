__title__="RenameSheets(Prefix)"
__author__="Bogdan Popa"
__doc__="""Sheet Number = XX-XXX
Sheet Name = ABC - Level 00"""

from Autodesk.Revit.DB import ViewSheet
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

# Prompt the user to select sheets
sheets_to_modify = forms.select_sheets(title='Select Sheets to Modify')

# Prompt the user for the new prefix
sheet_prefix = forms.ask_for_string(default="",
                                    prompt="Enter prefix for sheet names:",
                                    title="Prefix for Sheet Names")

# Make sure the user has selected at least one sheet and entered the prefix
if not sheets_to_modify or not sheet_prefix:
    TaskDialog.Show("Error", "Please select at least one sheet and enter the prefix.")
else:
    with revit.Transaction("Modify Sheet Names"):
        for sheet in sheets_to_modify:
            # Modify the sheet name by adding the user-provided prefix
            original_sheet_name = sheet.Name
            new_sheet_name = sheet_prefix + original_sheet_name
            sheet.Name = new_sheet_name

    TaskDialog.Show("Success", "Sheet names have been modified.")











