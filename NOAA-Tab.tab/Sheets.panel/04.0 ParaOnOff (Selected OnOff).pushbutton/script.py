__title__="4.0 ParaOnOff (SELECTED ON/OFF)"
__author__="Bogdan Popa"
__doc__="""Sets selcted paramters to ON or OFF"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System import Array
from System.Windows.Forms import Application, Form, Button, CheckedListBox, DialogResult
from System.Drawing import Point

# Import necessary modules
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, FamilyInstance
from Autodesk.Revit.UI import TaskDialog
from pyrevit import forms
from pyrevit import revit, DB

# Get the active Revit application and document
doc = __revit__.ActiveUIDocument.Document

class ParameterForm(Form):
    def __init__(self, param_names):
        self.param_names = param_names  # Store as an attribute of the class
        self.Text = "Select Parameters to Modify"

        self.checkedListBox = CheckedListBox()
        self.checkedListBox.Items.AddRange(param_names)
        self.checkedListBox.CheckOnClick = True
        self.checkedListBox.Location = Point(10, 10)
        self.checkedListBox.Width = 200
        self.checkedListBox.Height = 200

        self.buttonOn = Button()
        self.buttonOn.Text = "ON"
        self.buttonOn.Location = Point(220, 10)
        self.buttonOn.Click += self.button_click

        self.buttonOff = Button()
        self.buttonOff.Text = "OFF"
        self.buttonOff.Location = Point(220, 40)
        self.buttonOff.Click += self.button_click

        self.Controls.Add(self.checkedListBox)
        self.Controls.Add(self.buttonOn)
        self.Controls.Add(self.buttonOff)

    def button_click(self, sender, args):
        selected_params = [self.checkedListBox.Items[i] for i in range(self.checkedListBox.Items.Count) if self.checkedListBox.GetItemChecked(i)]
        turn_on = sender.Text == "ON"
        param_value = 1 if turn_on else 0

        try:
            with revit.Transaction("Modify Title Block Parameters"):
                for sheet in sheets_to_modify:
                    print("Modifying parameters for sheet: " + sheet.Name)
                    title_blocks = FilteredElementCollector(doc, sheet.Id).OfClass(FamilyInstance).ToElements()
                    title_block = next((tb for tb in title_blocks if tb.Category.Id.IntegerValue == int(BuiltInCategory.OST_TitleBlocks)), None)
                    
                    if title_block is None:
                        print("No title block found for sheet: " + sheet.Name)
                        continue

                    for param_name in selected_params:
                        param = title_block.LookupParameter(param_name)
                        if param:
                            if param.IsReadOnly:
                                print("Parameter '{}' is read-only.".format(param_name))
                            else:
                                param.Set(param_value)
                                print("Parameter '{}' set to {}.".format(param_name, param_value))
                        else:
                            print("Parameter '{}' not found.".format(param_name))

                doc.Regenerate()  # Force Revit to regenerate the document
                print("Transaction completed successfully.")

            TaskDialog.Show("Success", "Parameter values have been set in the title blocks of selected sheets.")
        except Exception as e:
            print("Error: " + str(e))
            TaskDialog.Show("Error", "An error occurred. See console for details.")

        self.Close()



# Prompt the user to select multiple sheets
sheets_to_modify = forms.select_sheets(title='Select Sheets to Modify Title Blocks')
if not sheets_to_modify:
    TaskDialog.Show("Error", "Please select sheets.")
    exit()

# Get the title block of the first selected sheet as a sample
sample_sheet = sheets_to_modify[0]
title_blocks = FilteredElementCollector(doc, sample_sheet.Id).OfClass(FamilyInstance).ToElements()
sample_title_block = next((tb for tb in title_blocks if tb.Category.Id.IntegerValue == int(BuiltInCategory.OST_TitleBlocks)), None)

# Get a list of Boolean (On/Off) parameters from the sample title block
sample_tb_params = sample_title_block.Parameters
param_names = [param.Definition.Name for param in sample_tb_params if param.StorageType == DB.StorageType.Integer]

# Prompt the user to select multiple parameters to modify from the list
#params_to_modify = forms.SelectFromList.show(param_names, title='Select Parameters to Modify', multiselect=True)
#if not params_to_modify:
#    TaskDialog.Show("Error", "No parameters selected.")
#    exit()
param_names_array = Array[object](param_names)


# Usage
form = ParameterForm(param_names_array)
Application.EnableVisualStyles()
Application.Run(form)
















