import unrealsdk

from mods_base import SliderOption, build_mod, hook
from unrealsdk.hooks import Type, Block
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

minimap_scale = SliderOption(
    identifier="Minimap Scale %",
    value=100,
    min_value=100,
    max_value=180,
    step=1,
    is_integer=True,
    description="Minimap size as a percentage. 100% = original size."
)

minimap_target_world_radius = SliderOption(
    identifier="Minimap Target World Radius",
    value=5500,
    min_value=5500,
    max_value=10000,
    step=100,
    is_integer=True,
    description="Minimap world/radar radius."
)

hud_active = False


last_minimap = None
last_scale = None

last_radius_minimap = None
last_radius = None


def get_display_info(minimap):
    try:
        dummy = unrealsdk.make_struct("GFxObject:ASDisplayInfo")
        result = minimap.GetDisplayInfo(dummy)

        if isinstance(result, tuple) and len(result) >= 2:
            return result[1]

    except Exception:
        pass

    return None


def resize_minimap_widget(minimap):
    global last_minimap
    global last_scale

    if minimap is None:
        return

    scale = float(minimap_scale.value)

    # already applied to this minimap
    if minimap is last_minimap and scale == last_scale:
        return

    display_info = get_display_info(minimap)

    if display_info is None:
        return

    try:
        display_info.XScale = scale
        display_info.YScale = scale
        display_info.hasXScale = True
        display_info.hasYScale = True

        minimap.SetDisplayInfo(display_info)

    except Exception:
        return

    last_minimap = minimap
    last_scale = scale


def resize_minimap_world_radius(minimap):
    global last_radius_minimap
    global last_radius

    if minimap is None:
        return

    radius = float(minimap_target_world_radius.value)

    # already applied to this minimap
    if minimap is last_radius_minimap and radius == last_radius:
        return

    try:
        if float(minimap.WorldRadius) != radius:
            minimap.WorldRadius = radius

        if float(minimap.TargetWorldRadius) != radius:
            minimap.TargetWorldRadius = radius

    except Exception:
        return

    last_radius_minimap = minimap
    last_radius = radius

def resize_gfx_clip(clip, scale):
    if clip is None:
        return

    info = get_display_info(clip)

    if info is None:
        return

    info.XScale = scale
    info.YScale = scale
    info.hasXScale = True
    info.hasYScale = True

    try:
        clip.SetDisplayInfo(info)
    except Exception as e:
        print(f"GFx SCALE ERROR {clip}: {e}")

def resize_minimap_elements(minimap):
    widget_scale = float(minimap_scale.value)

    inverse_scale = 10000.0 / widget_scale

    clips = [
        "DirArrowClip",
        "NorthMarkerClip",
    ]

    for name in clips:
        try:
            clip = getattr(minimap, name)

            if clip is not None:
                resize_gfx_clip(clip, inverse_scale)

        except Exception as e:
            print(f"RESIZE MINIMAP ELEMENT ERROR ({name}): {e}")
            pass

def update_minimap(hud):
    try:
        minimap = hud.MyMinimapWidget
    except Exception:
        return

    if minimap is None:
        return

    resize_minimap_widget(minimap)
    resize_minimap_world_radius(minimap)
    resize_minimap_elements(minimap)

@hook("WillowGame.WillowHUD:OpenHUDMovie", Type.POST)
def open_hud_movie(obj: UObject, _args: WrappedStruct, _ret, _func: BoundFunction):
    global hud_active
    
    hud_active = True
    update_minimap(obj)


@hook("WillowGame.WillowHUD:HUDIsClosing", Type.POST)
def hud_closing(obj: UObject, _args: WrappedStruct, _ret, _func: BoundFunction):
    global hud_active

    hud_active = False

@hook("WillowGame.WillowPlayerController:UpdateHUDMinimapRadius", Type.PRE)
def update_hud_minimap_radius(_obj: UObject, _args: WrappedStruct, _ret, _func: BoundFunction):
    return Block

@hook("WillowGame.WillowPlayerController:PlayerTick", Type.POST)
def player_tick(obj: UObject, _args: WrappedStruct, _ret, _func: BoundFunction):
    global hud_active
    
    if not hud_active:
        return
    
    try:
        hud = obj.GetHUDMovie()
    except Exception:
        return

    if hud is not None:
        update_minimap(hud)

build_mod(
    options=[
        minimap_scale,
        minimap_target_world_radius
    ]
)
