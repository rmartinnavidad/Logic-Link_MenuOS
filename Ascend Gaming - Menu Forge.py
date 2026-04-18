bl_info = {
    "name": "Ascend Gaming | Menu Forge",
    "author": "Royal Navidad + Codex",
    "version": (0, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Sidebar > Menu Forge",
    "description": "Create reusable video game menu layouts for Blender previews and UPBGE-ready workflows",
    "category": "Game Engine",
}

import json
import math
import os
import random

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Operator, Panel, PropertyGroup, UIList

try:
    import aud
except Exception:
    aud = None








try:
    import bpy.utils.previews
    _CUSTOM_ICONS = None
except Exception:
    _CUSTOM_ICONS = None

def get_track_icon_id(filepath):
    global _CUSTOM_ICONS
    if _CUSTOM_ICONS is None or not filepath:
        return 0


_AUDIO_DEVICE = None
_AUDIO_HANDLE = None
_AUDIO_TRACK_INDEX = -1
_LIVE_REBUILD_PENDING = False
_WIDGET_ANIM_STATE = "HIDDEN"  # HIDDEN, IN, IDLE, OUT
_WIDGET_ANIM_TIMER = 0.0
_WIDGET_CURRENT_OFFSET = 0.0
_WIDGET_CONTAINER_NAME = ""
_WIDGET_SLIDE_DIR = "UP"
_WIDGET_SLIDE_DIST = 1.0
_LIVE_PANEL_APPLYING = False


MENU_ITEM_TYPES = [
    ("BUTTON", "Button", "Interactive action button"),
    ("LABEL", "Label", "Static text label"),
    ("IMAGE", "Image", "Image or icon placeholder"),
    ("CONTAINER", "Container", "Grouping block"),
    ("LOGO", "Logo", "Game, company, or account logo"),
    ("ACCOUNT", "Account", "User account display block"),
    ("SOUNDTRACK_NOW", "Now Playing", "Soundtrack information display"),
]

LAYOUT_TYPES = [
    ("FREEFORM", "Photoshop Canvas", "Manually position and size every element"),
    ("VERTICAL", "Vertical Stack", "Stack menu items vertically"),
    ("HORIZONTAL", "Horizontal Row", "Place menu items left to right"),
    ("GRID", "Grid", "Place menu items in a grid"),
    ("RADIAL", "Radial", "Place menu items in a radial layout"),
]

THEME_TYPES = [
    ("LOW_BUDGET", "Low Budget", "Fast, readable default look"),
    ("STYLIZED_INDIE", "Stylized Indie", "Bolder scale and color changes"),
    ("AA", "AA", "Balanced polish and movement"),
    ("AAAA", "AAAA Cinematic", "High contrast, larger motion, dramatic presentation"),
]

STATE_TYPES = [
    ("IDLE", "Idle", "Neutral state"),
    ("FOCUSED", "Focused", "Selected or highlighted"),
    ("PRESSED", "Pressed", "Pressed or confirmed"),
    ("DISABLED", "Disabled", "Disabled or unavailable"),
    ("HIDDEN", "Hidden", "Temporarily hidden"),
]

ACTION_TYPES = [
    ("NONE", "None", "No action assigned"),
    ("START_GAME", "Start Game", "Begin the game"),
    ("OPEN_SUBMENU", "Open Submenu", "Open another menu"),
    ("BACK", "Back", "Return to the previous menu"),
    ("OPTIONS", "Options", "Open options"),
    ("QUIT", "Quit", "Exit the game"),
    ("CUSTOM", "Custom", "User-defined action hook"),
]

BACKGROUND_TYPES = [
    ("COLOR", "Color", "Solid color background"),
    ("COLOR_RAMP", "Color Ramp", "Two-color generated ramp placeholder"),
    ("IMAGE", "Image", "Still image background"),
    ("VIDEO", "Video", "Video file background for runtime/export"),
    ("SEQUENCE", "Image Sequence", "Image sequence folder for runtime/export"),
    ("SCENE", "Scene Window", "Backdrop is a window into a Blender or UPBGE scene"),
    ("HYBRID", "Hybrid", "Layer media and a live scene together"),
]

BACKGROUND_LAYER_TYPES = [
    ("IMAGE", "Image", "Still image layer"),
    ("VIDEO", "Video", "Video texture layer"),
]

BACKGROUND_LAYER_USE_TYPES = [
    ("BACKGROUND", "Background", "Use this plane as a normal menu background"),
    ("SCENE_WINDOW", "Scene Window", "Use this plane as a window/mask placeholder for a live scene"),
    ("OVERLAY", "Overlay", "Use this plane as an overlay above the live scene"),
]

BACKGROUND_DURATION_TYPES = [
    ("AUTO", "Auto", "Use movie length when Blender can read it"),
    ("CUSTOM", "Custom", "Use the custom duration slider"),
]

BACKGROUND_FIT_TYPES = [
    ("STRETCH", "Stretch", "Stretch media to the plane"),
    ("FIT", "Fit", "Fit entire media inside the plane"),
    ("FILL", "Fill", "Fill the plane, cropping if needed"),
    ("TILE", "Tile", "Tile/repeat the media"),
]

SCREEN_TYPES = [
    ("INTRO_LOGO", "Intro Logo", "Company or technology logo screen"),
    ("INTRO_VIDEO", "Intro Video", "Intro video or cinematic screen"),
    ("PRESS_START", "Press Start", "Press start / any button gate"),
    ("MAIN_MENU", "Main Menu", "Primary menu screen"),
    ("SUBMENU", "Submenu", "Secondary menu page"),
    ("SOUNDTRACK", "Soundtrack", "Soundtrack management page"),
]

PLAYBACK_ORDER_TYPES = [
    ("SEQUENTIAL", "Sequential", "Play in list order"),
    ("SHUFFLE", "Shuffle", "Randomized playback order"),
    ("RANDOM", "Random Pick", "Pick randomly each time"),
]

FILL_TYPES = [
    ("COLOR", "Color", "Use a solid color"),
    ("COLOR_RAMP", "Color Ramp", "Use an editable shader color ramp"),
    ("IMAGE", "Image", "Use an image texture"),
    ("VIDEO", "Video", "Use runtime video media"),
    ("SEQUENCE", "Sequence", "Use runtime image sequence media"),
    ("NONE", "None", "Transparent or text-only element"),
]

TEXT_ALIGN_X_TYPES = [
    ("LEFT", "Left", "Align text to the left side of the element"),
    ("CENTER", "Center", "Center text inside the element"),
    ("RIGHT", "Right", "Align text to the right side of the element"),
]

LAYOUT_ALIGN_X_TYPES = [
    ("LEFT", "Left", "Anchor the option block to the left side of the backdrop"),
    ("CENTER", "Center", "Center the option block inside the backdrop"),
    ("RIGHT", "Right", "Anchor the option block to the right side of the backdrop"),
    ("CUSTOM", "Custom X", "Use the custom Align X value"),
]

TEXT_ALIGN_Y_TYPES = [
    ("TOP", "Top", "Align text toward the top"),
    ("CENTER", "Center", "Center text vertically"),
    ("BOTTOM", "Bottom", "Align text toward the bottom"),
]

RAMP_DIRECTION_TYPES = [
    ("HORIZONTAL", "Horizontal", "Ramp left to right"),
    ("VERTICAL", "Vertical", "Ramp bottom to top"),
    ("DIAGONAL", "Diagonal", "Ramp diagonally"),
    ("RADIAL", "Radial", "Radial ramp"),
]

ANIMATION_TYPES = [
    ("NONE", "None", "No animation"),
    ("SCALE_PULSE", "Scale Pulse", "Pulse scale while focused"),
    ("SLIDE_IN", "Slide In", "Slide from an offset"),
    ("GLOW", "Glow", "Increase brightness/emission"),
    ("SHAKE", "Shake", "Small impact shake"),
    ("CUSTOM", "Custom", "Runtime custom animation hook"),
]


def menu_collection_name(root_name):
    return f"{root_name}_COL"


def item_object_name(root_name, item_name):
    return f"{root_name}_{item_name}_Text"


def item_description_object_name(root_name, item_name):
    return f"{root_name}_{item_name}_Description"


def item_container_object_name(root_name, item_name):
    return f"{root_name}_{item_name}_Container"


def item_rect_object_name(root_name, item_name):
    return f"{root_name}_{item_name}_Rect"


def item_border_object_name(root_name, item_name):
    return f"{root_name}_{item_name}_Border"


def backdrop_object_name(root_name):
    return f"{root_name}_Backdrop"


def canvas_center_object_name(root_name):
    return f"{root_name}_CanvasCenter"


def background_layer_object_name(root_name, layer_name, index):
    safe_name = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in layer_name) or "Layer"
    return f"{root_name}_BG_{index:02d}_{safe_name}"


def item_collection_name(root_name, item_name):
    safe_name = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in item_name) or "Item"
    return f"{root_name}_{safe_name}_COL"


def camera_object_name(root_name):
    return f"{root_name}_Camera"


def ensure_collection(scene, name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
    return collection


def ensure_child_collection(parent_collection, name):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if all(child.name != collection.name for child in parent_collection.children):
        try:
            parent_collection.children.link(collection)
        except RuntimeError:
            pass
    return collection


def live_update_callback(self, context):
    request_live_rebuild()


def panel_live_update_callback(self, context):
    global _LIVE_PANEL_APPLYING
    if _LIVE_PANEL_APPLYING:
        request_live_rebuild()
        return
    _LIVE_PANEL_APPLYING = True
    try:
        props = getattr(context.scene, "agmf_props", None) if context and context.scene else None
        if props and props.live_edit:
            apply_panel_settings_to_items(props, self)
    except Exception as exc:
        print(f"Menu Forge panel live update skipped: {exc}")
    finally:
        _LIVE_PANEL_APPLYING = False
    request_live_rebuild()


def find_scene_camera(scene):
    if scene is None:
        return None
    if scene.camera and scene.camera.type == "CAMERA":
        return scene.camera
    for obj in scene.objects:
        if obj.type == "CAMERA":
            return obj
    return None


def background_scene_update_callback(self, context):
    if self.background_scene:
        self.background_type = "SCENE"
        self.background_scene_camera = find_scene_camera(self.background_scene)
    request_live_rebuild()


def request_live_rebuild():
    global _LIVE_REBUILD_PENDING
    if _LIVE_REBUILD_PENDING:
        return
    _LIVE_REBUILD_PENDING = True

    def _do_rebuild():
        global _LIVE_REBUILD_PENDING
        _LIVE_REBUILD_PENDING = False
        try:
            scene = bpy.context.scene
            props = getattr(scene, "agmf_props", None)
            if props and props.live_edit:
                rebuild_menu_objects(bpy.context)
        except Exception as exc:
            print(f"Menu Forge live rebuild skipped: {exc}")
        return None

    try:
        bpy.app.timers.register(_do_rebuild, first_interval=0.05)
    except Exception:
        _LIVE_REBUILD_PENDING = False


def unlink_from_other_collections(obj, target_collection):
    for collection in list(obj.users_collection):
        if collection != target_collection:
            collection.objects.unlink(obj)


def parent_as_local(obj, parent_obj):
    obj.parent = parent_obj
    obj.matrix_parent_inverse.identity()


def get_or_create_material(name, color, roughness=0.65, metallic=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    mat.diffuse_color = color
    if mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if "Base Color" in bsdf.inputs:
                bsdf.inputs["Base Color"].default_value = color
            if "Alpha" in bsdf.inputs:
                bsdf.inputs["Alpha"].default_value = color[3]
            if "Roughness" in bsdf.inputs:
                bsdf.inputs["Roughness"].default_value = roughness
            if "Metallic" in bsdf.inputs:
                bsdf.inputs["Metallic"].default_value = metallic
    mat.blend_method = "BLEND" if color[3] < 1.0 else "OPAQUE"
    return mat


def assign_material(obj, mat):
    if not obj.data.materials:
        obj.data.materials.append(mat)
    else:
        obj.data.materials[0] = mat


def get_or_create_ramp_material(name, color_a, color_b, direction="HORIZONTAL", roughness=0.65, offset_x=0.0, offset_y=0.0):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = color_a
    mat.blend_method = "BLEND" if color_a[3] < 1.0 or color_b[3] < 1.0 else "OPAQUE"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    texcoord = nodes.get("MenuOS Texture Coordinates") or nodes.new(type="ShaderNodeTexCoord")
    texcoord.name = "MenuOS Texture Coordinates"
    mapping = nodes.get("MenuOS Vector Mapping") or nodes.new(type="ShaderNodeMapping")
    mapping.name = "MenuOS Vector Mapping"
    gradient = nodes.get("MenuOS Gradient") or nodes.new(type="ShaderNodeTexGradient")
    gradient.name = "MenuOS Gradient"
    ramp = nodes.get("MenuOS Color Ramp") or nodes.new(type="ShaderNodeValToRGB")
    ramp.name = "MenuOS Color Ramp"

    gradient.gradient_type = "RADIAL" if direction == "RADIAL" else "LINEAR"
    if "Rotation" in mapping.inputs:
        if direction == "VERTICAL":
            mapping.inputs["Rotation"].default_value[2] = math.radians(90.0)
        elif direction == "DIAGONAL":
            mapping.inputs["Rotation"].default_value[2] = math.radians(45.0)
        else:
            mapping.inputs["Rotation"].default_value[2] = 0.0

    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = color_a
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = color_b
    if "Location" in mapping.inputs:
        mapping.inputs["Location"].default_value[0] = offset_x
        mapping.inputs["Location"].default_value[1] = offset_y

    def link_once(output, input_socket):
        for link in links:
            if link.to_socket == input_socket:
                links.remove(link)
        links.new(output, input_socket)

    link_once(texcoord.outputs["Generated"] if "Generated" in texcoord.outputs else texcoord.outputs["Object"], mapping.inputs["Vector"])
    link_once(mapping.outputs["Vector"], gradient.inputs["Vector"])
    link_once(gradient.outputs["Fac"], ramp.inputs["Fac"])
    link_once(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = max(color_a[3], color_b[3])
    if "Roughness" in bsdf.inputs:
        bsdf.inputs["Roughness"].default_value = roughness
    return mat


def try_load_image_material(name, image_path, fallback_color):
    mat = get_or_create_material(name, fallback_color)
    abs_path = bpy.path.abspath(image_path) if image_path else ""
    if not abs_path or not os.path.exists(abs_path):
        return mat

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        return mat

    image_node = nodes.get("MenuOS Image Texture")
    if image_node is None:
        image_node = nodes.new(type="ShaderNodeTexImage")
        image_node.name = "MenuOS Image Texture"
    try:
        image_node.image = bpy.data.images.load(abs_path, check_existing=True)
        links.new(image_node.outputs["Color"], bsdf.inputs["Base Color"])
    except Exception:
        pass
    return mat


def try_load_media_material(name, media_path, fallback_color, frame_start=1):
    mat = get_or_create_material(name, fallback_color)
    abs_path = bpy.path.abspath(media_path) if media_path else ""
    if not abs_path or not os.path.exists(abs_path):
        return mat

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        return mat

    image_node = nodes.get("MenuOS Media Texture")
    if image_node is None:
        image_node = nodes.new(type="ShaderNodeTexImage")
        image_node.name = "MenuOS Media Texture"
    try:
        image = bpy.data.images.load(abs_path, check_existing=True)
        image_node.image = image
        image_node.extension = "CLIP"
        if hasattr(image_node, "image_user"):
            image_node.image_user.frame_start = frame_start
            image_node.image_user.use_auto_refresh = True
            if getattr(image, "source", "") == "MOVIE":
                image_node.image_user.frame_duration = max(1, getattr(image, "frame_duration", 250))
        if not any(link.to_node == bsdf and link.to_socket == bsdf.inputs["Base Color"] for link in links):
            links.new(image_node.outputs["Color"], bsdf.inputs["Base Color"])
    except Exception:
        pass
    return mat


def get_or_create_mapped_media_material(name, layer):
    mat = get_or_create_material(name, layer.tint_color)
    abs_path = bpy.path.abspath(layer.filepath) if layer.filepath else ""
    if not abs_path or not os.path.exists(abs_path):
        return mat

    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")

    texcoord = nodes.get("MenuOS Media Coordinates") or nodes.new(type="ShaderNodeTexCoord")
    texcoord.name = "MenuOS Media Coordinates"
    mapping = nodes.get("MenuOS Media Mapping") or nodes.new(type="ShaderNodeMapping")
    mapping.name = "MenuOS Media Mapping"
    image_node = nodes.get("MenuOS Media Image") or nodes.new(type="ShaderNodeTexImage")
    image_node.name = "MenuOS Media Image"

    try:
        image_node.image = bpy.data.images.load(abs_path, check_existing=True)
        image_node.extension = "REPEAT" if layer.fit_mode == "TILE" else "CLIP"
        if hasattr(image_node, "image_user"):
            image_node.image_user.frame_start = layer.frame_start
            image_node.image_user.use_auto_refresh = layer.layer_type == "VIDEO"
            if layer.layer_type == "VIDEO" and getattr(image_node.image, "frame_duration", 0):
                image_node.image_user.frame_duration = max(1, image_node.image.frame_duration)
                if layer.duration_mode == "AUTO":
                    fps = max(1.0, bpy.context.scene.render.fps / max(1.0, bpy.context.scene.render.fps_base))
                    layer.auto_duration = image_node.image.frame_duration / fps
    except Exception:
        return mat

    if "Location" in mapping.inputs:
        mapping.inputs["Location"].default_value[0] = layer.map_offset_x
        mapping.inputs["Location"].default_value[1] = layer.map_offset_y
        mapping.inputs["Location"].default_value[2] = layer.map_offset_z
    if "Scale" in mapping.inputs:
        zoom = max(0.001, layer.map_zoom)
        mapping.inputs["Scale"].default_value[0] = max(0.001, layer.map_scale_x * zoom)
        mapping.inputs["Scale"].default_value[1] = max(0.001, layer.map_scale_y * zoom)
        mapping.inputs["Scale"].default_value[2] = max(0.001, layer.map_scale_z)
    if "Rotation" in mapping.inputs:
        mapping.inputs["Rotation"].default_value[2] = layer.map_rotation

    def relink(output, input_socket):
        for link in list(links):
            if link.to_socket == input_socket:
                links.remove(link)
        links.new(output, input_socket)

    relink(texcoord.outputs["UV"] if "UV" in texcoord.outputs else texcoord.outputs["Generated"], mapping.inputs["Vector"])
    relink(mapping.outputs["Vector"], image_node.inputs["Vector"])
    relink(image_node.outputs["Color"], bsdf.inputs["Base Color"])
    if "Alpha" in bsdf.inputs:
        bsdf.inputs["Alpha"].default_value = layer.opacity
    mat.diffuse_color = (layer.tint_color[0], layer.tint_color[1], layer.tint_color[2], layer.opacity)
    mat.blend_method = "BLEND" if layer.opacity < 1.0 else "OPAQUE"
    return mat


def get_or_create_plane_object(context, name, collection, location, scale):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        mesh = bpy.data.meshes.new(f"{name}_Mesh")
        obj = bpy.data.objects.new(name, mesh)
        obj.name = name
        collection.objects.link(obj)
    mesh = obj.data
    mesh.clear_geometry()
    half_width = max(0.01, scale[0]) * 0.5
    half_height = max(0.01, scale[1]) * 0.5
    vertices = [
        (-half_width, 0.0, -half_height),
        (half_width, 0.0, -half_height),
        (half_width, 0.0, half_height),
        (-half_width, 0.0, half_height),
    ]
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="MenuOS_UV") if not mesh.uv_layers else mesh.uv_layers[0]
    for loop, uv in zip(mesh.polygons[0].loop_indices, [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]):
        uv_layer.data[loop].uv = uv
    obj.location = location
    obj.scale = (1.0, 1.0, 1.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    unlink_from_other_collections(obj, collection)
    return obj


def get_or_create_bottom_center_plane(context, name, collection, width, height, location):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        mesh = bpy.data.meshes.new(f"{name}_Mesh")
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
    mesh = obj.data
    mesh.clear_geometry()
    half_width = width * 0.5
    vertices = [
        (-half_width, 0.0, 0.0),
        (half_width, 0.0, 0.0),
        (half_width, 0.0, height),
        (-half_width, 0.0, height),
    ]
    mesh.from_pydata(vertices, [], [(0, 1, 2, 3)])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="MenuOS_UV") if not mesh.uv_layers else mesh.uv_layers[0]
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for loop, uv in zip(mesh.polygons[0].loop_indices, uvs):
        uv_layer.data[loop].uv = uv
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, 0.0)
    unlink_from_other_collections(obj, collection)
    return obj


def get_audio_device():
    global _AUDIO_DEVICE
    if aud is None:
        return None
    if _AUDIO_DEVICE is None:
        _AUDIO_DEVICE = aud.Device()
    return _AUDIO_DEVICE




def widget_anim_tick():
    global _WIDGET_ANIM_STATE, _WIDGET_ANIM_TIMER, _WIDGET_CURRENT_OFFSET, _WIDGET_CONTAINER_NAME

    if _WIDGET_ANIM_STATE == "HIDDEN":
        return 0.1

    try:
        wm = bpy.context.window_manager
        if not wm.windows: return 0.1
        scene = wm.windows[0].scene
        props = scene.agmf_props
        widget = props.now_playing_widget

        container = bpy.data.objects.get(_WIDGET_CONTAINER_NAME)
        if not container:
            return 0.1

        dt = 0.05
        _WIDGET_ANIM_TIMER += dt

        target_offset = 0.0

        if _WIDGET_ANIM_STATE == "IN":
            # Slide in
            progress = min(1.0, _WIDGET_ANIM_TIMER / max(0.1, widget.fade_in))
            # easing easeOutCubic
            ease = 1 - pow(1 - progress, 3)
            _WIDGET_CURRENT_OFFSET = _WIDGET_SLIDE_DIST * (1.0 - ease)
            if progress >= 1.0:
                _WIDGET_ANIM_STATE = "IDLE"
                _WIDGET_ANIM_TIMER = 0.0

        elif _WIDGET_ANIM_STATE == "IDLE":
            _WIDGET_CURRENT_OFFSET = 0.0
            if _WIDGET_ANIM_TIMER >= props.now_playing_duration:
                _WIDGET_ANIM_STATE = "OUT"
                _WIDGET_ANIM_TIMER = 0.0

        elif _WIDGET_ANIM_STATE == "OUT":
            # Slide out
            progress = min(1.0, _WIDGET_ANIM_TIMER / max(0.1, widget.fade_out))
            # easing easeInCubic
            ease = progress * progress * progress
            _WIDGET_CURRENT_OFFSET = _WIDGET_SLIDE_DIST * ease
            if progress >= 1.0:
                _WIDGET_ANIM_STATE = "HIDDEN"
                _WIDGET_CURRENT_OFFSET = _WIDGET_SLIDE_DIST
                # Hide the widget objects entirely
                for child in container.children:
                    child.hide_viewport = True
                    child.hide_render = True

        # Apply offset to base location
        base_x = widget.pos_x
        base_y = widget.pos_y
        if _WIDGET_SLIDE_DIR == "UP": base_y -= _WIDGET_CURRENT_OFFSET
        elif _WIDGET_SLIDE_DIR == "DOWN": base_y += _WIDGET_CURRENT_OFFSET
        elif _WIDGET_SLIDE_DIR == "LEFT": base_x += _WIDGET_CURRENT_OFFSET
        elif _WIDGET_SLIDE_DIR == "RIGHT": base_x -= _WIDGET_CURRENT_OFFSET

        container.location = (base_x, -0.1, base_y)

    except Exception as exc:
        pass

    return 0.05

def autoplay_tick():
    global _AUDIO_HANDLE, _AUDIO_TRACK_INDEX

    # Check if a track is playing and if it has finished
    if _AUDIO_HANDLE and _AUDIO_TRACK_INDEX >= 0:
        try:
            # status tells us if it's playing (1) or finished (0)
            if _AUDIO_HANDLE.status == 0:
                _AUDIO_HANDLE = None # clear old handle

                # We need context to play next track, so we get the current window manager's first window's scene
                wm = bpy.context.window_manager
                if wm.windows:
                    scene = wm.windows[0].scene
                    props = scene.agmf_props

                    if props.soundtrack_enabled:
                        index = choose_next_track_index(props, _AUDIO_TRACK_INDEX)
                        if index >= 0:
                            props.soundtrack_tracks_index = index
                            play_soundtrack_track(props.soundtrack_tracks[index], index)
        except Exception as exc:
            pass

    return 1.0 # poll every 1 second

def stop_audio_preview():
    global _AUDIO_HANDLE, _AUDIO_TRACK_INDEX
    if _AUDIO_HANDLE:
        try:
            _AUDIO_HANDLE.stop()
        except Exception:
            pass
    _AUDIO_HANDLE = None
    _AUDIO_TRACK_INDEX = -1


def get_track_filepath(track):
    if track.sound and getattr(track.sound, "filepath", ""):
        return bpy.path.abspath(track.sound.filepath)
    return bpy.path.abspath(track.filepath) if track.filepath else ""




def extract_mp3_metadata(filepath):
    import os
    import struct
    metadata = {
        'title': '',
        'artist': '',
        'album': '',
        'artwork_path': ''
    }
    if not os.path.exists(filepath):
        return metadata

    def decode_text_frame(data):
        if not data: return ""
        encoding = data[0]
        try:
            if encoding == 0: return data[1:].decode('iso-8859-1').rstrip('\x00')
            elif encoding == 1: return data[1:].decode('utf-16').rstrip('\x00')
            elif encoding == 2: return data[1:].decode('utf-16-be').rstrip('\x00')
            elif encoding == 3: return data[1:].decode('utf-8').rstrip('\x00')
        except: pass
        return ""

    def extract_apic_frame(data, mp3_filepath):
        try:
            encoding = data[0]
            idx = 1
            mime_end = data.find(b'\x00', idx)
            if mime_end == -1: return ""
            mime_type = data[idx:mime_end].decode('iso-8859-1')
            idx = mime_end + 1
            idx += 1 # pic_type
            if encoding in (1, 2):
                desc_end = data.find(b'\x00\x00', idx)
                if desc_end != -1:
                    if desc_end % 2 != idx % 2: desc_end += 1
                    idx = desc_end + 2
                else: idx = len(data)
            else:
                desc_end = data.find(b'\x00', idx)
                if desc_end != -1: idx = desc_end + 1
                else: idx = len(data)
            image_data = data[idx:]
            if not image_data: return ""
            ext = '.png' if 'png' in mime_type.lower() else '.jpg'
            base_name = os.path.splitext(os.path.basename(mp3_filepath))[0]
            artwork_path = os.path.join(os.path.dirname(mp3_filepath), f"{base_name}_artwork{ext}")
            with open(artwork_path, 'wb') as img_f:
                img_f.write(image_data)
            return artwork_path
        except:
            return ""

    try:
        with open(filepath, 'rb') as f:
            header = f.read(10)
            if header[:3] == b'ID3':
                version = header[3]
                flags = header[5]
                size = ((header[6] & 0x7F) << 21) | ((header[7] & 0x7F) << 14) | ((header[8] & 0x7F) << 7) | (header[9] & 0x7F)
                if flags & 0x40:
                    ext_header_size = struct.unpack('>I', f.read(4))[0]
                    f.read(ext_header_size - 4)
                read_size = 0
                while read_size < size:
                    if version >= 3:
                        frame_header = f.read(10)
                        if len(frame_header) < 10 or frame_header[0] == 0: break
                        frame_id = frame_header[:4]
                        if version == 4:
                            frame_size = ((frame_header[4] & 0x7F) << 21) | ((frame_header[5] & 0x7F) << 14) | ((frame_header[6] & 0x7F) << 7) | (frame_header[7] & 0x7F)
                        else:
                            frame_size = int.from_bytes(frame_header[4:8], 'big')
                        read_size += 10 + frame_size
                    else:
                        frame_header = f.read(6)
                        if len(frame_header) < 6 or frame_header[0] == 0: break
                        frame_id = frame_header[:3]
                        frame_size = int.from_bytes(frame_header[3:6], 'big')
                        read_size += 6 + frame_size
                    frame_data = f.read(frame_size)
                    if frame_id in (b'TIT2', b'TT2'): metadata['title'] = decode_text_frame(frame_data)
                    elif frame_id in (b'TPE1', b'TP1'): metadata['artist'] = decode_text_frame(frame_data)
                    elif frame_id in (b'TALB', b'TAL'): metadata['album'] = decode_text_frame(frame_data)
                    elif frame_id in (b'APIC', b'PIC'):
                        aw_path = extract_apic_frame(frame_data, filepath)
                        if aw_path: metadata['artwork_path'] = aw_path
    except: pass
    return metadata

def play_soundtrack_track(track, index=-1):
    global _AUDIO_HANDLE, _AUDIO_TRACK_INDEX
    device = get_audio_device()
    if device is None:
        return False, "Blender audio module is unavailable."

    filepath = get_track_filepath(track)
    if not filepath or not os.path.exists(filepath):
        return False, "Track file is missing."

    stop_audio_preview()
    try:
        sound = aud.Sound.file(filepath)
        if track.fade_in > 0.0:
            sound = sound.fadein(0.0, track.fade_in)
        handle = device.play(sound)
        handle.volume = track.volume
        _AUDIO_HANDLE = handle
        _AUDIO_TRACK_INDEX = index

        # Trigger live rebuild to update widget
        request_live_rebuild()

        return True, f"Playing {track.song_title or track.name}"
    except Exception as exc:
        return False, f"Could not preview audio: {exc}"


def choose_next_track_index(props, current_index):
    enabled = [idx for idx, track in enumerate(props.soundtrack_tracks) if track.enabled]
    if not enabled:
        return -1
    if props.soundtrack_order == "SEQUENTIAL":
        if current_index in enabled:
            pos = enabled.index(current_index)
            return enabled[(pos + 1) % len(enabled)] if props.soundtrack_loop or pos + 1 < len(enabled) else -1
        return enabled[0]
    if props.soundtrack_order in {"SHUFFLE", "RANDOM"}:
        choices = [idx for idx in enabled if idx != current_index] or enabled
        return random.choice(choices)
    return enabled[0]

def choose_prev_track_index(props, current_index):
    enabled = [idx for idx, track in enumerate(props.soundtrack_tracks) if track.enabled]
    if not enabled:
        return -1
    if props.soundtrack_order == "SEQUENTIAL":
        if current_index in enabled:
            pos = enabled.index(current_index)
            return enabled[(pos - 1) % len(enabled)] if props.soundtrack_loop or pos - 1 >= 0 else -1
        return enabled[-1]
    if props.soundtrack_order in {"SHUFFLE", "RANDOM"}:
        choices = [idx for idx in enabled if idx != current_index] or enabled
        return random.choice(choices)
    return enabled[0]


def create_or_update_text_block(name, body):
    text = bpy.data.texts.get(name)
    if text is None:
        text = bpy.data.texts.new(name)
    text.clear()
    text.write(body)
    return text


def theme_values(theme):
    mapping = {
        "LOW_BUDGET": {
            "text_scale": 0.85,
            "item_spacing": 0.65,
            "focus_scale": 1.05,
            "press_scale": 0.98,
            "base_color": (0.92, 0.92, 0.92, 1.0),
            "focus_color": (1.0, 0.82, 0.25, 1.0),
            "disabled_color": (0.45, 0.45, 0.45, 1.0),
            "backdrop_color": (0.04, 0.04, 0.05, 1.0),
        },
        "STYLIZED_INDIE": {
            "text_scale": 1.0,
            "item_spacing": 0.8,
            "focus_scale": 1.12,
            "press_scale": 0.96,
            "base_color": (0.95, 0.93, 0.86, 1.0),
            "focus_color": (0.94, 0.40, 0.24, 1.0),
            "disabled_color": (0.36, 0.34, 0.33, 1.0),
            "backdrop_color": (0.08, 0.06, 0.10, 1.0),
        },
        "AA": {
            "text_scale": 1.1,
            "item_spacing": 0.9,
            "focus_scale": 1.16,
            "press_scale": 0.95,
            "base_color": (0.90, 0.94, 1.0, 1.0),
            "focus_color": (0.22, 0.67, 1.0, 1.0),
            "disabled_color": (0.33, 0.38, 0.44, 1.0),
            "backdrop_color": (0.03, 0.05, 0.08, 1.0),
        },
        "AAAA": {
            "text_scale": 1.22,
            "item_spacing": 1.02,
            "focus_scale": 1.22,
            "press_scale": 0.93,
            "base_color": (0.95, 0.97, 1.0, 1.0),
            "focus_color": (0.15, 0.92, 0.78, 1.0),
            "disabled_color": (0.24, 0.29, 0.33, 1.0),
            "backdrop_color": (0.02, 0.03, 0.05, 1.0),
        },
    }
    return mapping.get(theme, mapping["LOW_BUDGET"])


def get_menu_root(props):
    if not props.menu_root_name:
        return None
    return bpy.data.objects.get(props.menu_root_name)


def get_or_create_item_container(context, root, item, location, parent_obj=None):
    scene = context.scene
    root_collection = ensure_collection(scene, menu_collection_name(root.name))
    collection = ensure_child_collection(root_collection, item_collection_name(root.name, item.name))
    obj_name = item_container_object_name(root.name, item.name)
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        obj = bpy.data.objects.new(obj_name, None)
        obj.empty_display_type = "CUBE"
        obj.empty_display_size = 0.18
        collection.objects.link(obj)
    unlink_from_other_collections(obj, collection)
    parent_as_local(obj, parent_obj or root)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj["agmf_root"] = root.name
    obj["agmf_item_name"] = item.name
    obj["agmf_role"] = "MENU_ITEM_CONTAINER"
    return obj


def text_content_width(item):
    container_width, _container_height = item_container_size(item)
    return max(0.01, container_width - (item.container_padding_x * 2.0) - (abs(item.text_padding_x) * 2.0))


def label_text_size(item):
    available = max(0.01, item.height - (item.container_padding_y * 2.0) - (abs(item.text_padding_y) * 2.0))
    return min(item.text_size, max(0.08, available * 0.82))


def set_text_box_width(text_curve, width):
    try:
        if text_curve.text_boxes:
            text_curve.text_boxes[0].width = width
    except Exception:
        pass


def get_or_create_text_object(context, root, item, parent_obj=None):
    scene = context.scene
    root_collection = ensure_collection(scene, menu_collection_name(root.name))
    collection = ensure_child_collection(root_collection, item_collection_name(root.name, item.name))
    obj_name = item_object_name(root.name, item.name)
    obj = bpy.data.objects.get(obj_name)
    if obj and obj.type != "FONT":
        obj.name = f"{obj.name}_OLD"
        obj = None

    if obj is None:
        bpy.ops.object.text_add(location=(0.0, 0.0, 0.0))
        obj = context.active_object
        obj.name = obj_name
        obj.data.name = f"{obj_name}_Curve"
        collection.objects.link(obj)
        unlink_from_other_collections(obj, collection)

    parent_as_local(obj, parent_obj or root)
    obj["agmf_root"] = root.name
    obj["agmf_item_name"] = item.name
    obj["agmf_item_type"] = item.item_type
    obj.data.body = item.label
    obj.data.align_x = item.text_align_x
    obj.data.align_y = item.text_align_y
    obj.data.size = label_text_size(item)

    if hasattr(obj.data, "space_character"):
        obj.data.space_character = item.text_kerning

    if item.text_font:
        abs_path = bpy.path.abspath(item.text_font)
        if os.path.exists(abs_path):
            font_name = os.path.basename(abs_path)
            fnt = bpy.data.fonts.get(font_name)
            if not fnt:
                try:
                    fnt = bpy.data.fonts.load(abs_path)
                except:
                    pass
            if fnt:
                obj.data.font = fnt

    set_text_box_width(obj.data, text_content_width(item))
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    assign_material(obj, get_or_create_material(f"{obj.name}_Text_MAT", item.text_color))

    if item.item_type == "LOGO":
        obj.hide_viewport = True
        obj.hide_render = True

    return obj


def get_or_create_description_object(context, root, item, parent_obj=None):
    scene = context.scene
    root_collection = ensure_collection(scene, menu_collection_name(root.name))
    collection = ensure_child_collection(root_collection, item_collection_name(root.name, item.name))
    obj_name = item_description_object_name(root.name, item.name)
    obj = bpy.data.objects.get(obj_name)
    if obj and obj.type != "FONT":
        obj.name = f"{obj.name}_OLD"
        obj = None

    if obj is None:
        bpy.ops.object.text_add(location=(0.0, 0.0, 0.0))
        obj = context.active_object
        obj.name = obj_name
        obj.data.name = f"{obj_name}_Curve"
        collection.objects.link(obj)
        unlink_from_other_collections(obj, collection)

    parent_as_local(obj, parent_obj or root)
    obj["agmf_root"] = root.name
    obj["agmf_item_name"] = item.name
    obj["agmf_role"] = "MENU_DESCRIPTION"
    obj.data.body = item.description
    obj.data.align_x = item.text_align_x
    obj.data.align_y = "TOP"
    obj.data.size = min(item.description_scale, max(0.05, item_description_height(item)))
    set_text_box_width(obj.data, text_content_width(item))
    obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    assign_material(obj, get_or_create_material(f"{obj.name}_Description_MAT", item.description_color))
    obj.hide_viewport = not item.show_description or not item.description
    obj.hide_render = obj.hide_viewport
    return obj


def item_description_height(item):
    if not item.show_description or not item.description:
        return 0.0
    return max(0.01, item.description_scale * 0.34)


def item_container_size(item):
    width = max(0.01, item.width)
    height = max(0.01, item.height)
    if item.show_description and item.description:
        height += item.description_gap + item_description_height(item)
    return width, height


def text_location_for_item(item):
    container_width, container_height = item_container_size(item)
    x = item.text_padding_x
    z = item.text_padding_y
    if item.text_align_x == "LEFT":
        x = -(container_width * 0.5) + item.container_padding_x + item.text_padding_x
    elif item.text_align_x == "RIGHT":
        x = (container_width * 0.5) - item.container_padding_x - item.text_padding_x

    if item.text_align_y == "TOP":
        z = (container_height * 0.5) - item.container_padding_y - item.text_padding_y
    elif item.text_align_y == "BOTTOM":
        z = -(container_height * 0.5) + item.container_padding_y + item.text_padding_y
    return (x, -0.08, z)


def description_location_for_item(item):
    label_location = text_location_for_item(item)
    label_drop = max(0.01, item.height * 0.42)
    desc_z = label_location[2] - label_drop - max(0.0, item.description_gap)
    return (label_location[0], -0.081, desc_z)


def apply_panel_settings_to_items(props, panel):
    if not props or not panel:
        return 0
    panel_items = [item for item in props.menu_items if item.panel == panel.name]
    cursor_y = panel.start_y
    for item in panel_items:
        item.width = panel.option_width
        item.height = panel.option_height
        item.text_size = panel.batch_text_size
        item.text_align_x = panel.batch_text_align_x
        item.text_align_y = panel.batch_text_align_y
        item.text_padding_x = panel.batch_text_padding_x
        item.text_padding_y = panel.batch_text_padding_y
        item.container_padding_x = panel.batch_container_padding_x
        item.container_padding_y = panel.batch_container_padding_y
        item.margin_top = panel.batch_margin_top
        item.margin_bottom = panel.batch_margin_bottom
        item.show_description = panel.batch_show_description
        item.description_gap = panel.batch_description_gap
        item.description_scale = panel.batch_description_scale
        item.description_color = panel.batch_description_color
        item.fill_type = panel.batch_fill_type
        item.fill_color = panel.batch_fill_color
        item.ramp_color_a = panel.batch_ramp_color_a
        item.ramp_color_b = panel.batch_ramp_color_b
        item.ramp_offset_x = panel.batch_ramp_offset_x
        item.ramp_offset_y = panel.batch_ramp_offset_y
        item.focus_fill_color = panel.batch_focus_color
        item.press_fill_color = panel.batch_press_color
        item.text_color = panel.batch_text_color
        item.text_font = panel.batch_text_font
        item.text_kerning = panel.batch_text_kerning

        container_width, container_height = item_container_size(item)
        if panel.layout_align_x == "LEFT":
            item.pos_x = -(props.background_canvas_width * 0.5) + panel.layout_margin_x + (container_width * 0.5)
        elif panel.layout_align_x == "RIGHT":
            item.pos_x = (props.background_canvas_width * 0.5) - panel.layout_margin_x - (container_width * 0.5)
        elif panel.layout_align_x == "CENTER":
            item.pos_x = 0.0
        else:
            item.pos_x = panel.align_x

        cursor_y -= item.margin_top
        item.pos_y = cursor_y - (container_height * 0.5)
        cursor_y -= container_height + item.margin_bottom + panel.option_spacing
    return len(panel_items)


def get_or_create_button_rect(context, root, item, location, parent_obj=None):
    scene = context.scene
    root_collection = ensure_collection(scene, menu_collection_name(root.name))
    collection = ensure_child_collection(root_collection, item_collection_name(root.name, item.name))
    rect_name = item_rect_object_name(root.name, item.name)
    border_name = item_border_object_name(root.name, item.name)
    container_width, container_height = item_container_size(item)

    rect = get_or_create_plane_object(
        context,
        rect_name,
        collection,
        (0.0, -0.04, 0.0),
        (container_width, container_height, 1.0),
    )
    parent_as_local(rect, parent_obj or root)
    rect.location = (0.0, -0.04, 0.0)
    rect["agmf_root"] = root.name
    rect["agmf_item_name"] = item.name
    rect["agmf_role"] = "MENU_RECTANGLE"

    color = item.fill_color
    if item.preview_state == "FOCUSED":
        color = item.focus_fill_color
    elif item.preview_state == "PRESSED":
        color = item.press_fill_color
    elif item.preview_state == "DISABLED":
        color = (color[0] * 0.35, color[1] * 0.35, color[2] * 0.35, color[3])
    elif item.preview_state == "HIDDEN":
        color = (color[0], color[1], color[2], 0.0)

    props = context.scene.agmf_props
    if item.item_type == "LOGO":
        mat = try_load_image_material(f"{rect_name}_Logo_MAT", props.logo_path, color)
    elif item.fill_type == "COLOR_RAMP" and item.preview_state == "IDLE":
        mat = get_or_create_ramp_material(
            f"{rect_name}_Ramp_MAT",
            item.ramp_color_a,
            item.ramp_color_b,
            item.ramp_direction,
            offset_x=item.ramp_offset_x,
            offset_y=item.ramp_offset_y,
        )
    elif item.fill_type == "IMAGE":
        mat = try_load_image_material(f"{rect_name}_Image_MAT", item.media_path, color)
    elif item.fill_type in {"VIDEO", "SEQUENCE"}:
        mat = try_load_media_material(f"{rect_name}_Media_MAT", item.media_path, color)
    else:
        mat = get_or_create_material(f"{rect_name}_MAT", color)
    assign_material(rect, mat)
    rect.hide_viewport = item.preview_state == "HIDDEN"
    rect.hide_render = item.preview_state == "HIDDEN"

    if item.use_border:
        border_scale = (
            max(0.01, container_width + item.border_thickness),
            max(0.01, container_height + item.border_thickness),
            1.0,
        )
        border = get_or_create_plane_object(
            context,
            border_name,
            collection,
            (0.0, -0.05, 0.0),
            border_scale,
        )
        parent_as_local(border, parent_obj or root)
        border.location = (0.0, -0.05, 0.0)
        border["agmf_root"] = root.name
        border["agmf_item_name"] = item.name
        border["agmf_role"] = "MENU_BORDER"
        if item.border_fill_type == "COLOR_RAMP":
            border_mat = get_or_create_ramp_material(
                f"{border_name}_Ramp_MAT",
                item.border_ramp_color_a,
                item.border_ramp_color_b,
                item.ramp_direction,
            )
        else:
            border_mat = get_or_create_material(f"{border_name}_MAT", item.border_color)
        assign_material(border, border_mat)
        border.hide_viewport = item.preview_state == "HIDDEN"
        border.hide_render = item.preview_state == "HIDDEN"
    else:
        border = bpy.data.objects.get(border_name)
        if border:
            border.hide_viewport = True
            border.hide_render = True

    return rect


def ensure_menu_camera(context, root, parent_obj=None):
    scene = context.scene
    collection = ensure_collection(scene, menu_collection_name(root.name))
    camera_name = camera_object_name(root.name)
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != "CAMERA":
        cam_data = bpy.data.cameras.new(name=f"{camera_name}_Data")
        camera = bpy.data.objects.new(camera_name, cam_data)
        collection.objects.link(camera)

    parent_as_local(camera, parent_obj or root)
    camera.location = (0.0, -12.0, 0.0)
    camera.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    camera.data.type = "PERSP"
    scene.camera = camera
    return camera


def ensure_backdrop(context, root, props):
    scene = context.scene
    collection = ensure_collection(scene, menu_collection_name(root.name))
    name = backdrop_object_name(root.name)
    obj = bpy.data.objects.get(name)

    obj = get_or_create_bottom_center_plane(context, name, collection, props.background_canvas_width, props.background_canvas_height, (0.0, 0.0, 0.0))

    parent_as_local(obj, root)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj.location = (0.0, 0.0, 0.0)
    obj["agmf_role"] = "BACKDROP"
    obj["agmf_bottom_center_origin"] = True
    obj["agmf_canvas_parent"] = True
    obj["agmf_backdrop_mode"] = props.background_type
    obj["agmf_scene_window"] = props.background_scene.name if props.background_scene else ""
    obj["agmf_scene_window_camera"] = props.background_scene_camera.name if props.background_scene_camera else ""
    obj.hide_viewport = False
    obj.hide_render = len(props.background_layers) > 0
    obj.display_type = "TEXTURED"
    color = props.bg_color_a if props.background_type in {"COLOR", "COLOR_RAMP", "HYBRID"} else theme_values(props.theme_preset)["backdrop_color"]
    if props.background_type == "SCENE":
        if props.background_scene and not props.background_scene_camera:
            props.background_scene_camera = find_scene_camera(props.background_scene)
        mat = get_or_create_material(f"{name}_Scene_Window_MAT", (0.0, 0.0, 0.0, 1.0))
        obj.show_name = True
        obj.hide_render = False
    elif props.background_type == "COLOR_RAMP":
        mat = get_or_create_ramp_material(f"{name}_Ramp_MAT", props.bg_color_a, props.bg_color_b, "HORIZONTAL")
    elif props.background_type in {"VIDEO", "HYBRID"} and props.background_media_path:
        mat = try_load_media_material(f"{name}_Media_MAT", props.background_media_path, color)
    elif props.background_type in {"IMAGE", "HYBRID"} and props.background_media_path:
        mat = try_load_image_material(f"{name}_Image_MAT", props.background_media_path, color)
    else:
        mat = get_or_create_material(f"{name}_MAT", color)
    assign_material(obj, mat)
    if hasattr(obj, "color"):
        obj.color = color
    return obj


def ensure_canvas_center(context, root, props, backdrop_obj):
    scene = context.scene
    collection = ensure_collection(scene, menu_collection_name(root.name))
    name = canvas_center_object_name(root.name)
    obj = bpy.data.objects.get(name)
    if obj is None:
        obj = bpy.data.objects.new(name, None)
        obj.empty_display_type = "PLAIN_AXES"
        obj.empty_display_size = 0.35
        collection.objects.link(obj)
    unlink_from_other_collections(obj, collection)
    parent_as_local(obj, backdrop_obj)
    obj.location = (0.0, 0.0, props.background_canvas_height * 0.5)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    obj["agmf_role"] = "CANVAS_CENTER"
    obj["agmf_origin_note"] = "UI layout origin: center of backdrop canvas. Parent backdrop keeps bottom-center origin."
    return obj


def ensure_background_media_layers(context, root, props, parent_obj=None):
    scene = context.scene
    collection = ensure_collection(scene, menu_collection_name(root.name))
    active_names = set()

    for index, layer in enumerate(props.background_layers):
        obj_name = background_layer_object_name(root.name, layer.name, index)
        active_names.add(obj_name)
        obj = get_or_create_bottom_center_plane(
            context,
            obj_name,
            collection,
            max(0.01, layer.width),
            max(0.01, layer.height),
            (layer.move_x, layer.move_y, layer.move_z),
        )
        parent_as_local(obj, parent_obj or root)
        obj.location = (layer.move_x, layer.move_y, layer.move_z)
        obj["agmf_role"] = "BACKGROUND_MEDIA_LAYER"
        obj["agmf_layer_use"] = layer.layer_use
        obj["agmf_media_type"] = layer.layer_type
        obj["agmf_bottom_center_origin"] = True
        obj.hide_viewport = not layer.enabled
        obj.hide_render = not layer.enabled

        mat = get_or_create_mapped_media_material(f"{obj_name}_MAT", layer)
        assign_material(obj, mat)

    prefix = f"{root.name}_BG_"
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix) and obj.name not in active_names:
            bpy.data.objects.remove(obj, do_unlink=True)


def compute_item_location(index, count, props):
    if props.layout_mode == "FREEFORM":
        return None
    spacing = props.item_spacing
    if props.layout_mode == "VERTICAL":
        origin = ((count - 1) * spacing) * 0.5
        return (0.0, 0.0, origin - (index * spacing))
    if props.layout_mode == "HORIZONTAL":
        origin = ((count - 1) * spacing) * 0.5
        return (index * spacing - origin, 0.0, 0.0)
    if props.layout_mode == "GRID":
        cols = max(1, props.grid_columns)
        row = index // cols
        col = index % cols
        row_count = max(1, math.ceil(count / cols))
        x_origin = ((min(cols, count) - 1) * spacing) * 0.5
        z_origin = ((row_count - 1) * spacing) * 0.5
        return (col * spacing - x_origin, 0.0, z_origin - (row * spacing))

    angle_step = (math.tau / max(1, count))
    angle = props.radial_offset + (index * angle_step)
    radius = max(0.1, props.radial_radius)
    return (math.cos(angle) * radius, 0.0, math.sin(angle) * radius)


def apply_state_to_object(obj, item, props):
    values = theme_values(props.theme_preset)
    state = item.preview_state
    scale_value = item.base_scale * values["text_scale"]
    color = values["base_color"]
    alpha = 1.0

    if state == "FOCUSED":
        color = values["focus_color"]
    elif state == "PRESSED":
        color = values["focus_color"]
    elif state == "DISABLED":
        color = values["disabled_color"]
    elif state == "HIDDEN":
        alpha = 0.0

    obj.scale = (1.0, 1.0, 1.0) if obj.type == "FONT" else (scale_value, scale_value, scale_value)
    obj.hide_viewport = state == "HIDDEN"
    obj.hide_render = state == "HIDDEN"
    if hasattr(obj, "color"):
        obj.color = (color[0], color[1], color[2], alpha)


def panel_for_item(props, item):
    for panel in props.panels:
        if panel.name == item.panel:
            return panel
    return None


def item_world_location(item, base_location, props):
    panel = panel_for_item(props, item)
    px = panel.offset_x if panel and panel.visible else 0.0
    pz = panel.offset_y if panel and panel.visible else 0.0
    py = panel.depth_y if panel and panel.visible else 0.0
    return (base_location[0] + px, base_location[1] + py, base_location[2] + pz)



def rebuild_now_playing_widget(context, root, props):

    scene = context.scene
    collection = ensure_collection(scene, menu_collection_name(root.name))
    widget = props.now_playing_widget

    # Base Container
    base_name = f"{root.name}_NowPlaying"
    container = bpy.data.objects.get(base_name)
    if container is None:
        container = bpy.data.objects.new(base_name, None)
        container.empty_display_type = "PLAIN_AXES"
        collection.objects.link(container)
    unlink_from_other_collections(container, collection)
    parent_as_local(container, root)
    container.location = (widget.pos_x, -0.1, widget.pos_y)
    container["agmf_item_name"] = "NowPlayingContainer"

    global _WIDGET_CONTAINER_NAME, _WIDGET_SLIDE_DIR, _WIDGET_SLIDE_DIST
    _WIDGET_CONTAINER_NAME = base_name
    _WIDGET_SLIDE_DIR = widget.slide_dir
    _WIDGET_SLIDE_DIST = widget.slide_dist

    # Hide all contents if widget is not showing
    should_show = props.soundtrack_enabled and props.show_now_playing


    # Background Plane
    bg_name = f"{base_name}_BG"
    bg = get_or_create_plane_object(context, bg_name, collection, (0.0, 0.0, 0.0), (widget.width, widget.height, 1.0))
    parent_as_local(bg, container)
    bg.location = (0.0, 0.0, 0.0)
    bg.hide_viewport = not should_show
    bg.hide_render = not should_show
    bg["agmf_item_name"] = "NowPlayingBG"

    if widget.fill_type == "COLOR_RAMP":
        mat = get_or_create_ramp_material(f"{bg_name}_MAT", widget.ramp_color_a, widget.ramp_color_b, widget.ramp_direction, offset_x=widget.ramp_offset_x, offset_y=widget.ramp_offset_y)
    else:
        mat = get_or_create_material(f"{bg_name}_MAT", widget.fill_color)
    assign_material(bg, mat)

    # Text: Title
    title_name = f"{base_name}_Title"
    title_obj = bpy.data.objects.get(title_name)
    if title_obj is None:
        bpy.ops.object.text_add(location=(0.0, 0.0, 0.0))
        title_obj = context.active_object
        title_obj.name = title_name
        collection.objects.link(title_obj)
        unlink_from_other_collections(title_obj, collection)
    parent_as_local(title_obj, container)
    title_obj.location = (widget.title_offset_x, -0.01, widget.title_offset_y)
    title_obj.hide_viewport = not should_show
    title_obj.hide_render = not should_show
    title_obj["agmf_item_name"] = "NowPlayingTitle"
    title_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    title_obj.data.size = widget.title_size
    title_obj.data.body = "Song Title"
    assign_material(title_obj, get_or_create_material(f"{title_name}_MAT", widget.title_color))

    # Text: Artist
    artist_name = f"{base_name}_Artist"
    artist_obj = bpy.data.objects.get(artist_name)
    if artist_obj is None:
        bpy.ops.object.text_add(location=(0.0, 0.0, 0.0))
        artist_obj = context.active_object
        artist_obj.name = artist_name
        collection.objects.link(artist_obj)
        unlink_from_other_collections(artist_obj, collection)
    parent_as_local(artist_obj, container)
    artist_obj.location = (widget.artist_offset_x, -0.01, widget.artist_offset_y)
    artist_obj.hide_viewport = not should_show
    artist_obj.hide_render = not should_show
    artist_obj["agmf_item_name"] = "NowPlayingArtist"
    artist_obj.rotation_euler = (math.radians(90.0), 0.0, 0.0)
    artist_obj.data.size = widget.artist_size
    artist_obj.data.body = "Artist Name"
    assign_material(artist_obj, get_or_create_material(f"{artist_name}_MAT", widget.artist_color))

    # Artwork
    art_name = f"{base_name}_Artwork"
    art_obj = get_or_create_plane_object(context, art_name, collection, (0.0, 0.0, 0.0), (widget.artwork_size, widget.artwork_size, 1.0))
    parent_as_local(art_obj, container)
    art_obj.location = (widget.artwork_offset_x, -0.02, widget.artwork_offset_y)
    art_obj.hide_viewport = not (should_show and widget.show_artwork)
    art_obj.hide_render = not (should_show and widget.show_artwork)
    art_obj["agmf_item_name"] = "NowPlayingArtwork"

    # Fetch active track details
    title_str = "Song Title"
    artist_str = "Artist Name"
    art_path = ""
    global _AUDIO_TRACK_INDEX
    if _AUDIO_TRACK_INDEX >= 0 and _AUDIO_TRACK_INDEX < len(props.soundtrack_tracks):
        track = props.soundtrack_tracks[_AUDIO_TRACK_INDEX]
        title_str = track.song_title or track.name or "Unknown Track"
        artist_str = track.artist or ""
        art_path = track.album_art_path

    title_obj.data.body = title_str
    artist_obj.data.body = artist_str

    art_mat = None
    if widget.show_artwork and art_path:
        art_mat = try_load_image_material(f"{art_name}_MAT", art_path, (0.2, 0.2, 0.2, 1.0))
    if not art_mat:
        art_mat = get_or_create_material(f"{art_name}_MAT", (0.2, 0.2, 0.2, 1.0))
    assign_material(art_obj, art_mat)


def rebuild_menu_objects(context):
    props = context.scene.agmf_props
    root = get_menu_root(props)
    if root is None:
        return "Create a menu root first."

    background_parent = ensure_backdrop(context, root, props)
    canvas_parent = ensure_canvas_center(context, root, props, background_parent)
    ensure_menu_camera(context, root, canvas_parent)
    ensure_background_media_layers(context, root, props, background_parent)

    item_names = {item.name for item in props.menu_items}
    item_names.update({"NowPlayingContainer", "NowPlayingBG", "NowPlayingTitle", "NowPlayingArtist", "NowPlayingArtwork"})
    prefix = f"{root.name}_"
    for obj in list(bpy.data.objects):
        if obj.name.startswith(prefix) and obj.type in {"FONT", "MESH", "EMPTY"}:
            existing_name = obj.get("agmf_item_name")
            if existing_name and existing_name not in item_names:
                bpy.data.objects.remove(obj, do_unlink=True)

    rebuild_now_playing_widget(context, root, props)

    count = len(props.menu_items)
    for index, item in enumerate(props.menu_items):
        layout_location = compute_item_location(index, count, props)
        base_location = layout_location if layout_location else (item.pos_x, item.depth_y, item.pos_y)
        location = item_world_location(item, base_location, props)
        container = get_or_create_item_container(context, root, item, location, canvas_parent)
        if item.item_type in {"BUTTON", "IMAGE", "CONTAINER", "LOGO", "ACCOUNT", "SOUNDTRACK_NOW"}:
            get_or_create_button_rect(context, root, item, (0.0, 0.0, 0.0), container)
        obj = get_or_create_text_object(context, root, item, container)
        obj.location = text_location_for_item(item)
        apply_state_to_object(obj, item, props)
        desc = get_or_create_description_object(context, root, item, container)
        desc.location = description_location_for_item(item)
        apply_state_to_object(desc, item, props)
        if not item.show_description or not item.description:
            desc.hide_viewport = True
            desc.hide_render = True

    return f"Rebuilt {count} menu items."


def generate_preview_summary(scene):
    props = scene.agmf_props
    root = get_menu_root(props)
    payload = {
        "menu_name": props.menu_name,
        "root": root.name if root else "",
        "target_mode": props.target_mode,
        "layout_mode": props.layout_mode,
        "theme_preset": props.theme_preset,
        "camera_style": props.camera_style,
        "background": {
            "type": props.background_type,
            "media_path": props.background_media_path,
            "sequence_folder": props.background_sequence_folder,
            "scene": props.background_scene.name if props.background_scene else "",
            "scene_camera": props.background_scene_camera.name if props.background_scene_camera else "",
            "is_scene_window": props.background_type == "SCENE",
            "scene_rotation_mode": props.scene_rotation_mode,
            "canvas": [props.background_canvas_width, props.background_canvas_height],
            "layers": [],
        },
        "screens": [],
        "soundtrack": {
            "enabled": props.soundtrack_enabled,
            "order": props.soundtrack_order,
            "loop": props.soundtrack_loop,
            "show_now_playing": props.show_now_playing,
            "now_playing_duration": props.now_playing_duration,
            "tracks": [],
        },
        "live_scenes": [],
        "panels": [],
        "items": [],
    }
    for panel in props.panels:
        payload["panels"].append(
            {
                "name": panel.name,
                "page": panel.page,
                "offset": [panel.offset_x, panel.offset_y, panel.depth_y],
                "visible": panel.visible,
                "locked": panel.locked,
            }
        )
    for layer in props.background_layers:
        duration = layer.auto_duration if layer.duration_mode == "AUTO" else layer.custom_duration
        payload["background"]["layers"].append(
            {
                "name": layer.name,
                "enabled": layer.enabled,
                "type": layer.layer_type,
                "use": layer.layer_use,
                "filepath": layer.filepath,
                "scene_window": layer.scene_window.name if layer.scene_window else "",
                "size": [layer.width, layer.height],
                "move": [layer.move_x, layer.move_y, layer.move_z],
                "fit": layer.fit_mode,
                "mapping": {
                    "zoom": layer.map_zoom,
                    "scale": [layer.map_scale_x, layer.map_scale_y, layer.map_scale_z],
                    "offset": [layer.map_offset_x, layer.map_offset_y, layer.map_offset_z],
                    "rotation": layer.map_rotation,
                },
                "duration_mode": layer.duration_mode,
                "duration": duration,
                "transition_in": layer.transition_in,
                "transition_out": layer.transition_out,
                "opacity": layer.opacity,
            }
        )
    for slot in props.live_scenes:
        payload["live_scenes"].append(
            {
                "name": slot.name,
                "scene": slot.scene,
                "trigger_item": slot.trigger_item,
                "weight": slot.weight,
                "enabled": slot.enabled,
            }
        )
    for screen in props.screens:
        payload["screens"].append(
            {
                "name": screen.name,
                "type": screen.screen_type,
                "duration": screen.duration,
                "skippable": screen.skippable,
                "media_path": screen.media_path,
                "target_page": screen.target_page,
            }
        )
    for track in props.soundtrack_tracks:
        payload["soundtrack"]["tracks"].append(
            {
                "name": track.name,
                "song": track.song_title,
                "artist": track.artist,
                "album": track.album,
                "enabled": track.enabled,
                "track_number": track.track_number,
                "volume": track.volume,
                "filepath": track.sound.filepath if track.sound else track.filepath,
                "album_art": track.album_art_path,
            }
        )
    for index, item in enumerate(props.menu_items):
        payload["items"].append(
            {
                "index": index,
                "name": item.name,
                "label": item.label,
                "page": item.page,
                "panel": item.panel,
                "item_type": item.item_type,
                "action": item.action,
                "target_menu": item.target_menu,
                "preview_state": item.preview_state,
                "position": [item.pos_x, item.pos_y],
                "size": [item.width, item.height],
                "fill_type": item.fill_type,
                "ramp": {
                    "color_a": list(item.ramp_color_a),
                    "color_b": list(item.ramp_color_b),
                    "direction": item.ramp_direction,
                },
                "media_path": item.media_path,
                "text": {
                    "align_x": item.text_align_x,
                    "align_y": item.text_align_y,
                    "padding": [item.text_padding_x, item.text_padding_y],
                    "container_padding": [item.container_padding_x, item.container_padding_y],
                    "color": list(item.text_color),
                    "description_enabled": item.show_description,
                    "description": item.description,
                    "description_gap": item.description_gap,
                    "description_scale": item.description_scale,
                    "description_color": list(item.description_color),
                },
                "animation": item.focus_animation,
            }
        )
    return json.dumps(payload, indent=2)


def generate_upbge_runtime_script(config_json):
    return f'''# Auto-generated by Ascend Gaming | Menu Forge.
# Attach this script to a persistent UPBGE menu controller object.
# Call main() from an Always sensor with True pulse mode.

import json
import random

try:
    from bge import logic, events
except Exception:
    logic = None
    events = None
try:
    import aud
except Exception:
    aud = None





try:

try:
    from bge import texture
except Exception:
    texture = None

MENUOS_CONFIG = {config_json!r}

STATE = {{
    "boot_index": 0,
    "boot_timer": 0.0,
    "focus_index": 0,
    "active_page": "MainMenu",
    "active_bg_scene": "",
    "track_index": -1,
    "initialized": False,
}}

AUDIO_DEVICE = None
AUDIO_HANDLE = None
VIDEO_TEXTURE = None
VIDEO_SOURCE = None
SCENE_WINDOW_TEXTURE = None
SCENE_WINDOW_SOURCE = None


def _config():
    return json.loads(MENUOS_CONFIG)


def _audio_device():
    global AUDIO_DEVICE
    if aud is None:
        return None
    if AUDIO_DEVICE is None:
        AUDIO_DEVICE = aud.Device()
    return AUDIO_DEVICE


def _keyboard():
    return logic.keyboard.inputs if logic else {{}}


def _pressed(key):
    keyboard = _keyboard()
    entry = keyboard.get(key)
    return bool(entry and entry.activated)


def _active_items(data):
    page = STATE.get("active_page", "MainMenu")
    items = [item for item in data.get("items", []) if item.get("item_type") != "LABEL"]
    page_items = [item for item in items if item.get("page", "MainMenu") == page]
    return page_items or items


def _set_object_visible(obj_name, visible):
    scene = logic.getCurrentScene()
    obj = scene.objects.get(obj_name)
    if obj:
        obj.visible = visible


def _setup_background_video(data):
    global VIDEO_TEXTURE, VIDEO_SOURCE
    if texture is None:
        return
    background = data.get("background", {{}})
    if background.get("type") not in {{"VIDEO", "HYBRID"}}:
        return
    path = background.get("media_path", "")
    if not path:
        return
    scene = logic.getCurrentScene()
    backdrop_name = f"AGMF_{{data.get('menu_name', 'MainMenu')}}_Backdrop"
    obj = scene.objects.get(backdrop_name) or scene.objects.get("MenuOS_BackgroundVideo")
    if not obj:
        return
    try:
        VIDEO_TEXTURE = texture.Texture(obj, 0, 0)
        VIDEO_SOURCE = texture.VideoFFmpeg(path)
        VIDEO_SOURCE.repeat = -1
        VIDEO_SOURCE.play()
        VIDEO_TEXTURE.source = VIDEO_SOURCE
    except Exception as exc:
        print("MenuOS video setup failed:", exc)


def _setup_scene_window(data):
    global SCENE_WINDOW_TEXTURE, SCENE_WINDOW_SOURCE
    if texture is None:
        return
    background = data.get("background", {{}})
    if not background.get("is_scene_window"):
        return
    scene_name = background.get("scene", "")
    camera_name = background.get("scene_camera", "")
    if not scene_name:
        return
    scene = logic.getCurrentScene()
    backdrop_name = f"AGMF_{{data.get('menu_name', 'MainMenu')}}_Backdrop"
    backdrop = scene.objects.get(backdrop_name)
    if not backdrop:
        return
    try:
        scene_list = logic.getSceneList()
        source_scene = scene_list.get(scene_name) if hasattr(scene_list, "get") else None
        if source_scene is None:
            logic.addScene(scene_name, 0)
            source_scene = logic.getSceneList().get(scene_name) if hasattr(logic.getSceneList(), "get") else None
        if source_scene is None:
            print("MenuOS scene window could not find scene:", scene_name)
            return
        camera = source_scene.objects.get(camera_name) if camera_name else source_scene.active_camera
        if camera is None:
            print("MenuOS scene window has no camera:", scene_name)
            return
        SCENE_WINDOW_TEXTURE = texture.Texture(backdrop, 0, 0)
        SCENE_WINDOW_SOURCE = texture.ImageRender(source_scene, camera)
        SCENE_WINDOW_TEXTURE.source = SCENE_WINDOW_SOURCE
    except Exception as exc:
        print("MenuOS scene window setup failed:", exc)


def _refresh_background_video():
    if VIDEO_TEXTURE is None:
        pass
    else:
        try:
            VIDEO_TEXTURE.refresh(False)
        except Exception:
            pass
    if SCENE_WINDOW_TEXTURE is not None:
        try:
            SCENE_WINDOW_TEXTURE.refresh(True)
        except Exception:
            pass


def _apply_focus_visuals(data):
    items = _active_items(data)
    for idx, item in enumerate(items):
        focused = idx == STATE["focus_index"]
        rect = f"AGMF_{{data.get('menu_name', 'MainMenu')}}_{{item.get('name')}}_Rect"
        text = f"AGMF_{{data.get('menu_name', 'MainMenu')}}_{{item.get('name')}}_Text"
        _set_object_visible(rect, True)
        _set_object_visible(text, True)
        # Runtime material swaps are project-specific; Menu Forge exports names so you can
        # replace this block with shader, animation, or LogicLink calls later.
        scene = logic.getCurrentScene()
        for obj_name in (rect, text):
            obj = scene.objects.get(obj_name)
            if obj:
                obj["MenuOSFocused"] = focused
                obj["MenuOSState"] = "FOCUSED" if focused else "IDLE"


def _switch_background_scene(data, item=None):
    # Scene windows are render-to-texture surfaces, not editor/runtime scene switches.
    if data.get("background", {{}}).get("is_scene_window"):
        return
    slots = [slot for slot in data.get("live_scenes", []) if slot.get("enabled") and slot.get("scene")]
    if not slots:
        scene_name = data.get("background", {{}}).get("scene", "")
    else:
        scene_name = ""
        if item:
            for slot in slots:
                if slot.get("trigger_item") in {{item.get("name"), item.get("label")}}:
                    scene_name = slot.get("scene")
                    break
        if not scene_name:
            mode = data.get("background", {{}}).get("scene_rotation_mode", "ON_NAV")
            if mode == "RANDOM":
                weighted = []
                for slot in slots:
                    weighted.extend([slot] * max(1, int(slot.get("weight", 1))))
                scene_name = random.choice(weighted).get("scene")
            elif mode == "SEQUENTIAL":
                names = [slot.get("scene") for slot in slots]
                last = STATE.get("active_bg_scene", "")
                scene_name = names[(names.index(last) + 1) % len(names)] if last in names else names[0]
            else:
                scene_name = slots[0].get("scene")

    if not scene_name or scene_name == STATE.get("active_bg_scene"):
        return

    try:
        if STATE.get("active_bg_scene"):
            old_scene = logic.getSceneList().get(STATE["active_bg_scene"])
            if old_scene:
                old_scene.end()
        logic.addScene(scene_name, 0)
        STATE["active_bg_scene"] = scene_name
    except Exception as exc:
        print("MenuOS scene switch failed:", scene_name, exc)


def _play_track(data, index=None):
    global AUDIO_HANDLE
    tracks = [track for track in data.get("soundtrack", {{}}).get("tracks", []) if track.get("enabled") and track.get("filepath")]
    if not tracks:
        return
    order = data.get("soundtrack", {{}}).get("order", "SHUFFLE")
    if index is None:
        if order == "SEQUENTIAL":
            index = (STATE["track_index"] + 1) % len(tracks)
        else:
            choices = [i for i in range(len(tracks)) if i != STATE["track_index"]] or list(range(len(tracks)))
            index = random.choice(choices)
    STATE["track_index"] = index
    track = tracks[index]
    print(f"MenuOS Now Playing: {{track.get('song') or track.get('name')}} - {{track.get('artist')}}")
    device = _audio_device()
    if device is None:
        return
    try:
        if AUDIO_HANDLE:
            AUDIO_HANDLE.stop()
        sound = aud.Sound.file(track.get("filepath"))
        AUDIO_HANDLE = device.play(sound)
        AUDIO_HANDLE.volume = float(track.get("volume", 1.0))
    except Exception as exc:
        print("MenuOS audio playback failed:", exc)


def _advance_boot(data):
    screens = [screen for screen in data.get("screens", []) if screen.get("type") != "MAIN_MENU"]
    if STATE["boot_index"] >= len(screens):
        return True
    current = screens[STATE["boot_index"]]
    if current.get("type") == "PRESS_START":
        if _pressed(events.SPACEKEY) or _pressed(events.ENTERKEY) or _pressed(events.AKEY):
            STATE["boot_index"] += 1
        return False
    duration = float(current.get("duration", 0.0))
    STATE["boot_timer"] += 1.0 / max(1.0, logic.getAverageFrameRate())
    if duration <= 0.0 or STATE["boot_timer"] >= duration or (current.get("skippable") and _pressed(events.SPACEKEY)):
        STATE["boot_index"] += 1
        STATE["boot_timer"] = 0.0
    return False


def _activate_item(data, item):
    action = item.get("action")
    if action == "OPEN_SUBMENU" or action == "OPTIONS":
        STATE["active_page"] = item.get("target_menu") or item.get("label") or "Options"
        STATE["focus_index"] = 0
    elif action == "BACK":
        STATE["active_page"] = "MainMenu"
        STATE["focus_index"] = 0
    elif action == "QUIT":
        logic.endGame()
    elif action == "START_GAME":
        target = item.get("target_menu") or "Game"
        try:
            logic.startGame(target)
        except Exception:
            print("MenuOS START_GAME:", target)
    else:
        print("MenuOS action:", action, item.get("label"))


def main():
    if logic is None:
        return
    data = _config()
    if not STATE["initialized"]:
        STATE["initialized"] = True
        _switch_background_scene(data)
        _setup_scene_window(data)
        _setup_background_video(data)
        if data.get("soundtrack", {{}}).get("enabled"):
            _play_track(data)

    _refresh_background_video()

    if not _advance_boot(data):
        return

    items = _active_items(data)
    if not items:
        return

    changed = False
    if _pressed(events.DOWNARROWKEY) or _pressed(events.SKEY):
        STATE["focus_index"] = (STATE["focus_index"] + 1) % len(items)
        changed = True
    elif _pressed(events.UPARROWKEY) or _pressed(events.WKEY):
        STATE["focus_index"] = (STATE["focus_index"] - 1) % len(items)
        changed = True

    focused = items[STATE["focus_index"]]
    if changed:
        _switch_background_scene(data, focused)
    _apply_focus_visuals(data)

    if _pressed(events.ENTERKEY) or _pressed(events.SPACEKEY):
        _activate_item(data, focused)
    if _pressed(events.NKEY):
        _play_track(data)
'''


class AGMF_MenuItem(PropertyGroup):
    name: StringProperty(name="Item Name", default="NewItem", update=live_update_callback)
    label: StringProperty(name="Label", default="New Item", update=live_update_callback)
    description: StringProperty(name="Sub Description", default="", update=live_update_callback)
    show_description: BoolProperty(name="Show Description", default=False, update=live_update_callback)
    item_type: EnumProperty(name="Type", items=MENU_ITEM_TYPES, default="BUTTON", update=live_update_callback)
    action: EnumProperty(name="Action", items=ACTION_TYPES, default="NONE", update=live_update_callback)
    target_menu: StringProperty(name="Target Menu", default="", update=live_update_callback)
    preview_state: EnumProperty(name="Preview State", items=STATE_TYPES, default="IDLE", update=live_update_callback)
    base_scale: FloatProperty(name="Base Scale", default=1.0, min=0.1, max=10.0, update=live_update_callback)
    page: StringProperty(name="Page", default="MainMenu", update=live_update_callback)
    panel: StringProperty(name="Panel / Group", default="Main Options", update=live_update_callback)
    pos_x: FloatProperty(name="X", default=-5.4, min=-100.0, max=100.0, update=live_update_callback)
    pos_y: FloatProperty(name="Y", default=3.0, min=-100.0, max=100.0, update=live_update_callback)
    depth_y: FloatProperty(name="Depth", default=0.0, min=-100.0, max=100.0, update=live_update_callback)
    width: FloatProperty(name="Width", default=3.4, min=0.01, max=100.0, update=live_update_callback)
    height: FloatProperty(name="Height", default=0.55, min=0.01, max=100.0, update=live_update_callback)
    fill_type: EnumProperty(name="Fill", items=FILL_TYPES, default="COLOR_RAMP", update=live_update_callback)
    fill_color: FloatVectorProperty(name="Fill Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.45, 0.02, 0.02, 0.92), update=live_update_callback)
    ramp_color_a: FloatVectorProperty(name="Ramp A", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.04, 0.0, 0.0, 0.88), update=live_update_callback)
    ramp_color_b: FloatVectorProperty(name="Ramp B", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.65, 0.02, 0.01, 0.96), update=live_update_callback)
    ramp_direction: EnumProperty(name="Ramp Direction", items=RAMP_DIRECTION_TYPES, default="HORIZONTAL", update=live_update_callback)
    ramp_offset_x: FloatProperty(name="Ramp Offset X", default=0.0, min=-10.0, max=10.0, update=live_update_callback)
    ramp_offset_y: FloatProperty(name="Ramp Offset Y", default=0.0, min=-10.0, max=10.0, update=live_update_callback)
    focus_fill_color: FloatVectorProperty(name="Focus Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.75, 0.03, 0.02, 0.98), update=live_update_callback)
    press_fill_color: FloatVectorProperty(name="Press Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.95, 0.72, 0.18, 1.0), update=live_update_callback)
    media_path: StringProperty(name="Media Path", subtype="FILE_PATH", default="", update=live_update_callback)
    use_border: BoolProperty(name="Use Border", default=True, update=live_update_callback)
    border_thickness: FloatProperty(name="Border Thickness", default=0.04, min=0.0, max=5.0, update=live_update_callback)
    border_fill_type: EnumProperty(name="Border Fill", items=[("COLOR", "Color", ""), ("COLOR_RAMP", "Color Ramp", "")], default="COLOR", update=live_update_callback)
    border_color: FloatVectorProperty(name="Border Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.9, 0.65, 0.22, 1.0), update=live_update_callback)
    border_ramp_color_a: FloatVectorProperty(name="Border Ramp A", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.15, 0.10, 0.03, 1.0), update=live_update_callback)
    border_ramp_color_b: FloatVectorProperty(name="Border Ramp B", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 0.74, 0.25, 1.0), update=live_update_callback)
    text_color: FloatVectorProperty(name="Text Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=live_update_callback)
    text_font: StringProperty(name="Font", subtype="FILE_PATH", default="", update=live_update_callback)
    text_kerning: FloatProperty(name="Kerning", default=1.0, min=0.0, max=10.0, update=live_update_callback)
    text_size: FloatProperty(name="Text Size", default=0.36, min=0.01, max=10.0, update=live_update_callback)
    text_align_x: EnumProperty(name="Text Align X", items=TEXT_ALIGN_X_TYPES, default="LEFT", update=live_update_callback)
    text_align_y: EnumProperty(name="Text Align Y", items=TEXT_ALIGN_Y_TYPES, default="CENTER", update=live_update_callback)
    text_padding_x: FloatProperty(name="Text Padding X", default=0.18, min=-10.0, max=10.0, update=live_update_callback)
    text_padding_y: FloatProperty(name="Text Padding Y", default=0.0, min=-10.0, max=10.0, update=live_update_callback)
    container_padding_x: FloatProperty(name="Container Pad X", default=0.18, min=0.0, max=10.0, update=live_update_callback)
    container_padding_y: FloatProperty(name="Container Pad Y", default=0.08, min=0.0, max=10.0, update=live_update_callback)
    margin_top: FloatProperty(name="Margin Top", default=0.0, min=0.0, max=10.0, update=live_update_callback)
    margin_bottom: FloatProperty(name="Margin Bottom", default=0.12, min=0.0, max=10.0, update=live_update_callback)
    description_gap: FloatProperty(name="Description Gap", default=0.22, min=0.0, max=10.0, update=live_update_callback)
    description_scale: FloatProperty(name="Description Size", default=0.32, min=0.01, max=10.0, update=live_update_callback)
    description_color: FloatVectorProperty(name="Description Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.78, 0.78, 0.78, 1.0), update=live_update_callback)
    focus_animation: EnumProperty(name="Focus Animation", items=ANIMATION_TYPES, default="SCALE_PULSE", update=live_update_callback)
    press_animation: EnumProperty(name="Press Animation", items=ANIMATION_TYPES, default="SHAKE", update=live_update_callback)
    show_advanced: BoolProperty(name="Advanced", default=False)


class AGMF_MenuPanel(PropertyGroup):
    name: StringProperty(name="Panel Name", default="Main Options", update=panel_live_update_callback)
    page: StringProperty(name="Page", default="MainMenu", update=panel_live_update_callback)
    offset_x: FloatProperty(name="Offset X", default=0.0, min=-100.0, max=100.0, update=panel_live_update_callback)
    offset_y: FloatProperty(name="Offset Y", default=0.0, min=-100.0, max=100.0, update=panel_live_update_callback)
    depth_y: FloatProperty(name="Depth", default=0.0, min=-100.0, max=100.0, update=panel_live_update_callback)
    visible: BoolProperty(name="Visible", default=True, update=panel_live_update_callback)
    locked: BoolProperty(name="Locked", default=False)
    option_spacing: FloatProperty(name="Option Spacing", default=0.48, min=0.0, max=20.0, update=panel_live_update_callback)
    option_width: FloatProperty(name="Option Width", default=3.25, min=0.01, max=100.0, update=panel_live_update_callback)
    option_height: FloatProperty(name="Option Height", default=0.38, min=0.01, max=100.0, update=panel_live_update_callback)
    layout_align_x: EnumProperty(name="Layout Align", items=LAYOUT_ALIGN_X_TYPES, default="LEFT", update=panel_live_update_callback)
    layout_margin_x: FloatProperty(name="Layout Margin X", default=1.0, min=0.0, max=100.0, update=panel_live_update_callback)
    align_x: FloatProperty(name="Align X", default=-5.4, min=-100.0, max=100.0, update=panel_live_update_callback)
    start_y: FloatProperty(name="Start Y", default=4.15, min=-100.0, max=100.0, update=panel_live_update_callback)
    batch_fill_type: EnumProperty(name="Batch Fill", items=FILL_TYPES, default="COLOR_RAMP", update=panel_live_update_callback)
    batch_ramp_color_a: FloatVectorProperty(name="Batch Ramp A", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.04, 0.0, 0.0, 0.88), update=panel_live_update_callback)
    batch_ramp_color_b: FloatVectorProperty(name="Batch Ramp B", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.65, 0.02, 0.01, 0.96), update=panel_live_update_callback)
    batch_ramp_offset_x: FloatProperty(name="Batch Ramp Offset X", default=0.0, min=-10.0, max=10.0, update=panel_live_update_callback)
    batch_ramp_offset_y: FloatProperty(name="Batch Ramp Offset Y", default=0.0, min=-10.0, max=10.0, update=panel_live_update_callback)
    batch_fill_color: FloatVectorProperty(name="Batch Fill Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.45, 0.02, 0.02, 0.92), update=panel_live_update_callback)
    batch_focus_color: FloatVectorProperty(name="Batch Focus Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.75, 0.03, 0.02, 0.98), update=panel_live_update_callback)
    batch_press_color: FloatVectorProperty(name="Batch Press Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.95, 0.72, 0.18, 1.0), update=panel_live_update_callback)
    batch_text_color: FloatVectorProperty(name="Batch Text Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=panel_live_update_callback)
    batch_text_font: StringProperty(name="Batch Font", subtype="FILE_PATH", default="", update=panel_live_update_callback)
    batch_text_kerning: FloatProperty(name="Batch Kerning", default=1.0, min=0.0, max=10.0, update=panel_live_update_callback)
    batch_text_size: FloatProperty(name="Batch Text Size", default=0.36, min=0.01, max=10.0, update=panel_live_update_callback)
    batch_text_align_x: EnumProperty(name="Batch Text Align X", items=TEXT_ALIGN_X_TYPES, default="LEFT", update=panel_live_update_callback)
    batch_text_align_y: EnumProperty(name="Batch Text Align Y", items=TEXT_ALIGN_Y_TYPES, default="CENTER", update=panel_live_update_callback)
    batch_text_padding_x: FloatProperty(name="Batch Text Pad X", default=0.18, min=-10.0, max=10.0, update=panel_live_update_callback)
    batch_text_padding_y: FloatProperty(name="Batch Text Pad Y", default=0.0, min=-10.0, max=10.0, update=panel_live_update_callback)
    batch_container_padding_x: FloatProperty(name="Batch Container Pad X", default=0.18, min=0.0, max=10.0, update=panel_live_update_callback)
    batch_container_padding_y: FloatProperty(name="Batch Container Pad Y", default=0.08, min=0.0, max=10.0, update=panel_live_update_callback)
    batch_margin_top: FloatProperty(name="Batch Margin Top", default=0.0, min=0.0, max=10.0, update=panel_live_update_callback)
    batch_margin_bottom: FloatProperty(name="Batch Margin Bottom", default=0.12, min=0.0, max=10.0, update=panel_live_update_callback)
    batch_show_description: BoolProperty(name="Batch Show Descriptions", default=False, update=panel_live_update_callback)
    batch_description_gap: FloatProperty(name="Batch Description Gap", default=0.22, min=0.0, max=10.0, update=panel_live_update_callback)
    batch_description_scale: FloatProperty(name="Batch Description Size", default=0.32, min=0.01, max=10.0, update=panel_live_update_callback)
    batch_description_color: FloatVectorProperty(name="Batch Description Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.78, 0.78, 0.78, 1.0), update=panel_live_update_callback)


class AGMF_MenuScreen(PropertyGroup):
    name: StringProperty(name="Screen Name", default="NewScreen")
    screen_type: EnumProperty(name="Type", items=SCREEN_TYPES, default="SUBMENU")
    target_page: StringProperty(name="Target Page", default="MainMenu")
    media_path: StringProperty(name="Media", subtype="FILE_PATH", default="")
    scene: StringProperty(name="Scene Name", default="")
    duration: FloatProperty(name="Duration", default=3.0, min=0.0, max=3600.0)
    skippable: BoolProperty(name="Skippable", default=True)
    enabled: BoolProperty(name="Enabled", default=True)


class AGMF_LiveSceneSlot(PropertyGroup):
    name: StringProperty(name="Slot Name", default="LiveScene")
    scene: StringProperty(name="Scene Name", default="")
    trigger_item: StringProperty(name="Trigger Item", default="")
    weight: FloatProperty(name="Weight", default=1.0, min=0.0, max=100.0)
    enabled: BoolProperty(name="Enabled", default=True)


class AGMF_BackgroundMediaLayer(PropertyGroup):
    name: StringProperty(name="Layer Name", default="Background Layer", update=live_update_callback)
    enabled: BoolProperty(name="Enabled", default=True, update=live_update_callback)
    layer_type: EnumProperty(name="Type", items=BACKGROUND_LAYER_TYPES, default="IMAGE", update=live_update_callback)
    layer_use: EnumProperty(name="Use As", items=BACKGROUND_LAYER_USE_TYPES, default="BACKGROUND", update=live_update_callback)
    filepath: StringProperty(name="Image / Video", subtype="FILE_PATH", default="", update=live_update_callback)
    scene_window: bpy.props.PointerProperty(type=bpy.types.Scene, name="Scene Window", update=live_update_callback)
    width: FloatProperty(name="Width", default=16.0, min=0.01, max=1000.0, update=live_update_callback)
    height: FloatProperty(name="Height", default=9.0, min=0.01, max=1000.0, update=live_update_callback)
    move_x: FloatProperty(name="Move X", default=0.0, min=-1000.0, max=1000.0, update=live_update_callback)
    move_y: FloatProperty(name="Move Y / Depth", default=0.0, min=-1000.0, max=1000.0, update=live_update_callback)
    move_z: FloatProperty(name="Move Z", default=0.0, min=-1000.0, max=1000.0, update=live_update_callback)
    fit_mode: EnumProperty(name="Fit", items=BACKGROUND_FIT_TYPES, default="STRETCH", update=live_update_callback)
    map_zoom: FloatProperty(name="Texture Zoom", default=1.0, min=0.001, max=100.0, update=live_update_callback)
    map_scale_x: FloatProperty(name="Texture Scale X", default=1.0, min=0.001, max=100.0, update=live_update_callback)
    map_scale_y: FloatProperty(name="Texture Scale Y", default=1.0, min=0.001, max=100.0, update=live_update_callback)
    map_scale_z: FloatProperty(name="Texture Scale Z", default=1.0, min=0.001, max=100.0, update=live_update_callback)
    map_offset_x: FloatProperty(name="Texture Move X", default=0.0, min=-100.0, max=100.0, update=live_update_callback)
    map_offset_y: FloatProperty(name="Texture Move Y", default=0.0, min=-100.0, max=100.0, update=live_update_callback)
    map_offset_z: FloatProperty(name="Texture Move Z", default=0.0, min=-100.0, max=100.0, update=live_update_callback)
    map_rotation: FloatProperty(name="Texture Rotation", default=0.0, subtype="ANGLE", update=live_update_callback)
    opacity: FloatProperty(name="Opacity", default=1.0, min=0.0, max=1.0, update=live_update_callback)
    tint_color: FloatVectorProperty(name="Tint", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=live_update_callback)
    frame_start: IntProperty(name="Start Frame", default=1, min=1, update=live_update_callback)
    duration_mode: EnumProperty(name="Duration", items=BACKGROUND_DURATION_TYPES, default="AUTO", update=live_update_callback)
    auto_duration: FloatProperty(name="Auto Duration", default=0.0, min=0.0, update=live_update_callback)
    custom_duration: FloatProperty(name="Custom Duration", default=5.0, min=0.0, max=36000.0, update=live_update_callback)
    transition_in: FloatProperty(name="Transition In", default=0.35, min=0.0, max=120.0, update=live_update_callback)
    transition_out: FloatProperty(name="Transition Out", default=0.35, min=0.0, max=120.0, update=live_update_callback)


class AGMF_SoundtrackTrack(PropertyGroup):
    name: StringProperty(name="Track Name", default="New Track")
    sound: bpy.props.PointerProperty(type=bpy.types.Sound, name="Audio File")
    filepath: StringProperty(name="Filepath", subtype="FILE_PATH", default="")
    song_title: StringProperty(name="Song", default="")
    artist: StringProperty(name="Artist", default="")
    album: StringProperty(name="Album", default="")
    album_art_path: StringProperty(name="Album Art", subtype="FILE_PATH", default="")
    track_number: IntProperty(name="Track #", default=1, min=1)
    enabled: BoolProperty(name="Enabled", default=True)
    show_in_soundtrack_page: BoolProperty(name="Show On Page", default=True)
    volume: FloatProperty(name="Volume", default=1.0, min=0.0, max=2.0)
    fade_in: FloatProperty(name="Fade In", default=0.25, min=0.0, max=30.0)
    fade_out: FloatProperty(name="Fade Out", default=0.5, min=0.0, max=30.0)



def get_widget_preset_filepath():
    import os
    import bpy
    user_dir = bpy.utils.user_resource('SCRIPTS', path="presets")
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "agmf_now_playing_presets.json")

def get_widget_presets():
    import json
    import os
    filepath = get_widget_preset_filepath()
    presets = [("DEFAULT", "Default", ""), ("SLEEK", "Sleek Bottom", ""), ("CORNER", "Corner Card", "")]
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                for name in data.keys():
                    presets.append((name, name, ""))
        except: pass
    return presets

def apply_widget_preset(self, context):
    import json
    import os
    preset = self.active_preset

    # Built-in presets
    data = None
    if preset == "DEFAULT":
        data = {"pos_x": 6.0, "pos_y": -4.0, "width": 4.0, "height": 1.0, "fade_in": 0.5, "fade_out": 0.5, "slide_dir": "UP", "slide_dist": 0.5, "fill_type": "COLOR_RAMP", "fill_color": [0.05, 0.05, 0.05, 0.8], "ramp_color_a": [0.04, 0.0, 0.0, 0.88], "ramp_color_b": [0.65, 0.02, 0.01, 0.0], "ramp_direction": "HORIZONTAL", "ramp_offset_x": 0.0, "ramp_offset_y": 0.0, "show_artwork": True, "artwork_size": 0.8, "artwork_offset_x": -1.4, "artwork_offset_y": 0.0, "title_size": 0.3, "title_color": [1.0, 1.0, 1.0, 1.0], "title_offset_x": -0.8, "title_offset_y": 0.15, "artist_size": 0.2, "artist_color": [0.7, 0.7, 0.7, 1.0], "artist_offset_x": -0.8, "artist_offset_y": -0.2}
    elif preset == "SLEEK":
        data = {"pos_x": 0.0, "pos_y": -4.5, "width": 10.0, "height": 0.8, "fade_in": 0.8, "fade_out": 0.8, "slide_dir": "UP", "slide_dist": 1.0, "fill_type": "COLOR_RAMP", "fill_color": [0.0, 0.0, 0.0, 0.8], "ramp_color_a": [0.0, 0.0, 0.0, 0.9], "ramp_color_b": [0.0, 0.0, 0.0, 0.0], "ramp_direction": "VERTICAL", "ramp_offset_x": 0.0, "ramp_offset_y": -0.5, "show_artwork": False, "artwork_size": 0.8, "artwork_offset_x": -1.4, "artwork_offset_y": 0.0, "title_size": 0.35, "title_color": [1.0, 1.0, 1.0, 1.0], "title_offset_x": -4.0, "title_offset_y": 0.0, "artist_size": 0.25, "artist_color": [0.8, 0.8, 0.8, 1.0], "artist_offset_x": 2.0, "artist_offset_y": 0.0}
    elif preset == "CORNER":
        data = {"pos_x": -6.5, "pos_y": 3.5, "width": 3.0, "height": 1.5, "fade_in": 0.3, "fade_out": 0.3, "slide_dir": "RIGHT", "slide_dist": 0.8, "fill_type": "COLOR", "fill_color": [0.1, 0.1, 0.15, 0.85], "ramp_color_a": [0.04, 0.0, 0.0, 0.88], "ramp_color_b": [0.65, 0.02, 0.01, 0.0], "ramp_direction": "HORIZONTAL", "ramp_offset_x": 0.0, "ramp_offset_y": 0.0, "show_artwork": True, "artwork_size": 1.2, "artwork_offset_x": 0.0, "artwork_offset_y": 0.0, "title_size": 0.25, "title_color": [1.0, 1.0, 1.0, 1.0], "title_offset_x": 0.0, "title_offset_y": -1.0, "artist_size": 0.18, "artist_color": [0.7, 0.7, 0.7, 1.0], "artist_offset_x": 0.0, "artist_offset_y": -1.3}
    else:
        filepath = get_widget_preset_filepath()
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    all_presets = json.load(f)
                    if preset in all_presets:
                        data = all_presets[preset]
            except: pass

    if data:
        for k, v in data.items():
            try: setattr(self, k, v)
            except: pass
        request_live_rebuild()


class AGMF_NowPlayingWidget(PropertyGroup):
    pos_x: FloatProperty(name="Pos X", default=6.0, min=-100.0, max=100.0, update=live_update_callback)
    pos_y: FloatProperty(name="Pos Y", default=-4.0, min=-100.0, max=100.0, update=live_update_callback)
    width: FloatProperty(name="Width", default=4.0, min=0.1, max=100.0, update=live_update_callback)
    height: FloatProperty(name="Height", default=1.0, min=0.1, max=100.0, update=live_update_callback)

    fade_in: FloatProperty(name="Fade In Speed", default=0.5, min=0.0, max=10.0)
    fade_out: FloatProperty(name="Fade Out Speed", default=0.5, min=0.0, max=10.0)
    slide_dir: EnumProperty(name="Slide Direction", items=[("UP", "Up", ""), ("DOWN", "Down", ""), ("LEFT", "Left", ""), ("RIGHT", "Right", ""), ("NONE", "None", "")], default="UP")
    slide_dist: FloatProperty(name="Slide Distance", default=0.5, min=0.0, max=10.0)

    fill_type: EnumProperty(name="Background Fill", items=FILL_TYPES, default="COLOR_RAMP", update=live_update_callback)
    fill_color: FloatVectorProperty(name="Fill Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.05, 0.05, 0.05, 0.8), update=live_update_callback)
    ramp_color_a: FloatVectorProperty(name="Ramp A", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.04, 0.0, 0.0, 0.88), update=live_update_callback)
    ramp_color_b: FloatVectorProperty(name="Ramp B", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.65, 0.02, 0.01, 0.0), update=live_update_callback)
    ramp_direction: EnumProperty(name="Ramp Direction", items=RAMP_DIRECTION_TYPES, default="HORIZONTAL", update=live_update_callback)
    ramp_offset_x: FloatProperty(name="Ramp Offset X", default=0.0, min=-10.0, max=10.0, update=live_update_callback)
    ramp_offset_y: FloatProperty(name="Ramp Offset Y", default=0.0, min=-10.0, max=10.0, update=live_update_callback)

    show_artwork: BoolProperty(name="Show Album Art", default=True, update=live_update_callback)
    artwork_size: FloatProperty(name="Artwork Size", default=0.8, min=0.1, max=10.0, update=live_update_callback)
    artwork_offset_x: FloatProperty(name="Artwork Offset X", default=-1.4, min=-10.0, max=10.0, update=live_update_callback)
    artwork_offset_y: FloatProperty(name="Artwork Offset Y", default=0.0, min=-10.0, max=10.0, update=live_update_callback)

    title_size: FloatProperty(name="Title Size", default=0.3, min=0.05, max=5.0, update=live_update_callback)
    title_color: FloatVectorProperty(name="Title Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0), update=live_update_callback)
    title_offset_x: FloatProperty(name="Title Offset X", default=-0.8, min=-10.0, max=10.0, update=live_update_callback)
    title_offset_y: FloatProperty(name="Title Offset Y", default=0.15, min=-10.0, max=10.0, update=live_update_callback)

    artist_size: FloatProperty(name="Artist Size", default=0.2, min=0.05, max=5.0, update=live_update_callback)
    artist_color: FloatVectorProperty(name="Artist Color", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.7, 0.7, 0.7, 1.0), update=live_update_callback)
    artist_offset_x: FloatProperty(name="Artist Offset X", default=-0.8, min=-10.0, max=10.0, update=live_update_callback)
    artist_offset_y: FloatProperty(name="Artist Offset Y", default=-0.2, min=-10.0, max=10.0, update=live_update_callback)

    preset_name: StringProperty(name="Preset Name", default="My Preset")
    active_preset: EnumProperty(name="Preset", items=lambda self, context: get_widget_presets(), update=apply_widget_preset)

class AGMF_OT_SaveWidgetPreset(Operator):
    bl_idname = "agmf.save_widget_preset"
    bl_label = "Save Preset"

    def execute(self, context):
        import json
        import os
        props = context.scene.agmf_props.now_playing_widget
        name = props.preset_name
        if not name: return {'CANCELLED'}

        data = {
            "pos_x": props.pos_x, "pos_y": props.pos_y, "width": props.width, "height": props.height,
            "fade_in": props.fade_in, "fade_out": props.fade_out, "slide_dir": props.slide_dir, "slide_dist": props.slide_dist,
            "fill_type": props.fill_type, "fill_color": list(props.fill_color),
            "ramp_color_a": list(props.ramp_color_a), "ramp_color_b": list(props.ramp_color_b),
            "ramp_direction": props.ramp_direction, "ramp_offset_x": props.ramp_offset_x, "ramp_offset_y": props.ramp_offset_y,
            "show_artwork": props.show_artwork, "artwork_size": props.artwork_size, "artwork_offset_x": props.artwork_offset_x, "artwork_offset_y": props.artwork_offset_y,
            "title_size": props.title_size, "title_color": list(props.title_color), "title_offset_x": props.title_offset_x, "title_offset_y": props.title_offset_y,
            "artist_size": props.artist_size, "artist_color": list(props.artist_color), "artist_offset_x": props.artist_offset_x, "artist_offset_y": props.artist_offset_y,
        }

        filepath = get_widget_preset_filepath()
        all_presets = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    all_presets = json.load(f)
            except: pass

        all_presets[name] = data
        with open(filepath, 'w') as f:
            json.dump(all_presets, f)

        self.report({'INFO'}, f"Saved widget preset '{name}'")
        return {'FINISHED'}

class AGMF_OT_DeleteWidgetPreset(Operator):
    bl_idname = "agmf.delete_widget_preset"
    bl_label = "Delete Preset"

    def execute(self, context):
        import json
        import os
        props = context.scene.agmf_props.now_playing_widget
        name = props.active_preset
        if name in ["DEFAULT", "SLEEK", "CORNER"]:
            self.report({'WARNING'}, "Cannot delete built-in presets")
            return {'CANCELLED'}

        filepath = get_widget_preset_filepath()
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    all_presets = json.load(f)
                if name in all_presets:
                    del all_presets[name]
                    with open(filepath, 'w') as f:
                        json.dump(all_presets, f)
                    self.report({'INFO'}, f"Deleted preset '{name}'")
                    props.active_preset = "DEFAULT"
            except: pass

        return {'FINISHED'}


class AGMF_Properties(PropertyGroup):
    now_playing_widget: PointerProperty(type=AGMF_NowPlayingWidget)
    live_edit: BoolProperty(name="Live Edit", default=True)
    menu_name: StringProperty(name="Menu Name", default="MainMenu", update=live_update_callback)
    menu_root_name: StringProperty(name="Root Name", default="")
    target_mode: EnumProperty(
        name="Target",
        items=[
            ("BLENDER", "Blender Preview", "Build and preview in Blender"),
            ("UPBGE", "UPBGE Ready", "Prepare the menu for UPBGE logic"),
            ("BOTH", "Blender + UPBGE", "Support both workflows"),
        ],
        default="BOTH",
    )
    layout_mode: EnumProperty(name="Layout", items=LAYOUT_TYPES, default="FREEFORM", update=live_update_callback)
    theme_preset: EnumProperty(name="Theme", items=THEME_TYPES, default="LOW_BUDGET", update=live_update_callback)
    camera_style: EnumProperty(
        name="Camera Style",
        items=[
            ("STATIC", "Static", "Simple camera framing"),
            ("DRIFT", "Cinematic Drift", "Subtle camera movement"),
            ("ZOOM", "Dramatic Zoom", "Push-in feel"),
            ("ORBIT", "Orbit", "Orbit-style presentation"),
        ],
        default="STATIC",
        update=live_update_callback,
    )
    item_spacing: FloatProperty(name="Item Spacing", default=0.9, min=0.1, max=5.0, update=live_update_callback)
    grid_columns: IntProperty(name="Grid Columns", default=2, min=1, max=12, update=live_update_callback)
    radial_radius: FloatProperty(name="Radial Radius", default=2.0, min=0.1, max=20.0, update=live_update_callback)
    radial_offset: FloatProperty(name="Radial Offset", default=0.0, subtype="ANGLE", update=live_update_callback)
    auto_build_backdrop: BoolProperty(name="Use Backdrop", default=True, update=live_update_callback)
    add_default_items: BoolProperty(name="Add Starter Items", default=True)
    background_type: EnumProperty(name="Background Type", items=BACKGROUND_TYPES, default="HYBRID", update=live_update_callback)
    background_media_path: StringProperty(name="Media", subtype="FILE_PATH", default="", update=live_update_callback)
    background_sequence_folder: StringProperty(name="Sequence Folder", subtype="DIR_PATH", default="", update=live_update_callback)
    background_scene: bpy.props.PointerProperty(type=bpy.types.Scene, name="Live Scene", update=background_scene_update_callback)
    background_scene_camera: bpy.props.PointerProperty(type=bpy.types.Object, name="Scene Window Camera", update=live_update_callback)
    scene_rotation_mode: EnumProperty(
        name="Scene Switching",
        items=[
            ("STATIC", "Static", "Use one scene"),
            ("ON_NAV", "On Navigation", "Switch live scenes when menu focus changes"),
            ("RANDOM", "Random", "Choose a scene randomly"),
            ("SEQUENTIAL", "Sequential", "Cycle through scene slots in order"),
        ],
        default="ON_NAV",
        update=live_update_callback,
    )
    bg_color_a: FloatVectorProperty(name="BG Color A", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.0, 0.0, 0.0, 1.0), update=live_update_callback)
    bg_color_b: FloatVectorProperty(name="BG Color B", subtype="COLOR", size=4, min=0.0, max=1.0, default=(0.35, 0.02, 0.02, 1.0), update=live_update_callback)
    background_canvas_width: FloatProperty(name="Canvas Width", default=16.0, min=0.01, max=1000.0, update=live_update_callback)
    background_canvas_height: FloatProperty(name="Canvas Height", default=9.0, min=0.01, max=1000.0, update=live_update_callback)
    background_layers: CollectionProperty(type=AGMF_BackgroundMediaLayer)
    background_layers_index: IntProperty(default=0)
    logo_path: StringProperty(name="Game Logo", subtype="FILE_PATH", default="", update=live_update_callback)
    account_enabled: BoolProperty(name="Account HUD", default=True, update=live_update_callback)
    account_name: StringProperty(name="Account Name", default="NEVERFALLDOWN", update=live_update_callback)
    account_value: StringProperty(name="Account Value", default="163,403,230", update=live_update_callback)
    screens: CollectionProperty(type=AGMF_MenuScreen)
    screens_index: IntProperty(default=0)
    live_scenes: CollectionProperty(type=AGMF_LiveSceneSlot)
    live_scenes_index: IntProperty(default=0)
    soundtrack_enabled: BoolProperty(name="Soundtrack Enabled", default=True)
    soundtrack_order: EnumProperty(name="Playback Order", items=PLAYBACK_ORDER_TYPES, default="SHUFFLE")
    soundtrack_loop: BoolProperty(name="Loop Playlist", default=True)
    show_now_playing: BoolProperty(name="Show Track Info", default=True)
    now_playing_duration: FloatProperty(name="Info Duration", default=4.0, min=0.0, max=60.0)
    runtime_script_path: StringProperty(name="Runtime Script Path", subtype="FILE_PATH", default="")
    config_json_path: StringProperty(name="Config JSON Path", subtype="FILE_PATH", default="")
    active_runtime_scene: StringProperty(name="Active Runtime Scene", default="")
    video_preview_frame_start: IntProperty(name="Video Start Frame", default=1, min=1)
    panels: CollectionProperty(type=AGMF_MenuPanel)
    panels_index: IntProperty(default=0)
    soundtrack_tracks: CollectionProperty(type=AGMF_SoundtrackTrack)
    soundtrack_tracks_index: IntProperty(default=0)
    menu_items: CollectionProperty(type=AGMF_MenuItem)
    menu_items_index: IntProperty(default=0)
    preview_text: StringProperty(name="Preview Output", default="")
    theme_tint: FloatVectorProperty(
        name="Theme Tint",
        subtype="COLOR",
        size=3,
        min=0.0,
        max=1.0,
        default=(0.9, 0.9, 0.9),
    )


class AGMF_UL_MenuItems(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.45)
        split.label(text=item.label or item.name, icon="FONT_DATA")
        row = split.row(align=True)
        row.label(text=item.item_type)
        row.label(text=item.preview_state)


class AGMF_UL_MenuPanels(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "visible", text="")
        row.label(text=item.name, icon="GROUP")
        row.label(text=f"X {item.offset_x:.2f}  Y {item.offset_y:.2f}")
        row.prop(item, "locked", text="", icon="LOCKED" if item.locked else "UNLOCKED")


class AGMF_UL_MenuScreens(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.label(text=item.name, icon="SEQ_STRIP_META")
        row.label(text=item.screen_type)
        row.label(text=f"{item.duration:.1f}s")


class AGMF_UL_LiveSceneSlots(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.label(text=item.name, icon="SCENE_DATA")
        row.label(text=item.scene or "No scene")
        if item.trigger_item:
            row.label(text=item.trigger_item, icon="DRIVER")


class AGMF_UL_BackgroundMediaLayers(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")
        row.label(text=item.name, icon="IMAGE_DATA" if item.layer_type == "IMAGE" else "FILE_MOVIE")
        row.label(text=item.layer_use)
        duration = item.auto_duration if item.duration_mode == "AUTO" else item.custom_duration
        row.label(text=f"{duration:.2f}s")


class AGMF_UL_SoundtrackTracks(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)

        # Display the custom cover art icon if available
        custom_icon = get_track_icon_id(item.album_art_path) if getattr(item, "album_art_path", "") else 0
        if custom_icon:
            row.template_icon(icon_value=custom_icon, scale=2.5)
        else:
            row.label(text="", icon="DISC")

        col = row.column()
        title = item.song_title or item.name or "Unnamed Track"
        col.label(text=f"{item.track_number}. {title}")
        col.label(text=f"{item.artist} | {item.album}")

        row.prop(item, "enabled", text="")
        row.prop(item, "volume", text="Vol", slider=True)


class AGMF_OT_CreateMenuRoot(Operator):
    bl_idname = "agmf.create_menu_root"
    bl_label = "Create Game Menu"
    bl_description = "Create a menu root, collection, camera, and starter items"

    def execute(self, context):
        scene = context.scene
        props = scene.agmf_props
        root_name = f"AGMF_{props.menu_name}"

        root = bpy.data.objects.get(root_name)
        if root is None:
            root = bpy.data.objects.new(root_name, None)
            root.empty_display_type = "PLAIN_AXES"
            root.empty_display_size = 1.2
            ensure_collection(scene, menu_collection_name(root_name)).objects.link(root)

        root["agmf_role"] = "MENU_ROOT"
        root["agmf_target_mode"] = props.target_mode
        root.location = (0.0, 0.0, 0.0)
        props.menu_root_name = root.name
        props.layout_mode = "FREEFORM"

        if not props.panels:
            panel = props.panels.add()
            panel.name = "Main Options"
            panel.page = "MainMenu"
            panel.align_x = -props.background_canvas_width * 0.34
            panel.start_y = props.background_canvas_height * 0.46
            panel.align_x = -props.background_canvas_width * 0.34
            panel.start_y = props.background_canvas_height * 0.46

        if props.add_default_items and not props.menu_items:
            defaults = [
                ("Start", "START_GAME"),
                ("Options", "OPTIONS"),
                ("Quit", "QUIT"),
            ]
            for label, action in defaults:
                item = props.menu_items.add()
                item.name = label.replace(" ", "")
                item.label = label
                item.action = action
            props.menu_items[0].label = "FIGHT NOW"
            props.menu_items[0].width = 4.2
            props.menu_items[0].height = 0.75
            for idx, item in enumerate(props.menu_items):
                item.panel = "Main Options"
                item.pos_x = -props.background_canvas_width * 0.34
                item.pos_y = props.background_canvas_height * 0.46 - (idx * 0.72)

        if not props.screens:
            for name, screen_type, duration in [
                ("Company Logo", "INTRO_LOGO", 2.5),
                ("Press Any Button", "PRESS_START", 0.0),
                ("Main Menu", "MAIN_MENU", 0.0),
            ]:
                screen = props.screens.add()
                screen.name = name
                screen.screen_type = screen_type
                screen.duration = duration
                screen.target_page = "MainMenu"

        background_parent = ensure_backdrop(context, root, props)
        canvas_parent = ensure_canvas_center(context, root, props, background_parent)
        ensure_menu_camera(context, root, canvas_parent)

        message = rebuild_menu_objects(context)
        props.preview_text = generate_preview_summary(scene)
        self.report({"INFO"}, message)
        return {"FINISHED"}


class AGMF_OT_AddMenuItem(Operator):
    bl_idname = "agmf.add_menu_item"
    bl_label = "Add Menu Item"
    bl_description = "Add a menu item to the list"

    def execute(self, context):
        props = context.scene.agmf_props
        item = props.menu_items.add()
        index = len(props.menu_items)
        item.name = f"Item{index}"
        item.label = f"Menu Item {index}"
        item.pos_y = props.background_canvas_height * 0.46 - ((index - 1) * props.item_spacing)
        props.menu_items_index = len(props.menu_items) - 1
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_RemoveMenuItem(Operator):
    bl_idname = "agmf.remove_menu_item"
    bl_label = "Remove Menu Item"
    bl_description = "Remove the selected menu item"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.menu_items:
            return {"CANCELLED"}

        index = min(props.menu_items_index, len(props.menu_items) - 1)
        props.menu_items.remove(index)
        props.menu_items_index = max(0, index - 1)
        props.preview_text = generate_preview_summary(context.scene)
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_MoveMenuItem(Operator):
    bl_idname = "agmf.move_menu_item"
    bl_label = "Move Menu Item"
    bl_description = "Move the selected menu item up or down in menu order"

    direction: EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")], default="UP")

    def execute(self, context):
        props = context.scene.agmf_props
        index = props.menu_items_index
        if self.direction == "UP" and index > 0:
            props.menu_items.move(index, index - 1)
            props.menu_items_index = index - 1
        elif self.direction == "DOWN" and index < len(props.menu_items) - 1:
            props.menu_items.move(index, index + 1)
            props.menu_items_index = index + 1
        else:
            return {"CANCELLED"}
        rebuild_menu_objects(context)
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_AddPanel(Operator):
    bl_idname = "agmf.add_panel"
    bl_label = "Add Panel / Group"
    bl_description = "Add a moveable panel/group for menu elements"

    def execute(self, context):
        props = context.scene.agmf_props
        panel = props.panels.add()
        panel.name = f"Panel {len(props.panels)}"
        panel.page = "MainMenu"
        props.panels_index = len(props.panels) - 1
        return {"FINISHED"}


class AGMF_OT_RemovePanel(Operator):
    bl_idname = "agmf.remove_panel"
    bl_label = "Remove Panel / Group"
    bl_description = "Remove the selected panel/group without deleting its menu elements"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.panels:
            return {"CANCELLED"}
        index = min(props.panels_index, len(props.panels) - 1)
        removed_name = props.panels[index].name
        props.panels.remove(index)
        props.panels_index = max(0, index - 1)
        for item in props.menu_items:
            if item.panel == removed_name:
                item.panel = props.panels[0].name if props.panels else ""
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_AssignSelectedItemsToPanel(Operator):
    bl_idname = "agmf.assign_items_to_panel"
    bl_label = "Assign Item To Panel"
    bl_description = "Assign the active menu item to the selected panel/group"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.menu_items or not props.panels:
            return {"CANCELLED"}
        item = props.menu_items[props.menu_items_index]
        panel = props.panels[props.panels_index]
        item.panel = panel.name
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_NudgePanel(Operator):
    bl_idname = "agmf.nudge_panel"
    bl_label = "Nudge Panel"
    bl_description = "Move the selected panel/group"

    dx: FloatProperty(default=0.0)
    dy: FloatProperty(default=0.0)

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.panels:
            return {"CANCELLED"}
        panel = props.panels[props.panels_index]
        if panel.locked:
            self.report({"WARNING"}, "Panel is locked.")
            return {"CANCELLED"}
        panel.offset_x += self.dx
        panel.offset_y += self.dy
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_ApplyPanelLayout(Operator):
    bl_idname = "agmf.apply_panel_layout"
    bl_label = "Apply Panel Layout"
    bl_description = "Line up every menu item in the selected panel using panel spacing and alignment"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.panels:
            return {"CANCELLED"}
        panel = props.panels[props.panels_index]
        item_count = apply_panel_settings_to_items(props, panel)
        rebuild_menu_objects(context)
        self.report({"INFO"}, f"Aligned {item_count} item(s) in {panel.name}.")
        return {"FINISHED"}


class AGMF_OT_ApplyPanelColors(Operator):
    bl_idname = "agmf.apply_panel_colors"
    bl_label = "Apply Panel Colors"
    bl_description = "Apply panel batch colors/material settings to every item in the selected panel"

    include_text: BoolProperty(name="Include Text", default=True)

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.panels:
            return {"CANCELLED"}
        panel = props.panels[props.panels_index]
        panel_items = [item for item in props.menu_items if item.panel == panel.name]
        for item in panel_items:
            item.fill_type = panel.batch_fill_type
            item.fill_color = panel.batch_fill_color
            item.ramp_color_a = panel.batch_ramp_color_a
            item.ramp_color_b = panel.batch_ramp_color_b
            item.ramp_offset_x = panel.batch_ramp_offset_x
            item.ramp_offset_y = panel.batch_ramp_offset_y
            item.focus_fill_color = panel.batch_focus_color
            item.press_fill_color = panel.batch_press_color
            if self.include_text:
                item.text_color = panel.batch_text_color
        item.text_font = panel.batch_text_font
        item.text_kerning = panel.batch_text_kerning
        rebuild_menu_objects(context)
        self.report({"INFO"}, f"Applied colors to {len(panel_items)} item(s) in {panel.name}.")
        return {"FINISHED"}


class AGMF_OT_ApplyPanelAll(Operator):
    bl_idname = "agmf.apply_panel_all"
    bl_label = "Apply Layout + Colors"
    bl_description = "Apply panel spacing, alignment, sizing, text layout, and colors"

    def execute(self, context):
        bpy.ops.agmf.apply_panel_layout()
        bpy.ops.agmf.apply_panel_colors(include_text=True)
        return {"FINISHED"}


class AGMF_OT_FitPanelInsideBackdrop(Operator):
    bl_idname = "agmf.fit_panel_inside_backdrop"
    bl_label = "Fit Options Inside Backdrop"
    bl_description = "Move the selected panel's option list inside the backdrop window"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.panels:
            return {"CANCELLED"}
        panel = props.panels[props.panels_index]
        props.layout_mode = "FREEFORM"
        panel.align_x = -props.background_canvas_width * 0.34
        panel.start_y = props.background_canvas_height * 0.46
        panel.option_spacing = max(0.28, min(0.72, props.background_canvas_height / 18.0))
        panel.option_width = props.background_canvas_width * 0.26
        panel.option_height = max(0.28, min(0.55, props.background_canvas_height / 20.0))
        bpy.ops.agmf.apply_panel_layout()
        self.report({"INFO"}, f"Moved {panel.name} options inside the backdrop.")
        return {"FINISHED"}


class AGMF_OT_AddScreen(Operator):
    bl_idname = "agmf.add_screen"
    bl_label = "Add Screen"
    bl_description = "Add a MenuOS screen to the boot/menu flow"

    screen_type: EnumProperty(items=SCREEN_TYPES, default="SUBMENU")

    def execute(self, context):
        props = context.scene.agmf_props
        screen = props.screens.add()
        screen.screen_type = self.screen_type
        screen.name = screen.screen_type.replace("_", " ").title()
        screen.target_page = "MainMenu"
        screen.duration = 2.0 if screen.screen_type.startswith("INTRO") else 0.0
        props.screens_index = len(props.screens) - 1
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_RemoveScreen(Operator):
    bl_idname = "agmf.remove_screen"
    bl_label = "Remove Screen"
    bl_description = "Remove the selected MenuOS screen"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.screens:
            return {"CANCELLED"}
        index = min(props.screens_index, len(props.screens) - 1)
        props.screens.remove(index)
        props.screens_index = max(0, index - 1)
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_MoveScreen(Operator):
    bl_idname = "agmf.move_screen"
    bl_label = "Move Screen"
    bl_description = "Move the selected screen in the boot/menu flow"

    direction: EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")], default="UP")

    def execute(self, context):
        props = context.scene.agmf_props
        index = props.screens_index
        if self.direction == "UP" and index > 0:
            props.screens.move(index, index - 1)
            props.screens_index = index - 1
        elif self.direction == "DOWN" and index < len(props.screens) - 1:
            props.screens.move(index, index + 1)
            props.screens_index = index + 1
        else:
            return {"CANCELLED"}
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_AddLiveSceneSlot(Operator):
    bl_idname = "agmf.add_live_scene_slot"
    bl_label = "Add Live Scene Slot"
    bl_description = "Add a background scene slot for character/stage switching"

    def execute(self, context):
        props = context.scene.agmf_props
        slot = props.live_scenes.add()
        slot.name = f"Scene Slot {len(props.live_scenes)}"
        props.live_scenes_index = len(props.live_scenes) - 1
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_AddBackgroundMediaFiles(Operator, ImportHelper):
    bl_idname = "agmf.add_background_media_files"
    bl_label = "Add Background Media"
    bl_description = "Add one or more image/video layers to the background media stack"

    filename_ext = ".png;.jpg;.jpeg;.tga;.tif;.tiff;.bmp;.webp;.mp4;.mov;.avi;.mkv;.webm"
    filter_glob: StringProperty(default="*.png;*.jpg;*.jpeg;*.tga;*.tif;*.tiff;*.bmp;*.webp;*.mp4;*.mov;*.avi;*.mkv;*.webm", options={"HIDDEN"})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})
    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        props = context.scene.agmf_props
        filepaths = [os.path.join(self.directory, f.name) for f in self.files] if self.files else [self.filepath]
        video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
        added = 0
        for fp in filepaths:
            if not fp or not os.path.isfile(fp):
                continue
            layer = props.background_layers.add()
            base = os.path.splitext(os.path.basename(fp))[0]
            ext = os.path.splitext(fp)[1].lower()
            layer.name = base
            layer.filepath = fp
            layer.layer_type = "VIDEO" if ext in video_exts else "IMAGE"
            layer.width = props.background_canvas_width
            layer.height = props.background_canvas_height
            layer.move_x = 0.0
            layer.move_y = 0.0
            layer.move_z = 0.0
            props.background_layers_index = len(props.background_layers) - 1
            added += 1
        rebuild_menu_objects(context)
        self.report({"INFO"}, f"Added {added} background media layer(s).")
        return {"FINISHED"}


class AGMF_OT_RemoveBackgroundMediaLayer(Operator):
    bl_idname = "agmf.remove_background_media_layer"
    bl_label = "Remove Background Layer"
    bl_description = "Remove the selected background media layer"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.background_layers:
            return {"CANCELLED"}
        index = min(props.background_layers_index, len(props.background_layers) - 1)
        props.background_layers.remove(index)
        props.background_layers_index = max(0, index - 1)
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_MoveBackgroundMediaLayer(Operator):
    bl_idname = "agmf.move_background_media_layer"
    bl_label = "Move Background Layer"
    bl_description = "Move the selected background layer in the playback/render stack"

    direction: EnumProperty(items=[("UP", "Up", ""), ("DOWN", "Down", "")], default="UP")

    def execute(self, context):
        props = context.scene.agmf_props
        index = props.background_layers_index
        if self.direction == "UP" and index > 0:
            props.background_layers.move(index, index - 1)
            props.background_layers_index = index - 1
        elif self.direction == "DOWN" and index < len(props.background_layers) - 1:
            props.background_layers.move(index, index + 1)
            props.background_layers_index = index + 1
        else:
            return {"CANCELLED"}
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_SetBackgroundLayerAsCanvas(Operator):
    bl_idname = "agmf.set_background_layer_as_canvas"
    bl_label = "Fit Layer To Canvas"
    bl_description = "Set the active background layer to the canvas size and bottom-center world origin"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.background_layers:
            return {"CANCELLED"}
        layer = props.background_layers[props.background_layers_index]
        layer.width = props.background_canvas_width
        layer.height = props.background_canvas_height
        layer.move_x = 0.0
        layer.move_y = 0.0
        layer.move_z = 0.0
        rebuild_menu_objects(context)
        return {"FINISHED"}


class AGMF_OT_RemoveLiveSceneSlot(Operator):
    bl_idname = "agmf.remove_live_scene_slot"
    bl_label = "Remove Live Scene Slot"
    bl_description = "Remove the selected live background scene slot"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.live_scenes:
            return {"CANCELLED"}
        index = min(props.live_scenes_index, len(props.live_scenes) - 1)
        props.live_scenes.remove(index)
        props.live_scenes_index = max(0, index - 1)
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_RebuildMenu(Operator):
    bl_idname = "agmf.rebuild_menu"
    bl_label = "Rebuild Menu"
    bl_description = "Rebuild menu objects from the current item list and layout"

    def execute(self, context):
        message = rebuild_menu_objects(context)
        context.scene.agmf_props.preview_text = generate_preview_summary(context.scene)
        self.report({"INFO"}, message)
        return {"FINISHED"}


class AGMF_OT_ApplyTheme(Operator):
    bl_idname = "agmf.apply_theme"
    bl_label = "Apply Theme"
    bl_description = "Apply the selected theme preset to the generated menu objects"

    def execute(self, context):
        message = rebuild_menu_objects(context)
        self.report({"INFO"}, f"{context.scene.agmf_props.theme_preset} applied. {message}")
        return {"FINISHED"}


class AGMF_OT_CyclePreviewState(Operator):
    bl_idname = "agmf.cycle_preview_state"
    bl_label = "Cycle Preview State"
    bl_description = "Cycle the selected menu item through the preview states"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.menu_items:
            return {"CANCELLED"}

        item = props.menu_items[props.menu_items_index]
        states = [entry[0] for entry in STATE_TYPES]
        current_index = states.index(item.preview_state)
        item.preview_state = states[(current_index + 1) % len(states)]
        rebuild_menu_objects(context)
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_PreviewConfig(Operator):
    bl_idname = "agmf.preview_config"
    bl_label = "Refresh Preview Data"
    bl_description = "Generate a data preview for Blender and UPBGE use"

    def execute(self, context):
        context.scene.agmf_props.preview_text = generate_preview_summary(context.scene)
        self.report({"INFO"}, "Preview data refreshed.")
        return {"FINISHED"}


class AGMF_OT_LoadTemplate(Operator):
    bl_idname = "agmf.load_template"
    bl_label = "Load Template"
    bl_description = "Load a starter template into the menu item list"

    template_name: EnumProperty(
        name="Template",
        items=[
            ("MAIN_MENU", "Main Menu", "Classic title screen layout"),
            ("PAUSE_MENU", "Pause Menu", "Resume/options/quit layout"),
            ("OPTIONS_MENU", "Options Menu", "Settings-focused menu"),
            ("TITLE_FLOW", "Title Flow", "Company logo, press start, main menu, soundtrack"),
            ("SOUNDTRACK_PAGE", "Soundtrack Page", "Soundtrack menu page"),
        ],
        default="MAIN_MENU",
    )

    def execute(self, context):
        props = context.scene.agmf_props
        props.menu_items.clear()
        if not props.panels:
            panel = props.panels.add()
            panel.name = "Main Options"
            panel.page = "MainMenu"

        templates = {
            "MAIN_MENU": [
                ("Start", "START_GAME"),
                ("Load Game", "CUSTOM"),
                ("Options", "OPTIONS"),
                ("Quit", "QUIT"),
            ],
            "PAUSE_MENU": [
                ("Resume", "BACK"),
                ("Options", "OPTIONS"),
                ("Main Menu", "OPEN_SUBMENU"),
                ("Quit", "QUIT"),
            ],
            "OPTIONS_MENU": [
                ("Graphics", "OPEN_SUBMENU"),
                ("Audio", "OPEN_SUBMENU"),
                ("Controls", "OPEN_SUBMENU"),
                ("Back", "BACK"),
            ],
            "TITLE_FLOW": [
                ("FIGHT NOW", "START_GAME"),
                ("ONLINE", "CUSTOM"),
                ("WORLD", "OPEN_SUBMENU"),
                ("IMMORTAL", "OPEN_SUBMENU"),
                ("ROAD TO GLORY", "OPEN_SUBMENU"),
                ("CREATE", "OPEN_SUBMENU"),
                ("SHOP", "CUSTOM"),
                ("OPTIONS", "OPTIONS"),
            ],
            "SOUNDTRACK_PAGE": [
                ("Soundtrack", "NONE"),
                ("Now Playing", "NONE"),
                ("Toggle Selected", "CUSTOM"),
                ("Next Track", "CUSTOM"),
                ("Back", "BACK"),
            ],
        }

        for idx, (label, action) in enumerate(templates[self.template_name]):
            item = props.menu_items.add()
            item.name = label.replace(" ", "")
            item.label = label
            item.action = action
            item.panel = props.panels[0].name if props.panels else "Main Options"
            item.pos_x = -props.background_canvas_width * 0.34
            item.pos_y = props.background_canvas_height * 0.46 - (idx * 0.48)
            item.width = 4.25 if idx == 0 else 2.65
            item.height = 0.65 if idx == 0 else 0.38
            item.use_border = idx == 0
            if idx == 0:
                item.focus_fill_color = (0.72, 0.02, 0.02, 0.96)

        props.menu_items_index = 0
        if self.template_name == "TITLE_FLOW":
            props.layout_mode = "FREEFORM"
            props.background_type = "HYBRID"
            props.account_enabled = True
            if not props.screens:
                for name, screen_type, duration in [
                    ("Studio Logo", "INTRO_LOGO", 2.0),
                    ("Technology Logo", "INTRO_LOGO", 1.5),
                    ("Press Any Button", "PRESS_START", 0.0),
                    ("Main Menu", "MAIN_MENU", 0.0),
                    ("Soundtrack", "SOUNDTRACK", 0.0),
                ]:
                    screen = props.screens.add()
                    screen.name = name
                    screen.screen_type = screen_type
                    screen.duration = duration
        props.preview_text = generate_preview_summary(context.scene)
        rebuild_menu_objects(context)
        self.report({"INFO"}, f"{self.template_name} loaded.")
        return {"FINISHED"}


class AGMF_OT_AddSoundtrackFiles(Operator, ImportHelper):
    bl_idname = "agmf.add_soundtrack_files"
    bl_label = "Add Soundtrack Files"
    bl_description = "Add one or more songs to the MenuOS soundtrack bank"

    filename_ext = ".wav;.mp3;.ogg;.flac"
    filter_glob: StringProperty(default="*.wav;*.mp3;*.ogg;*.flac", options={"HIDDEN"})
    files: CollectionProperty(type=bpy.types.OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})
    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        props = context.scene.agmf_props
        filepaths = [os.path.join(self.directory, f.name) for f in self.files] if self.files else [self.filepath]
        added = 0
        for fp in filepaths:
            if not fp or not os.path.isfile(fp):
                continue
            try:
                snd = bpy.data.sounds.load(fp, check_existing=True)
            except Exception as exc:
                self.report({"WARNING"}, f"Could not load {os.path.basename(fp)}: {exc}")
                continue
            if any(track.sound == snd for track in props.soundtrack_tracks):
                continue
            track = props.soundtrack_tracks.add()
            base = os.path.splitext(os.path.basename(fp))[0]
            track.sound = snd
            track.filepath = fp

            meta = extract_mp3_metadata(fp)
            track.name = base
            track.song_title = meta.get('title') or base
            track.artist = meta.get('artist', '')
            track.album = meta.get('album', '')
            if meta.get('artwork_path'):
                track.album_art_path = meta.get('artwork_path')

            track.track_number = len(props.soundtrack_tracks)
            props.soundtrack_tracks_index = len(props.soundtrack_tracks) - 1
            added += 1
        props.preview_text = generate_preview_summary(context.scene)
        self.report({"INFO"}, f"Added {added} soundtrack track(s).")
        return {"FINISHED"}


class AGMF_OT_RemoveSoundtrackTrack(Operator):
    bl_idname = "agmf.remove_soundtrack_track"
    bl_label = "Remove Soundtrack Track"
    bl_description = "Remove the selected soundtrack track"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.soundtrack_tracks:
            return {"CANCELLED"}
        index = min(props.soundtrack_tracks_index, len(props.soundtrack_tracks) - 1)
        props.soundtrack_tracks.remove(index)
        props.soundtrack_tracks_index = max(0, index - 1)
        props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_SortSoundtrack(Operator):
    bl_idname = "agmf.sort_soundtrack"
    bl_label = "Sort Soundtrack"
    bl_description = "Sort soundtrack tracks by track number and title"

    def execute(self, context):
        tracks = context.scene.agmf_props.soundtrack_tracks
        order = sorted(range(len(tracks)), key=lambda i: (tracks[i].track_number, tracks[i].song_title, tracks[i].name))
        for target, original in enumerate(order):
            current = next((idx for idx, value in enumerate(order) if value == original), target)
            if current != target:
                tracks.move(current, target)
                moved = order.pop(current)
                order.insert(target, moved)
        context.scene.agmf_props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_ShuffleSoundtrack(Operator):
    bl_idname = "agmf.shuffle_soundtrack"
    bl_label = "Shuffle Soundtrack"
    bl_description = "Shuffle soundtrack track order"

    def execute(self, context):
        tracks = context.scene.agmf_props.soundtrack_tracks
        for i in range(len(tracks) - 1, 0, -1):
            j = random.randint(0, i)
            tracks.move(i, j)
        context.scene.agmf_props.preview_text = generate_preview_summary(context.scene)
        return {"FINISHED"}


class AGMF_OT_PreviewSoundtrackTrack(Operator):
    bl_idname = "agmf.preview_soundtrack_track"
    bl_label = "Preview Track"
    bl_description = "Preview the selected soundtrack track through Blender audio"

    def execute(self, context):
        props = context.scene.agmf_props
        if not props.soundtrack_tracks:
            self.report({"WARNING"}, "No soundtrack tracks to preview.")
            return {"CANCELLED"}
        index = min(props.soundtrack_tracks_index, len(props.soundtrack_tracks) - 1)
        ok, message = play_soundtrack_track(props.soundtrack_tracks[index], index)
        self.report({"INFO"} if ok else {"WARNING"}, message)
        return {"FINISHED"} if ok else {"CANCELLED"}


class AGMF_OT_PreviewNextSoundtrackTrack(Operator):
    bl_idname = "agmf.preview_next_soundtrack_track"
    bl_label = "Preview Next Track"
    bl_description = "Preview the next soundtrack track using the selected playback rule"

    def execute(self, context):
        props = context.scene.agmf_props
        index = choose_next_track_index(props, _AUDIO_TRACK_INDEX)
        if index < 0:
            self.report({"WARNING"}, "No enabled soundtrack tracks found.")
            return {"CANCELLED"}
        props.soundtrack_tracks_index = index
        ok, message = play_soundtrack_track(props.soundtrack_tracks[index], index)
        self.report({"INFO"} if ok else {"WARNING"}, message)
        return {"FINISHED"} if ok else {"CANCELLED"}

class AGMF_OT_PreviewPreviousSoundtrackTrack(Operator):
    bl_idname = "agmf.preview_prev_soundtrack_track"
    bl_label = "Preview Previous Track"
    bl_description = "Preview the previous soundtrack track using the selected playback rule"

    def execute(self, context):
        props = context.scene.agmf_props
        index = choose_prev_track_index(props, _AUDIO_TRACK_INDEX)
        if index < 0:
            self.report({"WARNING"}, "No enabled soundtrack tracks found.")
            return {"CANCELLED"}
        props.soundtrack_tracks_index = index
        ok, message = play_soundtrack_track(props.soundtrack_tracks[index], index)
        self.report({"INFO"} if ok else {"WARNING"}, message)
        return {"FINISHED"} if ok else {"CANCELLED"}


class AGMF_OT_StopSoundtrackPreview(Operator):
    bl_idname = "agmf.stop_soundtrack_preview"
    bl_label = "Stop Preview"
    bl_description = "Stop the current Blender soundtrack preview"

    def execute(self, context):
        stop_audio_preview()
        self.report({"INFO"}, "Soundtrack preview stopped.")
        return {"FINISHED"}


class AGMF_OT_PreviewBackgroundMedia(Operator):
    bl_idname = "agmf.preview_background_media"
    bl_label = "Preview Background Media"
    bl_description = "Apply image/video media to the generated background plane and start timeline playback for video"

    def execute(self, context):
        props = context.scene.agmf_props
        root = get_menu_root(props)
        if root is None:
            self.report({"WARNING"}, "Create a menu root first.")
            return {"CANCELLED"}
        if not props.background_layers:
            self.report({"WARNING"}, "Add an image or video background layer first.")
            return {"CANCELLED"}
        layer = props.background_layers[props.background_layers_index]
        if not layer.filepath:
            self.report({"WARNING"}, "Set a file for the active background layer first.")
            return {"CANCELLED"}
        background_parent = ensure_backdrop(context, root, props)
        ensure_background_media_layers(context, root, props, background_parent)
        if layer.layer_type == "VIDEO":
            context.scene.frame_set(layer.frame_start)
            try:
                bpy.ops.screen.animation_play()
            except Exception:
                pass
        props.preview_text = f"Previewing background layer: {layer.name}\n{bpy.path.abspath(layer.filepath)}"
        self.report({"INFO"}, "Background media preview applied.")
        return {"FINISHED"}


class AGMF_OT_StopVideoPreview(Operator):
    bl_idname = "agmf.stop_video_preview"
    bl_label = "Stop Video Preview"
    bl_description = "Stop Blender timeline playback used for video media preview"

    def execute(self, context):
        try:
            if context.screen and context.screen.is_animation_playing:
                bpy.ops.screen.animation_cancel(restore_frame=False)
        except Exception:
            pass
        self.report({"INFO"}, "Video preview stopped.")
        return {"FINISHED"}


class AGMF_OT_PreviewSceneSwitch(Operator):
    bl_idname = "agmf.preview_scene_switch"
    bl_label = "Mark Scene Window"
    bl_description = "Mark the backdrop as a scene window without switching the active Blender scene"

    def execute(self, context):
        props = context.scene.agmf_props
        root = get_menu_root(props)
        if root is None:
            self.report({"WARNING"}, "Create a menu root first.")
            return {"CANCELLED"}
        if not props.background_scene:
            self.report({"WARNING"}, "Assign a scene to Scene Seen Through Backdrop first.")
            return {"CANCELLED"}
        props.background_type = "SCENE"
        bg = ensure_backdrop(context, root, props)
        props.active_runtime_scene = props.background_scene.name
        self.report({"INFO"}, f"Backdrop marked as window into scene: {props.background_scene.name}")
        return {"FINISHED"}


class AGMF_OT_GenerateRuntimeScripts(Operator):
    bl_idname = "agmf.generate_runtime_scripts"
    bl_label = "Generate UPBGE Runtime"
    bl_description = "Create MenuOS config and UPBGE runtime controller scripts as Blender text blocks and optional files"

    write_files: BoolProperty(name="Write Files", default=False)

    def execute(self, context):
        props = context.scene.agmf_props
        config_json = generate_preview_summary(context.scene)
        runtime_script = generate_upbge_runtime_script(config_json)

        create_or_update_text_block("MenuOS_Config.json", config_json)
        create_or_update_text_block("MenuOS_UPBGE_Controller.py", runtime_script)

        wrote = []
        if self.write_files:
            if props.config_json_path:
                config_path = bpy.path.abspath(props.config_json_path)
                config_dir = os.path.dirname(config_path)
                if config_dir:
                    os.makedirs(config_dir, exist_ok=True)
                with open(config_path, "w", encoding="utf-8") as handle:
                    handle.write(config_json)
                wrote.append(config_path)
            if props.runtime_script_path:
                script_path = bpy.path.abspath(props.runtime_script_path)
                script_dir = os.path.dirname(script_path)
                if script_dir:
                    os.makedirs(script_dir, exist_ok=True)
                with open(script_path, "w", encoding="utf-8") as handle:
                    handle.write(runtime_script)
                wrote.append(script_path)

        props.preview_text = "Generated MenuOS_Config.json and MenuOS_UPBGE_Controller.py text blocks."
        if wrote:
            props.preview_text += "\nWrote files:\n" + "\n".join(wrote)
        self.report({"INFO"}, "UPBGE runtime generated.")
        return {"FINISHED"}


class AGMF_OT_ExportUpbgeNotes(Operator):
    bl_idname = "agmf.export_upbge_notes"
    bl_label = "Build UPBGE Notes"
    bl_description = "Generate implementation notes for UPBGE runtime hookup"

    def execute(self, context):
        props = context.scene.agmf_props
        data = json.loads(generate_preview_summary(context.scene))
        lines = [
            f"Menu: {data['menu_name']}",
            f"Target: {data['target_mode']}",
            f"Background: {data['background']['type']}",
            "UPBGE Hookup:",
            "- Boot through screens in order: intro logos/videos, press start, main menu, submenus.",
            "- Use background scene slots to swap live 3D wrestlers/stages during navigation.",
            "- Use keyboard, mouse, or gamepad input to move focus between listed items.",
            "- Read each item's action and call the matching runtime behavior.",
            "- Use rectangle position/size/fill/border settings to recreate Photoshop-style UI blocks.",
            "- Use soundtrack rules for sequential, shuffle, or random playback.",
            "- Use preview_state as the initial visual state reference.",
            "- Animate transitions using the same labels and object names generated in Blender.",
            "",
            "Screens:",
        ]
        for screen in data["screens"]:
            lines.append(f"- {screen['name']}: {screen['type']} | {screen['duration']}s | skippable={screen['skippable']}")
        lines.extend([
            "",
            "Actions:",
        ])
        for item in data["items"]:
            lines.append(f"- {item['label']}: {item['action']} -> {item['target_menu'] or 'No target menu'}")
        lines.extend([
            "",
            "Soundtrack:",
        ])
        for track in data["soundtrack"]["tracks"]:
            lines.append(f"- {track['track_number']}. {track['song']} | {track['artist']} | enabled={track['enabled']}")

        props.preview_text = "\n".join(lines)
        self.report({"INFO"}, "UPBGE notes generated.")
        return {"FINISHED"}



class AGMF_PT_NowPlayingWidgetPanel(Panel):
    bl_label = "Now Playing Widget Editor"
    bl_idname = "AGMF_PT_NowPlayingWidgetPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Menu Forge"
    bl_parent_id = "AGMF_PT_MainPanel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.agmf_props
        widget = props.now_playing_widget

        box = layout.box()
        box.label(text="Presets", icon='PRESET')
        row = box.row()
        row.prop(widget, "active_preset", text="")
        row = box.row()
        row.prop(widget, "preset_name", text="")
        row.operator("agmf.save_widget_preset", icon='FILE_TICK')
        row.operator("agmf.delete_widget_preset", icon='TRASH')

        box = layout.box()
        box.label(text="Layout & Animation", icon='VIEW_PAN')
        row = box.row(align=True)
        row.prop(widget, "pos_x")
        row.prop(widget, "pos_y")
        row = box.row(align=True)
        row.prop(widget, "width")
        row.prop(widget, "height")
        row = box.row(align=True)
        row.prop(widget, "fade_in")
        row.prop(widget, "fade_out")
        row = box.row(align=True)
        row.prop(widget, "slide_dir")
        row.prop(widget, "slide_dist")

        box = layout.box()
        box.label(text="Background", icon='SHADING_RENDERED')
        box.prop(widget, "fill_type")
        if widget.fill_type == "COLOR":
            box.prop(widget, "fill_color")
        elif widget.fill_type == "COLOR_RAMP":
            box.prop(widget, "ramp_color_a")
            box.prop(widget, "ramp_color_b")
            box.prop(widget, "ramp_direction")
            row = box.row(align=True)
            row.prop(widget, "ramp_offset_x")
            row.prop(widget, "ramp_offset_y")

        box = layout.box()
        box.label(text="Album Artwork", icon='IMAGE_DATA')
        box.prop(widget, "show_artwork")
        if widget.show_artwork:
            box.prop(widget, "artwork_size")
            row = box.row(align=True)
            row.prop(widget, "artwork_offset_x")
            row.prop(widget, "artwork_offset_y")

        box = layout.box()
        box.label(text="Text Info", icon='FONT_DATA')
        box.prop(widget, "title_size")
        box.prop(widget, "title_color")
        row = box.row(align=True)
        row.prop(widget, "title_offset_x")
        row.prop(widget, "title_offset_y")
        box.separator()
        box.prop(widget, "artist_size")
        box.prop(widget, "artist_color")
        row = box.row(align=True)
        row.prop(widget, "artist_offset_x")
        row.prop(widget, "artist_offset_y")


class AGMF_PT_MainPanel(Panel):
    bl_label = "Ascend Menu Forge"
    bl_idname = "AGMF_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Menu Forge"

    def draw(self, context):
        layout = self.layout
        props = context.scene.agmf_props

        box = layout.box()
        box.label(text="Create", icon="SEQ_STRIP_META")
        box.prop(props, "live_edit", toggle=True)
        box.prop(props, "menu_name")
        box.prop(props, "target_mode")
        box.prop(props, "add_default_items")
        box.prop(props, "auto_build_backdrop")
        box.operator("agmf.create_menu_root", icon="ADD")

        box = layout.box()
        box.label(text="Templates", icon="ASSET_MANAGER")
        row = box.row(align=True)
        op = row.operator("agmf.load_template", text="Title Flow")
        op.template_name = "TITLE_FLOW"
        op = row.operator("agmf.load_template", text="Music")
        op.template_name = "SOUNDTRACK_PAGE"
        row = box.row(align=True)
        op = row.operator("agmf.load_template", text="Main")
        op.template_name = "MAIN_MENU"
        op = row.operator("agmf.load_template", text="Pause")
        op.template_name = "PAUSE_MENU"
        op = row.operator("agmf.load_template", text="Options")
        op.template_name = "OPTIONS_MENU"

        box = layout.box()
        box.label(text="Boot + Pages", icon="SEQUENCE")
        row = box.row()
        row.template_list("AGMF_UL_MenuScreens", "", props, "screens", props, "screens_index", rows=3)
        col = row.column(align=True)
        col.operator("agmf.add_screen", text="", icon="ADD").screen_type = "SUBMENU"
        col.operator("agmf.remove_screen", text="", icon="REMOVE")
        up = col.operator("agmf.move_screen", text="", icon="TRIA_UP")
        up.direction = "UP"
        down = col.operator("agmf.move_screen", text="", icon="TRIA_DOWN")
        down.direction = "DOWN"
        if props.screens and props.screens_index < len(props.screens):
            screen = props.screens[props.screens_index]
            detail = box.box()
            detail.prop(screen, "name")
            detail.prop(screen, "screen_type")
            detail.prop(screen, "duration")
            detail.prop(screen, "skippable")
            detail.prop(screen, "target_page")
            detail.prop(screen, "media_path")

        box = layout.box()
        box.label(text="1. Background Canvas", icon="WORLD")
        box.label(text="Bottom-center origin is locked to world origin.", icon="PIVOT_BOUNDBOX")
        row = box.row(align=True)
        row.prop(props, "background_canvas_width")
        row.prop(props, "background_canvas_height")
        box.prop(props, "background_type", text="Scene Mode")
        if props.background_type == "SCENE":
            box.prop(props, "background_scene", text="Scene Seen Through Backdrop")
            camera_name = props.background_scene_camera.name if props.background_scene_camera else "No camera found"
            box.label(text=f"Auto Camera: {camera_name}", icon="CAMERA_DATA")
            box.label(text="This does not switch scenes; UPBGE renders this camera onto the backdrop.", icon="VIEW_CAMERA")
        if props.background_type in {"COLOR", "COLOR_RAMP", "HYBRID"}:
            row = box.row(align=True)
            row.prop(props, "bg_color_a")
            row.prop(props, "bg_color_b")

        layer_box = layout.box()
        layer_box.label(text="2. Background Media Stack", icon="SEQ_SEQUENCER")
        row = layer_box.row()
        row.template_list("AGMF_UL_BackgroundMediaLayers", "", props, "background_layers", props, "background_layers_index", rows=4)
        col = row.column(align=True)
        col.operator("agmf.add_background_media_files", text="", icon="ADD")
        col.operator("agmf.remove_background_media_layer", text="", icon="REMOVE")
        up = col.operator("agmf.move_background_media_layer", text="", icon="TRIA_UP")
        up.direction = "UP"
        down = col.operator("agmf.move_background_media_layer", text="", icon="TRIA_DOWN")
        down.direction = "DOWN"
        if props.background_layers and props.background_layers_index < len(props.background_layers):
            layer = props.background_layers[props.background_layers_index]
            detail = layer_box.box()
            detail.label(text="Active Layer", icon="IMAGE_DATA" if layer.layer_type == "IMAGE" else "FILE_MOVIE")
            detail.prop(layer, "enabled")
            detail.prop(layer, "name")
            row = detail.row(align=True)
            row.prop(layer, "layer_type")
            row.prop(layer, "layer_use")
            detail.prop(layer, "filepath")
            if layer.layer_use == "SCENE_WINDOW":
                detail.prop(layer, "scene_window")
            row = detail.row(align=True)
            row.prop(layer, "width")
            row.prop(layer, "height")
            detail.operator("agmf.set_background_layer_as_canvas", icon="FULLSCREEN_ENTER")
            move = detail.box()
            move.label(text="Move Plane In World", icon="ORIENTATION_GLOBAL")
            row = move.row(align=True)
            row.prop(layer, "move_x")
            row.prop(layer, "move_y")
            row.prop(layer, "move_z")
            tex = detail.box()
            tex.label(text="Texture Mapping", icon="NODE_TEXTURE")
            tex.prop(layer, "fit_mode")
            tex.prop(layer, "map_zoom")
            row = tex.row(align=True)
            row.prop(layer, "map_scale_x")
            row.prop(layer, "map_scale_y")
            row.prop(layer, "map_scale_z")
            row = tex.row(align=True)
            row.prop(layer, "map_offset_x")
            row.prop(layer, "map_offset_y")
            row.prop(layer, "map_offset_z")
            tex.prop(layer, "map_rotation")
            look = detail.box()
            look.label(text="Timing + Transition", icon="TIME")
            look.prop(layer, "duration_mode")
            if layer.duration_mode == "AUTO":
                look.prop(layer, "auto_duration")
            else:
                look.prop(layer, "custom_duration")
            row = look.row(align=True)
            row.prop(layer, "transition_in")
            row.prop(layer, "transition_out")
            row = look.row(align=True)
            row.prop(layer, "opacity")
            row.prop(layer, "tint_color")
            row = detail.row(align=True)
            row.operator("agmf.preview_background_media", text="Play Preview", icon="PLAY")
            row.operator("agmf.stop_video_preview", text="Pause", icon="PAUSE")

        box = layout.box()
        box.label(text="Canvas + Theme", icon="PREFERENCES")
        box.prop(props, "layout_mode")
        if props.layout_mode == "GRID":
            box.prop(props, "grid_columns")
        elif props.layout_mode == "RADIAL":
            box.prop(props, "radial_radius")
            box.prop(props, "radial_offset")
        box.prop(props, "item_spacing")
        box.prop(props, "theme_preset")
        box.prop(props, "camera_style")

        box = layout.box()
        box.label(text="Panels / Groups", icon="GROUP")
        row = box.row()
        row.template_list("AGMF_UL_MenuPanels", "", props, "panels", props, "panels_index", rows=3)
        col = row.column(align=True)
        col.operator("agmf.add_panel", text="", icon="ADD")
        col.operator("agmf.remove_panel", text="", icon="REMOVE")
        if props.panels and props.panels_index < len(props.panels):
            panel = props.panels[props.panels_index]
            pbox = box.box()
            pbox.prop(panel, "name")
            pbox.prop(panel, "page")
            pbox.prop(panel, "visible")
            pbox.prop(panel, "locked")
            row = pbox.row(align=True)
            row.prop(panel, "offset_x")
            row.prop(panel, "offset_y")
            pbox.prop(panel, "depth_y")
            layout_box = pbox.box()
            layout_box.label(text="Batch Option Layout", icon="ALIGN_LEFT")
            row = layout_box.row(align=True)
            row.prop(panel, "layout_align_x", expand=True)
            layout_box.prop(panel, "layout_margin_x")
            row = layout_box.row(align=True)
            row.prop(panel, "align_x")
            row.prop(panel, "start_y")
            layout_box.prop(panel, "option_spacing")
            row = layout_box.row(align=True)
            row.prop(panel, "option_width")
            row.prop(panel, "option_height")
            layout_box.prop(panel, "batch_text_font")
            layout_box.prop(panel, "batch_text_size")
            layout_box.prop(panel, "batch_text_kerning")
            row = layout_box.row(align=True)
            row.prop(panel, "batch_text_align_x", expand=True)
            row = layout_box.row(align=True)
            row.prop(panel, "batch_text_align_y", expand=True)
            row = layout_box.row(align=True)
            row.prop(panel, "batch_text_padding_x")
            row.prop(panel, "batch_text_padding_y")
            row = layout_box.row(align=True)
            row.prop(panel, "batch_container_padding_x")
            row.prop(panel, "batch_container_padding_y")
            row = layout_box.row(align=True)
            row.prop(panel, "batch_margin_top")
            row.prop(panel, "batch_margin_bottom")
            desc_box = layout_box.box()
            desc_box.label(text="Batch Sub Descriptions", icon="TEXT")
            desc_box.prop(panel, "batch_show_description")
            row = desc_box.row(align=True)
            row.prop(panel, "batch_description_gap")
            row.prop(panel, "batch_description_scale")
            desc_box.prop(panel, "batch_description_color")
            layout_box.operator("agmf.fit_panel_inside_backdrop", icon="FULLSCREEN_ENTER")
            color_box = pbox.box()
            color_box.label(text="Batch Colors", icon="COLOR")
            color_box.prop(panel, "batch_fill_type")
            if panel.batch_fill_type == "COLOR_RAMP":
                color_box.prop(panel, "batch_ramp_color_a")
                color_box.prop(panel, "batch_ramp_color_b")
                row = color_box.row(align=True)
                row.prop(panel, "batch_ramp_offset_x", text="Offset X")
                row.prop(panel, "batch_ramp_offset_y", text="Offset Y")
            else:
                color_box.prop(panel, "batch_fill_color")
            color_box.prop(panel, "batch_focus_color")
            color_box.prop(panel, "batch_press_color")
            color_box.prop(panel, "batch_text_color")
            row = pbox.row(align=True)
            op = row.operator("agmf.nudge_panel", text="Left")
            op.dx = -0.1
            op.dy = 0.0
            op = row.operator("agmf.nudge_panel", text="Right")
            op.dx = 0.1
            op.dy = 0.0
            op = row.operator("agmf.nudge_panel", text="Up")
            op.dx = 0.0
            op.dy = 0.1
            op = row.operator("agmf.nudge_panel", text="Down")
            op.dx = 0.0
            op.dy = -0.1
            pbox.operator("agmf.assign_items_to_panel", icon="LINKED")

        box = layout.box()
        box.label(text="Menu Elements", icon="TEXT")
        row = box.row()
        row.template_list("AGMF_UL_MenuItems", "", props, "menu_items", props, "menu_items_index", rows=4)
        col = row.column(align=True)
        col.operator("agmf.add_menu_item", text="", icon="ADD")
        col.operator("agmf.remove_menu_item", text="", icon="REMOVE")
        up = col.operator("agmf.move_menu_item", text="", icon="TRIA_UP")
        up.direction = "UP"
        down = col.operator("agmf.move_menu_item", text="", icon="TRIA_DOWN")
        down.direction = "DOWN"

        if props.menu_items and props.menu_items_index < len(props.menu_items):
            item = props.menu_items[props.menu_items_index]
            detail = box.box()
            detail.prop(item, "name")
            detail.prop(item, "label")
            detail.prop(item, "show_description")
            if item.show_description:
                detail.prop(item, "description")
            detail.prop(item, "page")
            detail.prop(item, "panel")
            detail.prop(item, "item_type")
            detail.prop(item, "action")
            if item.action in {"OPEN_SUBMENU", "CUSTOM"}:
                detail.prop(item, "target_menu")
            loc = detail.box()
            loc.label(text="Photoshop-Style Transform", icon="ORIENTATION_GLOBAL")
            row = loc.row(align=True)
            row.prop(item, "pos_x")
            row.prop(item, "pos_y")
            row = loc.row(align=True)
            row.prop(item, "width")
            row.prop(item, "height")
            row = loc.row(align=True)
            row.prop(item, "margin_top")
            row.prop(item, "margin_bottom")
            loc.prop(item, "depth_y")
            style = detail.box()
            style.label(text="Fill + Border", icon="COLOR")
            style.prop(item, "fill_type")
            if item.fill_type == "COLOR":
                style.prop(item, "fill_color")
                style.prop(item, "focus_fill_color")
                style.prop(item, "press_fill_color")
            elif item.fill_type == "COLOR_RAMP":
                style.prop(item, "ramp_color_a")
                style.prop(item, "ramp_color_b")
                style.prop(item, "ramp_direction")
                row = style.row(align=True)
                row.prop(item, "ramp_offset_x")
                row.prop(item, "ramp_offset_y")
                style.prop(item, "focus_fill_color")
                style.prop(item, "press_fill_color")
            elif item.fill_type in {"IMAGE", "VIDEO", "SEQUENCE"}:
                style.prop(item, "media_path")
            style.prop(item, "use_border")
            if item.use_border:
                style.prop(item, "border_fill_type")
                style.prop(item, "border_thickness")
                if item.border_fill_type == "COLOR_RAMP":
                    style.prop(item, "border_ramp_color_a")
                    style.prop(item, "border_ramp_color_b")
                else:
                    style.prop(item, "border_color")
            text_box = detail.box()
            text_box.label(text="Text Block Layout", icon="FONT_DATA")
            row = text_box.row(align=True)
            row.prop(item, "text_align_x", expand=True)
            row = text_box.row(align=True)
            row.prop(item, "text_align_y", expand=True)
            row = text_box.row(align=True)
            row.prop(item, "text_padding_x")
            row.prop(item, "text_padding_y")
            text_box.prop(item, "text_font")
            text_box.prop(item, "text_size")
            text_box.prop(item, "text_kerning")
            row = text_box.row(align=True)
            row.prop(item, "container_padding_x")
            row.prop(item, "container_padding_y")
            text_box.prop(item, "text_color")
            if item.show_description:
                sub = text_box.box()
                sub.label(text="Sub Description", icon="TEXT")
                row = sub.row(align=True)
                row.prop(item, "description_gap")
                row.prop(item, "description_scale")
                sub.prop(item, "description_color")
            anim = detail.box()
            anim.label(text="Button Action FX", icon="IPO_EASE_IN_OUT")
            anim.prop(item, "focus_animation")
            anim.prop(item, "press_animation")
            detail.prop(item, "base_scale")
            detail.prop(item, "preview_state")
            detail.operator("agmf.cycle_preview_state", icon="ARROW_LEFTRIGHT")

        box = layout.box()
        box.label(text="Logo + Account HUD", icon="USER")
        box.prop(props, "logo_path")
        box.prop(props, "account_enabled")
        if props.account_enabled:
            box.prop(props, "account_name")
            box.prop(props, "account_value")

        box = layout.box()
        box.label(text="Soundtrack OS", icon="PLAY_SOUND")

        # Eye candy "Now Playing" preview in the UI Panel
        if props.soundtrack_tracks and _AUDIO_TRACK_INDEX >= 0 and _AUDIO_TRACK_INDEX < len(props.soundtrack_tracks):
            active_track = props.soundtrack_tracks[_AUDIO_TRACK_INDEX]
            preview_box = box.box()
            row = preview_box.row()
            custom_icon = get_track_icon_id(active_track.album_art_path) if getattr(active_track, "album_art_path", "") else 0
            if custom_icon:
                row.template_icon(icon_value=custom_icon, scale=4.0)
            col = row.column()
            col.label(text="NOW PLAYING", icon='PLAY')
            col.label(text=active_track.song_title or active_track.name or "Unknown Track")
            col.label(text=f"Artist: {active_track.artist}")
            col.label(text=f"Album: {active_track.album}")

        box.prop(props, "soundtrack_enabled")
        box.prop(props, "soundtrack_order")
        box.prop(props, "soundtrack_loop")
        box.prop(props, "show_now_playing")
        if props.show_now_playing:
            box.prop(props, "now_playing_duration")
        row = box.row()
        row.template_list("AGMF_UL_SoundtrackTracks", "", props, "soundtrack_tracks", props, "soundtrack_tracks_index", rows=5)
        col = row.column(align=True)
        col.operator("agmf.add_soundtrack_files", text="", icon="ADD")
        col.operator("agmf.remove_soundtrack_track", text="", icon="REMOVE")
        col.operator("agmf.sort_soundtrack", text="", icon="SORTALPHA")
        col.operator("agmf.shuffle_soundtrack", text="", icon="FILE_REFRESH")
        row = box.row(align=True)
        row.operator("agmf.preview_prev_soundtrack_track", text="Prev", icon="PREV_KEYFRAME")
        row.operator("agmf.preview_soundtrack_track", text="Play", icon="PLAY")
        row.operator("agmf.preview_next_soundtrack_track", text="Next", icon="NEXT_KEYFRAME")
        row.operator("agmf.stop_soundtrack_preview", text="Stop", icon="PAUSE")
        if props.soundtrack_tracks and props.soundtrack_tracks_index < len(props.soundtrack_tracks):
            track = props.soundtrack_tracks[props.soundtrack_tracks_index]
            tr_box = box.box()
            tr_box.prop(track, "song_title")
            tr_box.prop(track, "artist")
            tr_box.prop(track, "album")
            tr_box.prop(track, "track_number")
            tr_box.prop(track, "album_art_path")
            tr_box.prop(track, "show_in_soundtrack_page")
            tr_box.prop(track, "volume")
            row = tr_box.row(align=True)
            row.prop(track, "fade_in")
            row.prop(track, "fade_out")

        box = layout.box()
        box.label(text="Preview + Runtime", icon="CONSOLE")
        row = box.row(align=True)
        row.operator("agmf.preview_config", icon="TEXT")
        row.operator("agmf.export_upbge_notes", icon="EXPORT")
        row = box.row(align=True)
        row.operator("agmf.generate_runtime_scripts", text="Generate Runtime", icon="SCRIPT").write_files = False
        row.operator("agmf.generate_runtime_scripts", text="Write Files", icon="FILE_TICK").write_files = True
        box.prop(props, "runtime_script_path")
        box.prop(props, "config_json_path")
        box.prop(props, "preview_text", text="")


classes = (
    AGMF_MenuItem,
    AGMF_MenuPanel,
    AGMF_MenuScreen,
    AGMF_LiveSceneSlot,
    AGMF_BackgroundMediaLayer,
    AGMF_NowPlayingWidget,
    AGMF_OT_SaveWidgetPreset,
    AGMF_OT_DeleteWidgetPreset,
    AGMF_SoundtrackTrack,
    AGMF_Properties,
    AGMF_UL_MenuItems,
    AGMF_UL_MenuPanels,
    AGMF_UL_MenuScreens,
    AGMF_UL_LiveSceneSlots,
    AGMF_UL_BackgroundMediaLayers,
    AGMF_UL_SoundtrackTracks,
    AGMF_OT_CreateMenuRoot,
    AGMF_OT_AddMenuItem,
    AGMF_OT_RemoveMenuItem,
    AGMF_OT_MoveMenuItem,
    AGMF_OT_AddPanel,
    AGMF_OT_RemovePanel,
    AGMF_OT_AssignSelectedItemsToPanel,
    AGMF_OT_NudgePanel,
    AGMF_OT_ApplyPanelLayout,
    AGMF_OT_ApplyPanelColors,
    AGMF_OT_ApplyPanelAll,
    AGMF_OT_FitPanelInsideBackdrop,
    AGMF_OT_AddScreen,
    AGMF_OT_RemoveScreen,
    AGMF_OT_MoveScreen,
    AGMF_OT_AddLiveSceneSlot,
    AGMF_OT_AddBackgroundMediaFiles,
    AGMF_OT_RemoveBackgroundMediaLayer,
    AGMF_OT_MoveBackgroundMediaLayer,
    AGMF_OT_SetBackgroundLayerAsCanvas,
    AGMF_OT_RemoveLiveSceneSlot,
    AGMF_OT_RebuildMenu,
    AGMF_OT_ApplyTheme,
    AGMF_OT_CyclePreviewState,
    AGMF_OT_PreviewConfig,
    AGMF_OT_LoadTemplate,
    AGMF_OT_AddSoundtrackFiles,
    AGMF_OT_RemoveSoundtrackTrack,
    AGMF_OT_SortSoundtrack,
    AGMF_OT_ShuffleSoundtrack,
    AGMF_OT_PreviewSoundtrackTrack,
    AGMF_OT_PreviewPreviousSoundtrackTrack,
    AGMF_OT_PreviewNextSoundtrackTrack,
    AGMF_OT_StopSoundtrackPreview,
    AGMF_OT_PreviewBackgroundMedia,
    AGMF_OT_StopVideoPreview,
    AGMF_OT_PreviewSceneSwitch,
    AGMF_OT_GenerateRuntimeScripts,
    AGMF_OT_ExportUpbgeNotes,
    AGMF_PT_MainPanel,
    AGMF_PT_NowPlayingWidgetPanel,
)


def register():
    global _CUSTOM_ICONS
    try:
        import bpy.utils.previews
        _CUSTOM_ICONS = bpy.utils.previews.new()
    except Exception:
        pass
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.agmf_props = PointerProperty(type=AGMF_Properties)

    if not bpy.app.timers.is_registered(autoplay_tick):
        bpy.app.timers.register(autoplay_tick)
    if not bpy.app.timers.is_registered(widget_anim_tick):
        bpy.app.timers.register(widget_anim_tick)


def unregister():
    global _CUSTOM_ICONS

    if bpy.app.timers.is_registered(autoplay_tick):
        bpy.app.timers.unregister(autoplay_tick)
    if bpy.app.timers.is_registered(widget_anim_tick):
        bpy.app.timers.unregister(widget_anim_tick)

    if _CUSTOM_ICONS is not None:
        try:
            import bpy.utils.previews
            bpy.utils.previews.remove(_CUSTOM_ICONS)
        except Exception:
            pass
        _CUSTOM_ICONS = None
    del bpy.types.Scene.agmf_props
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
