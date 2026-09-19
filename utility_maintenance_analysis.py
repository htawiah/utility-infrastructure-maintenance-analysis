"""
Utility Infrastructure Maintenance Priority Analysis
Naperville, Illinois

Purpose:
Perform QA/QC and maintenance-priority analysis on water mains,
hydrants, and system valves using ArcPy.

Data source:
Esri water distribution network demonstration data representing
Naperville, Illinois.

Note:
Priority classifications are analytical outputs created for this
portfolio project and do not represent official municipal
maintenance decisions.
"""

import arcpy
from datetime import datetime

# -------------------------------------------------------------------
# WORKSPACE
# -------------------------------------------------------------------

gdb = r"PATH_TO_YOUR\Utility_Infrastructure_Analysis.gdb"
arcpy.env.workspace = gdb
arcpy.env.overwriteOutput = True

water_mains = "Water_Mains"
hydrants = "Hydrants"
system_valves = "System_Valves"

CURRENT_YEAR = datetime.now().year


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------

def add_field_if_missing(dataset, field_name, field_type, length=None):
    """Add a field only when it does not already exist."""

    existing_fields = [field.name for field in arcpy.ListFields(dataset)]

    if field_name not in existing_fields:
        if length:
            arcpy.management.AddField(
                dataset,
                field_name,
                field_type,
                field_length=length
            )
        else:
            arcpy.management.AddField(
                dataset,
                field_name,
                field_type
            )


def calculate_asset_age(dataset):
    """
    Calculate asset age from INSTALLDATE.

    Missing dates and placeholder year 1900 are left unclassified
    so they can be flagged for review.
    """

    add_field_if_missing(dataset, "Asset_Age", "LONG")

    with arcpy.da.UpdateCursor(
        dataset,
        ["INSTALLDATE", "Asset_Age"]
    ) as cursor:

        for install_date, asset_age in cursor:

            if install_date and install_date.year != 1900:
                asset_age = CURRENT_YEAR - install_date.year
            else:
                asset_age = None

            cursor.updateRow((install_date, asset_age))


def classify_age(dataset):
    """Group assets into age-based review classes."""

    add_field_if_missing(dataset, "Age_Class", "TEXT", 30)

    with arcpy.da.UpdateCursor(
        dataset,
        ["Asset_Age", "Age_Class"]
    ) as cursor:

        for age, age_class in cursor:

            if age is None:
                age_class = "Review Required"
            elif age >= 50:
                age_class = "50+ Years"
            elif age >= 30:
                age_class = "30-49 Years"
            else:
                age_class = "Under 30 Years"

            cursor.updateRow((age, age_class))


# -------------------------------------------------------------------
# ASSET AGE ANALYSIS
# -------------------------------------------------------------------

for dataset in [water_mains, hydrants, system_valves]:
    calculate_asset_age(dataset)
    classify_age(dataset)


# -------------------------------------------------------------------
# WATER MAIN PRIORITY
# -------------------------------------------------------------------

add_field_if_missing(water_mains, "Priority", "TEXT", 30)

with arcpy.da.UpdateCursor(
    water_mains,
    ["Asset_Age", "Priority"]
) as cursor:

    for age, priority in cursor:

        if age is None:
            priority = "Review Required"
        elif age >= 50:
            priority = "High"
        elif age >= 30:
            priority = "Medium"
        else:
            priority = "Low"

        cursor.updateRow((age, priority))


# -------------------------------------------------------------------
# HYDRANT REVIEW PRIORITY
# -------------------------------------------------------------------

add_field_if_missing(hydrants, "Review_Priority", "TEXT", 30)

with arcpy.da.UpdateCursor(
    hydrants,
    ["OPERABLE", "Asset_Age", "Review_Priority"]
) as cursor:

    for operable, age, priority in cursor:

        if operable == 0:
            priority = "High"
        elif age is None:
            priority = "Review Required"
        elif age >= 50:
            priority = "Medium"
        else:
            priority = "Low"

        cursor.updateRow((operable, age, priority))


# -------------------------------------------------------------------
# SYSTEM VALVE REVIEW PRIORITY
# -------------------------------------------------------------------

add_field_if_missing(system_valves, "Review_Priority", "TEXT", 30)

with arcpy.da.UpdateCursor(
    system_valves,
    ["OPERABLE", "Asset_Age", "Review_Priority"]
) as cursor:

    for operable, age, priority in cursor:

        if operable == 0:
            priority = "High"
        elif age is None:
            priority = "Review Required"
        elif age >= 50:
            priority = "Medium"
        else:
            priority = "Low"

        cursor.updateRow((operable, age, priority))


# -------------------------------------------------------------------
# SPATIAL PROXIMITY ANALYSIS
# -------------------------------------------------------------------

main_layer = "high_priority_mains"
valve_layer = "system_valves_layer"

arcpy.management.MakeFeatureLayer(
    water_mains,
    main_layer,
    "Priority = 'High'"
)

arcpy.management.MakeFeatureLayer(
    system_valves,
    valve_layer,
    "Review_Priority = 'High'"
)

# Identify high-priority valves within 100 feet of
# high-priority water mains.
arcpy.management.SelectLayerByLocation(
    valve_layer,
    "WITHIN_A_DISTANCE",
    main_layer,
    "100 Feet"
)

output_valves = "Priority_Valve_Maintenance"

arcpy.management.CopyFeatures(
    valve_layer,
    output_valves
)

selected_count = int(
    arcpy.management.GetCount(output_valves)[0]
)

print(
    f"Priority valve maintenance dataset created: "
    f"{selected_count} features exported."
)
