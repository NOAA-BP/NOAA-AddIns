__title__="DeleteViews,Sheets,Rooms,Areas"
__author__="Bogdan Popa"
__doc__=""""""

from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, Transaction, View

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
active_view_id = uidoc.ActiveView.Id

# Start a transaction
t = Transaction(doc, "Delete All Sheets")
t.Start()

try:
    sheets = FilteredElementCollector(doc).OfClass(ViewSheet).ToElements()
    for sheet in sheets:
        if sheet.Id != active_view_id:
            doc.Delete(sheet.Id)

    t.Commit()
except Exception as e:
    print("Error:", str(e))
    t.RollBack()

# Start a transaction
t = Transaction(doc, "Delete All Views")
t.Start()

try:
    views = FilteredElementCollector(doc).OfClass(View).ToElements()
    print("Views to be deleted:", len(views))
    for view in views:
        if view.Id == active_view_id:
            print("View",view.Id,"is the active view")
        else: 
            try:
                doc.Delete(view.Id)
            except Exception as e:
                print("Failed to delete view:", view.Id, "Error:", str(e))

    #t.Commit()
except Exception as e:
    print("Error:", str(e))

t.Commit()
    #t.RollBack()




























