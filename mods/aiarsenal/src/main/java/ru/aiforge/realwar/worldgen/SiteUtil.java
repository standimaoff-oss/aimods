package ru.aiforge.realwar.worldgen;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.WorldGenLevel;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.levelgen.Heightmap;
import ru.aiforge.realwar.deco.CrateBlock;
import ru.aiforge.realwar.deco.CrateBlockEntity;

/** r17: shared helpers for the wreck-site / supply-cache features. */
final class SiteUtil {
    private SiteUtil() {
    }

    /** First free block above the terrain surface (ignores leaves / plants via WORLD_SURFACE_WG + replaceable check). */
    static BlockPos surface(WorldGenLevel l, int x, int z) {
        BlockPos p = new BlockPos(x, l.getHeight(Heightmap.Types.WORLD_SURFACE_WG, x, z), z);
        while (p.getY() > l.getMinBuildHeight() + 1 && l.getBlockState(p.below()).canBeReplaced() && l.getFluidState(p.below()).isEmpty())
            p = p.below();
        return p;
    }

    static boolean dryGround(WorldGenLevel l, BlockPos surf) {
        BlockState b = l.getBlockState(surf.below());
        return l.getFluidState(surf.below()).isEmpty() && l.getFluidState(surf).isEmpty() && b.isSolidRender(l, surf.below())
                && !b.is(Blocks.ICE) && !b.is(Blocks.PACKED_ICE);
    }

    static void crate(WorldGenLevel l, BlockPos p, Block crate, RandomSource r) {
        if (!l.getBlockState(p).canBeReplaced()) return;
        l.setBlock(p, crate.defaultBlockState().setValue(CrateBlock.FACING, Direction.Plane.HORIZONTAL.getRandomDirection(r)), 2);
        if (l.getBlockEntity(p) instanceof CrateBlockEntity be && crate instanceof CrateBlock cb) be.setLootTable(cb.kind.loot(), r.nextLong());
    }

    public static void placeCrate(WorldGenLevel l, BlockPos p, Block crate, Direction facing, RandomSource r) {
        l.setBlock(p, crate.defaultBlockState().setValue(CrateBlock.FACING, facing), 2);
        if (l.getBlockEntity(p) instanceof CrateBlockEntity be && crate instanceof CrateBlock cb) {
            be.setLootTable(cb.kind.loot(), r.nextLong());
        }
    }

    private static net.minecraft.world.level.block.state.properties.BooleanProperty prop(Direction d) {
        return switch (d) {
            case NORTH -> net.minecraft.world.level.block.CrossCollisionBlock.NORTH;
            case SOUTH -> net.minecraft.world.level.block.CrossCollisionBlock.SOUTH;
            case EAST -> net.minecraft.world.level.block.CrossCollisionBlock.EAST;
            default -> net.minecraft.world.level.block.CrossCollisionBlock.WEST;
        };
    }

    /** Re-evaluates horizontal connections for every LinkedFortBlock and IronBarsBlock (e.g. ElectricFenceBlock) inside a box around origin. */
    public static void connectFort(WorldGenLevel level, BlockPos origin, int r) {
        for (int dx = -r; dx <= r; dx++) {
            for (int dz = -r; dz <= r; dz++) {
                for (int dy = -2; dy <= 8; dy++) {
                    BlockPos p = origin.offset(dx, dy, dz);
                    BlockState s = level.getBlockState(p);
                    if (s.getBlock() instanceof ru.aiforge.realwar.fort.LinkedFortBlock fb) {
                        for (Direction d : Direction.Plane.HORIZONTAL) {
                            BlockPos q = p.relative(d);
                            BlockState ns = level.getBlockState(q);
                            boolean c = fb.connectsTo(ns, ns.isFaceSturdy(level, q, d.getOpposite()), d);
                            s = s.setValue(prop(d), c);
                        }
                        level.setBlock(p, s, 2);
                    } else if (s.getBlock() instanceof net.minecraft.world.level.block.IronBarsBlock ib) {
                        for (Direction d : Direction.Plane.HORIZONTAL) {
                            BlockPos q = p.relative(d);
                            BlockState ns = level.getBlockState(q);
                            boolean c = ib.attachsTo(ns, ns.isFaceSturdy(level, q, d.getOpposite()));
                            s = s.setValue(prop(d), c);
                        }
                        level.setBlock(p, s, 2);
                    }
                }
            }
        }
    }
}
