# data_service.py
__all__ = ["DataService"]

import requests
import re
import logging
import json
import carb
from requests import Response

import omni
import omni.usd

from pxr import UsdGeom
from pxr import Usd, UsdGeom, Gf, Sdf, Kind
from typing import Optional, Tuple, Dict, Any

from datetime import datetime, timedelta
import time
stage = omni.usd.get_context().get_stage()

# from paho.mqtt import client as mqtt_client
# from .custom_events import CustomEvents
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)
class DataService:
    def __init__(self):
        self.base_url = "https://digital-twin.expangea.com/"
        self.headers = {
            'X-API-KEY': '2c38e689-8bac-4ec6-9e0e-70e98222dc2d'
        }
        self.stage = stage

        self.session = requests.Session()
        self.result_dict = {}

    def create_rack_column(self, x_start, y_start, col_number, level="3", rack_number="38", rack_depth="2",
                           cube_size=100):
        """
        Creates a rack column with cubes at specified levels and positions.

        :param x_start: Starting x-coordinate for the column.
        :param y_start: Starting y-coordinate for the column.
        :param col_number: The column number (for rack identification).
        :param level: The level of the rack (default is "3").
        :param rack_number: The rack number (default is "38").
        :param rack_depth: The rack depth (default is "2").
        :param cube_size: The size of the cubes (default is 100).
        """
        z_levels = [0, 220] + [220 + 175 * i for i in range(1, 5)]  # Z increments for 6 levels

        for rack_level, z in enumerate(z_levels, 1):
            xform_name = f"{level}{rack_number}{rack_level}{col_number:02d}{rack_depth}"
            xform_prim_path = f"/rack_location/_{xform_name}"

            # Check if the prim already exists
            if not self.stage.GetPrimAtPath(xform_prim_path).IsValid():
                # Define a new Xform at the given path
                xform = UsdGeom.Xform.Define(self.stage, xform_prim_path)
                xform.AddTranslateOp().Set(Gf.Vec3d(x_start, y_start, z))
                carb.log_warn(f"Created: {xform_prim_path} at ({x_start}, {y_start}, {z})")

                # Spawn a cube at this location
                self.spawn_cube_at_xform(xform_prim_path, cube_size)
            else:
                carb.log_info(f"Xform already exists at {xform_prim_path}")

    def spawn_cube_at_xform(self, xform_prim_path, cube_size):
        """
        Spawns a cube as a child of the given Xform.

        :param xform_prim_path: The Xform path where the cube will be spawned.
        :param cube_size: The size of the cube to be spawned.
        """
        xform_prim = self.stage.GetPrimAtPath(xform_prim_path)
        if not xform_prim.IsValid():
            carb.log_error(f"Xform not found at {xform_prim_path}")
            return

        # Create a new cube as a child of the Xform
        cube_prim_path = f"{xform_prim_path}/Cube"
        if not self.stage.GetPrimAtPath(cube_prim_path).IsValid():
            cube = UsdGeom.Cube.Define(self.stage, cube_prim_path)
            cube.GetSizeAttr().Set(cube_size)  # Set cube size
            cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, cube_size / 2))  # Move cube up by half its size
            carb.log_warn(f"Created Cube at {cube_prim_path}")
        else:
            carb.log_info(f"Cube already exists at {cube_prim_path}")

    def create_multiple_columns(self, x_start_1, y_start_1, number_of_columns=48, distance_between_columns=-140):
        """
        Create multiple rack columns and spawn cubes in each.

        :param x_start_1: Starting x-coordinate for the first column.
        :param y_start_1: Starting y-coordinate for the first column.
        :param number_of_columns: Total number of columns to create.
        :param distance_between_columns: Distance between each column.
        """
        for col in range(number_of_columns):
            x_start = x_start_1 + col * distance_between_columns
            y_start = y_start_1
            self.create_rack_column(x_start, y_start, col + 1)
    @staticmethod
    def manage_extension():
        try:
            # Get the extension manager from the application
            extension_manager = omni.kit.app.get_app().get_extension_manager()

            # Enable the extension immediately
            extension_manager.set_extension_enabled_immediate("omni.example.ui_scene.widget_info", False)

            # Get the path of the extension by its module name
            widget_extension_path = extension_manager.get_extension_path_by_module("omni.example.ui_scene.widget_info")

            if widget_extension_path:
                carb.log_info(f"Extension path for 'omni.example.ui_scene.widget_info': {widget_extension_path}")
            else:
                carb.log_error(f"Could not retrieve path for 'omni.example.ui_scene.widget_info'")

            # Optionally check if the extension is enabled
            is_enabled = extension_manager.is_extension_enabled("omni.example.ui_scene.widget_info")
            if is_enabled:
                carb.log.warn("'omni.example.ui_scene.widget_info' is Enabled")
            else:
                carb.log_error("'omni.example.ui_scene.widget_info' is Disabled")

        except Exception as e:
            carb.log_error(f"An error occurred while managing the extension: {str(e)}")

    def construct_api_url(self, endpoint: str) -> str:
        return f"{self.base_url}{endpoint}"

    def handle_api_request(self, api_url: str) -> Response | dict[Any, Any]:
        try:
            response = requests.post(api_url, headers=self.headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response
        except requests.RequestException as e:
            carb.log_error(f"API request error: {e}")
            return {}

    def fetch_stock_info(self, endpoint: str) -> dict:
        api_url = self.construct_api_url(endpoint)
        response = self.handle_api_request(api_url)
        return response.json().get("data", {})
        # api_url = self.construct_api_url(endpoint)
        # stock_info = self.handle_api_request(api_url)
        # CustomEvents.emit_stock_info(stock_info)  # Emit the custom event with stock info
        # return stock_info

    def fetch_coordinates(self, endpoint: str) -> tuple:
        api_url = self.construct_api_url(endpoint)
        response = self.handle_api_request(api_url)
        data = response.json().get("data", {})
        coordinates = data.get("rack_location", {}).get("coordinates", {})
        # print(coordinates)
        return coordinates.get('x'), coordinates.get('y'), coordinates.get('z')

    def check_expiring_goods(self, alert_days=7):
        stage = omni.usd.get_context().get_stage()

        # Set to keep track of processed location IDs
        processed_locations = set()
        endpoint = "expiry/5BTG/"
        api_url = self.construct_api_url(endpoint)
        data = self.handle_api_request(api_url)

        # Check if the request was successful
        if data.status_code == 200:
            data = data.json()
            expired_items = data.get('expired', [])

            for item in expired_items:
                pallet_id = item.get('pallet_id')
                if pallet_id and isinstance(pallet_id, str):
                    pallet_id = re.sub(r'^\d+', '', pallet_id)

                location_id = item.get('location_id')
                rack_no = item.get('rack_no')
                floor_no = item.get('floor_no')
                xform_prim_path = f"/expired/{pallet_id}"
                balance_shelf_life_days = item['inventory'].get('Balance Shelf Life to Expiry (days)')

                # Extracting the coordinates from the data, using default values if None
                coordinates = item.get('coordinates', {})
                x = coordinates.get('x', 0.0) if coordinates is not None else 0.0
                y = coordinates.get('y', 0.0) if coordinates is not None else 0.0
                z = coordinates.get('z', 0.0) if coordinates is not None else 0.0

                # Check if location_id has already been processed
                if location_id not in processed_locations:
                    # Add the location_id to the set
                    processed_locations.add(location_id)
                    self.result_dict[location_id] = {
                        'pallet_id': pallet_id,
                        'rack_no': rack_no,
                        'floor_no': floor_no,
                        'balance_shelf_life_days': balance_shelf_life_days,
                        'coordinates': {'x': x, 'y': y, 'z': z}
                    }

                    # Log the information, including coordinates
                    carb.log_warn(f"Pallet ID: {pallet_id}, Location ID: {location_id}, Rack No: {rack_no}, "
                                  f"Balance Shelf Life (days): {balance_shelf_life_days}, Floor No: {floor_no}, Coordinates: ({x}, {y}, {z})")


                    # Spawn an Xform and then the cube at the given coordinates
                    if not stage.GetPrimAtPath(xform_prim_path).IsValid():
                        # Create an Xform for the pallet at the location
                        xform = UsdGeom.Xform.Define(stage, xform_prim_path)
                        xform.AddTranslateOp().Set(Gf.Vec3f(x, y, z))

                        # Spawn a cube as a child of the Xform
                        cube_prim_path = f"{xform_prim_path}/Cube"
                        cube_prim = UsdGeom.Cube.Define(stage, cube_prim_path)
                        cube_prim.GetSizeAttr().Set(120.0)  # Set the cube size
                        cube_prim.AddTranslateOp().Set(
                            Gf.Vec3f(0, 0, 60))  # Adjust Z to position the cube above the ground
                        Usd.ModelAPI(xform).SetKind(Kind.Tokens.assembly)
                        carb.log_warn(f"Spawned cube for Pallet {pallet_id} at coordinates ({x}, {y}, {z})")
                    else:
                        carb.log_warn(f"Xform already exists for {xform_prim_path}")
                else:
                    carb.log_warn(f"Duplicate location_id {location_id} detected, skipping...")
        else:
            carb.log_error(f"Failed to retrieve data: {data.status_code} - {data.text}")

        # Notification showing the expired item list
        pallet_ids = [item['pallet_id'] for item in self.result_dict.values()]
        pallet_id_string = "\n".join(pallet_ids)
        show_notification(title="Expired item list", message=pallet_id_string)

    def close(self):
        self.session.close()
        carb.log_info("API connection closed")


def move_camera(self, x: float, y: float, z: float):
    xform_path = "/Camera"
    view_camera_path = "/Camera/Camera_001"
    new_xyz_location = Gf.Vec3d(x + 220, y + 50, z + 70)
    new_rotation = Gf.Vec3f(75, 0.0, 0.0)
    focal_length = 20

    move_xform_and_set_view(xform_path, view_camera_path, new_xyz_location, new_rotation, focal_length=focal_length)
    print(f"Moved camera to location: {new_xyz_location}, with rotation: {new_rotation}, focal length: {focal_length}")


def move_xform_and_set_view(xform_path: str, view_camera_path: str, new_location: Optional[Gf.Vec3f] = None,
                            new_rotation: Optional[Gf.Vec3f] = None, focal_length: float = 20.0):
    xform_api = get_xform_by_path(xform_path)
    if not xform_api:
        print(f"Camera xform at '{xform_path}' not found or invalid!")
        return

    if new_location is not None:
        xform_api.SetTranslate(new_location)
    if new_rotation is not None:
        xform_api.SetRotate(new_rotation)
    stage = omni.usd.get_context().get_stage()
    view_camera_prim = stage.GetPrimAtPath(view_camera_path)
    if not view_camera_prim:
        print(f"View camera at '{view_camera_path}' not found!")
        return

    if not view_camera_prim.IsA(UsdGeom.Camera):
        print(f"Prim at '{view_camera_path}' is not a camera!")
        return

    view_camera = UsdGeom.Camera(view_camera_prim)
    view_camera.GetFocalLengthAttr().Set(focal_length)

    viewport_api = omni.kit.viewport.utility.get_active_viewport()
    viewport_api.camera_path = view_camera_prim.GetPath().pathString
    print(
        f"Moved xform of '{xform_api.GetPrim().GetName()}' and viewport is now viewing from '{view_camera_prim.GetName()}' with focal length {focal_length}")


def get_xform_by_path(prim_path: str) -> Optional[UsdGeom.XformCommonAPI]:
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(prim_path)
    if prim.IsValid() and prim.IsA(UsdGeom.Xform):
        return UsdGeom.XformCommonAPI(prim)
    return None


def traverse(prim, name):
    if prim.GetName() == name:
        return prim
    for child in prim.GetAllChildren():
        result = traverse(child, name)
        if result:
            return result
    return None


def find_prim_by_name(stage, name):
    root_prim = stage.GetPseudoRoot()
    return traverse(root_prim, name)


def find_prim_then_select(name: str):
    # Get the stage from the Omniverse context
    stage = omni.usd.get_context().get_stage()

    # Find the prim by name
    prim = find_prim_by_name(stage, name)
    if not prim:
        carb.log_error(f"Prim with name '{name}' not found!")
        return

    # Get the selection context
    selection = omni.usd.get_context().get_selection()

    # Select the item
    selection.clear_selected_prim_paths()
    selection.set_selected_prim_paths([prim.GetPath().pathString], True)

    carb.log_info(f"Selected item with name '{name}' at path: '{prim.GetPath()}'")


def load_usd_file(file_path):
    context = omni.usd.get_context()
    if not context:
        print("Failed to get USD context.")
        return

    stage = context.get_stage()
    if not stage:
        carb.log_error("Failed to get the USD stage. Ensure a stage is open or created.")
        return

    try:
        # Set the stage up axis and orientation
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(stage, 1.0)  # Optional: set scale to meters

        ref_prim_path = '/root'
        # Ensure the root is an Xform
        stage.DefinePrim(ref_prim_path, 'Xform')
        ref_prim = stage.GetPrimAtPath(ref_prim_path)
        if not ref_prim.IsValid():
            carb.log_error(f"Failed to define or get the reference prim at {ref_prim_path}.")
            return

        ref_prim.GetReferences().AddReference(file_path)
        carb.log_info(f"Successfully referenced USD file at {file_path}")

        # Additional handling might be needed to ensure X is front orientation
        """
            Adjusts the orientation of the root prim to ensure Z is up and X is front in the scene.
            """
        xform = UsdGeom.Xformable(ref_prim)

        # Apply rotation to align orientations properly if needed.
        # Assuming that Z-up and X-front might require rotations.
        # For some scenes, importing USD with correct orientation might be enough.
        rotation = (0, 0, 0)  # This depends on how the USD is set up. Adjust as needed.
        xform.AddRotateXYZOp().Set(rotation)
    except Exception as e:
        carb.log_error(f"An error occurred while referencing the USD file: {str(e)}")


def _fetch_and_move_camera(self):
    """Fetch stock info from endpoint and move the camera"""
    pallet_id = self._pallet_info_widget.get_input_value()
    endpoint = f"pallet/{pallet_id}/"
    print(f"Fetching stock info from endpoint: {endpoint}")

    find_prim_then_select(pallet_id)

    stock_info = self._data_service.fetch_stock_info(endpoint)
    if stock_info:
        limited_items = list(stock_info.items())[:11]
        info_text = "\n".join([f"{key}: {value}" for key, value in limited_items])
        print(info_text)

        if "rack_location" in stock_info and stock_info["rack_location"]:
            location_id = stock_info["rack_location"].get("location_id")
            location_endpoint = f"rack-location/{location_id}/"
            print(f"Fetching coordinates from endpoint: {location_endpoint}")

            x, y, z = self._data_service.fetch_coordinates(location_endpoint)
            print(x, y, z)
            if x is not None and y is not None and z is not None:
                move_camera(x, y, z)
            else:
                print("Failed to fetch coordinates")
        else:
            print("Failed to fetch stock info")


def show_notification(title: str, message: str):
    status = omni.kit.notification_manager.NotificationStatus.INFO
    ok_button = omni.kit.notification_manager.NotificationButtonInfo("OK", on_complete=None)
    omni.kit.notification_manager.post_notification(text=message,
                                                    hide_after_timeout=False,
                                                    duration=0,
                                                    status=status,
                                                    button_infos=[ok_button])


