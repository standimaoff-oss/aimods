/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  net.minecraft.core.registries.BuiltInRegistries
 *  net.minecraft.core.registries.Registries
 *  net.minecraft.network.chat.Component
 *  net.minecraft.resources.ResourceKey
 *  net.minecraft.resources.ResourceLocation
 *  net.minecraft.world.item.CreativeModeTab
 *  net.minecraft.world.item.CreativeModeTab$Output
 *  net.minecraft.world.item.Item
 *  net.minecraft.world.item.ItemStack
 *  net.minecraft.world.level.ItemLike
 *  net.minecraftforge.registries.DeferredRegister
 *  net.minecraftforge.registries.RegistryObject
 */
package ru.aiforge.realwar.registry;

import ru.aiforge.realwar.missile.MissileType;
import ru.aiforge.realwar.registry.ModBlocks;
import ru.aiforge.realwar.registry.ModItems;
import ru.aiforge.realwar.registry.ModS3;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.function.Supplier;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.CreativeModeTab;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ItemLike;
import net.minecraftforge.registries.DeferredRegister;
import net.minecraftforge.registries.RegistryObject;

public final class ModTabs {
    public static final DeferredRegister<CreativeModeTab> TABS = DeferredRegister.create((ResourceKey)Registries.CREATIVE_MODE_TAB, (String)"aiarsenal");
    private static final Map<String, Cat> MAP = new java.util.LinkedHashMap<String, Cat>();
    public static final RegistryObject<CreativeModeTab> NUCLEAR;
    public static final RegistryObject<CreativeModeTab> MISSILES;
    public static final RegistryObject<CreativeModeTab> VEHICLES;
    public static final RegistryObject<CreativeModeTab> DRONES;
    public static final RegistryObject<CreativeModeTab> AMMO;
    public static final RegistryObject<CreativeModeTab> PARTS;
    public static final RegistryObject<CreativeModeTab> INDUSTRY;
    public static final RegistryObject<CreativeModeTab> PROTECTION;
    public static final RegistryObject<CreativeModeTab> FORTIFICATION;
    public static final RegistryObject<CreativeModeTab> WEAPONS;
    public static final RegistryObject<CreativeModeTab> BUILDING;
    public static final RegistryObject<CreativeModeTab> UNIFORMS;

    private ModTabs() {
    }

    private static void put(Cat c, String ... names) {
        for (String n : names) {
            MAP.put(n, c);
        }
    }

    public static Cat tabOf(String path) {
        return MAP.get(path);
    }

    public static Set<String> mappedNames() {
        return new HashSet<String>(MAP.keySet());
    }

    private static RegistryObject<CreativeModeTab> tab(String id, Cat cat, Supplier<ItemStack> icon) {
        return TABS.register(id, () -> CreativeModeTab.builder().title((Component)Component.translatable((String)("itemGroup.aiarsenal." + id))).icon(icon).displayItems((params, out) -> {
            ArrayList<Item> list = new ArrayList<Item>();
            for (Map.Entry<String, Cat> en : MAP.entrySet()) {
                if (en.getValue() != cat) continue;
                ResourceLocation key = new ResourceLocation("aiarsenal", en.getKey());
                if (BuiltInRegistries.ITEM.containsKey(key)) list.add((Item)BuiltInRegistries.ITEM.get(key));
            }
            list.forEach(arg_0 -> ((CreativeModeTab.Output)out).accept(arg_0));
        }).build());
    }

    static {
        // one set of sections for the whole mod (Real War + Tu bombers + BM-21 + arsenal)
        ModTabs.put(Cat.VEHICLES, "bm21", "grad_vehicle", "smerch_vehicle", "s400_vehicle", "zu23_vehicle", "t90m_vehicle", "plasma_tank_vehicle", "abrams_vehicle", "bmp3_vehicle", "msta_vehicle", "d30_vehicle", "m777_vehicle", "pz2_vehicle", "pz4_vehicle", "tiger_vehicle", "sturmtiger_vehicle", "maus_vehicle", "ratte_vehicle", "t34_vehicle", "kv2_vehicle", "is2_vehicle", "kv5_vehicle", "bm13_vehicle", "bradley_vehicle", "tos1a_vehicle", "ural_vehicle", "radar_mobile_vehicle", "radar_post_vehicle", "yars_tel", "cruise_launcher", "shahed_rail", "tu95ms", "tu160", "tu95_vehicle", "ka52_vehicle", "ah64_vehicle", "raptor_boat", "cb90_boat", "sub636_vehicle", "bismarck_ship", "bf109_plane", "yak3_plane", "he111_plane", "pe8_plane", "su57_plane", "plasmaheli_vehicle", "starship_plane", "sanctuary_remote");
        ModTabs.put(Cat.DRONES, "mq9", "orion", "shahed136", "shahed131", "shahed238", "liutyi", "fpv7", "fpv10", "tablet", "fpv_goggles");
        ModTabs.put(Cat.NUCLEAR, "yars", "rds1", "an602", "detonator", "little_boy", "rds_4", "arming_plug", "remote_detonator", "barometric_fuze", "lb_casing", "rds_core", "rds_casing", "cordite", "bridgewire_detonator");
        ModTabs.put(Cat.MISSILES, "kh101", "kh55", "kalibr", "tomahawk", "missile_tactical_he", "missile_tactical_kinetic", "missile_tactical_mirv", "missile_tactical_thermobaric", "missile_operational_he", "missile_operational_kinetic", "missile_operational_mirv", "missile_operational_penetrator", "missile_cruise_he", "missile_cruise_cluster", "missile_icbm_he", "missile_icbm_kinetic", "missile_icbm_mirv", "missile_icbm_mirv_heavy", "launch_pad_1", "launch_pad_2", "launch_pad_3", "launch_computer", "siren");
        ModTabs.put(Cat.AMMO, "grenade_rgd5", "grenade_f1", "grenade_flashbang", "grenade_smoke_white", "grenade_smoke_red", "grenade_smoke_green", "grenade_smoke_blue", "grenade_incendiary");
        ModTabs.put(Cat.AMMO, "rocket_9m22u", "rocket_9m28f", "rocket_9m22s", "rocket_9m218", "rocket_9m43", "grad_rocket", "smerch_rocket", "sam_48n6", "flak_ammo_box", "shells_125", "shells_120", "shells_100", "shells_122", "shells_152", "shells_155", "shells_20", "shells_75", "shells_88", "shells_85", "shells_107", "shells_128", "shells_280", "rocket_380", "rocket_m13", "shells_25", "rocket_220", "fab250", "fab500", "fab1500", "fab500m54", "fab1500m54", "fab5000", "sc250", "sc1000", "fab250sv", "fab1000", "craft_service_kit");
        ModTabs.put(Cat.PARTS, "propellant_grain", "rocket_motor_122", "rocket_motor_300", "warhead_122", "warhead_300", "contact_fuze", "proximity_fuze", "radar_seeker", "guidance_unit", "sam_motor", "sam_warhead", "diesel_engine", "truck_wheel", "hydraulic_drive", "chassis_6x6", "chassis_8x8", "armored_cab", "launcher_package_122", "launcher_package_300", "sam_launcher_frame", "gun_mount_23", "gun_barrels_23");
        ModTabs.put(Cat.INDUSTRY, "uranium_ore", "deepslate_uranium_ore", "raw_uranium", "uranium_ingot", "steel_ingot", "steel_plate", "steel_tube", "rubberized_fabric", "scorched_earth", "trinitite");
        ModTabs.put(Cat.PROTECTION, "rangefinder", "artillery_designator", "radio", "geiger_counter", "potassium_iodide", "hazmat_helmet", "hazmat_chestplate", "hazmat_leggings", "hazmat_boots");
        ModTabs.put(Cat.FORTIFICATION, "sandbags", "barbed_wire", "concertina_wire", "czech_hedgehog", "dragon_teeth", "concrete_barrier", "camo_net", "reinforced_concrete", "steel_block", "trench_wall", "trench_wall_tin", "duckboard", "firing_step", "fuel_drum_olive", "fuel_drum_red", "fuel_drum_blue", "egoza", "bruno_spiral", "mine_pmn2", "mine_tm62", "mine_mon50", "mine_ozm72", "tripwire_f1", "bear_trap", "warning_sign_mines", "warning_sign_radiation", "warning_sign_voltage", "warning_sign_biohazard", "warning_sign_checkpoint", "warning_sign_noentry", "entrenching_tool");
        ModTabs.put(Cat.BUILDING, "flagpole", "flag_russia", "flag_ussr", "flag_germany", "flag_usa", "flag_uk", "flag_france", "flag_china", "flag_japan", "flag_balkenkreuz", "flag_vdv", "flag_vmf", "flag_vks", "flag_nato", "flag_un", "flag_white", "flag_victory", "lantern_hurricane", "lamp_bulkhead", "lamp_street", "lamp_flood", "beacon_red", "beacon_rotating", "searchlight", "armor_plate", "armor_plate_hazard", "armor_plate_star_red", "armor_plate_balkenkreuz", "armor_plate_us_star", "armor_plate_roundel", "armor_plate_vdv", "armor_plate_vmf");
        // >>> r16 doors
        ModTabs.put(Cat.BUILDING, "door_steel", "door_bunker", "door_bars", "door_wood_army", "door_lab", "hatch_steel", "hatch_bunker", "hatch_grate", "gate_sliding", "gate_swing", "gate_boom", "gate_blast", "camo_screen_forest", "camo_canopy_forest", "camo_bush_forest", "camo_screen_desert", "camo_canopy_desert", "camo_bush_dry", "camo_screen_winter", "camo_canopy_winter", "camo_bush_snow");
        // <<< r16 doors
        // >>> r17
        ModTabs.put(Cat.BUILDING, "wreck_tank_hull", "wreck_tank_turret", "wreck_tank_track", "wreck_heli_body", "wreck_heli_tail", "wreck_heli_rotor", "wreck_jet_body", "wreck_jet_wing", "wreck_jet_tail", "crate_ammo", "crate_medical", "crate_military", "crate_weapons", "crate_secret");
        ModTabs.put(Cat.FORTIFICATION, "trap_punji", "trap_spike_strip", "trap_flare", "trap_ied", "trap_electric_fence");
        ModTabs.put(Cat.PROTECTION, "ration_irp", "bandage", "first_aid_kit");
        // <<< r17
        ModTabs.put(Cat.WEAPONS, "ak12", "mag_ak12", "m4a1", "mag_stanag", "t5000", "mag_t5000", "pkp", "box_pkp", "saiga12", "mag_saiga12", "r870", "shell_12", "rpg7", "pg7v", "igla", "igla_missile", "stinger", "stinger_missile", "javelin", "javelin_missile", "ppsh41", "mag_ppsh", "mp40", "mag_mp40", "mosin", "clip_mosin", "k98k", "clip_k98", "laser", "mag_laser", "plasma", "mag_plasma", "plasma_charge");
        VEHICLES = ModTabs.tab("vehicles", Cat.VEHICLES, () -> new ItemStack((ItemLike)ModItems.GRAD_VEHICLE.get()));
        DRONES = ModTabs.tab("drones", Cat.DRONES, () -> new ItemStack((ItemLike)BuiltInRegistries.ITEM.get(new ResourceLocation("aiarsenal", "shahed136"))));
        NUCLEAR = ModTabs.tab("nuclear", Cat.NUCLEAR, () -> new ItemStack((ItemLike)ModItems.LITTLE_BOY.get()));
        MISSILES = ModTabs.tab("missiles", Cat.MISSILES, () -> new ItemStack((ItemLike)ModS3.missileItem(MissileType.ICBM_MIRV).get()));
        AMMO = ModTabs.tab("ammo", Cat.AMMO, () -> new ItemStack((ItemLike)ModItems.GRAD_ROCKET.get()));
        PARTS = ModTabs.tab("parts", Cat.PARTS, () -> new ItemStack((ItemLike)ModItems.DIESEL_ENGINE.get()));
        INDUSTRY = ModTabs.tab("industry", Cat.INDUSTRY, () -> new ItemStack((ItemLike)ModItems.URANIUM_INGOT.get()));
        PROTECTION = ModTabs.tab("protection", Cat.PROTECTION, () -> new ItemStack((ItemLike)ModItems.GEIGER_COUNTER.get()));
        WEAPONS = ModTabs.tab("weapons", Cat.WEAPONS, () -> new ItemStack((ItemLike)ModItems.RPG7.get()));
        BUILDING = ModTabs.tab("building", Cat.BUILDING, () -> new ItemStack((ItemLike)ModItems.SEARCHLIGHT.get()));
        for (String set : ru.aiforge.realwar.item.UniformItem.SETS)
            for (String sl : new String[]{"head", "chest", "legs", "feet"}) ModTabs.put(Cat.UNIFORMS, "uniform_" + set + "_" + sl);
        UNIFORMS = ModTabs.tab("uniforms", Cat.UNIFORMS, () -> new ItemStack((ItemLike)ModItems.UNIFORMS.get("uniform_ru_general_head").get()));
        FORTIFICATION = ModTabs.tab("fortification", Cat.FORTIFICATION, () -> new ItemStack((ItemLike)ModItems.CZECH_HEDGEHOG.get()));
    }

    public static enum Cat {
        NUCLEAR,
        MISSILES,
        VEHICLES,
        DRONES,
        AMMO,
        PARTS,
        INDUSTRY,
        PROTECTION,
        FORTIFICATION,
        WEAPONS,
        BUILDING,
        UNIFORMS;

    }
}

