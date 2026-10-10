package ru.aiforge.realwar.gametest;

import net.minecraft.gametest.framework.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraftforge.gametest.GameTestHolder;
import net.minecraftforge.gametest.PrefixGameTestTemplate;
import ru.aiforge.realwar.handheld.GunKind;
import ru.aiforge.realwar.ordnance.Ballistics;
import ru.aiforge.realwar.vehicle.VehicleKind;

/** r28: contract of the future weapons (laser and plasma rifles) and the plasma tank Vikhr. */
@GameTestHolder("aiarsenal")
@PrefixGameTestTemplate(false)
public final class FutureTests {
    private FutureTests() {
    }

    @GameTest(template = "arena", batch = "rw_future", timeoutTicks = 20)
    public static void futureRiflesAreMagazineFed(GameTestHelper h) {
        h.assertTrue(GunKind.LASER.cap == 40 && GunKind.LASER.auto, "r28: лазер - 40 зарядов, полный огонь");
        h.assertTrue(GunKind.PLASMA.cap == 20 && !GunKind.PLASMA.auto, "r28: плазмомёт - 20 зарядов, одиночный огонь");
        h.assertTrue(GunKind.LASER.ammo.equals("mag_laser") && GunKind.PLASMA.ammo.equals("mag_plasma"),
                "r28: магазины future-винтовок");
        h.assertTrue(!GunKind.LASER.launcher() && !GunKind.PLASMA.launcher(), "r28: future-винтовки не гранатомёты");
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_future", timeoutTicks = 20)
    public static void plasmaTankIsGunVehicle(GameTestHelper h) {
        VehicleKind k = VehicleKind.PLASMA_TANK;
        h.assertTrue(k.isGun() && k.tracked() && k.drivable(), "r28: Вихрь - гусеничная боевая машина");
        h.assertTrue(k.spec.id().equals("plasma_tank"), "r28: модель plasma_tank.glb");
        h.assertTrue(k.tubeLen > 0.0f, "r28: у Вихря есть ствол");
        h.assertTrue(Ballistics.Profile.PLASMA_BOLT.isShell() && !Ballistics.Profile.PLASMA_BOLT.kinetic(),
                "r28: плазменный сгусток - снаряд с энергетическим зарядом, не кинетический");
        h.succeed();
    }

    @GameTest(template = "arena", batch = "rw_future", timeoutTicks = 20)
    public static void futureAircraftContracts(GameTestHelper h) {
        ru.aiforge.realwar.craft.CraftKind.Heli hp = ru.aiforge.realwar.craft.CraftKind.PLASMA_HELI.heli;
        h.assertTrue(hp != null && hp.coaxial() && hp.tailR() == 0f, "r30: плазмолёт без хвостового винта (соосная схема)");
        h.assertTrue(ru.aiforge.realwar.craft.CraftKind.PLASMA_HELI.isHeli(), "r30: плазмолёт - вертолётный класс");
        ru.aiforge.realwar.craft.CraftKind.Plane sp = ru.aiforge.realwar.craft.CraftKind.STARSHIP.plane;
        h.assertTrue(sp != null && sp.jet() && sp.span() == 18f && sp.vmax() == 300f, "r30: звездолёт - реактивный, размах 18 м");
        h.succeed();
    }
}
