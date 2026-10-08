package ru.aiforge.realwar.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.Holder;
import net.minecraft.tags.BiomeTags;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.biome.Biome;
import net.minecraft.world.level.biome.Biomes;
import net.minecraft.world.level.block.BarrelBlock;
import net.minecraft.world.level.block.BedBlock;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.CrossCollisionBlock;
import net.minecraft.world.level.block.DoorBlock;
import net.minecraft.world.level.block.HorizontalDirectionalBlock;
import net.minecraft.world.level.block.IronBarsBlock;
import net.minecraft.world.level.block.LadderBlock;
import net.minecraft.world.level.block.LanternBlock;
import net.minecraft.world.level.block.LeverBlock;
import net.minecraft.world.level.block.RedstoneLampBlock;
import net.minecraft.world.level.block.SlabBlock;
import net.minecraft.world.level.block.StairBlock;
import net.minecraft.world.level.block.TrapDoorBlock;
import net.minecraft.world.level.block.entity.BarrelBlockEntity;
import net.minecraft.world.level.block.entity.BlockEntity;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.properties.AttachFace;
import net.minecraft.world.level.block.state.properties.BedPart;
import net.minecraft.world.level.block.state.properties.DoorHingeSide;
import net.minecraft.world.level.block.state.properties.DoubleBlockHalf;
import net.minecraft.world.level.block.state.properties.Half;
import net.minecraft.world.level.block.state.properties.SlabType;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.Feature;
import net.minecraft.world.level.levelgen.feature.FeaturePlaceContext;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraft.world.phys.AABB;
import ru.aiforge.arsenal.registry.ArsenalRegistry;
import ru.aiforge.realwar.RWConfig;
import ru.aiforge.realwar.deco.DirectionalLampBlock;
import ru.aiforge.realwar.deco.FacingLampBlock;
import ru.aiforge.realwar.deco.FlagBlock;
import ru.aiforge.realwar.deco.FlagpoleBlock;
import ru.aiforge.realwar.deco.GateBlock;
import ru.aiforge.realwar.deco.GateKind;
import ru.aiforge.realwar.deco.LampBlock;
import ru.aiforge.realwar.deco.SearchlightBlock;
import ru.aiforge.realwar.deco.SearchlightBlockEntity;
import ru.aiforge.realwar.field.ElectricFenceBlock;
import ru.aiforge.realwar.field.WarningSignBlock;
import ru.aiforge.realwar.fort.FacingFortBlock;
import ru.aiforge.realwar.item.UniformItem;
import ru.aiforge.realwar.radar.RadarVehicleEntity;
import ru.aiforge.realwar.registry.ModBlocks;
import ru.aiforge.realwar.registry.ModEntities;
import ru.aiforge.realwar.registry.ModItems;
import ru.aiforge.realwar.vehicle.FlakEntity;
import ru.aiforge.realwar.vehicle.SamLauncherEntity;
import ru.aiforge.realwar.vehicle.VehicleEntity;
import ru.aiforge.realwar.vehicle.VehicleKind;

/**
 * Fortified Air-Defense (PVO) Military Base with a Multi-Room Underground Command Bunker.
 *
 * Surface layout (35x35 footprint, dx = -17..+17, dz = -17..+17):
 * - Outer anti-tank defence line (dragon's teeth, Czech hedgehogs, warning signs).
 * - Electrified security fence & reinforced concrete perimeter wall topped with Egoza razor wire.
 * - 4 corner guard towers with sandbag parapets, sweeping searchlights, and red obstruction beacons.
 * - Southern Checkpoint (KPP) with paved asphalt road, Jersey barriers, red/white barrier boom (GATE_BOOM),
 *   motorized sliding gate (GATE_SLIDING), guardhouse, and 6-block parade flagpole.
 * - Armored bunker roof mound & PVO complex:
 *   * Elevated steel/concrete radar tower with active spinning RADAR_POST.
 *   * Hardened West SAM revetment with camo canopy and deployed S-400 Triumph (4x 48N6 tubes erected at 88 deg, combat duty).
 *   * Hardened East radar pad with deployed mobile 96L6E radar vehicle (RADAR_MOBILE).
 *   * Twin sandbagged ZU-23-2 anti-aircraft gun emplacements on the bunker roof corners.
 *   * Bunded fuel & munitions depot in the SW courtyard.
 *
 * Underground Bunker layout (dy = -10..-1 beneath the surface PVO mound):
 * - Armored entrance casemate with 3x3 Blast Gate (GATE_BLAST), descending stairwell, and NBC Decontamination Airlock
 *   sealed by two hermetic handwheel bunker doors (DOOR_BUNKER).
 * - Central PVO Command & Radar Control Center (illuminated tactical map table, S-400/radar control consoles, flags, secret loot).
 * - West North Wing: Armory, SAM missile & uniform vault behind steel bars door (DOOR_BARS) with weapon/ammo/secret crates
 *   and lockers stocked with RKKA & Wehrmacht uniforms, S-400 missiles, and small arms.
 * - West South Wing: Underground Medical Bay behind lab door (DOOR_LAB) with hospital beds and medical crates.
 * - East South Wing: Garrison Barracks & Mess Hall with 2-tier military bunks, lockers, and rations.
 * - East North Wing: Diesel Generator & Air Filtration (FVU) room with floor grates (HATCH_GRATE) and vertical emergency
 *   escape shaft climbing a ladder up to a surface armoured bunker hatch (HATCH_BUNKER).
 */
public class MilitaryBaseFeature extends Feature<NoneFeatureConfiguration> {
    public static final int RADIUS = 17;

    public MilitaryBaseFeature() {
        super(NoneFeatureConfiguration.CODEC);
    }

    @Override
    public boolean place(FeaturePlaceContext<NoneFeatureConfiguration> ctx) {
        if (!RWConfig.COMMON.militaryBases.get()) return false;
        WorldGenLevel level = ctx.level();
        BlockPos o = ctx.origin();
        // Center in chunk so the entire 35x35 footprint (-17..+17) stays strictly inside the 3x3 chunk WorldGenRegion
        int cx = (o.getX() & ~15) + 8;
        int cz = (o.getZ() & ~15) + 8;
        int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, cx, cz);
        BlockPos origin = new BlockPos(cx, y, cz);
        if (!canPlaceAt(level, origin)) return false;
        build(level, origin, ctx.random(), false);
        return true;
    }

    private static boolean canPlaceAt(WorldGenLevel level, BlockPos origin) {
        if (origin.getY() < level.getMinBuildHeight() + 16 || origin.getY() > level.getMaxBuildHeight() - 18) {
            return false;
        }
        Holder<Biome> b = level.getBiome(origin);
        if (b.is(BiomeTags.IS_OCEAN) || b.is(BiomeTags.IS_RIVER) || b.is(BiomeTags.IS_BEACH) || b.is(BiomeTags.IS_DEEP_OCEAN)) {
            return false;
        }
        int y0 = origin.getY();
        int minY = y0, maxY = y0;
        for (int dx = -14; dx <= 14; dx += 7) {
            for (int dz = -14; dz <= 14; dz += 7) {
                int x = origin.getX() + dx;
                int z = origin.getZ() + dz;
                int y = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, x, z);
                BlockPos ground = new BlockPos(x, y - 1, z);
                BlockState gs = level.getBlockState(ground);
                if (!gs.getFluidState().isEmpty() || !level.getFluidState(ground.above()).isEmpty()) {
                    return false;
                }
                minY = Math.min(minY, y);
                maxY = Math.max(maxY, y);
            }
        }
        return (maxY - minY) <= 7;
    }

    public static void build(WorldGenLevel level, BlockPos origin, RandomSource rand, boolean force) {
        // Ensure the 10-block-deep underground bunker (-10..-1) never drops below bedrock in shallow superflat worlds
        int minSafeY = level.getMinBuildHeight() + 11;
        if (origin.getY() < minSafeY) {
            origin = new BlockPos(origin.getX(), minSafeY, origin.getZ());
        }
        Holder<Biome> b = level.getBiome(origin);
        boolean cold = b.value().coldEnoughToSnow(origin) || b.is(BiomeTags.IS_MOUNTAIN);
        boolean sandy = b.is(Biomes.DESERT) || b.is(BiomeTags.IS_BADLANDS) || b.is(Biomes.SAVANNA) || b.is(Biomes.SAVANNA_PLATEAU);

        Block camoCanopy = (cold ? ModBlocks.CAMO_CANOPY_WINTER : sandy ? ModBlocks.CAMO_CANOPY_DESERT : ModBlocks.CAMO_CANOPY_FOREST).get();
        Block camoScreen = (cold ? ModBlocks.CAMO_SCREEN_WINTER : sandy ? ModBlocks.CAMO_SCREEN_DESERT : ModBlocks.CAMO_SCREEN_FOREST).get();
        Block camoBush = (cold ? ModBlocks.CAMO_BUSH_SNOW : sandy ? ModBlocks.CAMO_BUSH_DRY : ModBlocks.CAMO_BUSH_FOREST).get();

        Block rc = ModBlocks.REINFORCED_CONCRETE.get();
        Block steel = ModBlocks.STEEL_BLOCK.get();
        Block armor = ModBlocks.ARMOR_PLATE.get();
        Block hazard = ModBlocks.ARMOR_PLATE_HAZARD.get();
        Block redStar = ModBlocks.ARMOR_PLATE_STAR_RED.get();

        // 1. Clear air volume above compound and build engineered terrain foundation
        prepareFoundationAndClear(level, origin, rc, sandy, cold, force);

        // 2. Build the Deep Multi-Room Underground Command Bunker (dy = -10..-1)
        buildUndergroundBunker(level, origin, rand, rc, steel, armor, hazard, redStar);

        // 3. Build the Armored Surface Bunker Mound, Blast Portal & PVO Emplacements (dy = +1..+6)
        buildSurfaceBunkerAndPvoPads(level, origin, rand, rc, steel, armor, hazard, redStar, camoCanopy, camoScreen);

        // 4. Build the Courtyard, Checkpoint (KPP), Gates, Fuel Depot & Flagpole (dz = +6..+17)
        buildCourtyardAndCheckpoint(level, origin, rand, rc, steel, armor, hazard, redStar, camoCanopy, camoBush);

        // 5. Build the Perimeter Wall, Live Electric Fence, Egoza Wire, 4 Watchtowers & Outer Anti-Tank Obstacles
        buildPerimeterAndWatchtowers(level, origin, rand, rc, steel, armor, hazard, camoCanopy);

        // 6. Refresh fortification connections (sandbags, wire, egoza, electric fence)
        SiteUtil.connectFort(level, origin, RADIUS);

        // 7. Spawn Active Air-Defense (PVO) Vehicles & Emplacements on top of the Base/Bunker
        spawnPvoUnits(level, origin);
    }

    private static void prepareFoundationAndClear(WorldGenLevel level, BlockPos o, Block rc, boolean sandy, boolean cold, boolean force) {
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockState rcSt = rc.defaultBlockState();
        BlockState stoneBricks = Blocks.STONE_BRICKS.defaultBlockState();
        BlockState gravel = (sandy ? Blocks.SMOOTH_SANDSTONE : Blocks.ANDESITE).defaultBlockState();
        BlockState courtyardFloor = Blocks.POLISHED_ANDESITE.defaultBlockState();

        for (int dx = -RADIUS; dx <= RADIUS; dx++) {
            for (int dz = -RADIUS; dz <= RADIUS; dz++) {
                // Clear trees/foliage/blocks above surface (dy = +1..+13)
                for (int dy = 1; dy <= 13; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
                boolean insidePerimeter = Math.abs(dx) <= 15 && Math.abs(dz) <= 15;
                BlockState topSurface = insidePerimeter ? courtyardFloor : gravel;
                set(level, o.offset(dx, 0, dz), topSurface);
                // Retaining wall / solid fill downward so base never floats on slopes
                for (int dy = -1; dy >= -11; dy--) {
                    BlockPos p = o.offset(dx, dy, dz);
                    if (insidePerimeter && dy >= -10 && dx >= -14 && dx <= 14 && dz >= -12 && dz <= 6) {
                        // Underground bunker volume will be carved & built next
                        continue;
                    }
                    BlockState cur = level.getBlockState(p);
                    if (cur.isAir() || !cur.getFluidState().isEmpty() || cur.canBeReplaced()) {
                        set(level, p, insidePerimeter ? rcSt : stoneBricks);
                    } else if (dy < -3) {
                        break;
                    }
                }
            }
        }

        // Main asphalt road from outer approach (dz = +17) through KPP gates into courtyard (dz = +6)
        BlockState asphalt = Blocks.POLISHED_BLACKSTONE.defaultBlockState();
        BlockState curb = Blocks.SMOOTH_STONE.defaultBlockState();
        BlockState roadLine = Blocks.YELLOW_CONCRETE.defaultBlockState();
        for (int dz = 6; dz <= RADIUS; dz++) {
            for (int dx = -3; dx <= 3; dx++) {
                if (Math.abs(dx) == 3) {
                    set(level, o.offset(dx, 0, dz), curb);
                } else if (dx == 0 && dz % 2 == 0) {
                    set(level, o.offset(dx, 0, dz), roadLine);
                } else {
                    set(level, o.offset(dx, 0, dz), asphalt);
                }
            }
        }

        // If raised above shallow ground (e.g. default superflat), build a south approach ramp up to the KPP gate
        if (force) {
            int groundY = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, o.getX(), o.getZ() + RADIUS + 1) - 1;
            int diff = o.getY() - groundY;
            if (diff > 0 && diff <= 12) {
                for (int step = 1; step <= diff; step++) {
                    int dz = RADIUS + step;
                    int ry = o.getY() - step + 1;
                    for (int dx = -3; dx <= 3; dx++) {
                        set(level, new BlockPos(o.getX() + dx, ry, o.getZ() + dz),
                                Math.abs(dx) == 3 ? stair(Blocks.STONE_BRICK_STAIRS, Direction.NORTH, Half.BOTTOM)
                                        : stair(Blocks.POLISHED_BLACKSTONE_STAIRS, Direction.NORTH, Half.BOTTOM));
                        for (int fy = groundY; fy < ry; fy++) {
                            set(level, new BlockPos(o.getX() + dx, fy, o.getZ() + dz), stoneBricks);
                        }
                    }
                }
            }
        }
    }

    private static void buildUndergroundBunker(WorldGenLevel level, BlockPos o, RandomSource rand,
                                               Block rc, Block steel, Block armor, Block hazard, Block redStar) {
        BlockState air = Blocks.AIR.defaultBlockState();
        BlockState rcSt = rc.defaultBlockState();
        BlockState steelSt = steel.defaultBlockState();
        BlockState armorSt = armor.defaultBlockState();
        BlockState hazardSt = hazard.defaultBlockState();
        BlockState floorSt = Blocks.POLISHED_DEEPSLATE.defaultBlockState();
        BlockState subFloorSt = Blocks.DEEPSLATE_TILES.defaultBlockState();
        BlockState wallTrim = Blocks.POLISHED_ANDESITE.defaultBlockState();

        // Outer armored shell: dx = -14..+14, dz = -12..+5, dy = -10..-1
        for (int dx = -14; dx <= 14; dx++) {
            for (int dz = -12; dz <= 5; dz++) {
                for (int dy = -10; dy <= -1; dy++) {
                    BlockPos p = o.offset(dx, dy, dz);
                    if (dy == -10) {
                        set(level, p, rcSt);
                    } else if (dy == -9) {
                        set(level, p, floorSt);
                    } else if (dy == -3) {
                        set(level, p, steelSt); // Steel blast ceiling
                    } else if (dy >= -2) {
                        set(level, p, rcSt);    // 2m reinforced concrete burster slab
                    } else if (Math.abs(dx) >= 13 || dz <= -11 || dz >= 5) {
                        // 2-block thick outer reinforced concrete & steel armor shell
                        set(level, p, (dy == -6 && (Math.abs(dx) == 13 || dz == -11)) ? steelSt : rcSt);
                    } else {
                        set(level, p, air);
                    }
                }
            }
        }

        // Partition walls dividing the underground bunker into 6 functional rooms (dy = -8..-4):
        // West Partition Wall at dx = -5 (separates Command Center & Airlock from Armory & Medbay)
        // East Partition Wall at dx = +5 (separates Command Center & Airlock from Generator Room & Barracks)
        for (int dz = -10; dz <= 4; dz++) {
            for (int dy = -8; dy <= -4; dy++) {
                BlockState w = (dy == -8 || dy == -4) ? steelSt : rcSt;
                set(level, o.offset(-5, dy, dz), w);
                set(level, o.offset(5, dy, dz), w);
            }
        }
        // Cross wall between Command Center (dz = -10..-3) and Airlock Corridor (dz = -1..+4) at dz = -2
        for (int dx = -4; dx <= 4; dx++) {
            for (int dy = -8; dy <= -4; dy++) {
                set(level, o.offset(dx, dy, -2), (Math.abs(dx) == 2 || dy == -4) ? steelSt : rcSt);
            }
        }
        // Airlock side walls at dx = -2 and dx = +2 (dz = -2..+4)
        for (int dz = -2; dz <= 4; dz++) {
            for (int dy = -8; dy <= -4; dy++) {
                set(level, o.offset(-2, dy, dz), rcSt);
                set(level, o.offset(2, dy, dz), rcSt);
            }
        }
        // Cross wall on West Wing at dz = -2 (separates North Armory dz=-10..-3 from South Medbay dz=-1..+4)
        for (int dx = -12; dx <= -6; dx++) {
            for (int dy = -8; dy <= -4; dy++) {
                set(level, o.offset(dx, dy, -2), rcSt);
            }
        }
        // Cross wall on East Wing at dz = -4 (separates North Generator/FVU Room dz=-10..-5 from South Barracks dz=-3..+4)
        for (int dx = 6; dx <= 12; dx++) {
            for (int dy = -8; dy <= -4; dy++) {
                set(level, o.offset(dx, dy, -4), rcSt);
            }
        }

        // Transverse corridor connecting Airlock (dx=-2..+2) to West Medbay (dx=-5) and East Barracks (dx=+5) at dz = +1..+2
        for (int dx = -5; dx <= 5; dx++) {
            for (int dz = 1; dz <= 2; dz++) {
                if (Math.abs(dx) <= 1) continue;
                for (int dy = -8; dy <= -5; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
                set(level, o.offset(dx, -9, dz), hazardSt);
            }
            // Corridor walls at dz = 0 and dz = 3 between dx = -4..-3 and dx = +3..+4
            if (Math.abs(dx) == 3 || Math.abs(dx) == 4) {
                for (int dy = -8; dy <= -4; dy++) {
                    set(level, o.offset(dx, dy, 0), rcSt);
                    set(level, o.offset(dx, dy, 3), rcSt);
                    set(level, o.offset(dx, dy, 4), rcSt);
                    set(level, o.offset(dx, dy, -1), rcSt);
                }
            }
        }

        // ---- 1. DESCENDING BLAST STAIRWELL & DECONTAMINATION AIRLOCK (dx = -1..+1, dz = -1..+6) ----
        // Carve stairwell tunnel from surface portal (dz = +6, dy = +1) down to lower landing (dz = +3, dy = -8)
        for (int dz = 2; dz <= 6; dz++) {
            int stepBaseY = -8 + (dz - 2) * 2;
            for (int dx = -2; dx <= 2; dx++) {
                for (int dy = stepBaseY - 1; dy <= stepBaseY + 4; dy++) {
                    if (Math.abs(dx) == 2 || dy == stepBaseY - 1 || dy == stepBaseY + 4) {
                        set(level, o.offset(dx, dy, dz), (dy == stepBaseY + 4) ? steelSt : rcSt);
                    } else {
                        set(level, o.offset(dx, dy, dz), air);
                    }
                }
            }
        }
        // Build clean walkable stairs from dz = +6 (dy = 0) down to dz = +2 (dy = -8)
        for (int i = 0; i <= 8; i++) {
            // Two steps per Z or smooth 1:1 descent from dz = +6 down to dz = -2:
            // Let's place stairs from dz = +6 (dy = 0) to dz = +2 (dy = -4) and a second flight or continuous ramp:
        }
        // Let's make the stairwell 8 steps long (dz = +6 down to dz = -1, 1 step per block so players walk straight down/up without jumping!):
        // Wait: if stairs run dz = +6 (dy = -1) down to dz = -1 (dy = -8), then at dz = -1 you are at dy = -8!
        // Let's adjust the cross wall to dz = -3 so the Airlock is at dz = -2..0 and stairs descend smoothly from dz = +6 (dy = 0) to dz = -1 (dy = -7), landing at dz = -2 (dy = -8)!
        // Wait: let's make the stairwell start at dz = +8 (inside the extended casemate) or start at dz = +6 (dy = -1) down to dz = 0 (dy = -7), landing at dz = -1 (dy = -8)!
        // Let's check:
        // At dz = +7: surface threshold (dy = +1 air, dy = 0 hazard floor).
        // At dz = +6: dy = 0 stairs (facing NORTH)
        // At dz = +5: dy = -1 stairs
        // At dz = +4: dy = -2 stairs
        // At dz = +3: dy = -3 stairs
        // At dz = +2: dy = -4 stairs
        // At dz = +1: dy = -5 stairs
        // At dz =  0: dy = -6 stairs
        // At dz = -1: dy = -7 stairs
        // At dz = -2: dy = -8 flat landing inside the bunker!
        // Wait — if stairs are at dz = +6..0, what about the side doors to Medbay and Barracks?
        // We can put all 4 wing doors opening directly off the Central Command Hall & North/South side corridors at dy = -8!
        // Let's trace that! If all 4 wing rooms (Armory, Medbay, Generator, Barracks) open off the Central Hall (dx = -5 and dx = +5), then the player walks straight down the grand armored staircase (dz = +6 down to dz = -1) through the Outer Bunker Door at dz = +6 and Inner Bunker Door at dz = -2 directly into the Central Bunker Hall!
        // Let's verify how clean and walkable that is:
        // Every single step from dz = +6 (dy = 0) to dz = -1 (dy = -7) is a standard 1-block stair (`STONE_BRICK_STAIRS` facing SOUTH so you walk down going NORTH, with 4 blocks of headroom above every step)!
        buildGrandStairwell(level, o, rcSt, steelSt, hazardSt, air);

        // ---- 2. CENTRAL PVO COMMAND & RADAR CONTROL CENTER (dx = -4..+4, dz = -10..-3, dy = -8..-4) ----
        // Restore solid side walls at dx = ±2 for the stairwell (dz = -2..+4) and open the Command Hall (dx = -4..+4, dz = -10..-3)
        for (int dx = -4; dx <= 4; dx++) {
            for (int dz = -10; dz <= -3; dz++) {
                set(level, o.offset(dx, -9, dz), (Math.abs(dx) == 4 || dz == -10 || dz == -3) ? hazardSt : floorSt);
                for (int dy = -8; dy <= -4; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
            }
        }
        // Steel structural pillars in corners of Command Hall
        for (int cx : new int[]{-4, 4}) {
            for (int cz : new int[]{-10, -3}) {
                for (int dy = -8; dy <= -4; dy++) {
                    set(level, o.offset(cx, dy, cz), steelSt);
                }
            }
        }
        // Inner Hermetic Bunker Door (DOOR_BUNKER) at the bottom of the stairwell (dx = 0, dz = -2, dy = -8)
        for (int dx = -4; dx <= 4; dx++) {
            for (int dy = -8; dy <= -4; dy++) {
                set(level, o.offset(dx, dy, -2), (Math.abs(dx) <= 1 && dy <= -6) ? hazardSt : rcSt);
            }
        }
        set(level, o.offset(0, -8, -2), air);
        set(level, o.offset(0, -7, -2), air);
        placeAnimDoor(level, o.offset(0, -8, -2), ModBlocks.DOOR_BUNKER.get(), Direction.NORTH, DoorHingeSide.LEFT);
        // Warning signs flanking the inner bunker airlock door
        placeWallWarningSign(level, o.offset(-1, -7, -3), ModBlocks.WARNING_SIGN_RADIATION.get(), Direction.NORTH);
        placeWallWarningSign(level, o.offset(1, -7, -3), ModBlocks.WARNING_SIGN_NOENTRY.get(), Direction.NORTH);

        // Central Illuminated Tactical Air-Defense Map Table (dx = -1..+1, dz = -7..-5, dy = -8)
        for (int dx = -1; dx <= 1; dx++) {
            for (int dz = -7; dz <= -5; dz++) {
                set(level, o.offset(dx, -9, dz), Blocks.SEA_LANTERN.defaultBlockState());
                set(level, o.offset(dx, -8, dz), (dx == 0 && dz == -6)
                        ? Blocks.TINTED_GLASS.defaultBlockState()
                        : Blocks.SCULK_SENSOR.defaultBlockState());
            }
        }
        // Operator chairs around tactical table
        set(level, o.offset(-2, -8, -6), stair(Blocks.DARK_OAK_STAIRS, Direction.EAST, Half.BOTTOM));
        set(level, o.offset(2, -8, -6), stair(Blocks.DARK_OAK_STAIRS, Direction.WEST, Half.BOTTOM));
        set(level, o.offset(0, -8, -4), stair(Blocks.DARK_OAK_STAIRS, Direction.NORTH, Half.BOTTOM));

        // North Wall Radar & S-400 Fire-Control Console Bank (dx = -3..+3, dz = -10)
        for (int dx = -3; dx <= 3; dx++) {
            set(level, o.offset(dx, -8, -10), steelSt);
            if (dx == 0) {
                set(level, o.offset(dx, -7, -10), Blocks.REDSTONE_LAMP.defaultBlockState().setValue(RedstoneLampBlock.LIT, true));
                set(level, o.offset(dx, -9, -10), Blocks.REDSTONE_BLOCK.defaultBlockState());
                set(level, o.offset(dx, -6, -10), redStar.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.SOUTH));
            } else if (Math.abs(dx) == 1) {
                set(level, o.offset(dx, -7, -10), Blocks.OBSERVER.defaultBlockState().setValue(net.minecraft.world.level.block.ObserverBlock.FACING, Direction.SOUTH));
                set(level, o.offset(dx, -6, -10), Blocks.BLACK_STAINED_GLASS.defaultBlockState());
            } else if (Math.abs(dx) == 2) {
                set(level, o.offset(dx, -7, -10), Blocks.LECTERN.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.SOUTH));
                set(level, o.offset(dx, -6, -10), ModBlocks.ARMOR_PLATE_VDV.get().defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.SOUTH));
            } else {
                set(level, o.offset(dx, -7, -10), hazardSt);
            }
        }
        // Console control levers on the desk edge
        set(level, o.offset(-1, -8, -9), stair(Blocks.POLISHED_BLACKSTONE_STAIRS, Direction.NORTH, Half.TOP));
        set(level, o.offset(1, -8, -9), stair(Blocks.POLISHED_BLACKSTONE_STAIRS, Direction.NORTH, Half.TOP));
        set(level, o.offset(0, -8, -9), Blocks.LECTERN.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.SOUTH));

        // Ceiling bulkhead lamps & combat-alert red beacon in Command Center
        placeBulkheadLamp(level, o.offset(-2, -4, -8), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(2, -4, -8), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(-2, -4, -4), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(2, -4, -4), Direction.DOWN);
        set(level, o.offset(0, -8, -8), air);
        // Secret & Military Crates in the Command Center
        SiteUtil.placeCrate(level, o.offset(-3, -8, -9), ModBlocks.CRATE_SECRET.get(), Direction.SOUTH, rand);
        SiteUtil.placeCrate(level, o.offset(3, -8, -9), ModBlocks.CRATE_MILITARY.get(), Direction.SOUTH, rand);
        // Commander's Stocked Safe Locker
        placeStockedBarrel(level, o.offset(3, -8, -8), Direction.WEST,
                new ItemStack(ArsenalRegistry.TABLET.get()),
                new ItemStack(ArsenalRegistry.GOGGLES.get()),
                new ItemStack(ModItems.RADIO.get()),
                new ItemStack(ModItems.ARTILLERY_DESIGNATOR.get()),
                new ItemStack(ModItems.GEIGER_COUNTER.get()),
                new ItemStack(ModItems.REMOTE_DETONATOR.get()),
                uniform("rkka_officer", "head"),
                uniform("rkka_officer", "chest"),
                uniform("rkka_officer", "legs"),
                uniform("rkka_officer", "feet"),
                uniform("wehr_offizier", "head"),
                uniform("wehr_offizier", "chest"),
                uniform("wehr_offizier", "legs"),
                uniform("wehr_offizier", "feet")
        );

        // ---- 3. WEST NORTH WING: ARMORY, SAM MISSILE & UNIFORM VAULT (dx = -12..-6, dz = -10..-3) ----
        // Doorway from Command Center at dx = -5, dz = -6 (`DOOR_BARS` heavy steel bars door)
        set(level, o.offset(-5, -8, -6), air);
        set(level, o.offset(-5, -7, -6), air);
        placeAnimDoor(level, o.offset(-5, -8, -6), ModBlocks.DOOR_BARS.get(), Direction.WEST, DoorHingeSide.LEFT);
        placeWallWarningSign(level, o.offset(-4, -7, -5), ModBlocks.WARNING_SIGN_NOENTRY.get(), Direction.EAST);

        // Armory interior
        for (int dx = -12; dx <= -6; dx++) {
            for (int dz = -10; dz <= -3; dz++) {
                set(level, o.offset(dx, -9, dz), (dx == -6) ? hazardSt : floorSt);
            }
        }
        placeBulkheadLamp(level, o.offset(-9, -4, -8), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(-9, -4, -5), Direction.DOWN);

        // North rack: Weapons & Secret Crates
        SiteUtil.placeCrate(level, o.offset(-12, -8, -10), ModBlocks.CRATE_SECRET.get(), Direction.SOUTH, rand);
        SiteUtil.placeCrate(level, o.offset(-10, -8, -10), ModBlocks.CRATE_WEAPONS.get(), Direction.SOUTH, rand);
        SiteUtil.placeCrate(level, o.offset(-8, -8, -10), ModBlocks.CRATE_WEAPONS.get(), Direction.SOUTH, rand);
        SiteUtil.placeCrate(level, o.offset(-7, -8, -10), ModBlocks.CRATE_AMMO.get(), Direction.SOUTH, rand);

        // West wall shelving with Ammo & Military Crates
        for (int dz = -9; dz <= -4; dz++) {
            set(level, o.offset(-12, -7, dz), slab(Blocks.SMOOTH_STONE_SLAB, SlabType.TOP));
        }
        SiteUtil.placeCrate(level, o.offset(-12, -8, -8), ModBlocks.CRATE_WEAPONS.get(), Direction.EAST, rand);
        SiteUtil.placeCrate(level, o.offset(-12, -8, -6), ModBlocks.CRATE_AMMO.get(), Direction.EAST, rand);
        SiteUtil.placeCrate(level, o.offset(-12, -8, -4), ModBlocks.CRATE_MILITARY.get(), Direction.EAST, rand);
        SiteUtil.placeCrate(level, o.offset(-8, -8, -3), ModBlocks.CRATE_AMMO.get(), Direction.NORTH, rand);

        // Spare S-400 SAM missile canister cradle in center of Armory (dx = -10..-9, dz = -7..-6)
        set(level, o.offset(-10, -8, -7), hazardSt);
        set(level, o.offset(-9, -8, -7), hazardSt);
        set(level, o.offset(-10, -7, -7), ModBlocks.FUEL_DRUM_OLIVE.get().defaultBlockState());
        set(level, o.offset(-9, -7, -7), ModBlocks.FUEL_DRUM_OLIVE.get().defaultBlockState());

        // Stocked Armory Lockers (Small Arms + PVO Missiles + All WWII Uniform Sets)
        placeStockedBarrel(level, o.offset(-12, -6, -8), Direction.EAST,
                new ItemStack(ModItems.SAM_48N6.get(), 2),
                new ItemStack(ModItems.SAM_48N6.get(), 2),
                new ItemStack(ModItems.FLAK_AMMO_BOX.get(), 4),
                new ItemStack(ModItems.AK12.get()),
                new ItemStack(ModItems.MAG_AK12.get(), 6),
                new ItemStack(ModItems.PKP.get()),
                new ItemStack(ModItems.BOX_PKP.get(), 4),
                new ItemStack(ModItems.T5000.get()),
                new ItemStack(ModItems.MAG_T5000.get(), 5),
                new ItemStack(ModItems.RPG7.get()),
                new ItemStack(ModItems.PG7V.get(), 6),
                new ItemStack(ModItems.IGLA.get()),
                new ItemStack(ModItems.IGLA_MISSILE.get(), 4),
                new ItemStack(ModItems.PPSH41.get()),
                new ItemStack(ModItems.MAG_PPSH.get(), 6),
                new ItemStack(ModItems.MP40.get()),
                new ItemStack(ModItems.MAG_MP40.get(), 6),
                new ItemStack(ModItems.MOSIN.get()),
                new ItemStack(ModItems.CLIP_MOSIN.get(), 8),
                new ItemStack(ModItems.K98K.get()),
                new ItemStack(ModItems.CLIP_K98.get(), 8)
        );
        placeStockedBarrel(level, o.offset(-12, -6, -5), Direction.EAST,
                uniform("rkka_rifleman", "head"),
                uniform("rkka_rifleman", "chest"),
                uniform("rkka_rifleman", "legs"),
                uniform("rkka_rifleman", "feet"),
                uniform("rkka_winter", "head"),
                uniform("rkka_winter", "chest"),
                uniform("rkka_winter", "legs"),
                uniform("rkka_winter", "feet"),
                uniform("wehr_soldat", "head"),
                uniform("wehr_soldat", "chest"),
                uniform("wehr_soldat", "legs"),
                uniform("wehr_soldat", "feet"),
                uniform("wehr_panzer", "head"),
                uniform("wehr_panzer", "chest"),
                uniform("wehr_panzer", "legs"),
                uniform("wehr_panzer", "feet"),
                new ItemStack(ModItems.HAZMAT_HELMET.get()),
                new ItemStack(ModItems.HAZMAT_CHESTPLATE.get()),
                new ItemStack(ModItems.HAZMAT_LEGGINGS.get()),
                new ItemStack(ModItems.HAZMAT_BOOTS.get())
        );

        // ---- 4. WEST SOUTH WING: UNDERGROUND MEDICAL BAY (dx = -12..-6, dz = -1..+4) ----
        // Doorway from Armory/West Wing at dx = -8, dz = -2 (`DOOR_LAB` sterile white medical door)
        set(level, o.offset(-8, -8, -2), air);
        set(level, o.offset(-8, -7, -2), air);
        placeAnimDoor(level, o.offset(-8, -8, -2), ModBlocks.DOOR_LAB.get(), Direction.SOUTH, DoorHingeSide.LEFT);
        placeWallWarningSign(level, o.offset(-7, -7, -3), ModBlocks.WARNING_SIGN_BIOHAZARD.get(), Direction.NORTH);

        BlockState sterileFloor = Blocks.SMOOTH_QUARTZ.defaultBlockState();
        BlockState redCrossFloor = Blocks.RED_CONCRETE.defaultBlockState();
        BlockState sterileWall = Blocks.QUARTZ_BRICKS.defaultBlockState();
        for (int dx = -12; dx <= -6; dx++) {
            for (int dz = -1; dz <= 4; dz++) {
                boolean cross = (dx == -9 && dz >= 0 && dz <= 2) || (dz == 1 && dx >= -10 && dx <= -8);
                set(level, o.offset(dx, -9, dz), cross ? redCrossFloor : sterileFloor);
                for (int dy = -8; dy <= -4; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
                if (dx == -12) {
                    set(level, o.offset(dx, -7, dz), sterileWall);
                }
            }
        }
        placeBulkheadLamp(level, o.offset(-9, -4, 0), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(-9, -4, 3), Direction.DOWN);
        // Hospital Beds along West & South walls
        placeBed(level, o.offset(-11, -8, 0), Blocks.WHITE_BED, Direction.WEST);
        placeBed(level, o.offset(-11, -8, 2), Blocks.WHITE_BED, Direction.WEST);
        placeBed(level, o.offset(-11, -8, 4), Blocks.WHITE_BED, Direction.WEST);
        // Medical Crates & Surgical Table
        SiteUtil.placeCrate(level, o.offset(-6, -8, 0), ModBlocks.CRATE_MEDICAL.get(), Direction.WEST, rand);
        SiteUtil.placeCrate(level, o.offset(-6, -8, 2), ModBlocks.CRATE_MEDICAL.get(), Direction.WEST, rand);
        SiteUtil.placeCrate(level, o.offset(-6, -8, 4), ModBlocks.CRATE_MEDICAL.get(), Direction.WEST, rand);
        placeStockedBarrel(level, o.offset(-7, -8, 4), Direction.NORTH,
                new ItemStack(ModItems.FIRST_AID_KIT.get(), 8),
                new ItemStack(ModItems.BANDAGE.get(), 16),
                new ItemStack(ModItems.POTASSIUM_IODIDE.get(), 16),
                new ItemStack(ModItems.RATION_IRP.get(), 8)
        );

        // ---- 5. EAST NORTH WING: DIESEL GENERATOR, FVU FILTRATION & ESCAPE SHAFT (dx = +6..+12, dz = -10..-5) ----
        // Doorway from Command Center at dx = +5, dz = -8 (`DOOR_STEEL`)
        set(level, o.offset(5, -8, -8), air);
        set(level, o.offset(5, -7, -8), air);
        placeAnimDoor(level, o.offset(5, -8, -8), ModBlocks.DOOR_STEEL.get(), Direction.EAST, DoorHingeSide.LEFT);
        placeWallWarningSign(level, o.offset(4, -7, -7), ModBlocks.WARNING_SIGN_VOLTAGE.get(), Direction.WEST);

        for (int dx = 6; dx <= 12; dx++) {
            for (int dz = -10; dz <= -5; dz++) {
                set(level, o.offset(dx, -9, dz), (dz == -8) ? hazardSt : subFloorSt);
                for (int dy = -8; dy <= -4; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
            }
        }
        // Floor maintenance cable trench covered with steel HATCH_GRATE at dz = -7
        for (int dx = 7; dx <= 10; dx++) {
            set(level, o.offset(dx, -9, -7), Blocks.REDSTONE_BLOCK.defaultBlockState());
            placeHatch(level, o.offset(dx, -8, -7), ModBlocks.HATCH_GRATE.get(), Direction.NORTH, Half.BOTTOM, false);
        }
        // Twin Diesel-Electric Generator Turbines (dx = 7..9, dz = -10..-9)
        for (int dx = 7; dx <= 9; dx++) {
            set(level, o.offset(dx, -8, -10), (dx == 8) ? Blocks.BLAST_FURNACE.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.SOUTH) : steelSt);
            set(level, o.offset(dx, -7, -10), Blocks.COPPER_BLOCK.defaultBlockState());
            set(level, o.offset(dx, -6, -10), Blocks.IRON_BARS.defaultBlockState());
        }
        // Diesel Fuel Reserve Drums
        set(level, o.offset(11, -8, -6), ModBlocks.FUEL_DRUM_RED.get().defaultBlockState());
        set(level, o.offset(12, -8, -6), ModBlocks.FUEL_DRUM_RED.get().defaultBlockState());
        set(level, o.offset(12, -8, -5), ModBlocks.FUEL_DRUM_BLUE.get().defaultBlockState());
        placeBulkheadLamp(level, o.offset(8, -4, -8), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(11, -4, -8), Direction.DOWN);

        // Vertical Emergency Escape Shaft at (dx = 11, dz = -9) climbing from dy = -8 up to surface dy = +2
        for (int dy = -8; dy <= 2; dy++) {
            for (int sdx = 10; sdx <= 12; sdx++) {
                for (int sdz = -10; sdz <= -8; sdz++) {
                    if (sdx == 11 && sdz == -9) {
                        if (dy == 2) {
                            placeHatch(level, o.offset(11, 2, -9), ModBlocks.HATCH_BUNKER.get(), Direction.SOUTH, Half.BOTTOM, false);
                        } else {
                            set(level, o.offset(11, dy, -9), Blocks.LADDER.defaultBlockState().setValue(LadderBlock.FACING, Direction.SOUTH));
                        }
                    } else if (dy >= -3 || (sdx == 12 || sdz == -10)) {
                        set(level, o.offset(sdx, dy, sdz), (dy == 1) ? hazardSt : rcSt);
                    }
                }
            }
        }
        // Opening into the escape shaft at the bottom (dx = 11, dz = -8, dy = -8..-7)
        set(level, o.offset(11, -8, -8), air);
        set(level, o.offset(11, -7, -8), air);

        // ---- 6. EAST SOUTH WING: GARRISON BARRACKS & MESS HALL (dx = +6..+12, dz = -3..+4) ----
        // Doorway from Command Center at dx = +5, dz = -3 (`DOOR_WOOD_ARMY` military barracks door)
        set(level, o.offset(5, -8, -3), air);
        set(level, o.offset(5, -7, -3), air);
        placeAnimDoor(level, o.offset(5, -8, -3), ModBlocks.DOOR_WOOD_ARMY.get(), Direction.EAST, DoorHingeSide.LEFT);

        for (int dx = 6; dx <= 12; dx++) {
            for (int dz = -3; dz <= 4; dz++) {
                set(level, o.offset(dx, -9, dz), Blocks.SPRUCE_PLANKS.defaultBlockState());
                for (int dy = -8; dy <= -4; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
            }
        }
        placeBulkheadLamp(level, o.offset(9, -4, -1), Direction.DOWN);
        placeBulkheadLamp(level, o.offset(9, -4, 2), Direction.DOWN);

        // Military Beds along East wall (dx = 11..12)
        placeBed(level, o.offset(11, -8, -2), Blocks.GREEN_BED, Direction.EAST);
        placeBed(level, o.offset(11, -8, 0), Blocks.GREEN_BED, Direction.EAST);
        placeBed(level, o.offset(11, -8, 2), Blocks.GREEN_BED, Direction.EAST);
        placeBed(level, o.offset(11, -8, 4), Blocks.GREEN_BED, Direction.EAST);

        // Mess Table & Hurricane Lantern in Barracks (dx = 7..8, dz = 1..2)
        set(level, o.offset(7, -8, 1), Blocks.SPRUCE_FENCE.defaultBlockState());
        set(level, o.offset(7, -7, 1), Blocks.BROWN_CARPET.defaultBlockState());
        set(level, o.offset(7, -8, 2), Blocks.SPRUCE_FENCE.defaultBlockState());
        set(level, o.offset(7, -7, 2), ModBlocks.LANTERN_HURRICANE.get().defaultBlockState().setValue(LampBlock.LIT, true));
        set(level, o.offset(6, -8, 1), stair(Blocks.SPRUCE_STAIRS, Direction.EAST, Half.BOTTOM));
        set(level, o.offset(6, -8, 2), stair(Blocks.SPRUCE_STAIRS, Direction.EAST, Half.BOTTOM));

        // Barracks Rations & Military Crates
        SiteUtil.placeCrate(level, o.offset(7, -8, -3), ModBlocks.CRATE_MILITARY.get(), Direction.SOUTH, rand);
        SiteUtil.placeCrate(level, o.offset(9, -8, -3), ModBlocks.CRATE_MILITARY.get(), Direction.SOUTH, rand);
        placeStockedBarrel(level, o.offset(8, -8, -3), Direction.SOUTH,
                new ItemStack(ModItems.RATION_IRP.get(), 16),
                new ItemStack(ModItems.RATION_IRP.get(), 16),
                new ItemStack(ModItems.BANDAGE.get(), 8)
        );
    }

    private static void buildGrandStairwell(WorldGenLevel level, BlockPos o, BlockState rcSt, BlockState steelSt,
                                            BlockState hazardSt, BlockState air) {
        // First seal the side walls along dx = ±2 from dz = -2 to dz = +6 so the stairwell is an armored blast tunnel
        for (int dz = -2; dz <= 6; dz++) {
            int stepY = (dz >= -1) ? (-7 + (dz + 1)) : -8; // dz=-1 -> -7, dz=0 -> -6, ..., dz=6 -> 0
            for (int dy = -9; dy <= stepY + 4; dy++) {
                set(level, o.offset(-2, dy, dz), (dy == stepY + 4) ? steelSt : rcSt);
                set(level, o.offset(2, dy, dz), (dy == stepY + 4) ? steelSt : rcSt);
            }
            for (int dx = -1; dx <= 1; dx++) {
                // Solid step foundation below
                for (int dy = -9; dy < stepY; dy++) {
                    set(level, o.offset(dx, dy, dz), rcSt);
                }
                // Walkable stair or landing at stepY
                if (dz >= -1 && dz <= 6) {
                    set(level, o.offset(dx, stepY, dz), stair(Blocks.STONE_BRICK_STAIRS, Direction.SOUTH, Half.BOTTOM));
                } else {
                    set(level, o.offset(dx, stepY, dz), hazardSt);
                }
                // 4 blocks of clear headroom above each step
                for (int dy = stepY + 1; dy <= stepY + 4; dy++) {
                    set(level, o.offset(dx, dy, dz), air);
                }
                // Armored roof slab above stairwell
                set(level, o.offset(dx, stepY + 5, dz), rcSt);
            }
            // Bulkhead lights along stairwell ceiling every 3 blocks
            if (dz == 0 || dz == 3 || dz == 6) {
                placeBulkheadLamp(level, o.offset(0, stepY + 4, dz), Direction.DOWN);
            }
        }
    }

    private static void buildSurfaceBunkerAndPvoPads(WorldGenLevel level, BlockPos o, RandomSource rand,
                                                     Block rc, Block steel, Block armor, Block hazard, Block redStar,
                                                     Block camoCanopy, Block camoScreen) {
        BlockState rcSt = rc.defaultBlockState();
        BlockState steelSt = steel.defaultBlockState();
        BlockState armorSt = armor.defaultBlockState();
        BlockState hazardSt = hazard.defaultBlockState();
        BlockState air = Blocks.AIR.defaultBlockState();

        // 1. Armored Surface Bunker Cap Mound (dx = -13..+13, dz = -12..+5, dy = +1)
        for (int dx = -13; dx <= 13; dx++) {
            for (int dz = -12; dz <= 5; dz++) {
                // Keep stairwell entrance portal & escape shaft clear
                if (Math.abs(dx) <= 2 && dz >= 0) continue;
                if (dx >= 10 && dx <= 12 && dz >= -10 && dz <= -8) continue;

                boolean edge = Math.abs(dx) == 13 || dz == -12 || dz == 5;
                if (edge) {
                    set(level, o.offset(dx, 1, dz), hazardSt);
                } else {
                    set(level, o.offset(dx, 1, dz), rcSt);
                }
            }
        }
        // Sloped stone-brick stairs on the East, West, and South edges of the bunker mound so players can walk right up onto the PVO roof!
        for (int dx = -6; dx <= -4; dx++) {
            set(level, o.offset(dx, 1, 5), stair(Blocks.STONE_BRICK_STAIRS, Direction.NORTH, Half.BOTTOM));
        }
        for (int dx = 4; dx <= 6; dx++) {
            set(level, o.offset(dx, 1, 5), stair(Blocks.STONE_BRICK_STAIRS, Direction.NORTH, Half.BOTTOM));
        }

        // 2. Main Bunker Entrance Casemate & 3x3 Armored Blast Gate (GATE_BLAST at dx = -1..+1, dz = +6, dy = +1..+3)
        for (int dx = -3; dx <= 3; dx++) {
            for (int dz = 4; dz <= 6; dz++) {
                for (int dy = 1; dy <= 4; dy++) {
                    if (Math.abs(dx) <= 1 && dy <= 3) {
                        set(level, o.offset(dx, dy, dz), air);
                    } else if (dz == 6 && (Math.abs(dx) == 2) && dy <= 3) {
                        set(level, o.offset(dx, dy, dz), hazardSt);
                    } else if (dy == 4) {
                        set(level, o.offset(dx, dy, dz), armorSt);
                    } else {
                        set(level, o.offset(dx, dy, dz), rcSt);
                    }
                }
            }
        }
        // Red Star emblem above the Bunker Blast Gate lintel and rotating orange beacons on the portal piers
        set(level, o.offset(0, 4, 6), redStar.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.SOUTH));
        set(level, o.offset(-2, 5, 6), ModBlocks.BEACON_ROTATING.get().defaultBlockState().setValue(LampBlock.LIT, true));
        set(level, o.offset(2, 5, 6), ModBlocks.BEACON_ROTATING.get().defaultBlockState().setValue(LampBlock.LIT, true));
        // Place the 3x3 Armored Blast Gate (GATE_BLAST, facing NORTH so origin is at dx=-1, dy=1, dz=6 extending +X)
        placeGate(level, o.offset(-1, 1, 6), ModBlocks.GATE_BLAST.get(), Direction.NORTH);

        // 3. Elevated Radar Tower on North-Center of Bunker Roof (dx = -2..+2, dz = -11..-7, dy = +2..+4)
        for (int dx = -2; dx <= 2; dx++) {
            for (int dz = -11; dz <= -7; dz++) {
                set(level, o.offset(dx, 2, dz), rcSt);
                if (Math.abs(dx) == 2 || dz == -11 || dz == -7) {
                    set(level, o.offset(dx, 3, dz), steelSt);
                } else {
                    set(level, o.offset(dx, 3, dz), rcSt);
                }
                set(level, o.offset(dx, 4, dz), (Math.abs(dx) == 2 || dz == -11 || dz == -7) ? hazardSt : steelSt);
            }
        }
        // Ladder up the South face of the Radar Tower (dx = 0, dz = -6, dy = +2..+4)
        for (int dy = 2; dy <= 4; dy++) {
            set(level, o.offset(0, dy, -6), Blocks.LADDER.defaultBlockState().setValue(LadderBlock.FACING, Direction.SOUTH));
        }
        // Corner red obstruction beacons on the Radar Tower
        set(level, o.offset(-2, 5, -11), ModBlocks.BEACON_RED.get().defaultBlockState().setValue(LampBlock.LIT, true));
        set(level, o.offset(2, 5, -11), ModBlocks.BEACON_RED.get().defaultBlockState().setValue(LampBlock.LIT, true));
        placeStandingWarningSign(level, o.offset(-2, 5, -7), ModBlocks.WARNING_SIGN_RADIATION.get(), Direction.SOUTH);

        // 4. West Hardened S-400 SAM Launch Pad & Revetment on the Bunker Roof (dx = -11..-4, dz = -9..0, dy = +1)
        for (int dx = -10; dx <= -5; dx++) {
            for (int dz = -8; dz <= 0; dz++) {
                boolean padBorder = (dx == -10 || dx == -5 || dz == -8 || dz == 0);
                set(level, o.offset(dx, 1, dz), padBorder ? hazardSt : steelSt);
            }
        }
        // U-shaped Sandbag Blast Revetment around the S-400 pad (dy = +2..+3)
        BlockState sandbag = ModBlocks.SANDBAGS.get().defaultBlockState();
        for (int dx = -11; dx <= -4; dx++) {
            set(level, o.offset(dx, 2, -9), sandbag);
            set(level, o.offset(dx, 3, -9), sandbag);
        }
        for (int dz = -9; dz <= 0; dz++) {
            set(level, o.offset(-11, 2, dz), sandbag);
            set(level, o.offset(-11, 3, dz), sandbag);
        }
        SiteUtil.placeCrate(level, o.offset(-10, 2, -8), ModBlocks.CRATE_AMMO.get(), Direction.SOUTH, rand);
        set(level, o.offset(-4, 2, -9), ModBlocks.BEACON_RED.get().defaultBlockState().setValue(LampBlock.LIT, true));

        // 5. East Hardened Mobile Radar Pad on the Bunker Roof (dx = +4..+10, dz = -7..0, dy = +1)
        for (int dx = 5; dx <= 9; dx++) {
            for (int dz = -6; dz <= -1; dz++) {
                boolean padBorder = (dx == 5 || dx == 9 || dz == -6 || dz == -1);
                set(level, o.offset(dx, 1, dz), padBorder ? hazardSt : steelSt);
            }
        }
        for (int dz = -6; dz <= -1; dz++) {
            set(level, o.offset(11, 2, dz), sandbag);
            set(level, o.offset(11, 3, dz), camoScreen.defaultBlockState());
        }

        // 6. Twin ZU-23-2 Anti-Aircraft Gun Emplacements on South-West (-10, +3) & South-East (+10, +3) Roof Corners
        for (int side : new int[]{-1, 1}) {
            int cx = side * 9;
            int cz = 3;
            for (int dx = -2; dx <= 2; dx++) {
                for (int dz = -2; dz <= 2; dz++) {
                    if (Math.abs(dx) == 2 || Math.abs(dz) == 2) {
                        if (dz == -2 && Math.abs(dx) <= 1) continue; // Entry gap from roof
                        set(level, o.offset(cx + dx, 2, cz + dz), sandbag);
                    }
                }
            }
            SiteUtil.placeCrate(level, o.offset(cx - side, 2, cz - 1), ModBlocks.CRATE_AMMO.get(), Direction.SOUTH, rand);
        }

        // Anti-aircraft sweeping Searchlight on the center of the Bunker Roof (dx = 0, dz = +2, dy = +2)
        set(level, o.offset(0, 2, 2), steelSt);
        placeSearchlight(level, o.offset(0, 3, 2), Direction.SOUTH, 25.0f);
    }

    private static void buildCourtyardAndCheckpoint(WorldGenLevel level, BlockPos o, RandomSource rand,
                                                    Block rc, Block steel, Block armor, Block hazard, Block redStar,
                                                    Block camoCanopy, Block camoBush) {
        BlockState rcSt = rc.defaultBlockState();
        BlockState steelSt = steel.defaultBlockState();
        BlockState hazardSt = hazard.defaultBlockState();
        BlockState air = Blocks.AIR.defaultBlockState();

        // 1. Checkpoint Guardhouse (KPP Building at dx = +4..+9, dz = +10..+14, dy = +1..+4)
        for (int dx = 4; dx <= 9; dx++) {
            for (int dz = 10; dz <= 14; dz++) {
                set(level, o.offset(dx, 0, dz), Blocks.POLISHED_DEEPSLATE.defaultBlockState());
                boolean wall = (dx == 4 || dx == 9 || dz == 10 || dz == 14);
                for (int dy = 1; dy <= 3; dy++) {
                    if (!wall) {
                        set(level, o.offset(dx, dy, dz), air);
                    } else if (dy == 2 && ((dx == 4 && dz >= 11 && dz <= 13) || (dz == 14 && dx >= 5 && dx <= 7))) {
                        // Tinted glass observation windows overlooking the gate road
                        set(level, o.offset(dx, dy, dz), Blocks.TINTED_GLASS.defaultBlockState());
                    } else if (dy == 1) {
                        set(level, o.offset(dx, dy, dz), hazardSt);
                    } else {
                        set(level, o.offset(dx, dy, dz), rcSt);
                    }
                }
                // Roof at dy = +4 with camo canopy at dy = +5
                set(level, o.offset(dx, 4, dz), steelSt);
                set(level, o.offset(dx, 5, dz), camoCanopy.defaultBlockState());
            }
        }
        // Guardhouse Door (DOOR_STEEL on North wall at dx = 6, dz = 10)
        set(level, o.offset(6, 1, 10), air);
        set(level, o.offset(6, 2, 10), air);
        placeAnimDoor(level, o.offset(6, 1, 10), ModBlocks.DOOR_STEEL.get(), Direction.SOUTH, DoorHingeSide.LEFT);
        // Guardhouse interior: bulkhead lamp, duty desk, crates, and gate control lever
        placeBulkheadLamp(level, o.offset(6, 3, 12), Direction.DOWN);
        set(level, o.offset(5, 1, 12), Blocks.LECTERN.defaultBlockState().setValue(HorizontalDirectionalBlock.FACING, Direction.WEST));
        SiteUtil.placeCrate(level, o.offset(8, 1, 13), ModBlocks.CRATE_WEAPONS.get(), Direction.WEST, rand);
        SiteUtil.placeCrate(level, o.offset(8, 1, 11), ModBlocks.CRATE_MILITARY.get(), Direction.WEST, rand);
        // Street lamp on Guardhouse West wall illuminating the checkpoint road
        set(level, o.offset(3, 3, 12), ModBlocks.LAMP_STREET.get().defaultBlockState()
                .setValue(FacingLampBlock.FACING, Direction.WEST)
                .setValue(LampBlock.LIT, true));

        // 2. Parade Flagpole & Floodlight (dx = -5, dz = +11)
        for (int dx = -6; dx <= -4; dx++) {
            for (int dz = 10; dz <= 12; dz++) {
                set(level, o.offset(dx, 1, dz), slab(Blocks.SMOOTH_STONE_SLAB, SlabType.BOTTOM));
            }
        }
        set(level, o.offset(-5, 1, 11), hazardSt);
        placeFlagpole(level, o.offset(-5, 2, 11), 6, ModBlocks.FLAG_RUSSIA.get(), Direction.EAST);
        set(level, o.offset(-6, 1, 12), ModBlocks.LAMP_FLOOD.get().defaultBlockState()
                .setValue(FacingLampBlock.FACING, Direction.NORTH)
                .setValue(LampBlock.LIT, true));

        // 3. Fuel & Munitions Depot in South-West Courtyard (dx = -13..-8, dz = +8..+13)
        BlockState sandbag = ModBlocks.SANDBAGS.get().defaultBlockState();
        for (int dx = -13; dx <= -8; dx++) {
            for (int dz = 8; dz <= 13; dz++) {
                boolean border = (dx == -13 || dx == -8 || dz == 8 || dz == 13);
                if (border && !(dx == -8 && dz >= 10 && dz <= 11)) {
                    set(level, o.offset(dx, 1, dz), sandbag);
                }
                if ((dx == -13 || dx == -8) && (dz == 8 || dz == 13)) {
                    for (int dy = 1; dy <= 3; dy++) {
                        set(level, o.offset(dx, dy, dz), Blocks.SPRUCE_FENCE.defaultBlockState());
                    }
                }
                set(level, o.offset(dx, 4, dz), camoCanopy.defaultBlockState());
            }
        }
        // Fuel Drums & Crates inside Depot
        for (int dz = 9; dz <= 12; dz++) {
            set(level, o.offset(-12, 1, dz), ModBlocks.FUEL_DRUM_RED.get().defaultBlockState());
            set(level, o.offset(-11, 1, dz), ModBlocks.FUEL_DRUM_OLIVE.get().defaultBlockState());
        }
        set(level, o.offset(-10, 1, 9), ModBlocks.FUEL_DRUM_BLUE.get().defaultBlockState());
        set(level, o.offset(-10, 1, 12), ModBlocks.FUEL_DRUM_BLUE.get().defaultBlockState());
        SiteUtil.placeCrate(level, o.offset(-9, 1, 9), ModBlocks.CRATE_AMMO.get(), Direction.SOUTH, rand);
        SiteUtil.placeCrate(level, o.offset(-9, 1, 12), ModBlocks.CRATE_MILITARY.get(), Direction.NORTH, rand);
        placeStandingWarningSign(level, o.offset(-7, 1, 9), ModBlocks.WARNING_SIGN_NOENTRY.get(), Direction.EAST);

        // 4. Main Entrance Gates at Southern Perimeter (dx = -2..+2, dz = +15..+16)
        // Gate piers at dx = -3 and dx = +3, dz = +15
        for (int dy = 1; dy <= 3; dy++) {
            set(level, o.offset(-3, dy, 15), (dy == 2) ? hazardSt : rcSt);
            set(level, o.offset(3, dy, 15), (dy == 2) ? hazardSt : rcSt);
        }
        set(level, o.offset(-3, 4, 15), ModBlocks.BEACON_ROTATING.get().defaultBlockState().setValue(LampBlock.LIT, true));
        set(level, o.offset(3, 4, 15), ModBlocks.BEACON_ROTATING.get().defaultBlockState().setValue(LampBlock.LIT, true));

        // 5x2 Motorized Sliding Gate (GATE_SLIDING) at dz = +15, origin dx = -2, dy = +1, facing NORTH
        placeGate(level, o.offset(-2, 1, 15), ModBlocks.GATE_SLIDING.get(), Direction.NORTH);

        // Outer 5x1 Red/White Checkpoint Barrier Boom (GATE_BOOM) at dz = +16, origin dx = -2, dy = +1, facing NORTH
        placeGate(level, o.offset(-2, 1, 16), ModBlocks.GATE_BOOM.get(), Direction.NORTH);

        // Jersey Concrete Barriers & Checkpoint Warning Signs flanking the road approach (dz = +16..+17)
        Block barrier = ModBlocks.CONCRETE_BARRIER.get();
        set(level, o.offset(-4, 1, 16), barrier.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.EAST));
        set(level, o.offset(-4, 1, 17), barrier.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.EAST));
        set(level, o.offset(4, 1, 16), barrier.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.WEST));
        set(level, o.offset(4, 1, 17), barrier.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.WEST));
        placeStandingWarningSign(level, o.offset(-3, 1, 17), ModBlocks.WARNING_SIGN_CHECKPOINT.get(), Direction.SOUTH);
        placeStandingWarningSign(level, o.offset(3, 1, 17), ModBlocks.WARNING_SIGN_NOENTRY.get(), Direction.SOUTH);
    }

    private static void buildPerimeterAndWatchtowers(WorldGenLevel level, BlockPos o, RandomSource rand,
                                                     Block rc, Block steel, Block armor, Block hazard, Block camoCanopy) {
        BlockState rcSt = rc.defaultBlockState();
        BlockState steelSt = steel.defaultBlockState();
        BlockState hazardSt = hazard.defaultBlockState();
        BlockState egoza = ModBlocks.EGOZA.get().defaultBlockState();
        BlockState fenceBase = ModBlocks.TRAP_ELECTRIC_FENCE.get().defaultBlockState().setValue(ElectricFenceBlock.POWERED, true);

        // Perimeter line at dx = ±15 and dz = ±15
        for (int i = -15; i <= 15; i++) {
            // North wall (dz = -15) & South wall (dz = +15, skipping gate opening dx = -3..+3)
            for (int dz : new int[]{-15, 15}) {
                if (dz == 15 && Math.abs(i) <= 3) continue;
                if (Math.abs(i) >= 13) continue; // Corner watchtowers occupy ±13..±15
                boolean pillar = (i % 4 == 0);
                set(level, o.offset(i, 1, dz), pillar ? hazardSt : rcSt);
                for (int dy = 2; dy <= 3; dy++) {
                    set(level, o.offset(i, dy, dz), pillar ? rcSt : fenceBase);
                }
                set(level, o.offset(i, 4, dz), egoza);
                if (pillar) {
                    placeStandingWarningSign(level, o.offset(i, 1, dz + (dz < 0 ? -1 : 1)),
                            ModBlocks.WARNING_SIGN_VOLTAGE.get(), dz < 0 ? Direction.NORTH : Direction.SOUTH);
                }
            }
            // West wall (dx = -15) & East wall (dx = +15)
            for (int dx : new int[]{-15, 15}) {
                if (Math.abs(i) >= 13) continue;
                boolean pillar = (i % 4 == 0);
                set(level, o.offset(dx, 1, i), pillar ? hazardSt : rcSt);
                for (int dy = 2; dy <= 3; dy++) {
                    set(level, o.offset(dx, dy, i), pillar ? rcSt : fenceBase);
                }
                set(level, o.offset(dx, 4, i), egoza);
            }
        }

        // 4 Corner Guard Watchtowers at (±14, ±14), each 3x3 footprint (dx/dz = ±13..±15)
        BlockState sandbag = ModBlocks.SANDBAGS.get().defaultBlockState();
        for (int sx : new int[]{-1, 1}) {
            for (int sz : new int[]{-1, 1}) {
                int cx = sx * 14;
                int cz = sz * 14;
                for (int dx = -1; dx <= 1; dx++) {
                    for (int dz = -1; dz <= 1; dz++) {
                        boolean wall = Math.abs(dx) == 1 || Math.abs(dz) == 1;
                        // Hidden redstone torch at (cx, 1, cz) powers the adjacent electric fence!
                        if (!wall) {
                            set(level, o.offset(cx, 1, cz), Blocks.REDSTONE_BLOCK.defaultBlockState());
                            set(level, o.offset(cx, 2, cz), Blocks.AIR.defaultBlockState());
                            set(level, o.offset(cx, 3, cz), Blocks.AIR.defaultBlockState());
                        } else {
                            set(level, o.offset(cx + dx, 1, cz + dz), hazardSt);
                            set(level, o.offset(cx + dx, 2, cz + dz), rcSt);
                            set(level, o.offset(cx + dx, 3, cz + dz), rcSt);
                        }
                        // Elevated platform floor at dy = +4
                        set(level, o.offset(cx + dx, 4, cz + dz), steelSt);
                        // Sandbag parapet & corner roof posts at dy = +5..+6
                        if (wall) {
                            set(level, o.offset(cx + dx, 5, cz + dz), sandbag);
                            if (Math.abs(dx) == 1 && Math.abs(dz) == 1) {
                                set(level, o.offset(cx + dx, 6, cz + dz), Blocks.IRON_BARS.defaultBlockState());
                                set(level, o.offset(cx + dx, 7, cz + dz), Blocks.IRON_BARS.defaultBlockState());
                            }
                        }
                        // Camo canopy roof at dy = +8
                        set(level, o.offset(cx + dx, 8, cz + dz), camoCanopy.defaultBlockState());
                    }
                }
                // Sweeping Searchlight at the center of each Watchtower platform (dy = +5)
                Direction outward = (sz < 0) ? Direction.NORTH : Direction.SOUTH;
                placeSearchlight(level, o.offset(cx, 5, cz), outward, -10.0f);
                // Red obstruction beacon on top of outer corner post
                set(level, o.offset(cx + sx, 8, cz + sz), ModBlocks.BEACON_RED.get().defaultBlockState().setValue(LampBlock.LIT, true));
                // Ladder on the inner face of the Watchtower (dy = +1..+4)
                Direction inward = (sz < 0) ? Direction.SOUTH : Direction.NORTH;
                for (int dy = 1; dy <= 4; dy++) {
                    set(level, o.offset(cx, dy, cz - sz * 2), Blocks.LADDER.defaultBlockState().setValue(LadderBlock.FACING, inward));
                }
            }
        }

        // Outer Anti-Tank Defense Line (Dragon's Teeth & Czech Hedgehogs at ±17)
        Block teeth = ModBlocks.DRAGON_TEETH.get();
        Block hedgehog = ModBlocks.CZECH_HEDGEHOG.get();
        for (int i = -16; i <= 16; i += 2) {
            // North outer line (dz = -17)
            Block bNorth = (i % 4 == 0) ? hedgehog : teeth;
            set(level, o.offset(i, 1, -17), bNorth.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.NORTH));
            // South outer line (dz = +17, skipping road dx = -5..+5)
            if (Math.abs(i) >= 6) {
                Block bSouth = (i % 4 == 0) ? hedgehog : teeth;
                set(level, o.offset(i, 1, 17), bSouth.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.SOUTH));
            }
            // West & East outer lines (dx = ±17)
            Block bSide = (i % 4 == 0) ? hedgehog : teeth;
            set(level, o.offset(-17, 1, i), bSide.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.WEST));
            set(level, o.offset(17, 1, i), bSide.defaultBlockState().setValue(FacingFortBlock.FACING, Direction.EAST));
        }
        placeStandingWarningSign(level, o.offset(-10, 1, -16), ModBlocks.WARNING_SIGN_MINES.get(), Direction.NORTH);
        placeStandingWarningSign(level, o.offset(10, 1, -16), ModBlocks.WARNING_SIGN_NOENTRY.get(), Direction.NORTH);
    }

    private static void spawnPvoUnits(WorldGenLevel level, BlockPos o) {
        if (level.getLevel() == null) return;
        // Remove any existing base vehicles in the footprint if re-running /realwar base at the same spot
        if (level instanceof net.minecraft.server.level.ServerLevel) {
            AABB bounds = new AABB(o.offset(-RADIUS, -12, -RADIUS), o.offset(RADIUS + 1, 14, RADIUS + 1));
            for (VehicleEntity old : level.getEntitiesOfClass(VehicleEntity.class, bounds)) {
                old.discard();
            }
        }

        // 1. S-400 "Triumph" SAM Launcher on the West Bunker Roof Revetment (dx = -7.5, dy = +2.05, dz = -4.8)
        SamLauncherEntity s400 = new SamLauncherEntity(ModEntities.S400.get(), level.getLevel(), VehicleKind.S400);
        s400.moveTo(o.getX() - 7.5, o.getY() + 2.05, o.getZ() - 4.8, 0.0f, 0.0f);
        s400.setCombatDuty(true);
        level.addFreshEntity(s400);

        // 2. Stationary Radar Post on top of the North-Center Radar Tower (dx = +0.5, dy = +5.05, dz = -9.0)
        RadarVehicleEntity radarPost = new RadarVehicleEntity(ModEntities.RADAR_POST.get(), level.getLevel(), VehicleKind.RADAR_POST);
        radarPost.moveTo(o.getX() + 0.5, o.getY() + 5.05, o.getZ() - 9.0, 0.0f, 0.0f);
        radarPost.deployOnPad(0.0f, 0.0f);
        level.addFreshEntity(radarPost);

        // 3. Mobile 96L6E Radar Vehicle on the East Bunker Roof Pad (dx = +7.5, dy = +2.05, dz = -3.5)
        RadarVehicleEntity radarMobile = new RadarVehicleEntity(ModEntities.RADAR_MOBILE.get(), level.getLevel(), VehicleKind.RADAR_MOBILE);
        radarMobile.moveTo(o.getX() + 7.5, o.getY() + 2.05, o.getZ() - 3.5, -20.0f, 0.0f);
        radarMobile.deployOnPad(0.0f, 0.0f);
        level.addFreshEntity(radarMobile);

        // 4. Twin ZU-23-2 Anti-Aircraft Gun Emplacements on SW & SE Bunker Roof Corners
        FlakEntity zuWest = new FlakEntity(ModEntities.ZU23.get(), level.getLevel());
        zuWest.moveTo(o.getX() - 8.5, o.getY() + 2.05, o.getZ() + 3.5, 25.0f, 0.0f);
        zuWest.deployOnPosition(0.0f, 24.0f);
        level.addFreshEntity(zuWest);

        FlakEntity zuEast = new FlakEntity(ModEntities.ZU23.get(), level.getLevel());
        zuEast.moveTo(o.getX() + 9.5, o.getY() + 2.05, o.getZ() + 3.5, -25.0f, 0.0f);
        zuEast.deployOnPosition(0.0f, 24.0f);
        level.addFreshEntity(zuEast);
    }

    // ---- Helper methods for multi-block military doors, gates, hatches, lamps, signs, beds, and crates ----

    private static ItemStack uniform(String set, String slot) {
        var ro = ModItems.UNIFORMS.get("uniform_" + set + "_" + slot);
        return ro != null ? new ItemStack(ro.get()) : ItemStack.EMPTY;
    }

    private static void set(WorldGenLevel level, BlockPos pos, BlockState state) {
        level.setBlock(pos, state, 2);
    }

    private static BlockState stair(Block block, Direction facing, Half half) {
        return block.defaultBlockState()
                .setValue(StairBlock.FACING, facing)
                .setValue(StairBlock.HALF, half);
    }

    private static BlockState slab(Block block, SlabType type) {
        return block.defaultBlockState().setValue(SlabBlock.TYPE, type);
    }

    private static void placeGate(WorldGenLevel level, BlockPos origin, Block block, Direction facing) {
        if (!(block instanceof GateBlock gate)) return;
        GateKind kind = gate.kind;
        Direction right = facing.getClockWise();
        for (int ox = 0; ox < kind.w; ox++) {
            for (int oy = 0; oy < kind.h; oy++) {
                BlockPos p = origin.relative(right, ox).above(oy);
                BlockState st = gate.defaultBlockState()
                        .setValue(GateBlock.FACING, facing)
                        .setValue(GateBlock.OX, ox)
                        .setValue(GateBlock.OY, oy)
                        .setValue(GateBlock.OPEN, false)
                        .setValue(GateBlock.POWERED, false);
                set(level, p, st);
            }
        }
    }

    private static void placeAnimDoor(WorldGenLevel level, BlockPos bottomPos, Block doorBlock, Direction facing, DoorHingeSide hinge) {
        BlockState lower = doorBlock.defaultBlockState()
                .setValue(DoorBlock.FACING, facing)
                .setValue(DoorBlock.HALF, DoubleBlockHalf.LOWER)
                .setValue(DoorBlock.HINGE, hinge)
                .setValue(DoorBlock.OPEN, false)
                .setValue(DoorBlock.POWERED, false);
        BlockState upper = lower.setValue(DoorBlock.HALF, DoubleBlockHalf.UPPER);
        level.setBlock(bottomPos, lower, 18);
        level.setBlock(bottomPos.above(), upper, 18);
    }

    private static void placeHatch(WorldGenLevel level, BlockPos pos, Block hatchBlock, Direction facing, Half half, boolean open) {
        BlockState st = hatchBlock.defaultBlockState()
                .setValue(TrapDoorBlock.FACING, facing)
                .setValue(TrapDoorBlock.HALF, half)
                .setValue(TrapDoorBlock.OPEN, open)
                .setValue(TrapDoorBlock.POWERED, false)
                .setValue(TrapDoorBlock.WATERLOGGED, false);
        level.setBlock(pos, st, 18);
    }

    private static void placeBulkheadLamp(WorldGenLevel level, BlockPos pos, Direction facing) {
        BlockState st = ModBlocks.LAMP_BULKHEAD.get().defaultBlockState()
                .setValue(DirectionalLampBlock.FACING, facing)
                .setValue(LampBlock.LIT, true)
                .setValue(LampBlock.POWERED, false);
        level.setBlock(pos, st, 18);
    }

    private static void placeSearchlight(WorldGenLevel level, BlockPos pos, Direction facing, float basePitch) {
        BlockState st = ModBlocks.SEARCHLIGHT.get().defaultBlockState()
                .setValue(SearchlightBlock.FACING, facing)
                .setValue(SearchlightBlock.LIT, true);
        set(level, pos, st);
        BlockEntity be = level.getBlockEntity(pos);
        if (be instanceof SearchlightBlockEntity sbe) {
            sbe.mode = 2; // Sweep + lock-on mode
            sbe.baseYaw = SearchlightBlockEntity.yawOf(facing);
            sbe.basePitch = basePitch;
            sbe.yaw = sbe.baseYaw;
            sbe.pitch = sbe.basePitch;
            sbe.setChanged();
        }
    }

    private static void placeFlagpole(WorldGenLevel level, BlockPos basePos, int height, Block topFlagBlock, Direction flagDir) {
        for (int i = 0; i < height - 1; i++) {
            BlockState pole = ModBlocks.FLAGPOLE.get().defaultBlockState()
                    .setValue(FlagpoleBlock.BOTTOM, i == 0)
                    .setValue(FlagpoleBlock.TOP, false);
            level.setBlock(basePos.above(i), pole, 18);
        }
        BlockState top = topFlagBlock.defaultBlockState()
                .setValue(FlagpoleBlock.BOTTOM, false)
                .setValue(FlagpoleBlock.TOP, true)
                .setValue(FlagBlock.FACING, flagDir);
        level.setBlock(basePos.above(height - 1), top, 18);
    }

    private static void placeStandingWarningSign(WorldGenLevel level, BlockPos pos, Block signBlock, Direction facing) {
        BlockState st = signBlock.defaultBlockState()
                .setValue(WarningSignBlock.FACING, facing)
                .setValue(WarningSignBlock.WALL, false);
        level.setBlock(pos, st, 18);
    }

    private static void placeWallWarningSign(WorldGenLevel level, BlockPos pos, Block signBlock, Direction facing) {
        BlockState st = signBlock.defaultBlockState()
                .setValue(WarningSignBlock.FACING, facing)
                .setValue(WarningSignBlock.WALL, true);
        level.setBlock(pos, st, 18);
    }

    private static void placeBed(WorldGenLevel level, BlockPos footPos, Block bedBlock, Direction facing) {
        BlockState foot = bedBlock.defaultBlockState()
                .setValue(BedBlock.FACING, facing)
                .setValue(BedBlock.PART, BedPart.FOOT)
                .setValue(BedBlock.OCCUPIED, false);
        BlockState head = foot.setValue(BedBlock.PART, BedPart.HEAD);
        level.setBlock(footPos, foot, 18);
        level.setBlock(footPos.relative(facing), head, 18);
    }

    private static void placeStockedBarrel(WorldGenLevel level, BlockPos pos, Direction facing, ItemStack... items) {
        BlockState st = Blocks.BARREL.defaultBlockState().setValue(BarrelBlock.FACING, facing);
        set(level, pos, st);
        BlockEntity be = level.getBlockEntity(pos);
        if (be instanceof BarrelBlockEntity barrel) {
            for (int i = 0; i < items.length && i < barrel.getContainerSize(); i++) {
                barrel.setItem(i, items[i].copy());
            }
            barrel.setChanged();
        }
    }
}
