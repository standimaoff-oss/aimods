package ru.aiforge.realwar.gametest;

import com.mojang.authlib.GameProfile;
import java.util.UUID;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.monster.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.common.util.FakePlayer;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import ru.aiforge.realwar.handheld.AtMissileEntity;
import ru.aiforge.realwar.handheld.FirearmItem;
import ru.aiforge.realwar.handheld.Firearms;
import ru.aiforge.realwar.handheld.GunKind;
import ru.aiforge.realwar.handheld.MagazineItem;
import ru.aiforge.realwar.registry.ModItems;

/** Reply 22-24: AK-12 / M4A1 / RPG-7V2 / T-5000 / PKP / Saiga-12K / Remington 870 server logic. */
@GameTestHolder("aiarsenal")
@PrefixGameTestTemplate(false)
public final class SmallArmsTests {
    private SmallArmsTests() {
    }

    private static FakePlayer shooter(GameTestHelper h, ItemStack gun, double x, double y, double z) {
        FakePlayer p = new FakePlayer(h.getLevel(), new GameProfile(UUID.randomUUID(), "rw-rifle"));
        p.moveTo(x, y, z, 0f, 0f);                                     // yaw 0 = looking +Z
        p.setItemInHand(InteractionHand.MAIN_HAND, gun);
        return p;
    }

    @GameTest(template = "arena", batch = "rw_small", timeoutTicks = 120)
    public static void ak12_burst_hits_and_counts_rounds(GameTestHelper h) {
        ServerLevel level = h.getLevel();
        BlockPos o = h.absolutePos(new BlockPos(2, 1, 2));
        for (int dz = 0; dz < 14; dz++) for (int dy = 0; dy < 4; dy++) level.setBlock(o.offset(0, dy, dz), Blocks.AIR.defaultBlockState(), 2);
        ItemStack gun = new ItemStack(ModItems.AK12.get());
        FirearmItem.setAmmo(gun, 30);
        FakePlayer p = shooter(h, gun, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        Husk t = EntityType.HUSK.create(level);
        t.moveTo(o.getX() + 0.5, o.getY(), o.getZ() + 10.5, 180f, 0f);
        t.setNoAi(true);
        level.addFreshEntity(t);
        float hp0 = t.getHealth();
        for (int i = 0; i < 5; i++) Firearms.fire(p, gun, GunKind.AK12, true);
        h.assertTrue(FirearmItem.ammo(gun) == 25, "5 shots should leave 25 rounds, got " + FirearmItem.ammo(gun));
        h.assertTrue(Firearms.bullets(level) >= 1, "bullets in flight");
        h.runAfterDelay(6, () -> {
            h.assertTrue(!t.isAlive() || t.getHealth() < hp0, "aimed AK burst at 10 m must hit the husk (hp " + t.getHealth() + ")");
            t.discard();
            h.succeed();
        });
    }

    @GameTest(template = "arena", batch = "rw_small")
    public static void reload_takes_fullest_mag_and_keeps_chambered(GameTestHelper h) {
        BlockPos o = h.absolutePos(new BlockPos(2, 1, 2));
        ItemStack gun = new ItemStack(ModItems.M4A1.get());
        FirearmItem.setAmmo(gun, 5);
        FakePlayer p = shooter(h, gun, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        p.getInventory().add(MagazineItem.withRounds(ModItems.MAG_STANAG.get(), 12));
        p.getInventory().add(new ItemStack(ModItems.MAG_STANAG.get()));         // full (no NBT)
        Firearms.finishReload(p, gun, GunKind.M4A1);
        h.assertTrue(FirearmItem.ammo(gun) == 31, "tactical reload = 30 + 1 chambered, got " + FirearmItem.ammo(gun));
        int partial = -1, mags = 0;
        for (ItemStack s : p.getInventory().items) {
            if (s.getItem() instanceof MagazineItem) {
                mags += s.getCount();
                if (MagazineItem.rounds(s) == 4) partial = 4;
            }
        }
        h.assertTrue(mags == 2, "the 12-round mag stays, the old one comes back: " + mags);
        h.assertTrue(partial == 4, "old magazine returned with 4 rounds (5 - chambered)");
        ItemStack empty = new ItemStack(ModItems.AK12.get());
        FakePlayer q = shooter(h, empty, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        Firearms.finishReload(q, empty, GunKind.AK12);
        h.assertTrue(FirearmItem.ammo(empty) == 0, "no magazine -> nothing loaded");
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_small", timeoutTicks = 60)
    public static void rpg7_launches_pg7vl_and_needs_reload(GameTestHelper h) {
        ServerLevel level = h.getLevel();
        BlockPos o = h.absolutePos(new BlockPos(2, 2, 2));
        ItemStack rpg = new ItemStack(ModItems.RPG7.get());
        FirearmItem.setAmmo(rpg, 1);
        FakePlayer p = shooter(h, rpg, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        p.setXRot(-30f);
        Firearms.fire(p, rpg, GunKind.RPG7, true);
        h.assertTrue(FirearmItem.ammo(rpg) == 0, "RPG-7 holds one grenade");
        var m = level.getEntitiesOfClass(AtMissileEntity.class, new AABB(o).inflate(8));
        h.assertTrue(!m.isEmpty(), "PG-7VL launched");
        p.getInventory().add(new ItemStack(ModItems.PG7V.get(), 2));
        Firearms.finishReload(p, rpg, GunKind.RPG7);
        int left = 0;
        for (ItemStack s : p.getInventory().items) if (s.is(ModItems.PG7V.get())) left += s.getCount();
        h.assertTrue(FirearmItem.ammo(rpg) == 1 && left == 1, "reload consumes one PG-7VL");
        m.forEach(net.minecraft.world.entity.Entity::discard);
        h.succeed();
    }

    // ------------------------------------------------------------------ r23

    @GameTest(template = "arena", batch = "rw_small", timeoutTicks = 120)
    public static void t5000_one_shot_and_bolt_reload(GameTestHelper h) {
        ServerLevel level = h.getLevel();
        BlockPos o = h.absolutePos(new BlockPos(2, 1, 2));
        for (int dz = 0; dz < 14; dz++) for (int dy = 0; dy < 4; dy++) level.setBlock(o.offset(0, dy, dz), Blocks.AIR.defaultBlockState(), 2);
        ItemStack gun = new ItemStack(ModItems.T5000.get());
        FirearmItem.setAmmo(gun, 2);
        FakePlayer p = shooter(h, gun, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        Husk t = EntityType.HUSK.create(level);
        t.moveTo(o.getX() + 0.5, o.getY(), o.getZ() + 12.5, 180f, 0f);
        t.setNoAi(true);
        level.addFreshEntity(t);
        float hp0 = t.getHealth();
        Firearms.fire(p, gun, GunKind.T5000, true);
        h.assertTrue(FirearmItem.ammo(gun) == 1, ".338 LM: one round per shot");
        h.assertTrue(GunKind.T5000.boltAction() && !GunKind.T5000.selector() && GunKind.T5000.maxLoaded(true) == 6, "bolt action, 5 + 1");
        p.getInventory().add(new ItemStack(ModItems.MAG_T5000.get()));
        Firearms.finishReload(p, gun, GunKind.T5000);
        h.assertTrue(FirearmItem.ammo(gun) == 6, "tactical reload 5 + 1 chambered, got " + FirearmItem.ammo(gun));
        h.runAfterDelay(6, () -> {
            h.assertTrue(!t.isAlive() || t.getHealth() <= hp0 - 20f, ".338 LM at 12 m must (nearly) kill the husk: hp " + t.getHealth());
            t.discard();
            h.succeed();
        });
    }

    @GameTest(template = "arena", batch = "rw_small")
    public static void pkp_belt_box_reload_open_bolt(GameTestHelper h) {
        BlockPos o = h.absolutePos(new BlockPos(2, 1, 2));
        ItemStack gun = new ItemStack(ModItems.PKP.get());
        FirearmItem.setAmmo(gun, 10);
        FakePlayer p = shooter(h, gun, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        p.getInventory().add(new ItemStack(ModItems.BOX_PKP.get()));
        Firearms.finishReload(p, gun, GunKind.PKP);
        h.assertTrue(FirearmItem.ammo(gun) == 100, "open bolt: a new box = 100 (no chambered extra), got " + FirearmItem.ammo(gun));
        int back = -1;
        for (ItemStack s : p.getInventory().items) if (s.getItem() instanceof MagazineItem) back = MagazineItem.rounds(s);
        h.assertTrue(back == 10, "the old box keeps its 10-round belt: " + back);
        h.assertTrue(GunKind.PKP.auto && !GunKind.PKP.selector(), "PKP is full-auto only");
        for (int i = 0; i < 3; i++) Firearms.fire(p, gun, GunKind.PKP, false);
        h.assertTrue(FirearmItem.ammo(gun) == 97, "3 rounds fired");
        h.succeed();
    }

    // ------------------------------------------------------------------ r24

    @GameTest(template = "arena", batch = "rw_small", timeoutTicks = 120)
    public static void saiga12_buckshot_pattern_hits(GameTestHelper h) {
        ServerLevel level = h.getLevel();
        BlockPos o = h.absolutePos(new BlockPos(2, 1, 2));
        for (int dz = 0; dz < 10; dz++) for (int dy = 0; dy < 4; dy++) level.setBlock(o.offset(0, dy, dz), Blocks.AIR.defaultBlockState(), 2);
        ItemStack gun = new ItemStack(ModItems.SAIGA12.get());
        FirearmItem.setAmmo(gun, 8);
        FakePlayer p = shooter(h, gun, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        Husk t = EntityType.HUSK.create(level);
        t.moveTo(o.getX() + 0.5, o.getY(), o.getZ() + 6.5, 180f, 0f);
        t.setNoAi(true);
        level.addFreshEntity(t);
        float hp0 = t.getHealth();
        int b0 = Firearms.bullets(level);
        Firearms.fire(p, gun, GunKind.SAIGA12, true);
        h.assertTrue(FirearmItem.ammo(gun) == 7, "one shell per shot");
        h.assertTrue(Firearms.bullets(level) - b0 == 9, "00 buckshot = 9 pellets, got " + (Firearms.bullets(level) - b0));
        h.assertTrue(GunKind.SAIGA12.maxLoaded(true) == 9 && !GunKind.SAIGA12.auto, "semi-auto, 8 + 1");
        h.runAfterDelay(6, () -> {
            h.assertTrue(!t.isAlive() || t.getHealth() <= hp0 - 12f, "buckshot at 6 m must hit hard: hp " + t.getHealth());
            t.discard();
            h.succeed();
        });
    }

    @GameTest(template = "arena", batch = "rw_small")
    public static void r870_tube_loads_shell_by_shell(GameTestHelper h) {
        BlockPos o = h.absolutePos(new BlockPos(2, 1, 2));
        ItemStack gun = new ItemStack(ModItems.R870.get());
        FakePlayer p = shooter(h, gun, o.getX() + 0.5, o.getY(), o.getZ() + 0.5);
        p.getInventory().add(new ItemStack(ModItems.SHELL_12.get(), 7));
        for (int i = 0; i < 7; i++) Firearms.finishReload(p, gun, GunKind.R870);
        int left = 0;
        for (ItemStack s : p.getInventory().items) if (s.is(ModItems.SHELL_12.get())) left += s.getCount();
        h.assertTrue(FirearmItem.ammo(gun) == 5, "4 in the tube + 1 chambered, got " + FirearmItem.ammo(gun));
        h.assertTrue(left == 2, "only 5 shells used (7 tries), left " + left);
        h.assertTrue(GunKind.R870.pumpAction() && GunKind.R870.tube() && GunKind.R870.semiCooldown() >= 12, "pump action, tube fed");
        h.succeed();
    }
}
