__title__="04.1 IdentifyGroupsForKitchens(WriteAreaPara)"
__author__="Bogdan Popa"
__doc__="""It removes one filter at index and name, it adds a new filter at the end of the list"""

from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, BuiltInParameter, Transaction, ElementId, FilteredElementCollector, BuiltInCategory, XYZ
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from rpw.ui.forms import SelectFromList
from System.Collections.Generic import List
from pyrevit import forms
import re

# Access the current document
app = __revit__.Application
doc = __revit__.ActiveUIDocument.Document

TOLERANCE = 1e-0 # Example tolerance value; adjust based on your application's requirements

# Function to collect plumbing fixtures and allow user selection
def collect_and_select_plumbing_fixtures(doc):
    # Collect all plumbing fixtures
    collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()
    fixtures = list(collector)

    # Prepare fixture names for selection
    fixture_names = [f.Name for f in fixtures]
    unique_fixture_names = list(set(fixture_names))  # Remove duplicates

    # User selection
    selected_name = SelectFromList('Select Fixture Family', unique_fixture_names)

    return selected_name

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

# Function to list groups containing the selected fixture family
def list_fixture_groups(doc, selected_name):
    groups = []
    count = 0 
    # Ensure a selection was made
    if selected_name:
        # Collect all instances again to match the selected name and find their groups
        collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()
        for f in collector:
            if f.Name == selected_name and f.GroupId.IntegerValue != -1:  # Check if part of a group
                count += 1
                group = doc.GetElement(f.GroupId)
                if group.Name not in groups:
                    groups.append(group.Name)
        print("NUMBRER OF KITCHENS / GROUPS:",count)
    return groups

# Function to collect areas based on 'Apartment Number' and check if they are in the same group as the selected fixture
def list_areas_by_apartment_number(doc, selected_name, selected_groups):
    # Collect all areas
    area_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Areas).WhereElementIsNotElementType()
    areas = list(area_collector)

    count = 0
    # Filter areas by those that have a specified 'Apartment Number' and are in the selected groups
    apartment_areas = {}
    for area in areas:
        apartment_number = area.LookupParameter('Number')
        if apartment_number and apartment_number.AsString() and len(apartment_number.AsString()) <= 8 and area.GroupId in [ElementId(gid) for gid in selected_groups]:
            group_name = doc.GetElement(area.GroupId).Name
            if apartment_number.AsString() not in apartment_areas:
                apartment_areas[apartment_number.AsString()] = [group_name]
            elif group_name not in apartment_areas[apartment_number.AsString()]:
                apartment_areas[apartment_number.AsString()].append(group_name)
    print("NUMBER OF APARTMENT AREAS COLLECTED:", len(apartment_areas))
    # Start a transaction to modify the document
    t = Transaction(doc, "Update Area Parameters")
    try:
        t.Start()
        for apartment_number, selected_groups in apartment_areas.items():
            for group_name in selected_groups:
                for area in areas:
                    if area.GroupId != ElementId.InvalidElementId and doc.GetElement(area.GroupId).Name == group_name:
                        target_parameter = area.LookupParameter("KITCHEN TYPE")
                        if target_parameter and target_parameter.StorageType == StorageType.String:
                            print ("KITCHEN TYPE parameter identified for area:",area)
                            count += 1
                            target_parameter.Set(selected_name)
        t.Commit()
    except Exception as e:
        print("An error occurred: {}".format(str(e)))
        t.RollBack()
    finally:
        if t.HasStarted() and not t.HasEnded():
            t.RollBack()
    print ("TOTAL NUMBER OF AREAS MARKED:",count)
    return apartment_areas




def get_curve_loop_from_area_boundaries(doc, area):
    print("CURVE LOOP INITIATED")
    boundaryOptions = SpatialElementBoundaryOptions()
    #print("Area found: ", area.Id)
    boundary_segments = area.GetBoundarySegments(boundaryOptions)
    
    curves = []

    # Process each boundary segment to collect curves
    for boundaryList in boundary_segments:
        for segment in boundaryList:
            curve = segment.GetCurve()
            curves.append(curve)
    print("BOUNDARY CURVES FOR AREA {}: {}".format(area.Id,len(boundary_segments)))
    # Ensure continuity and create a CurveLoop for the Filled Region
    curve_loop = CurveLoop()
    for i, curve in enumerate(curves):
        next_curve = curves[(i + 1) % len(curves)]
        if not curve.GetEndPoint(1).IsAlmostEqualTo(next_curve.GetEndPoint(0)):
            curve = Line.CreateBound(curve.GetEndPoint(0), next_curve.GetEndPoint(0))
        curve_loop.Append(curve)
    return curve_loop

def convert_curves_to_vertices(curve_loop):
    """
    Converts a list of curves into a list of (X, Y) tuples representing the vertices of a polygon.
    
    Parameters:
    - curve_loop: A list of Curve objects forming a closed loop.
    
    Returns:
    - A list of (X, Y) tuples representing the vertices of the polygon defined by the curve loop.
    """
    polygon_vertices = []
    for curve in curve_loop:
        # Assuming curve is a Line or similar simple curve type with accessible start and end points
        start_point = curve.GetEndPoint(0)  # Get start point of the curve
        end_point = curve.GetEndPoint(1)    # Get end point of the curve

        # Add start point to the list if it's the first curve or if it doesn't duplicate the last added point
        if not polygon_vertices or (polygon_vertices[-1] != (start_point.X, start_point.Y, start_point.Z)):
            polygon_vertices.append((start_point.X, start_point.Y, start_point.Z))
        
        # Since curves are ordered and form a closed loop, we add the end point of the last curve outside the loop

    # Ensure the polygon is closed by adding the end point of the last curve, if not already added
    if not polygon_vertices or polygon_vertices[0] != (end_point.X, end_point.Y, end_point.Z):
        polygon_vertices.append((end_point.X, end_point.Y, end_point.Z))

    return polygon_vertices


def is_point_inside_polygon(px, py, polygon):
    print("CHECK IF LOCATION POINT IS INSIDE VERTICES")
    # polygon is a list of (x, y) pairs.
    num_intersections = 0
    n = len(polygon)

    for i in range(n):
        # Current point
        curr_x, curr_y = polygon[i]
        # Next point
        next_x, next_y = polygon[(i + 1) % n]

        # Check if the edge is intersected by the ray to the right
        if ((curr_y > py) != (next_y > py)) and \
                (px < (next_x - curr_x) * (py - curr_y) / (next_y - curr_y) + curr_x):
            num_intersections += 1

    # Odd number of intersections means the point is inside
    return num_intersections % 2 == 1

def project_point_to_plane(point, plane):
    # Assume 'plane' is an instance of Revit's Plane class, or similar
    # This could be constructed from the curve loop's normal and any point on it
    direction = point - plane.Origin
    distance = direction.DotProduct(plane.Normal)
    projected_point = point - (plane.Normal * distance)
    return XYZ(projected_point.X, projected_point.Y, plane.Origin.Z)  # Projected point in 3D, but effectively 2D

def get_area_plane(doc, area):
    # Get the level of the Area
    area_level = doc.GetElement(area.LevelId)
    area_elevation = area_level.Elevation

    # Get boundary segments of the Area
    boundary_options = SpatialElementBoundaryOptions()
    boundary_segments = area.GetBoundarySegments(boundary_options)
    if len(boundary_segments) == 0 or len(boundary_segments[0]) == 0:
        return None  # No boundary found

    # Use the first segment to get a point on the boundary
    first_segment = boundary_segments[0][0]
    curve = first_segment.GetCurve()
    point_on_curve = curve.GetEndPoint(0)

    # Create a plane using the normal vector and the point
    normal = XYZ(0, 0, 1)
    area_plane = Plane.CreateByNormalAndOrigin(normal, XYZ(point_on_curve.X, point_on_curve.Y, area_elevation))

    return area_plane

class PointInPoly:
    def get_quadrant(self, vertex, p):
        # Unpack only X and Y, ignore Z
        x, y, _ = vertex  # Assuming vertex is a tuple (x, y, z)
        p_x, p_y, _ = p  # Similarly, assuming p is a tuple (x, y, z)
        
        if x > p_x:
            return 0 if y > p_y else 3
        else:
            return 1 if y > p_y else 2

    def x_intercept(self, p, q, y):
        """
        Determine the X intercept of a polygon edge
        with a horizontal line at the Y value of the
        test point, considering a tolerance.
        """
        assert p[1] != q[1], "unexpected horizontal segment"
        x_intercept = q[0] - ((q[1] - y) * ((p[0] - q[0]) / (p[1] - q[1])))
        
        return x_intercept


    def adjust_delta(self, delta, vertex, next_vertex, p):
        """
        Adjust the delta based on the quadrant change.
        """
        # Convert 'p' to a tuple if it's not already
        p_tuple = (p.X, p.Y) if hasattr(p, 'X') else p

        if delta == 3:
            delta = -1
        elif delta == -3:
            delta = 1
        elif delta in [2, -2]:
            if self.x_intercept(vertex, next_vertex, p_tuple[1]) > p_tuple[0]:  # Use tuple indexing
                delta = -delta
        return delta

    def is_point_near_edge(self, p, q, point, tolerance):
        """
        Check if a point is near the line segment [p, q] within a given tolerance.
        
        Parameters:
        - p: Start point of the line segment (tuple of x, y).
        - q: End point of the line segment (tuple of x, y).
        - point: The point to check (tuple of x, y).
        - tolerance: The maximum distance from the edge for the point to be considered near.
        
        Returns:
        - True if the point is near the line segment, False otherwise.
        """
        px, py, pz = p
        qx, qy, qz = q
        x, y, _ = point

        # Calculate the length squared of the line segment [p, q]
        line_len_squared = (qx - px) ** 2 + (qy - py) ** 2
        
        # Avoid division by zero if p and q are the same point
        if line_len_squared == 0:
            #print("LINE_LEN_SQUARED IS 0")
            distance = ((px - x) ** 2 + (py - y) ** 2) ** 0.5
            return distance <= tolerance

        # Calculate the projection of the point onto the line defined by [p, q]
        # and clamp it to the line segment
        t = max(0, min(1, ((x - px) * (qx - px) + (y - py) * (qy - py)) / line_len_squared))
        proj_x = px + t * (qx - px)
        proj_y = py + t * (qy - py)

        # Calculate the distance from the point to the projection on the line segment
        distance = ((proj_x - x) ** 2 + (proj_y - y) ** 2) ** 0.5
        #print("LINE_LEN_SQUARED IS NOT 0")
        # Check if the distance is within tolerance
        return distance <= tolerance

    def polygon_contains(self, polygon, point, TOLERANCE=1e-6):
        """
        Determine whether given 2D point lies within the polygon or on its edge within a specified tolerance.
        
        Parameters:
        - polygon: A list of tuples representing the vertices of the polygon [(x1, y1), (x2, y2), ...].
        - point: The point to check (x, y).
        - TOLERANCE: The maximum distance from the edge for the point to be considered near.
        
        Returns:
        - True if the point is near the edge or inside the polygon, False otherwise.
        """
        # Initialize variables
        is_near_edge = False
        angle = 0
        n = len(polygon)
        quad = self.get_quadrant(polygon[0], point)

        for i in range(n):
            vertex = polygon[i]
            next_vertex = polygon[(i + 1) % n]

            # Check if point is near the current edge; if so, consider it as being on the boundary
            if self.is_point_near_edge(vertex, next_vertex, point, TOLERANCE):
                print("Point is near an edge.")
                is_near_edge = True
                # If considering on/near an edge as inside, no need to continue further checks
                return True

            next_quad = self.get_quadrant(next_vertex, point)
            delta = next_quad - quad
            delta = self.adjust_delta(delta, vertex, next_vertex, point)
            angle += delta
            quad = next_quad

        # If the point was not near any edge, continue with the usual inside/outside determination
        # The point is inside if the winding number (angle) is 4 or -4
        return angle == 4 or angle == -4







def list_areas_by_apartment_number_with_level_and_format_check(doc, selected_name):
    print("INITIALIZE MAIN FUNCTION")
    # Collect all plumbing fixtures and match by the selected name
    fixture_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType()
    fixtures = [f for f in fixture_collector if f.Name == selected_name]
    print("COLLECTED FIXTURES:", len(fixtures))

    apartment_areas = {}

    for fixture in fixtures:
        fixture_level_id = fixture.LevelId
        fixture_location = fixture.Location.Point if fixture.Location else None
        print("LOCATION FOR FIXTURE {} IS {}".format(fixture, fixture_location))

        if fixture_location:
            area_collector = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Areas).WhereElementIsNotElementType()
            areas_on_same_level = [
                a for a in area_collector
                if a.LevelId == fixture_level_id and 
                   re.match(r'W\d{1}-\d{2}-\d{2}', a.LookupParameter('Number').AsString() if a.LookupParameter('Number') else '')
            ]

            for area in areas_on_same_level:
                apartment_number = area.LookupParameter('Number').AsString() if area.LookupParameter('Number') else None
                print(apartment_number)
                curves_loop = get_curve_loop_from_area_boundaries(doc, area)
                print("NUMBER OF CURVES IN 'curves_loop' FOR AREA {} IS: {}".format(area.Id, sum(1 for _ in curves_loop)))
                area_plane = get_area_plane(doc, area)  # Assuming this function returns a Plane object
                pj_pnt = project_point_to_plane(fixture_location, area_plane)  # Ensure this returns an XYZ or similar 2D point
                
                if curves_loop and pj_pnt:
                    vertices = convert_curves_to_vertices(curves_loop)
                    if vertices:
                        print("NUMBER OF VERTICES OFR LOOP {}: {}".format(curves_loop,len(vertices)))
                        # Convert vertices to a format compatible with PointInPoly (assuming UV or similar)
                        # Adjusted line to handle tuples
                        vertices_uv = [(x, y, z) for x, y, z in vertices]
                        #vertices_vals = [(x, y, z) for x, y, z in vertices]
                        print("VERTICES UV:",vertices_uv)
                        pj_point_uv = (pj_pnt.X, pj_pnt.Y, pj_pnt.Z)  # Assuming pj_pnt is already a 2D point or has .X, .Y attributes
                        point_uv = (fixture_location.X,fixture_location.Y,fixture_location.Z)
                        print("PROJECTED POINT:",pj_point_uv)
                        print("LOCATION POINT:", point_uv)
                        pip = PointInPoly()
                        inside = pip.polygon_contains(vertices_uv, point_uv)
                        if apartment_number:
                            if inside:
                                print("@@@ IS INSIDE : {} @@@", format(inside))
                                print("CHECKING DONE FOR APARTMENT NUMBER {} AND AREA {}".format(apartment_number, area.Id))
                                if apartment_number not in apartment_areas:
                                    apartment_areas[apartment_number] = []
                                if area.Id not in [a.Id for a in apartment_areas[apartment_number]]:
                                    apartment_areas[apartment_number].append(area.Id)
                            else:
                                print("POINT NOT INSIDE OF AREA:", area.Id)
    sorted_apartment_areas = dict(sorted(apartment_areas.items(), key=lambda x: x[0]))
    return sorted_apartment_areas


selected_names = collect_and_select_plumbing_fixtures_multiple(doc)
#selected_name = collect_and_select_plumbing_fixtures(doc)

for selected_name in selected_names:
    print("SELECTED FAMILY:",selected_name)
    groups = list_fixture_groups(doc, selected_name)
    print(groups)


    ### CHECK AGAINST GROUPS ONLY ###
    selected_groups = [doc.GetElement(f.GroupId).Id.IntegerValue for f in FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_PlumbingFixtures).WhereElementIsNotElementType() if f.Name == selected_name and f.GroupId.IntegerValue != -1]
    apartment_areas = list_areas_by_apartment_number(doc, selected_name, selected_groups)
    print("Number of areas collected: ", len(apartment_areas))

    ### CHECK AGAINST ACTUAL (ALL!) AREAS ### might be a lot of areas to check for
    # Get areas by apartment number that are in the same group(s) as the selected fixture
    #apartment_areas = list_areas_by_apartment_number_with_level_and_format_check(doc, selected_name)
    #print("Number of areas collected: ", len(apartment_areas))





    # Sort the apartment_areas dictionary by the first two characters of the apartment number
    sorted_apartment_numbers = sorted(apartment_areas.items(), key=lambda x: x[0][:8])
    # For displaying the result, adjust according to your needs. Example:
    #for apartment_number, groups in apartment_areas.items():
    for apartment_number, groups in sorted_apartment_numbers:
        print("Sorted Apartment NUmbers:", len(sorted_apartment_numbers))
        print("Apartment Number:", apartment_number,"Groups:",groups)

    # Optional: Display results to the user
    #TaskDialog.Show("Selected Fixture Groups", "Fixture:", selected_name, "nGroups:", groups)

    # Commit transaction (if started)
    # t.Commit()