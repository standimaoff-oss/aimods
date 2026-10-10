package ru.aiforge.realwar.gametest;

import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.util.RandomSource;
import net.minecraft.world.phys.Vec3;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import ru.aiforge.realwar.artillery.FireControlBlockEntity;
import ru.aiforge.realwar.artillery.FireMission;
import ru.aiforge.realwar.registry.ModBlocks;

/** r28: artillery fire control - block placement and the mission rules (round counts, aim points, square cycle). */
@GameTestHolder("aiarsenal")
@PrefixGameTestTemplate(false)
public final class FireControlTests {
    private FireControlTests() {
    }

    @GameTest(template = "arena", batch = "rw_fdc", timeoutTicks = 40)
    public static void fireControlBlockHasEntity(GameTestHelper h) {
        BlockPos p = new BlockPos(2, 2, 2);
        h.setBlock(p, ModBlocks.FIRE_CONTROL.get());
        h.assertTrue(h.getBlockEntity(p) instanceof FireControlBlockEntity, "r28: ПУ арты без BlockEntity");
        FireControlBlockEntity be = (FireControlBlockEntity) h.getBlockEntity(p);
        h.assertTrue(be.batteries().isEmpty() && !be.active(), "r28: новый ПУ должен быть без батарей и без миссии");
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_fdc", timeoutTicks = 40)
    public static void missionRules(GameTestHelper h) {
        h.assertTrue(FireMission.roundsFor(FireMission.Mode.SALVO, 5) == 1, "r28: залп - один снаряд на орудие");
        h.assertTrue(FireMission.roundsFor(FireMission.Mode.ADJUST, 5) == 1, "r28: корректировка - один снаряд");
        h.assertTrue(FireMission.roundsFor(FireMission.Mode.COORD, 9) == FireMission.MAX_ROUNDS, "r28: количество снарядов ограничено");
        h.assertTrue(FireMission.roundsFor(FireMission.Mode.MAP, 0) == 1, "r28: минимум один снаряд");

        Vec3 c = FireMission.shotPoint(FireMission.Mode.COORD, 100.5, -40.5, 200, RandomSource.create(1));
        h.assertTrue(c.x == 100.5 && c.z == -40.5, "r28: координатная стрельба бьёт точно в точку");

        RandomSource r = RandomSource.create(7);
        for (int i = 0; i < 300; i++) {
            Vec3 m = FireMission.shotPoint(FireMission.Mode.MAP, 0.0, 0.0, 200, r);
            h.assertTrue(Math.abs(m.x) <= 100.0 && Math.abs(m.z) <= 100.0, "r28: удар по карте вышел за квадрат 200 м");
        }
        h.assertTrue(FireMission.square(0) == 100 && FireMission.square(2) == 400, "r28: размеры квадрата");
        h.assertTrue(FireMission.nextSquareIndex(2) == 0, "r28: цикл размеров квадрата");
        h.assertTrue(FireMission.Mode.COORD.next() == FireMission.Mode.SALVO && FireMission.Mode.ADJUST.next() == FireMission.Mode.COORD, "r28: цикл режимов");
        h.assertTrue(Math.abs(FireMission.distXZ(0, 0, 3, 4) - 5.0) < 1e-9, "r28: горизонтальная дистанция");
        h.succeed();
    }
}
