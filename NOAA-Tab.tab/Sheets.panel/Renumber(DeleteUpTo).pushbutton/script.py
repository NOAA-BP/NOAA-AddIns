__title__="02.01 Renumber(DeleteUpTo)"
__author__="Bogdan Popa"
__doc__="""Deletes all characters in the Sheet(s) Number up to specified location"""

import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, BuiltInParameter
from pyrevit import forms

# Function to modify the sheet number
def modify_sheet_number(sheet, delimiter):
    number_param = sheet.get_Parameter(BuiltInParameter.SHEET_NUMBER).AsString()
    # Find the delimiter in the sheet number
    index = number_param.find(delimiter)
    if index != -1:
        # Remove all characters up to the delimiter
        new_number = number_param[index:]
        return new_number
    else:
        return None

# Main script
doc = __revit__.ActiveUIDocument.Document

# Get all sheets in the project
all_sheets_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Sheets).WhereElementIsNotElementType().ToElements()
all_sheets = {sht.SheetNumber: sht for sht in all_sheets_collector}

# Prompt user to select sheets to modify
selected_sheet_numbers = forms.SelectFromList.show(sorted(all_sheets.keys()), multiselect=True, title='Select Sheets to Modify')

# If user cancels selection, end script
if not selected_sheet_numbers:
    forms.alert('No sheets selected. Exiting.', exitscript=True)

# Prompt user to enter the delimiter
delimiter = forms.ask_for_string(default='-', prompt='Enter the delimiter after which to keep the sheet number', title='Enter Delimiter')

# If user cancels input, end script
if delimiter is None:
    forms.alert('No delimiter provided. Exiting.', exitscript=True)

# Start a transaction to modify the document
t = Transaction(doc, "Modify Sheet Numbers")
t.Start()

try:
    for number in selected_sheet_numbers:
        sheet = all_sheets[number]
        new_number = modify_sheet_number(sheet, delimiter)
        if new_number:
            sheet.get_Parameter(BuiltInParameter.SHEET_NUMBER).Set(new_number)
            print("Modified sheet number to: {}".format(new_number))
        else:
            print("Delimiter '{}' not found in sheet number: {}".format(delimiter, sheet.SheetNumber))
    t.Commit()
except Exception as e:
    print(str(e))
    t.RollBack()














