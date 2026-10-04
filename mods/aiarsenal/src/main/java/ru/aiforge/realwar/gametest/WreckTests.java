package ru.aiforge.realwar.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.animal.Pig;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.level.levelgen.feature.configurations.NoneFeatureConfiguration;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import ru.aiforge.realwar.deco.CrateBlock;
import ru.aiforge.realwar.deco.CrateBlockEntity;
import ru.aiforge.realwar.deco.WreckBlock;
import ru.aiforge.realwar.deco.WreckBlockEntity;
import ru.aiforge.realwar.field.ElectricFenceBlock;
import ru.aiforge.realwar.registry.ModBlocks;
import ru.aiforge.realwar.worldgen.ModFeatures;

/** r17 building blocks part 4: wrecks, loot crates, traps, worldgen features. */
@GameTestHolder("aiarsenal")
@PrefixGameTestTemplate(false)
public final class WreckTests {
    private WreckTests() {
    }

    private static BlockPos pad(GameTestHelper h, int rx, int rz, int half) {
        ServerLevel level = h.getLevel();
        BlockPos c = h.absolutePos(new BlockPos(rx, 0, rz));
        int top = level.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, c.getX(), c.getZ());
        for (int dx = -half; dx <= half; ++dx)
            for (int dz = -half; dz <= half; ++dz)
                for (int y = top - 2; y <= top + 4; ++y)
                    level.setBlock(new BlockPos(c.getX() + dx, y, c.getZ() + dz), y < top ? Blocks.STONE.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
        return c.atY(top);
    }

    private static Pig pig(ServerLevel l, BlockPos p) {
        Pig e = EntityType.PIG.create(l);
        e.moveTo(p.getX() + 0.5, p.getY() + 0.05, p.getZ() + 0.5, 0, 0);
        l.addFreshEntity(e);
        return e;
    }

    @GameTest(template = "arena", batch = "rw_wrecks", timeoutTicks = 40)
    public static void crate_loot_tiers(GameTestHelper h) {
        ServerLevel l = h.getLevel();
        BlockPos c = pad(h, 4, 4, 2);
        for (CrateBlock cb : new CrateBlock[]{(CrateBlock) ModBlocks.CRATE_AMMO.get(), (CrateBlock) ModBlocks.CRATE_MEDICAL.get(),
                (CrateBlock) ModBlocks.CRATE_MILITARY.get(), (CrateBlock) ModBlocks.CRATE_WEAPONS.get(), (CrateBlock) ModBlocks.CRATE_SECRET.get()}) {
            for (int i = 0; i < 12; i++) {
                l.setBlock(c, Blocks.AIR.defaultBlockState(), 2);
                l.setBlock(c, cb.defaultBlockState(), 2);
                CrateBlockEntity be = (CrateBlockEntity) l.getBlockEntity(c);
                h.assertTrue(be != null, "crate block entity");
                be.setLootTable(cb.kind.loot(), 1000L + i * 7919L);
                be.unpackLootTable(null);
                int n = 0;
                boolean diamond = false, netherite = false;
                for (int s = 0; s < be.getContainerSize(); s++) {
                    ItemStack st = be.getItem(s);
                    if (st.isEmpty()) continue;
                    n++;
                    diamond |= st.is(Items.DIAMOND);
                    netherite |= st.is(Items.NETHERITE_INGOT) || st.is(Items.NETHERITE_SCRAP);
                }
                h.assertTrue(n > 0, cb.kind.id + " crate rolled empty");
                h.assertFalse(netherite, "no netherite in crates");
                if (!cb.kind.id.equals("secret")) h.assertFalse(diamond, cb.kind.id + " crate must not hold diamonds");
                else h.assertTrue(diamond, "the classified case always has 1-2 diamonds");
                be.clearContent();
            }
        }
        l.setBlock(c, Blocks.AIR.defaultBlockState(), 2);
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_wrecks", timeoutTicks = 40)
    public static void wreck_place_and_break(GameTestHelper h) {
        ServerLevel l = h.getLevel();
        BlockPos c = pad(h, 4, 4, 7);
        WreckBlock wb = (WreckBlock) ModBlocks.WRECK_TANK_TRACK.get();
        int placed = wb.placeAt(l, c, Direction.NORTH, 3);
        h.assertTrue(placed == wb.kind.count(), "all cells placed: " + placed + "/" + wb.kind.count());
        h.assertTrue(l.getBlockEntity(c) instanceof WreckBlockEntity, "anchor carries the block entity");
        BlockPos o = wb.originFromAnchor(c, Direction.NORTH);
        BlockPos far = null;
        int n = 0;
        for (BlockPos p : wb.footprint(o, Direction.NORTH)) {
            h.assertTrue(l.getBlockState(p).is(wb), "cell present at " + p);
            if (!p.equals(c)) far = p;
            n++;
        }
        h.assertTrue(n == wb.kind.count() && far != null, "footprint");
        ((WreckBlockEntity) l.getBlockEntity(c)).setSmoking(true);
        h.assertTrue(((WreckBlockEntity) l.getBlockEntity(c)).smoking(), "smoke on");
        l.destroyBlock(far, false);
        for (BlockPos p : wb.footprint(o, Direction.NORTH)) h.assertFalse(l.getBlockState(p).is(wb), "breaking one cell removes the whole wreck");
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_wrecks", timeoutTicks = 100)
    public static void punji_and_fence_hurt(GameTestHelper h) {
        ServerLevel l = h.getLevel();
        BlockPos c = pad(h, 4, 4, 3);
        BlockPos pit = c.west(2);
        l.setBlock(pit.below(), Blocks.AIR.defaultBlockState(), 2);
        l.setBlock(pit.below(), ModBlocks.TRAP_PUNJI.get().defaultBlockState(), 3);
        Pig a = pig(l, pit);
        BlockPos fence = c.east(2);
        l.setBlock(fence.below(), Blocks.REDSTONE_BLOCK.defaultBlockState(), 3);
        l.setBlock(fence, ModBlocks.TRAP_ELECTRIC_FENCE.get().defaultBlockState(), 3);
        l.setBlock(fence.north(), ModBlocks.TRAP_ELECTRIC_FENCE.get().defaultBlockState(), 3);
        Pig b = pig(l, fence);
        h.succeedWhen(() -> {
            h.assertTrue(l.getBlockState(fence.north()).getValue(ElectricFenceBlock.POWERED), "the whole fence run is live");
            h.assertTrue(a.getHealth() < a.getMaxHealth(), "punji stakes wound");
            h.assertFalse(l.getBlockState(pit.below()).getValue(ru.aiforge.realwar.field.PunjiTrapBlock.COVERED), "the leaf mat tears");
            h.assertTrue(b.getHealth() < b.getMaxHealth(), "electric fence shocks");
        });
    }

    @GameTest(template = "arena", batch = "rw_wgen", timeoutTicks = 40)
    public static void worldgen_sites(GameTestHelper h) {
        ServerLevel l = h.getLevel();
        BlockPos c = h.absolutePos(new BlockPos(4, 0, 4));
        BlockPos cc0 = new BlockPos((c.getX() & ~15) + 8, 0, (c.getZ() & ~15) + 8);
        int top = l.getHeight(Heightmap.Types.MOTION_BLOCKING_NO_LEAVES, cc0.getX(), cc0.getZ());
        for (BlockPos p : BlockPos.betweenClosed(cc0.offset(-4, top - 2, -4), cc0.offset(4, top + 5, 4)))
            l.setBlock(p, p.getY() < top ? Blocks.GRASS_BLOCK.defaultBlockState() : Blocks.AIR.defaultBlockState(), 2);
        c = c.atY(top);
        boolean cache = ModFeatures.SUPPLY_CACHE.get().place(NoneFeatureConfiguration.INSTANCE, l, l.getChunkSource().getGenerator(), RandomSource.create(5), c);
        boolean wreck = ModFeatures.WRECK_SITE.get().place(NoneFeatureConfiguration.INSTANCE, l, l.getChunkSource().getGenerator(), RandomSource.create(7),
                c.offset(48, 0, 0));
        h.assertTrue(cache, "supply cache placed on flat ground");
        h.assertTrue(wreck, "wreck site placed on flat ground");
        int crates = 0, cells = 0;
        BlockPos cc = new BlockPos((c.getX() & ~15) + 8, c.getY(), (c.getZ() & ~15) + 8);
        BlockPos wc = new BlockPos(((c.getX() + 48) & ~15) + 8, c.getY(), (c.getZ() & ~15) + 8);
        for (BlockPos p : BlockPos.betweenClosed(cc.offset(-2, -12, -2), cc.offset(2, 12, 2)))
            if (l.getBlockState(p).getBlock() instanceof CrateBlock) crates++;
        for (BlockPos p : BlockPos.betweenClosed(wc.offset(-14, -12, -14), wc.offset(14, 12, 14)))
            if (l.getBlockState(p).getBlock() instanceof WreckBlock) cells++;
        h.assertTrue(crates >= 1, "cache has crates");
        h.assertTrue(cells >= 10, "wreck site has wreck cells: " + cells);
        h.succeed();
    }
}
